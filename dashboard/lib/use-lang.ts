import { useCallback, useSyncExternalStore } from "react";

export type Lang = "en" | "bn";

const KEY = "lang";
const EVENT = "langchange";

function subscribe(onChange: () => void) {
  window.addEventListener(EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

function getSnapshot(): Lang {
  try {
    return localStorage.getItem(KEY) === "bn" ? "bn" : "en";
  } catch {
    return "en";
  }
}

const getServerSnapshot = (): Lang => "en";

/** The patient's reading language, chosen once and kept across pages and
 * visits. It used to be per-page state, so a Bangla reader had to switch
 * back to Bangla on every screen they opened. */
export function useLang(): [Lang, (lang: Lang) => void] {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const setLang = useCallback((next: Lang) => {
    try {
      localStorage.setItem(KEY, next);
    } catch {
      // Still applies until reload, it just won't be remembered.
    }
    window.dispatchEvent(new Event(EVENT));
  }, []);
  return [lang, setLang];
}
