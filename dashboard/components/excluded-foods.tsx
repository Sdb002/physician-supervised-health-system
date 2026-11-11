"use client";

import { useEffect, useMemo, useState } from "react";
import { AllowedFood, ExcludableFood, ExcludedFood, ExcludedFoodPick, api } from "@/lib/api";
import { localName, mealItemKey } from "@/lib/clinical-terms";
import { useT, type T } from "@/lib/use-t";
import { FoodCombobox } from "@/components/FoodCombobox";
import { IconX } from "@/components/icons";

/* The single foods and dishes a patient does not eat, beyond the tick-box
 * restrictions: picked from the food table and the recipe list, shown as a
 * removable list. The forms keep the entries and send each one's id and
 * name; the engine leaves each food out in every form, with every dish that
 * uses it. */

/** What a form sends for the entries it holds. */
export const excludedFoodPicks = (foods: ExcludedFood[]): ExcludedFoodPick[] =>
  foods.map(({ id, name_en }) => ({ id, name_en }));

/** An entry is its id under its name: after a food-table replacement an old
 * entry and the food that now has its id are two different things. */
const entryKey = (food: ExcludedFoodPick) => `${food.id}|${food.name_en}`;

/** The picker has no recommended picks; one array, so its memos hold. */
const NO_RECOMMENDED: AllowedFood[] = [];

/** What leaving an item out takes with it, as the picker's rows say it. */
function reach(food: ExcludableFood, t: T): string {
  if (food.kind === "recipe") return t("dish");
  if (food.dishes === 0) return t("in no dish");
  return food.dishes === 1 ? t("in 1 dish") : t("in {count} dishes", { count: food.dishes });
}

/** The picker lists dishes and foods the way the plan editor does. */
const asOption = (food: ExcludableFood): AllowedFood => ({
  kind: food.kind,
  ...(food.kind === "recipe" ? { recipe_id: food.id } : { food_id: food.id }),
  name_en: food.name_en,
  name_bn: food.name_bn,
  food_group: food.food_group,
  kcal_per_100g: 0,
  keywords: food.keywords,
});

const removeButton =
  "-mr-1 cursor-pointer rounded p-0.5 text-ink-muted hover:bg-crit-tint hover:text-crit-ink " +
  "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-crit-mark";

export function ExcludedFoodsField({
  value,
  onChange,
  label,
}: {
  value: ExcludedFood[];
  onChange: (next: ExcludedFood[]) => void;
  /** Accessible name of the search field, in the form's own voice. */
  label?: string;
}) {
  const { t, lang } = useT();
  const [catalogue, setCatalogue] = useState<ExcludableFood[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api
      .foodCatalogue()
      .then(setCatalogue)
      .catch(() => setFailed(true));
  }, []);

  const byId = useMemo(() => new Map((catalogue ?? []).map((f) => [f.id, f])), [catalogue]);
  // A search for "rice" matches thirty dishes and the one food that takes all
  // of them along: single foods come first, the most cooked-with at the top.
  const mostUsedFoodFirst = useMemo(() => {
    const rank = (option: AllowedFood) => {
      const food = byId.get(mealItemKey(option));
      return !food || food.kind === "recipe" ? -1 : food.dishes;
    };
    return (a: AllowedFood, b: AllowedFood) => rank(b) - rank(a) || a.name_en.localeCompare(b.name_en);
  }, [byId]);
  // what is already chosen is not offered again
  const options = useMemo(() => {
    const chosen = new Set(value.map(entryKey));
    return (catalogue ?? []).filter((f) => !chosen.has(entryKey(f))).map(asOption);
  }, [catalogue, value]);

  const add = (option: AllowedFood) => {
    const food = byId.get(mealItemKey(option));
    if (food) {
      onChange([...value, { id: food.id, kind: food.kind, name_en: food.name_en, name_bn: food.name_bn }]);
    }
  };

  return (
    <div className="space-y-2.5">
      {failed ? (
        <p className="text-sm text-ink-muted">
          {t("The food list could not be loaded, so nothing can be added here just now. Reload the page to try again.")}
        </p>
      ) : (
        <FoodCombobox
          foods={options}
          recommended={NO_RECOMMENDED}
          onSelect={add}
          label={label ?? t("Search a food or dish the patient does not eat")}
          placeholder={catalogue ? t("Search foods and dishes…") : t("Loading the food list…")}
          detail={(option) => {
            const food = byId.get(mealItemKey(option));
            return food ? reach(food, t) : "";
          }}
          compare={mostUsedFoodFirst}
        />
      )}
      {value.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label={t("Left out for this patient")}>
          {value.map((item) => (
            <li
              key={entryKey(item)}
              className="inline-flex items-center gap-1.5 rounded-md border border-line bg-surface-soft py-1 pl-2.5 pr-2 text-sm text-ink-strong"
            >
              <span>
                {localName(item, lang)}
                {item.name_bn && (
                  <span className="text-ink-muted"> · {lang === "bn" ? item.name_en : item.name_bn}</span>
                )}
              </span>
              <button
                type="button"
                aria-label={t("Stop leaving out {name}", { name: localName(item, lang) })}
                onClick={() => onChange(value.filter((v) => entryKey(v) !== entryKey(item)))}
                className={removeButton}
              >
                <IconX className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
