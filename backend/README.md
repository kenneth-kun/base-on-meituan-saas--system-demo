# backend —— Python FastAPI 后端

美团商家 SaaS 的服务端，对外提供 REST API，负责鉴权、业务逻辑、AI 客服、数据刷新与数据落库。前端管理端与移动端小程序都通过它读写数据。

## 模块功能

- **鉴权与权限**
  - 账号密码登录（bcrypt 哈希校验 + JWT），区分「平台管理员 / 商家」两类身份
  - 微信小程序 `code` 登录 + openid 绑定（`/auth/wx-login`、`/auth/wx-bind`）
  - 套餐功能点校验（`require_feature`）+ AI 调用配额校验（`consume_quota`）
- **经营看板**：KPI 汇总、营业额趋势、商品热销/滞销/售罄榜、评分趋势、好评/差评词频
- **分析**：订单时段分布、评分分布、好评率/差评率趋势
- **订单 / 商品 / 评价**：列表筛选/分页、批量接单、批量上下架/改价、评价回复
- **AI 客服**：意图识别 + 混合模式路由（全自动/半自动/转人工）+ RAG 知识库检索 + 多轮上下文 + 紧急消息标记
- **预警中心**：预警列表、标记已处理
- **管理系统**（平台管理员）：套餐 / 商家 / 商家账号 / 订阅的 CRUD
- **数据刷新**：APScheduler 定时 + 手动触发，从 `MockAdapter` 拉取新订单/评价并聚合营业日报

## 技术栈

| 层 | 选型 |
|---|---|
| 语言 / 框架 | Python 3.12、FastAPI、Uvicorn |
| ORM | SQLAlchemy 2.0（声明式 + `Mapped`） |
| 校验 / 配置 | Pydantic v2 + pydantic-settings（读 `.env`） |
| 鉴权 | PyJWT + bcrypt |
| 数据库 | SQLite（开发）/ PostgreSQL（生产，改 `DATABASE_URL`） |
| 定时任务 | APScheduler（进程内 `BackgroundScheduler`） |
| AI | DeepSeek（OpenAI 兼容接口，httpx 客户端 + 熔断降级） |
| Embedding / RAG | 可替换 `EmbeddingProvider`：本地 jieba + 哈希词袋（默认）/ OpenAI 兼容接口 |
| 中文分词 | jieba（评价词频、本地 embedding） |
| 仿真数据 | Faker（`MockAdapter`） |

**关键抽象 —— 多平台 Adapter**：业务层只依赖 `PlatformAdapter` 统一接口（拉订单/商品/评价/营业数据/改价/上下架/收发消息），当前只有 `MockAdapter` 实现；未来接美团/饿了么/抖音只需新增一个 adapter，业务层零改动。

## 目录结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口 + CORS + 全局异常处理 + 定时调度
│   ├── config.py            # Settings（读 .env）
│   ├── database.py          # SQLAlchemy engine / session / init_db
│   ├── deps.py              # 鉴权与权限依赖（get_current_user / require_admin / require_feature ...）
│   ├── models/              # 数据模型（15 张表）
│   │   ├── core.py          # 平台/商家/门店/分类/商品/顾客
│   │   ├── trade.py         # 订单/订单明细/评价/营业日报
│   │   ├── management.py    # 管理员/商家账号/套餐/订阅/配额用量
│   │   ├── engagement.py    # 预警/会话/顾客消息/AI回复记录/知识库
│   │   └── enums.py         # 枚举
│   ├── schemas/             # Pydantic 响应模型
│   ├── adapters/            # PlatformAdapter 抽象 + MockAdapter 实现
│   ├── services/            # 业务服务
│   │   ├── auth.py          # 密码哈希 + JWT
│   │   ├── llm.py           # DeepSeek 客户端（熔断）
│   │   ├── ai.py            # 意图识别 + 混合路由 + 回复生成
│   │   ├── quota.py         # AI 配额扣减
│   │   ├── refresh.py       # 定时刷新（拉订单/聚合日报）
│   │   ├── knowledge.py     # RAG 向量召回
│   │   └── embeddings.py    # 本地/OpenAI 兼容 embedding
│   └── api/                 # 路由（health/auth/dashboard/orders/products/reviews/alerts/ai/im/admin/analytics/settings/refresh）
├── scripts/
│   ├── seed_mock_data.py    # 生成 90 天仿真数据写入数据库
│   └── seed_admin.py        # 初始化管理员/套餐/商家账号/订阅
├── requirements.txt
└── .env.example             # 环境变量示例
```

## 运行

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m scripts.seed_mock_data   # 先建业务数据
python -m scripts.seed_admin       # 再建管理员/套餐/账号/订阅

uvicorn app.main:app --reload --port 8000
```

- Swagger 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

## 环境变量（`.env`）

见根目录 README 的「生产环境变量清单」。开发阶段默认值即可跑通；AI 功能需配置 `DEEPSEEK_API_KEY`（未配置时 AI 回复会降级为兜底文案）。

## 后续改进

- **多平台 Adapter**：接入真实美团 API，替换 `MockAdapter`
- **调度器独立化**：进程内 `BackgroundScheduler` 在多 worker 下会重复刷新 → 迁移到独立进程（Celery / 独立 APScheduler 进程）
- **配额原子化**：`used_count` 当前是「读-改-写」非原子，并发可突破上限；改为 `UPDATE ... WHERE used_count < limit` 原子扣减，且调用成功后再扣
- **健壮性**：`payload: dict` 直接取值，多处 `Decimal(str(x))` / `date.fromisoformat` 对脏输入会 500 → 补 Pydantic 请求模型 + 参数校验
- **安全**：`JWT_SECRET` 默认值硬编码、`.env` 含真实微信密钥 → 生产强制校验 + 密钥轮换；登录加限流
- **Embedding 升级**：本地哈希词袋替换为真实 embedding 模型（结构已预留）
- **测试**：补充单元测试 / 接口测试
