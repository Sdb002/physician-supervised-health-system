"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { IconChevronLeft } from "@/components/icons";
import { Brand } from "@/components/brand";
import { StethoscopeArt } from "@/components/stethoscope-art";
import { focusRing } from "@/components/ui";
import { LangSwitch } from "@/components/lang-switch";
import { useT } from "@/lib/use-t";

/** Frame for the sign-in and registration forms: the brand, one form on a
 * sheet, a way back to the portal chooser, and the stethoscope beside it -
 * the same drawing as the chooser, so every sign-in screen is one place. */
export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
  wide = false,
  back = true,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
  back?: boolean;
}) {
  const { t } = useT();
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <div className="mx-auto grid min-h-screen max-w-6xl gap-10 px-4 sm:px-8 lg:grid-cols-2">
        <div
          className={`relative mx-auto w-full py-6 sm:py-10 lg:mx-0 lg:self-center ${wide ? "max-w-lg" : "max-w-md"}`}
        >
          {/* phones: the instrument peeks out from behind the form */}
          <StethoscopeArt
            variant="mark"
            className="pointer-events-none absolute -top-1 right-0 w-28 sm:w-36 lg:hidden"
          />

          <div className="relative flex flex-wrap items-center justify-between gap-3">
            <Link href="/login" className={`inline-flex rounded-lg ${focusRing}`}>
              <Brand />
            </Link>
            <LangSwitch />
          </div>

          <div className="relative mt-8 rounded-2xl border border-line bg-surface px-6 py-7 shadow-[0_24px_48px_-32px_rgb(22_35_77/0.45)] sm:px-8">
            <h1 className="font-display text-2xl font-bold leading-8 text-ink">{title}</h1>
            {subtitle && <p className="mt-1 text-sm leading-6 text-ink-muted">{subtitle}</p>}
            <div className="mt-6">{children}</div>
            {footer && <div className="mt-6 border-t border-line pt-4 text-sm text-ink-muted">{footer}</div>}
          </div>

          {back && (
            <Link
              href="/login"
              className={`relative mt-5 inline-flex items-center gap-1 rounded text-sm font-medium text-ink-muted hover:text-ink ${focusRing}`}
            >
              <IconChevronLeft className="h-4 w-4" />
              {t("Choose a different portal")}
            </Link>
          )}
        </div>

        <div className="hidden lg:block">
          <div className="sticky top-0 flex h-screen items-center">
            <StethoscopeArt className="-mr-24 w-full max-w-xl xl:-mr-32" />
          </div>
        </div>
      </div>
    </div>
  );
}
