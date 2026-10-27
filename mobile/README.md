# mobile —— uni-app 微信小程序（商家移动端）

美团商家 SaaS 的移动端，以**微信小程序**形式提供，让商家在手机上随时看经营数据、处理订单、回复顾客和 AI 客服。

## 模块功能

- **登录**：账号密码登录（预留微信 `code` 登录接口）
- **经营看板**：KPI 与图表速览
- **客服工作台**：会话列表、会话详情、消息收发、AI 自动/半自动回复
- **订单管理**：订单列表
- **商品管理**：商品列表
- **评价管理**：评价列表
- **预警中心**：预警列表
- **设置**：门店信息、AI 客服配置、修改密码
- **我的**：账号信息

## 技术栈

| 层 | 选型 |
|---|---|
| 框架 | uni-app（Vue 3） |
| 语言 | TypeScript |
| 构建 | Vite 5 + @dcloudio/vite-plugin-uni |
| 图表 | uCharts（`@qiun/ucharts`） |
| 多端 | 可编译到微信小程序 / H5 / 支付宝 / 抖音等 |
| HTTP | uni.request 封装（自动带 token、401 跳登录） |

## 目录结构

```
mobile/
├── src/
│   ├── main.ts               # 入口
│   ├── App.vue
│   ├── pages.json            # 页面路由 + tabBar
│   ├── manifest.json         # 应用配置（appid 等）
│   ├── utils/
│   │   ├── config.ts         # API 地址（H5 / 小程序区分）
│   │   ├── auth.ts           # 鉴权状态
│   │   └── request.ts        # uni.request 封装
│   ├── components/u-chart/   # 图表封装
│   └── pages/                # login/dashboard/service/orders/products/reviews/alerts/settings/mine
└── package.json
```

## 运行

```bash
cd mobile
npm install
npm run dev:mp-weixin     # 开发编译到微信小程序
npm run build:mp-weixin   # 生产构建
npm run dev:h5            # 编译到 H5
```

用微信开发者工具导入 `dist/dev/mp-weixin`（开发）或 `dist/build/mp-weixin`（构建）即可预览。

**API 地址说明**（`src/utils/config.ts`）：

- H5 开发：走 vite 代理，`API_BASE = /api/v1`
- 小程序真机：需改成后端可达地址（Mac 局域网 IP 或已备案 HTTPS 域名），手机与电脑连同一 WiFi

**appid 说明**：`src/manifest.json` 里的 appid（DCloud / 微信小程序）在仓库中保持空值，本地构建/预览时自行填写，**勿提交到 git**。

## 后续改进

- **微信登录打通**：后端 `jscode2session` 接口已就绪，前端补上 `wx.login` → `code` 换 token 流程
- **API 地址配置化**：当前非 H5 地址写死在 `config.ts`（含本地 IP），改为按环境配置 / 统一 HTTPS 域名
- **推送通知**：接入微信订阅消息，把「紧急客服消息 / 预警」推送到商家
- **图表升级**：u-chart 为第三方组件，评估是否需要替换/自封装
- **多端样式适配**：小程序 / H5 差异样式统一
- **测试**：补充关键页面测试
