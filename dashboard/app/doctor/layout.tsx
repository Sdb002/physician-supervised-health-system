"use client";

import { Shell } from "@/components/shell";

export default function DoctorLayout({ children }: { children: React.ReactNode }) {
  return <Shell role="doctor">{children}</Shell>;
}
