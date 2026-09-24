"use client";

import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ReportView } from "@/components/report-view";

function PatientReportInner() {
  const { visitId } = useParams<{ visitId: string }>();
  const tab = useSearchParams().get("tab");
  return <ReportView visitId={visitId} viewer="patient" initialTab={tab ?? undefined} />;
}

export default function PatientReportPage() {
  return (
    <Suspense>
      <PatientReportInner />
    </Suspense>
  );
}
