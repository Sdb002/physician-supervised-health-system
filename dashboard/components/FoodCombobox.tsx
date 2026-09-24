"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { AllowedFood } from "@/lib/api";
import { IconSearch, IconStar } from "@/components/icons";

interface FoodCombobox {
  /** Live, contraindication-filtered candidates (never null once loaded). */
  foods: AllowedFood[];
  /** This patient's ranked picks, in rank order — pinned to the top and
   * starred, deduped out of the grouped list below so nothing appears twice. */
  recommended: AllowedFood[];
  onSelect: (food: AllowedFood) => void;
  placeholder?: string;
  /** Accessible name for the field. The visible label is an icon only. */
  label?: string;
}

/** Searchable food picker: type to filter by English or Bangla name across
 * the whole (gate-filtered) catalog; browsing with an empty query shows the
 * patient's recommended picks first, then everything else grouped by food
 * group — same information the old native <select> showed, just findable.
 *
 * Follows the ARIA combobox pattern: focus stays on the input and the active
 * row is published via aria-activedescendant, so the rows are deliberately
 * kept out of the tab order (tabIndex -1) — tabbing through several hundred
 * foods would be unusable. */
export function FoodCombobox({ foods, recommended, onSelect, placeholder, label }: FoodCombobox) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const listboxId = useId();
  const optionId = (index: number) => `${listboxId}-opt-${index}`;

  const recommendedIds = useMemo(() => new Set(recommended.map((f) => f.food_id)), [recommended]);

  const groups = useMemo(() => {
    const byGroup = new Map<string, AllowedFood[]>();
    for (const f of foods) {
      if (recommendedIds.has(f.food_id)) continue; // already shown in "recommended"
      const list = byGroup.get(f.food_group) ?? [];
      list.push(f);
      byGroup.set(f.food_group, list);
    }
    return [...byGroup.entries()];
  }, [foods, recommendedIds]);

  const trimmed = query.trim().toLowerCase();
  const searchResults = useMemo(() => {
    if (!trimmed) return [];
    const matches = foods.filter(
      (f) => f.name_en.toLowerCase().includes(trimmed) || f.name_bn.includes(trimmed)
    );
    // recommended matches first (in rank order), then the rest alphabetically
    return matches.sort((a, b) => {
      const ar = recommendedIds.has(a.food_id) ? 0 : 1;
      const br = recommendedIds.has(b.food_id) ? 0 : 1;
      return ar !== br ? ar - br : a.name_en.localeCompare(b.name_en);
    });
  }, [foods, trimmed, recommendedIds]);

  const flatList = trimmed ? searchResults : [...recommended, ...groups.flatMap(([, items]) => items)];
  const noMatches = trimmed !== "" && searchResults.length === 0;

  // Reset the highlighted row whenever the result set changes (query edited,
  // list opened/closed) — done during render, not in an effect, per React's
  // "adjusting state when props change" pattern, so it doesn't cost an extra
  // commit the way a useEffect reset would.
  const resetSignature = `${trimmed}|${open}`;
  const [prevResetSignature, setPrevResetSignature] = useState(resetSignature);
  if (resetSignature !== prevResetSignature) {
    setPrevResetSignature(resetSignature);
    setHighlight(0);
  }

  useEffect(() => {
    listRef.current
      ?.querySelector('[data-highlighted="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [highlight]);

  const select = (food: AllowedFood) => {
    onSelect(food);
    setQuery("");
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) {
      setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, flatList.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const food = flatList[highlight];
      if (food) select(food);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const row = (food: AllowedFood, index: number) => (
    <button
      key={food.food_id}
      type="button"
      role="option"
      id={optionId(index)}
      aria-selected={index === highlight}
      // Focus stays on the input; the combobox publishes the active row via
      // aria-activedescendant instead.
      tabIndex={-1}
      data-highlighted={index === highlight}
      // fires before the input's onBlur closes the list
      onMouseDown={(e) => e.preventDefault()}
      onClick={() => select(food)}
      onMouseEnter={() => setHighlight(index)}
      className={`flex w-full items-center justify-between gap-3 px-3 py-1.5 text-left text-sm ${
        index === highlight ? "bg-teal-50" : ""
      }`}
    >
      <span className="min-w-0 truncate text-ink-strong">
        {food.name_en}
        {food.name_bn && <span className="text-ink-muted"> · {food.name_bn}</span>}
        {recommendedIds.has(food.food_id) && (
          <>
            <IconStar className="ml-1.5 inline h-3.5 w-3.5 text-amber-500 dark:text-amber-400" />
            <span className="sr-only"> (recommended for this patient)</span>
          </>
        )}
      </span>
      <span className="shrink-0 text-xs tabular-nums text-ink-muted">
        {food.kcal_per_100g} kcal/100g
      </span>
    </button>
  );

  return (
    <div
      ref={containerRef}
      className="relative min-w-0 flex-1"
      onBlur={(e) => {
        if (!containerRef.current?.contains(e.relatedTarget as Node)) setOpen(false);
      }}
    >
      <label className="relative block">
        <span className="sr-only">{label ?? "Search foods"}</span>
        <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={open && flatList[highlight] ? optionId(highlight) : undefined}
          value={query}
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onKeyDown={onKeyDown}
          placeholder={placeholder ?? "Search foods (safety-filtered)…"}
          className="w-full rounded-lg border border-line-strong bg-surface py-1.5 pl-9 pr-3 text-sm shadow-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-100"
        />
      </label>
      {/* Filtering is otherwise a purely visual change - announce the count. */}
      <p className="sr-only" role="status">
        {open && trimmed
          ? noMatches
            ? `No foods match ${query}`
            : `${searchResults.length} food${searchResults.length === 1 ? "" : "s"} available`
          : ""}
      </p>

      {open && (
        <div
          ref={listRef}
          className="absolute z-20 mt-1 max-h-80 w-full overflow-y-auto rounded-lg border border-line bg-surface py-1 shadow-lg"
        >
          {/* Kept outside the listbox: a listbox may only contain options
            * and groups, and this row is neither. */}
          {noMatches && (
            <p className="px-3 py-4 text-center text-sm text-ink-muted">
              No foods match &ldquo;{query}&rdquo;
            </p>
          )}
          {/* Rendered even while empty so the input's aria-controls always
            * resolves to a real element. */}
          <div role="listbox" id={listboxId} aria-label={label ?? "Foods"}>
            {trimmed ? (
              searchResults.map((f, i) => row(f, i))
            ) : (
              <>
                {recommended.length > 0 && (
                  <div role="group" aria-label="Recommended for this patient">
                    <p
                      aria-hidden="true"
                      className="sticky top-0 bg-surface px-3 py-1.5 text-xs font-semibold text-teal-700"
                    >
                      Recommended for this patient
                    </p>
                    {recommended.map((f, i) => row(f, i))}
                  </div>
                )}
                {groups.map(([group, items]) => (
                  <div key={group} role="group" aria-label={group}>
                    <p
                      aria-hidden="true"
                      className="sticky top-0 bg-surface px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted"
                    >
                      {group}
                    </p>
                    {items.map((f, i) => row(f, recommended.length + flatIndexOffset(groups, group) + i))}
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** Index of `group`'s first item within the flattened (recommended-excluded)
 * groups list — lets each group's rows continue the same running highlight
 * index used by keyboard nav, without flattening the JSX itself. */
function flatIndexOffset(groups: [string, AllowedFood[]][], group: string): number {
  let offset = 0;
  for (const [g, items] of groups) {
    if (g === group) return offset;
    offset += items.length;
  }
  return offset;
}
