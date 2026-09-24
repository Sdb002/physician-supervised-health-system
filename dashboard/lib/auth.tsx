"use client";

import { useRouter } from "next/navigation";
import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { clearSession, loadSession, saveSession, Session } from "@/lib/api";

interface AuthContextValue {
  session: Session | null;
  /** false until localStorage has been read on the client */
  ready: boolean;
  signIn: (session: Session) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  session: null,
  ready: false,
  signIn: () => {},
  signOut: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setSession(loadSession());
    setReady(true);
  }, []);

  const signIn = useCallback((s: Session) => {
    saveSession(s);
    setSession(s);
  }, []);

  const signOut = useCallback(() => {
    clearSession();
    setSession(null);
    router.replace("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ session, ready, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
