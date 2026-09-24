"use client";

import { Shell } from "@/components/shell";

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return <Shell role="patient">{children}</Shell>;
}
