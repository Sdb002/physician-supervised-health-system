/** What to eat and what to avoid, one block per condition - the engine's
 * nutrition.condition_foods (src/diet/condition_foods.py). Shared by the
 * patient's Meals page, the report and the review page. */

import type { ConditionAvoidItem, ConditionFoods, RecommendedFood } from "@/lib/api";
import { avoidReasonName, conditionName, localName } from "@/lib/clinical-terms";
import { IconCheck, IconX } from "@/components/icons";

type Lang = "en" | "bn";

const L = {
  en: {
    eat: "Good to eat",
    eatHint: "Real sources of what this condition needs, the most often eaten first.",
    noEat: "Nothing extra to add for this condition: follow your meal plan.",
    avoid: "Avoid",
    avoidBecause: (reasons: string) => `Left out because they are ${reasons}.`,
    noAvoid: "Nothing is left out for this condition.",
    foods: "Foods",
    dishes: "Dishes",
    and: " or ",
  },
  bn: {
    eat: "যা খাওয়া ভালো",
    eatHint: "এই সমস্যায় যা দরকার তার ভালো উৎস, যা বেশি খাওয়া হয় তা আগে।",
    noEat: "এই সমস্যার জন্য বাড়তি কিছু যোগ করার নেই: খাবার পরিকল্পনা মেনে চলুন।",
    avoid: "যা এড়িয়ে চলবেন",
    avoidBecause: (reasons: string) => `বাদ দেওয়া হয়েছে কারণ এগুলোতে ${reasons}।`,
    noAvoid: "এই সমস্যার জন্য কোনো খাবার বাদ দেওয়া হয়নি।",
    foods: "খাবার",
    dishes: "রান্না",
    and: " বা ",
  },
} as const;

function EatList({ foods, lang }: { foods: RecommendedFood[]; lang: Lang }) {
  return (
    <ul className="space-y-1.5">
      {foods.map((food) => (
        <li key={food.food_id} className="flex items-start gap-2 leading-snug text-ink">
          <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-ok-ink" strokeWidth={2.5} aria-hidden="true" />
          <span>{localName(food, lang)}</span>
        </li>
      ))}
    </ul>
  );
}

function AvoidList({ items, lang }: { items: ConditionAvoidItem[]; lang: Lang }) {
  return (
    <ul className="space-y-1.5">
      {items.map((item) => (
        <li key={item.food_id ?? item.recipe_id} className="flex items-start gap-2 leading-snug text-ink">
          <IconX className="mt-0.5 h-4 w-4 shrink-0 text-high-ink" strokeWidth={2.5} aria-hidden="true" />
          <span>{localName(item, lang)}</span>
        </li>
      ))}
    </ul>
  );
}

function ConditionBlock({
  entry,
  explanation,
  lang,
}: {
  entry: ConditionFoods;
  explanation?: string;
  lang: Lang;
}) {
  const t = L[lang];
  const hasAvoid = entry.avoid_foods.length > 0 || entry.avoid_dishes.length > 0;
  const reasons = entry.avoid_tags.map((tag) => avoidReasonName(tag, lang)).join(t.and);
  const subhead = "mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted";
  return (
    <section className="py-5 first:pt-0 last:pb-0 print:break-inside-avoid">
      <h3 className="font-display text-base font-bold leading-6 text-ink">
        {conditionName(entry.condition, lang)}
      </h3>
      {explanation && <p className="mt-1 max-w-3xl text-sm text-ink-muted">{explanation}</p>}
      <div className="mt-3 grid gap-4 sm:grid-cols-2 print:grid-cols-2">
        <div className="rounded-md border border-ok-line bg-ok-tint/40 p-4">
          <h4 className="mb-1 flex items-center gap-1.5 font-semibold text-ok-ink">
            <IconCheck className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
            {t.eat}
          </h4>
          {entry.eat.length > 0 ? (
            <>
              <p className="mb-3 text-xs text-ink-muted">{t.eatHint}</p>
              <EatList foods={entry.eat} lang={lang} />
            </>
          ) : (
            <p className="text-sm text-ink-muted">{t.noEat}</p>
          )}
        </div>
        <div className="rounded-md border border-high-line bg-high-tint/40 p-4">
          <h4 className="mb-1 flex items-center gap-1.5 font-semibold text-high-ink">
            <IconX className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
            {t.avoid}
          </h4>
          {hasAvoid ? (
            <>
              <p className="mb-3 text-xs text-ink-muted">{t.avoidBecause(reasons)}</p>
              <div className="space-y-3">
                {entry.avoid_foods.length > 0 && (
                  <div>
                    <p className={subhead}>{t.foods}</p>
                    <AvoidList items={entry.avoid_foods} lang={lang} />
                  </div>
                )}
                {entry.avoid_dishes.length > 0 && (
                  <div>
                    <p className={subhead}>{t.dishes}</p>
                    <AvoidList items={entry.avoid_dishes} lang={lang} />
                  </div>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-ink-muted">{t.noAvoid}</p>
          )}
        </div>
      </div>
    </section>
  );
}

export function ConditionFoodsGuide({
  guide,
  rationales,
  lang,
}: {
  guide: ConditionFoods[];
  /** nutrition.patient_rationales: each condition explained to the patient */
  rationales?: Record<string, { en: string; bn: string }>;
  lang: Lang;
}) {
  return (
    <div className="divide-y divide-line">
      {guide.map((entry) => (
        <ConditionBlock
          key={entry.condition}
          entry={entry}
          explanation={rationales?.[entry.condition]?.[lang]}
          lang={lang}
        />
      ))}
    </div>
  );
}
