"use client";

import { useState } from "react";
import { api, ApiError, type PendingPurchase } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { ErrorBanner } from "@/components/ErrorBanner";
import { formatReply } from "@/lib/formatReply";

export default function AssistantPage() {
  useRequireAuth();
  const { email, refresh } = useAuth();
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const [trace, setTrace] = useState<string[]>([]);
  const [pending, setPending] = useState<PendingPurchase>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) {
      setError("Type a request first.");
      return;
    }

    setAsking(true);
    setError(null);
    try {
      const result = await api.assistant(question);
      setReply(result.reply);
      setTrace(result.trace);
      setPending(result.pending_purchase);
      await refresh(); // a confirmed purchase changes the real balance
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setAsking(false);
    }
  };

  if (!email) return null;

  return (
    <>
      <div className="section-heading">
        <h1>Ask the Assistant</h1>
      </div>
      <p className="hint">
        Try &quot;what&apos;s the cheapest bar stool&quot;, &quot;show me black chairs&quot;, or
        &quot;buy me a bar table&quot; - the assistant can browse, look things up, check
        balance, and place real orders. Buying always asks you to confirm the
        price first, in a follow-up message, before anything is actually charged.
      </p>

      {pending && (
        <div className="pending-banner">
          <strong>Waiting for your confirmation:</strong> {pending.quantity}x{" "}
          {pending.product_name} for ${pending.total.toFixed(2)}. Reply &quot;yes&quot; to
          confirm, or ask for something else.
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit} className="ask-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. buy me a cheap black bar stool"
          required
          autoFocus
        />
        <button type="submit" disabled={asking}>
          {asking ? "Asking..." : "Ask"}
        </button>
      </form>

      {reply && (
        <section className="cart">
          <h2>Reply</h2>
          {formatReply(reply)}

          {trace.length > 0 && (
            <>
              <h3>What it did</h3>
              <ul>
                {trace.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </>
  );
}
