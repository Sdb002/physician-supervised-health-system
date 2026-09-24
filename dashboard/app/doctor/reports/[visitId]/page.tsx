"use client";

import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ReportView } from "@/components/report-view";

function DoctorReportInner() {
  const { visitId } = useParams<{ visitId: string }>();
  const tab = useSearchParams().get("tab");
  return <ReportView visitId={visitId} viewer="doctor" initialTab={tab ?? undefined} />;
}

export default function DoctorReportPage() {
  return (
    <Suspense>
      <DoctorReportInner />
    </Suspense>
  );
}
