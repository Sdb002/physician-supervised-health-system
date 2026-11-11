import { Fragment, ReactNode, useMemo } from "react";
import { useLang } from "@/lib/use-lang";
import { Vars, bnDigits, template, translate } from "@/lib/ui-text";

/** The interface in the reader's language. `t` takes the English sentence
 * and returns it, or its Bangla from lib/ui-text.ts; `rich` does the same
 * for a sentence with elements set inside it (a name in bold, a link);
 * `n` writes a number in the reader's digits. */
export function useT() {
  const [lang] = useLang();
  return useMemo(
    () => ({
      lang,
      t: (en: string, vars?: Vars) => translate(lang, en, vars),
      n: (value: number | string) => (lang === "bn" ? bnDigits(String(value)) : String(value)),
      rich: (en: string, parts: Record<string, ReactNode>): ReactNode =>
        template(lang, en)
          .split(/(\{\w+\})/)
          .map((piece, i) => {
            const name = /^\{(\w+)\}$/.exec(piece)?.[1];
            return <Fragment key={i}>{name && name in parts ? parts[name] : piece}</Fragment>;
          }),
    }),
    [lang]
  );
}

export type T = ReturnType<typeof useT>["t"];
