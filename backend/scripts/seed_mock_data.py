"""生成 Mock 数据并写入数据库。

用法（在 backend 目录下）:
    python -m scripts.seed_mock_data
"""
from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

# 兼容 `python scripts/seed_mock_data.py` 直接执行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.adapters.mock import MockAdapter
from app.database import SessionLocal, engine, init_db
from app.models import (Alert, Base, Category, Customer, CustomerMessage,
                        DailyMetric, KnowledgeItem, Merchant, Order, OrderItem,
                        Platform, Product, ReplyRecord, Review, Session, Store)
from app.models.enums import AlertLevel, AlertStatus, KnowledgeType


def _phone_hash(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:16]


FAQS = [
    ("你们营业时间是几点？", "本店营业时间 10:00-22:00，最后一单 21:30 截止。", "营业时间,几点,关门,开门"),
    ("能开发票吗？", "可以开电子发票，下单备注或联系商家即可。", "发票,开票"),
    ("配送范围是多大？", "以店铺为中心约 3 公里，超出范围可能无法配送。", "配送范围,配送,范围,多远"),
    ("有不辣的菜吗？", "有的，招牌炒饭、卤肉饭、水饺都可以做不辣。", "不辣,辣吗,辣不辣,微辣,清淡"),
    ("可以备注忌口吗？", "可以，下单时在备注里写明，我们会尽量满足。", "忌口,备注"),
    ("打包费怎么收？", "每单打包费 1-2 元，具体以结算页为准。", "打包费,打包"),
    ("怎么申请退款？", "请在美团订单页申请退款，我们会尽快处理。", "申请退款,怎么退款,如何退款"),
    ("客服电话是多少？", "商家电话 13800000000，急事请直接拨打。", "电话,联系方式,手机号"),
]


def seed(seed: int = 42, days: int = 90) -> None:
    Base.metadata.drop_all(bind=engine)  # 清空旧数据，保证可重复播种
    init_db()
    adapter = MockAdapter(seed=seed)
    dataset = adapter.generate_dataset(days=days)

    db = SessionLocal()
    try:
        # 1. 平台 / 商家 / 门店
        platform = Platform(code="meituan", name="美团外卖")
        db.add(platform)
        db.flush()
        merchant = Merchant(name="测试商家", phone="13800000000")
        db.add(merchant)
        db.flush()
        store = Store(merchant_id=merchant.id, platform_id=platform.id,
                      name="测试门店", address="北京市朝阳区测试路1号",
                      business_hours="10:00-22:00", phone="13800000000")
        db.add(store)
        db.flush()

        # 2. 分类 + 商品
        category_map = {}
        for name in adapter.categories:
            cat = Category(store_id=store.id, name=name)
            db.add(cat)
            category_map[name] = cat
        db.flush()

        product_map = {}
        for p in dataset["products"]:
            prod = Product(store_id=store.id, category_id=category_map[p.category].id,
                           name=p.name, app_food_code=p.app_food_code,
                           price=p.price, stock=p.stock, status=p.status)
            db.add(prod)
            product_map[p.name] = prod
        db.flush()

        # 3. 顾客（按首次出现顺序，记录 first_order_at）
        customer_first: dict[str, object] = {}
        for o in dataset["orders"]:
            if o.customer_phone not in customer_first:
                customer_first[o.customer_phone] = o.placed_at

        customer_map = {}
        for phone, first_at in customer_first.items():
            cust = Customer(store_id=store.id, phone_hash=_phone_hash(phone),
                            first_order_at=first_at)
            db.add(cust)
            customer_map[phone] = cust
        db.flush()

        # 4. 订单 + 明细 + 评价
        sales: dict[str, int] = defaultdict(int)
        orders_to_add = []
        for o in dataset["orders"]:
            cust = customer_map[o.customer_phone]
            items = [OrderItem(product_id=product_map[it.product_name].id,
                               qty=it.qty, unit_price=it.unit_price)
                     for it in o.items]
            for it in o.items:
                sales[it.product_name] += it.qty
            order = Order(store_id=store.id, customer_id=cust.id, order_no=o.order_no,
                          wm_order_id_view=o.wm_order_id_view,
                          status=o.status, total_amount=o.total_amount,
                          commission=o.commission, subsidy=o.subsidy,
                          delivery_fee=o.delivery_fee, placed_at=o.placed_at,
                          is_valid=o.is_valid, items=items,
                          recipient_name=o.recipient_name,
                          recipient_phone=o.recipient_phone,
                          recipient_address=o.recipient_address,
                          original_price=o.original_price)
            if o.review is not None:
                order.review = Review(store_id=store.id, rating=o.review.rating,
                                      accurate_star=o.review.accurate_star,
                                      consume_amount=o.review.consume_amount,
                                      content=o.review.content,
                                      tags=",".join(o.review.tags),
                                      created_at=o.review.created_at)
            orders_to_add.append(order)
        db.add_all(orders_to_add)

        # 5. 营业日报（预聚合表）
        for m in dataset["daily_metrics"]:
            db.add(DailyMetric(store_id=store.id, date=m.date, revenue=m.revenue,
                               order_count=m.order_count,
                               valid_order_count=m.valid_order_count,
                               new_customer_count=m.new_customer_count,
                               return_customer_count=m.return_customer_count,
                               exposure=m.exposure, visits=m.visits,
                               orders_funnel=m.orders_funnel))

        # 6. 商品销量 + 热销品售罄异常（销量最高库存归零）
        for name, s in sales.items():
            product_map[name].sales = s
        top_name = max(sales, key=sales.get)
        product_map[top_name].stock = 0

        # 7. 知识库
        for q, a, kws in FAQS:
            db.add(KnowledgeItem(store_id=store.id, type=KnowledgeType.faq.value,
                                 question=q, answer=a, keywords=kws))

        # 7.1 SOP 话术规范（type=rule）：差评/投诉回复时由 RAG 检索引用
        SOPS = [
            ("差评处理规范", "收到差评先真诚道歉，不推卸责任、不辩解；不承诺具体赔偿金额；"
                            "引导顾客电话沟通或到店补偿。", "差评,投诉,道歉,赔偿"),
            ("退款处理规范", "先安抚顾客，核对订单后在美团后台发起退款；金额争议上报店长。",
             "退款,退回,少送,错送"),
            ("食品安全应急", "遇食品安全类投诉（异物、拉肚子、过期）立即标记紧急并转人工，"
                            "禁止 AI 自动回复，第一时间联系顾客并留存证据。",
             "食品安全,异物,拉肚子,过期,中毒"),
        ]
        for q, a, kws in SOPS:
            db.add(KnowledgeItem(store_id=store.id, type=KnowledgeType.rule.value,
                                 question=q, answer=a, keywords=kws))

        # 8. 示例预警（对应注入的异常）
        db.add(Alert(store_id=store.id, rule="订单骤降", level=AlertLevel.critical.value,
                     status=AlertStatus.open.value,
                     payload="3天前订单量较近7天同时段均值下降超过30%"))
        db.add(Alert(store_id=store.id, rule="差评激增", level=AlertLevel.warning.value,
                     status=AlertStatus.open.value, payload="昨日新增3条差评"))

        # 9. IM 会话 + 顾客消息
        message_objs = []
        session_map = {}
        for m in dataset["messages"]:
            sess = session_map.get(m.customer_phone)
            if sess is None:
                cust = customer_map.get(m.customer_phone)
                if cust is None:
                    continue
                sess = Session(store_id=store.id, customer_id=cust.id,
                               order_id=None, status="open")
                db.add(sess)
                db.flush()
                session_map[m.customer_phone] = sess
            msg = CustomerMessage(session_id=sess.id, store_id=store.id,
                                  content=m.content, direction="inbound",
                                  msg_id=m.msg_id, scene_tag=m.scene_tag,
                                  wm_order_id=m.order_no,
                                  is_urgent=(m.scene_tag in ("售后", "少送", "食品安全")),
                                  created_at=m.created_at)
            db.add(msg)
            message_objs.append(msg)

        # 10. 示例 AI 回复记录（催单 → 半自动草稿，待确认）
        for msg in message_objs:
            if "好了没" in msg.content or "还要多久" in msg.content:
                db.add(ReplyRecord(message_id=msg.id, intent="催单", confidence=0.9,
                                   ai_content="您的订单正在制作中，预计还需约10分钟送达，请稍等～",
                                   status="pending"))
                break

        db.commit()

        # 汇总输出
        n_orders = len(orders_to_add)
        n_customers = len(customer_map)
        n_reviews = sum(1 for o in orders_to_add if o.review is not None)
        print(f"✅ 种子数据已写入。")
        print(f"   商品 {len(product_map)} / 顾客 {n_customers} / 订单 {n_orders} / 评价 {n_reviews}")
        print(f"   营业日报 {len(dataset['daily_metrics'])} 天 / IM 消息 {len(message_objs)} 条")
        print(f"   热销售罄商品: {top_name}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
