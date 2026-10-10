"use client";

import { useLang } from "@/lib/use-lang";

/** English / বাংলা switch. Each option is labelled in its own script, so a
 * reader finds their language without having to read the other one. */
export function LangSwitch({ className }: { className?: string }) {
  const [lang, setLang] = useLang();
  return (
    <div
      role="radiogroup"
      aria-label="Language / ভাষা"
      className={`inline-flex rounded-lg border border-line-strong bg-surface p-0.5 ${className ?? ""}`}
    >
      {(["en", "bn"] as const).map((l) => (
        <button
          key={l}
          type="button"
          role="radio"
          aria-checked={lang === l}
          lang={l}
          onClick={() => setLang(l)}
          className={`min-h-8 flex-1 cursor-pointer rounded-md px-3 text-sm font-semibold transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-clinical ${
            lang === l ? "bg-clinical text-on-clinical" : "text-ink-soft hover:bg-surface-soft"
          }`}
        >
          {l === "en" ? "English" : "বাংলা"}
        </button>
      ))}
    </div>
  );
}
