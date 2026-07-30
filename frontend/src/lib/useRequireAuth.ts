"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./AuthContext";

/** Redirects to /login once we know for sure the user isn't logged in.
 * Call this at the top of any page that needs a session. */
export function useRequireAuth() {
  const { loading, email } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !email) {
      router.replace("/login");
    }
  }, [loading, email, router]);
}
