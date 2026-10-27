# 美团商家 SaaS

面向**单店/小店**的美团外卖商家经营工具，用「运营提效 + 数据看板 + AI 客服」三件事，帮不懂数据分析的小商家「看得懂生意、省掉重复操作、雇不起客服也能秒回顾客」。

> 产品需求与决策记录见 [requirements.md](requirements.md)

## 三大核心支柱

| 支柱 | 说明 |
|---|---|
| **数据看板（BI）** | 营业额 / 订单 / 客单价 / 复购 / 口碑，一张图看懂生意 |
| **运营提效** | 订单批量接单、商品批量上下架 / 改价 |
| **AI 客服** | 美团 IM 混合模式自动回复（全自动 / 半自动 / 转人工）+ 评价自动回复 |

## 项目结构

```
meituan-saas/
├── README.md               # 本文档（项目总览 + 运行 + 部署）
├── requirements.md         # 需求文档（产品决策的单一事实来源）
├── backend/                # Python FastAPI 后端（REST API + AI + 定时刷新）
│   └── README.md
├── frontend/               # Vue 3 管理端（PC Web，商家 + 平台管理员）
│   └── README.md
└── mobile/                 # uni-app 微信小程序（商家移动端）
    └── README.md
```

每个子模块的 README 都包含：模块功能、技术栈、目录结构、运行方式、后续改进。

## 功能总览

- **经营看板**：KPI 汇总（营业额/订单/客单价 + 环比）、营业额趋势、商品热销/滞销/售罄榜、评分趋势、好评/差评词频
- **分析**：订单时段分布、评分分布、好评率/差评率趋势
- **订单管理**：列表筛选/分页、详情、批量一键接单
- **商品管理**：分类、筛选、批量上下架、批量改价
- **评价管理**：列表筛选、AI 回复草稿、手动回复
- **预警中心**：订单骤降 / 差评激增 / 评分跌破 / 热销售罄，标记已处理
- **AI 客服**：意图识别 + 混合模式路由（咨询全自动 / 催单半自动 / 售后转人工）+ RAG 知识库检索
- **管理系统**（平台管理员）：套餐、商家、商家账号、订阅管理 + 功能点/配额权限
- **设置**：门店信息、知识库 FAQ、AI 客服阈值、修改密码

## 技术栈总览

| 层 | 选型 |
|---|---|
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 鉴权 | bcrypt + JWT |
| 数据库 | SQLite（开发）/ PostgreSQL（生产，改 `.env`） |
| 定时任务 | APScheduler（进程内） |
| AI | DeepSeek（OpenAI 兼容接口，带熔断降级） |
| Embedding / RAG | 本地 jieba + 哈希词袋（默认，可切 OpenAI 兼容接口） |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + ECharts |
| 移动端 | uni-app（Vue 3）+ TypeScript + uCharts |
| 仿真数据 | Faker（`MockAdapter` 生成 90 天经营数据） |

## 快速开始（本地开发）

### 1. 后端（Python 3.12）

```bash
cd backend

# 建虚拟环境 + 装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 生成仿真数据（会 drop_all 重建表，写入 90 天订单/评价/商品等）
python -m scripts.seed_mock_data

# 初始化管理系统数据（管理员 / 套餐 / 商家账号 / 订阅）
python -m scripts.seed_admin

# 启动服务
uvicorn app.main:app --reload --port 8000
```

> 顺序不能反：先 `seed_mock_data`（建商家/门店/商品/订单），再 `seed_admin`（给已有商家建账号和订阅）。

默认账号：

| 角色 | 账号 | 密码 |
|---|---|---|
| 平台管理员 | `admin` | `admin123` |
| 商家 | `merchant1` | `123456` |

验证：

- 健康检查：<http://localhost:8000/health>
- 交互文档（Swagger）：<http://localhost:8000/docs>

### 2. 前端管理端（Node ≥ 18）

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

开发时前端 `/api` 会自动代理到后端 `8000` 端口（见 `vite.config.ts`）。

### 3. 移动端小程序（微信开发者工具）

```bash
cd mobile
npm install
npm run dev:mp-weixin        # 或 npm run build:mp-weixin
```

用微信开发者工具导入 `mobile/dist/dev/mp-weixin`（或 `dist/build/mp-weixin`）即可预览。

- H5 开发走 vite 代理（`/api/v1`）
- 小程序真机调试需把 `mobile/src/utils/config.ts` 里的 `API_BASE` 改成后端可达地址（Mac 局域网 IP 或已备案 HTTPS 域名）

## 部署方法

### 后端（裸机 + Nginx）

```bash
cd backend
pip install -r requirements.txt

# 生产环境变量（写入 .env）
#   DATABASE_URL=postgresql+psycopg://user:pass@host:5432/meituan_saas
#   JWT_SECRET=<随机长字符串，务必替换默认值>
#   DEEPSEEK_API_KEY=sk-xxx
#   WX_APPID=... / WX_SECRET=...
#   REFRESH_INTERVAL_MINUTES=5

python -m scripts.seed_mock_data
python -m scripts.seed_admin

# 生产启动（注意：先单 worker，见下方「注意事项」）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **注意事项**：定时刷新使用进程内 `BackgroundScheduler`。若用 `--workers N`（N>1）多进程部署，每个进程都会跑一套调度器，导致数据被重复刷新。当前阶段请**单 worker** 部署；后续把调度器拆成独立进程后再多 worker 横向扩展（见 backend README 的「后续改进」）。

### 前端（构建静态产物 + Nginx）

```bash
cd frontend
npm install
npm run build        # 产物在 dist/
```

把 `dist/` 上传到任意静态服务器（Nginx 为例）：

```nginx
server {
    listen 80;
    server_name admin.example.com;

    root /var/www/meituan-saas-frontend/dist;
    index index.html;

    # Vue Router history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端接口反向代理（前端 baseURL 是相对路径 /api/v1）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 移动端小程序

1. `npm run build:mp-weixin` 生成小程序产物
2. 微信开发者工具导入并上传
3. 在小程序后台配置**合法域名**（request 域名）指向后端 HTTPS 域名（小程序要求 HTTPS + 已备案域名）
4. 把 `mobile/src/utils/config.ts` 的 `API_BASE` 改为该 HTTPS 域名后重新构建

### 生产环境变量清单（后端 `.env`）

| 变量 | 说明 | 默认 |
|---|---|---|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./meituan_saas.db` |
| `JWT_SECRET` | JWT 签名密钥（**生产必改**） | `dev-secret-change-me-in-production` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 空（未配置则 AI 降级） |
| `DEEPSEEK_MODEL` | 模型名 | `deepseek-chat` |
| `EMBEDDING_PROVIDER` | `local` / `openai` | `local` |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` / `EMBEDDING_MODEL` | OpenAI 兼容 embedding 接口 | 空 |
| `EMBEDDING_DIM` | embedding 维度 | `1024` |
| `JWT_EXPIRE_DAYS` | token 有效期（天） | `7` |
| `REFRESH_INTERVAL_MINUTES` | 定时刷新间隔（分钟） | `5` |
| `WX_APPID` / `WX_SECRET` | 微信小程序 appid/secret（登录用） | 空 |

> 生产上线前请务必：替换 `JWT_SECRET`、把 CORS `allow_origins` 收紧为具体域名、将 `.env` 加入 `.gitignore`（含真实微信密钥）。

## 文档索引

- [backend/README.md](backend/README.md) —— 后端模块
- [frontend/README.md](frontend/README.md) —— 前端管理端
- [mobile/README.md](mobile/README.md) —— 移动端小程序
- [requirements.md](requirements.md) —— 需求与决策记录
