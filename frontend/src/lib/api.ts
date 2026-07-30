// Talks to the Flask backend's JSON API (see ../../../api.py). The Flask app
// keeps the login session in a cookie, so every call here uses
// credentials: "include" so the browser sends/receives it even though the
// two dev servers run on different ports (localhost:3000 / localhost:5000).

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export type Product = {
  item_id: string;
  product_name: string;
  category: string | null;
  price: number;
};

export type PendingPurchase = {
  item_id: string;
  quantity: number;
  product_name: string;
  total: number;
} | null;

export type OrderItem = {
  product_id: string;
  product_name: string | null;
  quantity: number;
  unit_price: number;
};

export type Order = {
  order_id: string;
  items: OrderItem[];
  total_amount: number;
  timestamp: string | null;
};

export type MeResponse =
  | { authenticated: false }
  | { authenticated: true; email: string; balance: number | null };

export type BuyResult = {
  message: string;
  total_price: number;
  remaining_balance: number;
};

export type AssistantResult = {
  reply: string;
  trace: string[];
  pending_purchase: PendingPurchase;
};

class ApiError extends Error {}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiError("Could not reach the server. Is the Flask backend running?");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(data.error || `Request failed (${response.status}).`);
  }
  return data as T;
}

export const api = {
  me: () => apiFetch<MeResponse>("/api/me"),
  login: (email: string, password: string) =>
    apiFetch<{ email: string; balance: number | null }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => apiFetch<Record<string, never>>("/api/logout", { method: "POST" }),
  catalogue: () => apiFetch<{ products: Product[] }>("/api/catalogue"),
  buy: (item_id: string, quantity: number) =>
    apiFetch<BuyResult>("/api/buy", {
      method: "POST",
      body: JSON.stringify({ item_id, quantity }),
    }),
  assistant: (message: string) =>
    apiFetch<AssistantResult>("/api/assistant", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  orders: () => apiFetch<{ orders: Order[] }>("/api/orders"),
};

export { ApiError };
