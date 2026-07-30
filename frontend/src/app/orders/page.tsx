"use client";

import { useEffect, useState } from "react";
import { api, ApiError, type Order } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function OrdersPage() {
  useRequireAuth();
  const { email } = useAuth();
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!email) return;
    api
      .orders()
      .then((data) => setOrders(data.orders))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong."));
  }, [email]);

  if (!email) return null;

  return (
    <>
      <div className="section-heading">
        <h1>Order History</h1>
        {orders && <span className="count">{orders.length} orders</span>}
      </div>

      <ErrorBanner message={error} />

      {orders === null && !error && <p>Loading order history...</p>}

      {orders && orders.length === 0 && <p>No orders yet - place one from the catalogue page.</p>}

      {orders?.map((order) => (
        <div className="order-card" key={order.order_id}>
          <h3>
            Order #{order.order_id}
            {order.timestamp ? ` - ${order.timestamp}` : ""}
          </h3>
          <table>
            <tbody>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Unit price</th>
                <th>Line total</th>
              </tr>
              {order.items.map((item, i) => (
                <tr key={i}>
                  <td>{item.product_name || item.product_id}</td>
                  <td>{item.quantity}</td>
                  <td>${item.unit_price.toFixed(2)}</td>
                  <td>${(item.unit_price * item.quantity).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="cart-total">
            Order total: <strong>${order.total_amount.toFixed(2)}</strong>
          </p>
        </div>
      ))}
    </>
  );
}
