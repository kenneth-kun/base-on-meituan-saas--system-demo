# frontend —— Vue 3 管理端（PC Web）

美团商家 SaaS 的 Web 管理端，面向**商家**和**平台管理员**两类用户，提供经营看板、运营提效与 AI 客服的桌面端操作界面。

## 模块功能

- **登录**：账号密码登录，区分商家 / 平台管理员
- **经营看板**：KPI 卡（营业额/订单/客单价 + 环比）、营业额趋势、商品热销/滞销/售罄榜、评分趋势、好评/差评词频
- **趋势分析**：订单时段分布、评分分布、好评率/差评率趋势
- **口碑分析**：好评 / 差评词频洞察
- **订单管理**：列表筛选/分页、订单详情、批量一键接单
- **商品管理**：分类筛选、批量上下架、批量改价
- **评价管理**：按星级/回复状态筛选、AI 生成回复草稿、手动回复
- **预警中心**：预警列表、标记已处理
- **客服工作台**：会话列表、消息收发、AI 自动/半自动回复
- **设置**：门店信息、知识库 FAQ、AI 客服阈值
- **管理后台**（管理员）：套餐、商家、商家账号、订阅管理

## 技术栈

| 层 | 选型 |
|---|---|
| 框架 | Vue 3（`<script setup>` 组合式 API） |
| 语言 | TypeScript |
| 构建 | Vite 5 |
| UI 组件库 | Element Plus + @element-plus/icons-vue |
| 图表 | ECharts 5 |
| 路由 | Vue Router 4（history 模式） |
| HTTP | Axios（拦截器自动带 token、401 跳登录） |
| 样式 | 自定义主题 token（`src/styles/theme.css`） |

## 目录结构

```
frontend/
├── index.html
├── vite.config.ts            # 开发代理：/api → http://localhost:8000
├── src/
│   ├── main.ts               # 入口，挂载 Element Plus
│   ├── App.vue
│   ├── auth.ts               # 鉴权状态（token + 用户 + 功能点）
│   ├── router/index.ts       # 路由 + 登录/管理员守卫
│   ├── api/index.ts          # Axios 客户端 + 全部接口封装
│   ├── components/           # KpiCard、EChart 封装
│   ├── styles/theme.css      # 可视化主题 token
│   └── views/                # 页面（Dashboard/Orders/Products/Reviews/Alerts/Service/Settings/Admin/Trend/Reputation/Login）
└── package.json
```

## 运行

```bash
cd frontend
npm install
npm run dev        # 开发，http://localhost:5173
npm run build      # 生产构建，产物在 dist/
npm run preview    # 预览构建产物
```

开发时 `/api` 会通过 vite 代理到后端 `8000` 端口，无需手动改地址。

## 后续改进

- **状态管理**：鉴权状态目前是模块级 `reactive`，规模上来后引入 Pinia
- **权限粒度**：目前只做了「是否有功能点」的路由/菜单级控制，可细化到按钮级
- **组件复用**：列表页有较多重复的筛选/分页/表格逻辑，抽取通用列表组件
- **类型安全**：接口响应多数用 `any`，补全类型定义
- **响应式与移动适配**：当前面向桌面，未做窄屏适配
- **测试**：补充组件 / E2E 测试
