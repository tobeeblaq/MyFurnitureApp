"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, type Product } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { ErrorBanner } from "@/components/ErrorBanner";
import { ProductCard } from "@/components/ProductCard";

export default function CataloguePage() {
  useRequireAuth();
  const { email, refresh } = useAuth();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!email) return;
    api
      .catalogue()
      .then((data) => setProducts(data.products))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong."));
  }, [email]);

  const handleBuy = async (itemId: string, quantity: number) => {
    setError(null);
    setNotice(null);
    try {
      const result = await api.buy(itemId, quantity);
      setNotice(`${result.message} Remaining balance: $${result.remaining_balance.toFixed(2)}.`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  };

  if (!email) return null;

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <p className="hero-eyebrow">Real inventory - Live pricing</p>
          <h1>
            Furnish Your <em>Everyday</em> Space
          </h1>
          <p>
            Every item below comes straight from the shop&apos;s live catalogue - the
            price, and your balance, are both real.
          </p>
          <div className="hero-actions">
            <Link href="/assistant" className="btn">
              Ask the Assistant
            </Link>
            <a href="#catalogue" className="btn btn-outline">
              Browse Catalogue
            </a>
          </div>
          <div className="trust-row">
            <div className="trust-item">
              <span className="trust-dot" />
              {products ? products.length : "..."} live items
            </div>
            <div className="trust-item">
              <span className="trust-dot" />
              Real balance
            </div>
            <div className="trust-item">
              <span className="trust-dot" />
              Real checkout
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path
                d="M4 13V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M3 13h18v3a1 1 0 0 1-1 1h-1v3h-2v-3H6v3H4v-3H3a1 1 0 0 1 0-1z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M6 6V4h2M18 6V4h-2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>
      </section>

      <ErrorBanner message={error} />
      {notice && (
        <ul className="flash">
          <li>{notice}</li>
        </ul>
      )}

      <div className="section-heading" id="catalogue">
        <h2>Catalogue</h2>
        {products && <span className="count">{products.length} items</span>}
      </div>

      {products === null && !error && <p>Loading catalogue...</p>}

      {products && products.length > 0 && (
        <div className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.item_id} product={product} onBuy={handleBuy} />
          ))}
        </div>
      )}

      {products && products.length === 0 && <p>No products to show right now.</p>}
    </>
  );
}
