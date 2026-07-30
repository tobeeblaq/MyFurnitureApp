"use client";

import { useState } from "react";
import type { Product } from "@/lib/api";

export function ProductCard({
  product,
  onBuy,
}: {
  product: Product;
  onBuy: (itemId: string, quantity: number) => Promise<void>;
}) {
  const [quantity, setQuantity] = useState(1);
  const [buying, setBuying] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBuying(true);
    try {
      await onBuy(product.item_id, quantity);
    } finally {
      setBuying(false);
    }
  };

  return (
    <div className="product-card">
      <p className="category">{product.category || "Furniture"}</p>
      <h3>{product.product_name}</h3>
      <p className="price">${product.price.toFixed(2)}</p>
      <form className="add-form" onSubmit={handleSubmit}>
        <input
          type="number"
          min={1}
          value={quantity}
          onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
          required
        />
        <button type="submit" disabled={buying}>
          {buying ? "Buying..." : "Buy"}
        </button>
      </form>
    </div>
  );
}
