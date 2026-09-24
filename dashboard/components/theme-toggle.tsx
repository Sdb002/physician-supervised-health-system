"use client";

import { useCallback, useSyncExternalStore } from "react";
import { IconMoon, IconSun } from "@/components/icons";

const EVENT = "themechange";

function subscribe(onChange: () => void) {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  window.addEventListener(EVENT, onChange);
  window.addEventListener("storage", onChange);
  mq.addEventListener("change", onChange);
  return () => {
    window.removeEventListener(EVENT, onChange);
    window.removeEventListener("storage", onChange);
    mq.removeEventListener("change", onChange);
  };
}

/* The switch reflects what is actually on screen, not the stored preference:
 * with no stored choice that is the OS setting, so reading the resolved state
 * keeps the control honest on first load. */
function getSnapshot() {
  try {
    const stored = localStorage.getItem("theme");
    if (stored === "dark") return true;
    if (stored === "light") return false;
  } catch {
    // storage unavailable - fall through to the OS setting
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

const getServerSnapshot = () => false;

export function ThemeToggle() {
  const dark = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = useCallback(() => {
    const next = !getSnapshot();
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {
      // Choice still applies this session, it just will not survive a reload.
    }
    document.documentElement.classList.toggle("dark", next);
    window.dispatchEvent(new Event(EVENT));
  }, []);

  return (
    <button
      type="button"
      role="switch"
      aria-checked={dark}
      onClick={toggle}
      className="group relative inline-flex h-8 w-full cursor-pointer items-center justify-between gap-2 rounded-lg border border-white/10 bg-white/5 px-2 text-xs font-medium text-slate-300 transition-colors duration-200 hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clinical"
    >
      <span className="flex items-center gap-2">
        {dark ? <IconMoon className="h-4 w-4" /> : <IconSun className="h-4 w-4" />}
        {dark ? "Dark" : "Light"}
      </span>

      {/* Track */}
      <span
        aria-hidden="true"
        className={`relative h-4 w-8 shrink-0 rounded-full transition-colors duration-200 ${
          dark ? "bg-clinical" : "bg-white/20"
        }`}
      >
        <span
          className={`absolute top-0.5 h-3 w-3 rounded-full bg-white shadow transition-all duration-200 ${
            dark ? "left-4.5" : "left-0.5"
          }`}
        />
      </span>
      <span className="sr-only">Toggle dark mode</span>
    </button>
  );
}
