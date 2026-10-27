"""AI 服务：意图识别 + 混合模式路由 + 回复生成（走 DeepSeek）。"""
import json

from .llm import LLMError, llm

INTENTS = ["商品咨询", "营业信息", "催单", "售后", "改地址", "闲聊"]

AUTO_INTENTS = {"商品咨询", "营业信息", "闲聊"}
SEMI_INTENTS = {"催单"}
MANUAL_INTENTS = {"售后", "改地址"}

_INTENT_PROMPT = """你是外卖商家客服的意图识别器，判断顾客消息属于哪种意图。

可选意图：
- 商品咨询：询问菜品、口味、辣度、食材、份量
- 营业信息：询问营业时间、地址、电话、发票、配送范围
- 催单：催促订单、问进度、还要多久送到
- 售后：退款、少送、错送、质量问题、投诉、不满意
- 改地址：修改地址、加备注、加餐具、改口味
- 闲聊：感谢、打招呼、表情

顾客消息：{message}

只返回 JSON，不要输出其他内容，格式：{{"intent": "意图名", "confidence": 0.0}}"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1:
            return json.loads(raw[s:e + 1])
        raise


def classify_intent(message: str) -> tuple[str, float]:
    raw = llm.chat(
        [{"role": "user", "content": _INTENT_PROMPT.format(message=message)}],
        temperature=0, json_mode=True, max_tokens=200,
    )
    data = _parse_json(raw)
    intent = data.get("intent", "闲聊")
    if intent not in INTENTS:
        intent = "闲聊"
    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    return intent, confidence


# ---- [LEGACY] 单轮版本（无 LLM 降级，失败直接抛错），已弃用 ----
# def generate_review_reply(rating: int, content: str) -> str:
#     if rating >= 4:
#         system = "你是外卖商家。顾客给了好评，请回复一句真诚简短的感谢（30字以内，不喊口号）。"
#     else:
#         system = "你是外卖商家。顾客给了差评，请回复一句诚恳的道歉与改进表态（40字以内，不推卸责任、不承诺具体赔偿金额）。"
#     user = f"评价内容：{content or '（无文字）'}"
#     return llm.chat(
#         [{"role": "system", "content": system}, {"role": "user", "content": user}],
#         temperature=0.7, max_tokens=200,
#     )

# ---- [LEGACY] 差评不引用商家 SOP 话术，已弃用 ----
# def generate_review_reply(rating: int, content: str) -> str:
#     if rating >= 4:
#         system = "你是外卖商家。顾客给了好评，请回复一句真诚简短的感谢（30字以内，不喊口号）。"
#     else:
#         system = "你是外卖商家。顾客给了差评，请回复一句诚恳的道歉与改进表态（40字以内，不推卸责任、不承诺具体赔偿金额）。"
#     user = f"评价内容：{content or '（无文字）'}"
#     try:
#         return llm.chat(
#             [{"role": "system", "content": system}, {"role": "user", "content": user}],
#             temperature=0.7, max_tokens=200,
#         )
#     except LLMError:
#         if rating >= 4:
#             return "感谢您的支持，我们会继续努力！（AI 生成暂不可用，请酌情修改）"
#         return "非常抱歉给您带来不好的体验，我们已记录并会尽快改进。（AI 生成暂不可用，请酌情修改）"

def generate_review_reply(rating: int, content: str, sop_text: str = "") -> str:
    """生成评价回复草稿；差评会引用商家 SOP 话术规范。LLM 不可用时降级返回兜底文案。"""
    if rating >= 4:
        system = "你是外卖商家。顾客给了好评，请回复一句真诚简短的感谢（30字以内，不喊口号）。"
    else:
        base = ("收到差评时：先真诚道歉、不推卸责任、不辩解，不承诺具体赔偿金额，"
                "必要时引导顾客电话或到店沟通。")
        if sop_text:
            base += f"\n参考商家服务规范：\n{sop_text}"
        system = "你是外卖商家。" + base + "（40字以内）"
    user = f"评价内容：{content or '（无文字）'}"
    try:
        return llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7, max_tokens=200,
        )
    except LLMError:
        # 降级：LLM 挂了也给商家一个可手动调整的草稿，避免前端 502
        if rating >= 4:
            return "感谢您的支持，我们会继续努力！（AI 生成暂不可用，请酌情修改）"
        tail = "请参考店内服务规范妥善处理。" if sop_text else ""
        return f"非常抱歉给您带来不好的体验，我们已记录并会尽快改进。{tail}（AI 生成暂不可用，请酌情修改）"


def _build_messages(system: str, history: list[dict] | None, message: str) -> list[dict]:
    """组装多轮消息：system + 历史轮次(user/assistant) + 当前用户消息。"""
    messages = [{"role": "system", "content": system}]
    for h in (history or []):
        role = h.get("role")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    return messages


# ---- [LEGACY] 单轮版本（不接收 history），已弃用 ----
# def _auto_reply(message: str, faqs: list[dict], business_info: str) -> str:
#     faq_text = "\n".join(f"问：{f['question']}\n答：{f['answer']}" for f in faqs) if faqs else "（无）"
#     system = (
#         "你是外卖商家的客服，用友好、简短、口语化的语气回复顾客，一般不超过60字。\n"
#         "只依据下面的店铺信息和常见问题回答，不要编造其中没有的内容。\n"
#         f"【店铺信息】\n{business_info}\n"
#         f"【常见问题】\n{faq_text}"
#     )
#     return llm.chat(
#         [{"role": "system", "content": system}, {"role": "user", "content": message}],
#         temperature=0.5, max_tokens=300,
#     )

def _auto_reply(message: str, faqs: list[dict], business_info: str, history: list[dict] | None = None) -> str:
    """自动回复（咨询/营业/闲聊）；支持多轮上下文。"""
    faq_text = "\n".join(f"问：{f['question']}\n答：{f['answer']}" for f in faqs) if faqs else "（无）"
    system = (
        "你是外卖商家的客服，用友好、简短、口语化的语气回复顾客，一般不超过60字。\n"
        "只依据下面的店铺信息和已检索到的相关知识回答，不要编造其中没有的内容。\n"
        f"【店铺信息】\n{business_info}\n"
        f"【相关知识（已检索 top-k）】\n{faq_text}"
    )
    messages = _build_messages(system, history, message)
    return llm.chat(messages, temperature=0.5, max_tokens=300)


# ---- [LEGACY] 单轮版本（不接收 history），已弃用 ----
# def _order_draft(message: str, order_info: str | None) -> str:
#     ctx = f"顾客当前订单状态：{order_info}" if order_info else "顾客当前订单状态：制作中"
#     system = (
#         "你是外卖商家客服。顾客在催单，请安抚并告知进度。\n"
#         f"{ctx}\n"
#         "用简短友好的语气；不要承诺具体送达时间（除非信息里有）；不要承诺赔偿。"
#     )
#     return llm.chat(
#         [{"role": "system", "content": system}, {"role": "user", "content": message}],
#         temperature=0.5, max_tokens=300,
#     )

def _order_draft(message: str, order_info: str | None, history: list[dict] | None = None) -> str:
    """催单草稿；支持多轮上下文。"""
    ctx = f"顾客当前订单状态：{order_info}" if order_info else "顾客当前订单状态：制作中"
    system = (
        "你是外卖商家客服。顾客在催单，请安抚并告知进度。\n"
        f"{ctx}\n"
        "用简短友好的语气；不要承诺具体送达时间（除非信息里有）；不要承诺赔偿。"
    )
    messages = _build_messages(system, history, message)
    return llm.chat(messages, temperature=0.5, max_tokens=300)


def _manual_guide(business_info: str) -> str:
    return "您的问题已转交人工客服处理，请稍等。如需紧急处理，可直接拨打商家电话。"


def match_faq(message: str, faqs: list[dict]) -> dict | None:
    """关键词匹配 FAQ，命中返回 {answer, score}，未命中返回 None。

    兼容 keywords 为「逗号分隔字符串」或「列表」两种形态。
    """
    best = None
    for faq in faqs:
        raw = faq.get("keywords") or ""
        kws = raw.split(",") if isinstance(raw, str) else list(raw)
        score = 0
        for kw in kws:
            kw = kw.strip()
            if len(kw) >= 2 and kw in message:
                score += len(kw)  # 命中的关键词越长权重越高
        if score > 0 and (best is None or score > best["score"]):
            best = {"answer": faq["answer"], "score": score}
    return best


# ---- [LEGACY] 旧版：把全部 FAQ 塞入 prompt，未做向量检索，已弃用 ----
# def handle_im_message(
#     message: str,
#     faqs: list[dict],
#     business_info: str,
#     order_info: str | None = None,
#     history: list[dict] | None = None,
# ) -> dict:
#     match = match_faq(message, faqs)
#     if match:
#         return {... "source": "faq"}
#     try:
#         intent, confidence = classify_intent(message)
#         ...
#     return {... "source": "llm"}

def handle_im_message(
    message: str,
    knowledge_items: list[dict] | None = None,
    business_info: str = "",
    order_info: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """RAG 混合模式：
    1) 关键词快速命中（在向量召回的 top-k 结果上做子串匹配，仍零 LLM）；
    2) 未命中 → 把召回的 top-k 作为检索上下文交给 LLM 作答（来源标注 rag）。
    knowledge_items: retrieve_knowledge 返回的已排序 top-k 知识条目（可含 faq/rule/greeting）。
    """
    knowledge_items = knowledge_items or []

    # 1. 关键词快速命中
    match = match_faq(message, knowledge_items)
    if match:
        return {
            "intent": "FAQ命中",
            "confidence": 1.0,
            "action": "auto",
            "status": "sent",
            "reply": match["answer"],
            "source": "faq",
        }

    # 2. 未命中 → LLM 混合路由（带降级），召回的 top-k 作为上下文
    try:
        intent, confidence = classify_intent(message)
        if intent in AUTO_INTENTS:
            action, status = "auto", "sent"
            reply = _auto_reply(message, knowledge_items, business_info, history=history)
        elif intent in SEMI_INTENTS:
            action, status = "semi", "pending"
            reply = _order_draft(message, order_info, history=history)
        else:
            action, status = "manual", "manual"
            reply = _manual_guide(business_info)
    except LLMError:
        # LLM 失败/熔断 → 降级：转人工兜底，不让整条请求 502
        return {
            "intent": "降级兜底",
            "confidence": 0.0,
            "action": "manual",
            "status": "manual",
            "reply": "客服暂时繁忙，请稍后再试，或直接拨打商家电话。",
            "source": "degraded",
        }
    return {
        "intent": intent,
        "confidence": round(confidence, 2),
        "action": action,
        "status": status,
        "reply": reply,
        "source": "rag",
    }
