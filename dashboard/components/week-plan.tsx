"use client";

import { KeyboardEvent, useId, useRef, useState } from "react";
import type { Lang } from "@/lib/use-lang";
import {
  MEAL_ORDER,
  PlanDayView,
  localName,
  mealItemKey,
  mealName,
  portionText,
  saltCutPercent,
  todayIndex,
  todayWeekday,
  weekdayName,
} from "@/lib/clinical-terms";

const L = {
  en: {
    today: "Today", days: "Days of the week", everyDay: "Every day", kcal: "kcal", day: "Day",
    carbs: (grams: string) => `${grams} g carbohydrate`,
    salt: "Cooking salt",
    saltDay: (grams: string) => `${grams} g for the day`,
    saltLess: (grams: string, recipe: string, percent: string) =>
      `Cook this day's dishes with ${percent}% less salt than their recipes list: ${grams} g in your portions, not ${recipe} g. Add no salt at the table.`,
    saltAsListed: "Cook this day's dishes with the salt their recipes list. Add no salt at the table.",
    saltShort: (grams: string) => `salt ${grams} g`,
    saltFootnote:
      "Salt is the most cooking salt your portions should carry that day, which can be less than the recipes list. Add no salt at the table.",
  },
  bn: {
    today: "আজ", days: "সপ্তাহের দিন", everyDay: "প্রতিদিন", kcal: "কিলোক্যালরি", day: "দিন",
    carbs: (grams: string) => `শর্করা ${grams} গ্রাম`,
    salt: "রান্নার লবণ",
    saltDay: (grams: string) => `সারা দিনে ${grams} গ্রাম`,
    saltLess: (grams: string, recipe: string, percent: string) =>
      `এই দিনের রান্নায় রেসিপিতে লেখা পরিমাণের চেয়ে ${percent}% কম লবণ দিন: আপনার অংশে ${recipe} গ্রামের বদলে ${grams} গ্রাম। পাতে আলাদা লবণ নেবেন না।`,
    saltAsListed: "এই দিনের রান্নায় রেসিপিতে লেখা পরিমাণ লবণ দিন। পাতে আলাদা লবণ নেবেন না।",
    saltShort: (grams: string) => `লবণ ${grams} গ্রাম`,
    saltFootnote:
      "লবণ বলতে ওই দিনের রান্নায় আপনার অংশে সর্বোচ্চ যতটুকু লবণ থাকবে, যা রেসিপিতে লেখা পরিমাণের চেয়ে কম হতে পারে। পাতে আলাদা লবণ নেবেন না।",
  },
} as const;

/** Salt in grams to one decimal place, as the engine states it. */
const saltGrams = (grams: number, lang: Lang) =>
  grams.toLocaleString(lang === "bn" ? "bn-BD" : "en", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** Saturday-to-Friday tabs. Arrow keys move between days (the ARIA tabs
 * pattern), today carries a dot and says so to screen readers. */
export function DayPicker({
  days,
  selected,
  onSelect,
  lang,
  panelId,
}: {
  days: PlanDayView[];
  selected: number;
  onSelect: (index: number) => void;
  lang: Lang;
  panelId: string;
}) {
  const t = L[lang];
  const today = todayWeekday();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    let next = step ? (selected + step + days.length) % days.length : -1;
    if (e.key === "Home") next = 0;
    if (e.key === "End") next = days.length - 1;
    if (next < 0) return;
    e.preventDefault();
    onSelect(next);
    refs.current[next]?.focus();
  };

  return (
    <div role="tablist" aria-label={t.days} className="grid grid-cols-7 gap-1.5 print:hidden">
      {days.map((day, index) => {
        const active = index === selected;
        const isToday = day.weekday === today;
        return (
          <button
            key={day.day}
            ref={(el) => {
              refs.current[index] = el;
            }}
            type="button"
            role="tab"
            id={`${panelId}-tab-${index}`}
            aria-selected={active}
            aria-controls={panelId}
            tabIndex={active ? 0 : -1}
            onClick={() => onSelect(index)}
            onKeyDown={onKeyDown}
            className={`relative flex min-h-12 cursor-pointer flex-col items-center justify-center rounded-lg border px-1 py-1.5 text-sm font-semibold transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clinical ${
              active
                ? "border-clinical bg-clinical text-on-clinical"
                : "border-line bg-surface text-ink-soft hover:border-line-strong hover:text-ink"
            }`}
          >
            <span>{day.weekday ? weekdayName(day.weekday, lang, true) : day.day}</span>
            {isToday && (
              <>
                <span
                  aria-hidden="true"
                  className={`mt-1 h-1.5 w-1.5 rounded-full ${active ? "bg-on-clinical" : "bg-clinical"}`}
                />
                <span className="sr-only">, {t.today}</span>
              </>
            )}
          </button>
        );
      })}
    </div>
  );
}

/** One day's meals as a schedule, read top to bottom like the dosage times
 * on a prescription. The day's cooking salt closes it: the plan's sodium
 * holds only if the dishes are cooked with that much (engine 0.6.0 onwards;
 * older plans carry no salt figure and show none). */
export function DayMeals({
  day,
  lang,
  showItemKcal = false,
}: {
  day: PlanDayView;
  lang: Lang;
  /** staff screens show each line's energy; the patient sees portions */
  showItemKcal?: boolean;
}) {
  const t = L[lang];
  const { meals } = day;
  const saltCut = saltCutPercent(day);
  return (
    <div className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
      {MEAL_ORDER.filter((m) => meals[m]?.length).map((meal) => {
        const items = meals[meal];
        const mealKcal = items.reduce((sum, it) => sum + Number(it.kcal || 0), 0);
        // carbohydrate is counted by the meal; plans from before engine
        // 0.5.0 do not carry it line by line
        const mealCarbs = items.every((it) => it.carb_g != null)
          ? items.reduce((sum, it) => sum + (it.carb_g ?? 0), 0)
          : null;
        return (
          <div key={meal} className="grid gap-x-6 gap-y-2 px-5 py-4 sm:grid-cols-[10rem_1fr]">
            <div>
              <h3 className="font-semibold text-ink">{mealName(meal, lang)}</h3>
              <p className="text-sm text-ink-muted">
                {Math.round(mealKcal).toLocaleString(lang === "bn" ? "bn-BD" : "en")} {t.kcal}
              </p>
              {mealCarbs != null && (
                <p className="text-sm text-ink-muted">
                  {t.carbs(Math.round(mealCarbs).toLocaleString(lang === "bn" ? "bn-BD" : "en"))}
                </p>
              )}
            </div>
            <ul className="space-y-1.5">
              {items.map((item, index) => (
                <li key={`${mealItemKey(item)}-${index}`} className="flex items-baseline justify-between gap-4">
                  <span className="text-ink-strong">{localName(item, lang)}</span>
                  <span className="shrink-0 text-right text-sm text-ink-muted">
                    {portionText(item, lang)}
                    {showItemKcal && `, ${item.kcal} kcal`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
      {day.salt_g != null && (
        <div className="grid gap-x-6 gap-y-2 px-5 py-4 sm:grid-cols-[10rem_1fr]">
          <div>
            <h3 className="font-semibold text-ink">{t.salt}</h3>
            <p className="text-sm text-ink-muted">{t.saltDay(saltGrams(day.salt_g, lang))}</p>
          </div>
          <p className="text-sm leading-6 text-ink-soft">
            {saltCut > 0
              ? t.saltLess(
                  saltGrams(day.salt_g, lang),
                  saltGrams(day.recipe_salt_g ?? day.salt_g, lang),
                  saltCut.toLocaleString(lang === "bn" ? "bn-BD" : "en")
                )
              : t.saltAsListed}
          </p>
        </div>
      )}
    </div>
  );
}

/* Lunch and dinner carry the most lines, so they get the width that keeps a
 * portion on one line; breakfast and the snack can wrap without making the
 * row any taller. */
const MEAL_COLUMN: Record<string, string> = {
  breakfast: "w-[20.5%]",
  lunch: "w-[27%]",
  dinner: "w-[27%]",
  snack: "w-[13.5%]",
};

/** The whole week on paper: a row for each day and a column for each meal,
 * so the sheet reads across for today and down for the week's lunches. Each
 * line keeps its portion directly under its name, and each day its cooking
 * salt under its energy. */
function WeekTable({
  days,
  lang,
  showItemKcal,
}: {
  days: PlanDayView[];
  lang: Lang;
  showItemKcal: boolean;
}) {
  const t = L[lang];
  const meals = MEAL_ORDER.filter((m) => days.some((d) => d.meals[m]?.length));
  return (
    <table className="hidden w-full table-fixed text-left text-sm print:table">
      <thead className="border-b border-line-strong text-ink-muted">
        <tr>
          <th scope="col" className="py-1.5 pr-2 font-semibold">{t.day}</th>
          {meals.map((meal) => (
            <th key={meal} scope="col" className={`px-2 py-1.5 font-semibold last:pr-0 ${MEAL_COLUMN[meal]}`}>
              {mealName(meal, lang)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {days.map((d) => {
          // the engine's own day total, so the column agrees with the
          // planned average under the table; the line sum is a fallback
          const dayKcal = Math.round(
            d.totals?.kcal ??
              meals.reduce(
                (sum, meal) => sum + (d.meals[meal] ?? []).reduce((s, it) => s + Number(it.kcal || 0), 0),
                0
              )
          );
          return (
            <tr key={d.day}>
              <th scope="row" className="py-2.5 pr-2 align-top">
                <span className="font-display block whitespace-nowrap text-base font-bold text-ink">
                  {d.weekday ? weekdayName(d.weekday, lang) : t.everyDay}
                </span>
                <span className="block font-normal text-ink-muted">
                  {lang === "bn" ? dayKcal.toLocaleString("bn-BD") : dayKcal} {t.kcal}
                </span>
                {d.salt_g != null && (
                  <span className="block whitespace-nowrap font-normal text-ink-muted">
                    {t.saltShort(saltGrams(d.salt_g, lang))}
                  </span>
                )}
              </th>
              {meals.map((meal) => (
                <td key={meal} className="px-2 py-2.5 align-top last:pr-0">
                  <ul className="space-y-1.5">
                    {(d.meals[meal] ?? []).map((item, index) => (
                      <li key={`${mealItemKey(item)}-${index}`} className="leading-snug">
                        <span className="block font-medium text-ink">{localName(item, lang)}</span>
                        <span className="flex flex-wrap justify-between gap-x-2 text-ink-muted">
                          <span className="whitespace-nowrap">{portionText(item, lang)}</span>
                          {showItemKcal && <span className="ml-auto whitespace-nowrap">{item.kcal} kcal</span>}
                        </span>
                      </li>
                    ))}
                  </ul>
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/** A week plan with a day picker that opens on today. Printed, the whole
 * week is set as one table instead. A one-day plan (assessments made before
 * weekly plans) shows as a single "every day" schedule with no picker. */
export function WeekPlan({
  days,
  lang,
  showItemKcal = false,
}: {
  days: PlanDayView[];
  lang: Lang;
  showItemKcal?: boolean;
}) {
  const t = L[lang];
  const panelId = useId();
  const [selected, setSelected] = useState(() => todayIndex(days));
  if (days.length === 0) return null;
  const index = Math.min(selected, days.length - 1);
  const day = days[index];

  if (days.length === 1 && !day.weekday) {
    return <DayMeals day={day} lang={lang} showItemKcal={showItemKcal} />;
  }

  return (
    <div className="space-y-3">
      <DayPicker days={days} selected={index} onSelect={setSelected} lang={lang} panelId={panelId} />
      <div
        role="tabpanel"
        id={panelId}
        aria-labelledby={`${panelId}-tab-${index}`}
        className="space-y-2 print:hidden"
      >
        <p className="font-display text-lg font-bold text-ink">
          {day.weekday ? weekdayName(day.weekday, lang) : t.everyDay}
          {day.weekday === todayWeekday() && (
            <span className="ml-2 text-sm font-semibold text-clinical">{t.today}</span>
          )}
        </p>
        <DayMeals day={day} lang={lang} showItemKcal={showItemKcal} />
      </div>
      <WeekTable days={days} lang={lang} showItemKcal={showItemKcal} />
      {days.some((d) => d.salt_g != null) && (
        <p className="hidden text-sm text-ink-muted print:block">{t.saltFootnote}</p>
      )}
    </div>
  );
}
