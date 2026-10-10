import { IconRx } from "@/components/icons";

/** The ℞ tile. One definition so the shell, the sign-in screens and the
 * portal chooser can't drift apart. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-xl bg-clinical text-on-clinical shadow-[inset_0_-3px_0_rgb(0_0_0/0.18)] ${className ?? "h-10 w-10"}`}
    >
      <IconRx className="h-5 w-5" strokeWidth={2.4} />
    </span>
  );
}

/** Mark plus the service's name, set in the display face. */
export function Brand({ caption, lang }: { caption?: string; lang?: string }) {
  return (
    <span className="flex min-w-0 items-center gap-3">
      <BrandMark />
      <span className="min-w-0">
        <span lang="bn" className="font-display block truncate text-lg font-bold leading-6 text-ink">
          স্বাস্থ্য পরিকল্পনা
        </span>
        {caption && (
          <span lang={lang} className="block truncate text-xs font-medium text-ink-muted">
            {caption}
          </span>
        )}
      </span>
    </span>
  );
}
