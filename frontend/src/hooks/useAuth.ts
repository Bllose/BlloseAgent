"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { getAuth, setAuth, clearAuth } from "@/lib/auth";

export function useAuth() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    const auth = getAuth();
    return auth?.isLoggedIn ?? false;
  });
  const [email, setEmail] = useState(() => {
    const auth = getAuth();
    return auth?.email ?? "";
  });

  const login = useCallback(
    (userEmail: string) => {
      setAuth({ isLoggedIn: true, email: userEmail });
      setIsLoggedIn(true);
      setEmail(userEmail);
      router.push("/home");
    },
    [router],
  );

  const logout = useCallback(() => {
    clearAuth();
    setIsLoggedIn(false);
    setEmail("");
    router.push("/login");
  }, [router]);

  return { isLoggedIn, email, login, logout };
}
