// 后端 API 地址
// H5 开发：走 vite 代理（localhost:8000）
// 小程序真机：用 Mac 局域网 IP，手机和电脑连同一 WiFi
// #ifdef H5
export const API_BASE = "/api/v1";
// #endif
// #ifndef H5
export const API_BASE = "http://192.168.8.74:8000/api/v1";
// #endif
