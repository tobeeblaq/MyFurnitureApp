"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { email, balance, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Even if the backend call fails, the user still wants to leave -
      // don't strand them on the page over a network hiccup.
    }
    router.push("/login");
  };

  return (
    <>
      <header className="topbar">
        <Link href={email ? "/" : "/login"} className="brand">
          <span className="brand-name">MyFurniture</span>
          <span className="brand-tag">LIVE CATALOGUE</span>
        </Link>
        {email && (
          <>
            <nav>
              <Link href="/">Catalogue</Link>
              <Link href="/assistant">Ask the assistant</Link>
              <Link href="/orders">Order history</Link>
            </nav>
            <div className="header-right">
              <div className="budget">
                Balance: <strong>{balance !== null ? `$${balance.toFixed(2)}` : "unavailable"}</strong>
              </div>
              <a href="#" className="logout-link" onClick={(e) => { e.preventDefault(); handleLogout(); }}>
                Logout ({email})
              </a>
            </div>
          </>
        )}
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <div className="footer-inner">
          <div>
            <div className="brand-name">MyFurniture</div>
            <p>
              A Day 1 hackathon buyer app, backed by a real furniture shop API -
              every price, balance, and order here is real.
            </p>
          </div>
          {email && (
            <div className="footer-links">
              <div>
                <h4>Shop</h4>
                <ul>
                  <li><Link href="/">Catalogue</Link></li>
                  <li><Link href="/assistant">Ask the assistant</Link></li>
                  <li><Link href="/orders">Order history</Link></li>
                </ul>
              </div>
              <div>
                <h4>Account</h4>
                <ul>
                  <li>{email}</li>
                  <li><a href="#" onClick={(e) => { e.preventDefault(); handleLogout(); }}>Logout</a></li>
                </ul>
              </div>
            </div>
          )}
        </div>
        <div className="footer-bottom">MyFurnitureApp - built for Day 1 of a hackathon.</div>
      </footer>
    </>
  );
}
