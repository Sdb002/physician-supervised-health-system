"use client";

import { useEffect, useId, useRef } from "react";
import { IconX } from "@/components/icons";

/** Everything inside the dialog that can hold focus. Used to keep Tab from
 * wandering out into the page behind the overlay. */
const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

export function Modal({
  title,
  onClose,
  children,
}: {
  title?: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  // Move focus into the dialog on open and put it back where it came from on
  // close. Without this a keyboard or screen-reader user stays parked on the
  // trigger behind the overlay, with no way to reach the dialog's controls.
  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const dialog = dialogRef.current;
    const first = dialog?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? dialog)?.focus();

    return () => {
      // The trigger can be gone by now (e.g. the row that opened the dialog
      // was removed), so only restore focus if it is still in the document.
      if (previouslyFocused?.isConnected) previouslyFocused.focus();
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;

      // Focus trap: cycle within the dialog rather than letting Tab escape to
      // the inert page behind it.
      const dialog = dialogRef.current;
      if (!dialog) return;
      const items = [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
        (el) => el.offsetParent !== null || el === document.activeElement
      );
      if (items.length === 0) {
        e.preventDefault();
        dialog.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      } else if (e.shiftKey && (active === first || active === dialog)) {
        e.preventDefault();
        last.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 print:hidden">
      {/* Backdrop is its own element so the click-to-dismiss handler sits on
        * decorative chrome rather than on the dialog's own container. Escape
        * provides the equivalent keyboard path. */}
      <div className="absolute inset-0 bg-ink/50" aria-hidden="true" onClick={onClose} />
      <div
        ref={dialogRef}
        className="relative w-full max-w-2xl rounded-2xl border border-line bg-surface p-6 shadow-xl focus:outline-none"
        role="dialog"
        aria-modal="true"
        // Point at the visible heading so the name a screen reader announces
        // is the same text a sighted user reads.
        aria-labelledby={title ? titleId : undefined}
        aria-label={title ? undefined : "Dialog"}
        tabIndex={-1}
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="min-w-0 flex-1">
            {title && (
              <h2 id={titleId} className="font-display text-lg font-bold leading-7 text-ink">
                {title}
              </h2>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md p-1.5 text-ink-muted hover:bg-surface-soft hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clinical"
            aria-label="Close"
          >
            <IconX className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
