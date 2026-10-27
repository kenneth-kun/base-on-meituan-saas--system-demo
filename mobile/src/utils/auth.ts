export interface AuthUser {
  type: string;
  username: string;
  merchant_id?: number;
  features: string[];
}

export function setAuth(token: string, user: AuthUser) {
  uni.setStorageSync("token", token);
  uni.setStorageSync("user", JSON.stringify(user));
}

export function getToken(): string {
  return uni.getStorageSync("token") || "";
}

export function getUser(): AuthUser | null {
  const u = uni.getStorageSync("user");
  return u ? JSON.parse(u) : null;
}

export function logout() {
  uni.removeStorageSync("token");
  uni.removeStorageSync("user");
}
