import { API_BASE } from "./config";

// 请求封装：自动带 token，401 跳登录
const BASE_URL = API_BASE;

interface RequestOptions {
  url: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  data?: any;
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  const token = uni.getStorageSync("token");
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || "GET",
      data: options.data,
      header: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          uni.removeStorageSync("token");
          uni.removeStorageSync("user");
          uni.reLaunch({ url: "/pages/login/login" });
          reject(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: (err) => reject(err),
    });
  });
}

export const api = {
  get: <T = any>(url: string) => request<T>({ url, method: "GET" }),
  post: <T = any>(url: string, data?: any) => request<T>({ url, method: "POST", data }),
  put: <T = any>(url: string, data?: any) => request<T>({ url, method: "PUT", data }),
  del: <T = any>(url: string) => request<T>({ url, method: "DELETE" }),
};
