"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { Skeleton } from "@/components/ui";

/** Landing: send signed-in users to their dashboard, everyone else to the portal chooser. */
export default function Home() {
  const { session, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    router.replace(session ? `/${session.user.role}` : "/login");
  }, [ready, session, router]);

  return (
    <div className="mx-auto max-w-md space-y-4 p-10">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-32" />
    </div>
  );
}
