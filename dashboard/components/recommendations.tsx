/** Recommended foods and recommended home recipes — the two separate
 * sections of the diet recommendation, shared by the report, the patient
 * portal and the review page. */

import { RecommendedFood, RecommendedRecipe } from "@/lib/api";
import { IconChevronRight, IconClock } from "@/components/icons";
import { focusRing } from "@/components/ui";

type Lang = "en" | "bn";

const L = {
  en: {
    perServing: "per serving",
    serving: "1 serving",
    serves: "Serves",
    min: "min",
    kcal: "kcal",
    per100g: "kcal / 100 g",
    cookedAtHome: (score: number) => `Cooked at home: ${score} out of 10`,
    details: "Ingredients & method",
    ingredients: "Ingredients",
    method: "Method",
    optional: "optional",
    englishOnly: "",
    dish: "Dish",
    type: "Type",
    cooked: "Cooked at home",
    time: "Time",
  },
  bn: {
    perServing: "প্রতি পরিবেশন",
    serving: "১ পরিবেশন",
    serves: "পরিবেশন সংখ্যা",
    min: "মিনিট",
    kcal: "কিলোক্যালরি",
    per100g: "কিলোক্যালরি / ১০০ গ্রাম",
    cookedAtHome: (score: number) => `ঘরে রান্নার হার: ১০-এর মধ্যে ${score}`,
    details: "উপকরণ ও রান্নার পদ্ধতি",
    ingredients: "উপকরণ",
    method: "রান্নার পদ্ধতি",
    optional: "ঐচ্ছিক",
    englishOnly: "উপকরণের মাপ ও রান্নার ধাপ ইংরেজিতে দেওয়া আছে।",
    dish: "রান্না",
    type: "ধরন",
    cooked: "ঘরে রান্নার হার",
    time: "সময়",
  },
} as const;

const FOOD_GROUPS: Record<Lang, Record<string, string>> = {
  en: {
    grain: "Grain", legume: "Pulse / legume", vegetable: "Vegetable", fruit: "Fruit",
    fish: "Fish", meat: "Meat", egg: "Egg", dairy: "Dairy", oil: "Oil / fat",
    sweet: "Sweet", spice: "Spice", other: "Other",
  },
  bn: {
    grain: "শস্য", legume: "ডাল ও শিম", vegetable: "সবজি", fruit: "ফল", fish: "মাছ",
    meat: "মাংস", egg: "ডিম", dairy: "দুধ ও দুগ্ধজাত", oil: "তেল ও চর্বি",
    sweet: "মিষ্টি", spice: "মসলা", other: "অন্যান্য",
  },
};

// recipe dataset vocabularies (data/recipe/schema.md) — English is the source
const RECIPE_CATEGORIES_BN: Record<string, string> = {
  Vegetable: "সবজি", Fish: "মাছ", Meat: "মাংস", Bhorta: "ভর্তা",
  "Rice & Grain": "ভাত ও শস্য", "Bread & Pitha": "রুটি ও পিঠা", "Leafy Green": "শাক",
  Sweet: "মিষ্টি", Dal: "ডাল", Snack: "নাস্তা", Egg: "ডিম", Beverage: "পানীয়",
  "Salad & Chutney": "সালাদ ও চাটনি",
};
const DIET_TYPES_BN: Record<string, string> = {
  Vegan: "সম্পূর্ণ নিরামিষ", Vegetarian: "নিরামিষ", "Ovo-vegetarian": "ডিমসহ নিরামিষ",
  Pescatarian: "মাছসহ নিরামিষ", "Non-vegetarian": "আমিষ",
};
const FREQUENCY_TIERS_BN: Record<string, string> = {
  "Daily staple": "প্রতিদিনের প্রধান খাবার", "Near-daily": "প্রায় প্রতিদিন",
  "Very frequent": "খুব ঘন ঘন", Frequent: "প্রায়ই", Weekly: "সাপ্তাহিক",
  Regular: "নিয়মিত", Occasional: "মাঝে মাঝে", "Festive/seasonal": "উৎসব/মৌসুমি",
  "Rare/special": "বিশেষ উপলক্ষে",
};

const local = (table: Record<string, string>, lang: Lang, value: string) =>
  (lang === "bn" && table[value]) || value;

const nameOf = (item: { name_en: string; name_bn: string }, lang: Lang) =>
  (lang === "bn" && item.name_bn) || item.name_en;

/** 10 ticks filled up to the household frequency score — the label carries
 * the number in words, so the bar is never the only channel. */
export function FrequencyMeter({ score, lang }: { score: number; lang: Lang }) {
  return (
    <span role="img" aria-label={L[lang].cookedAtHome(score)} className="inline-flex items-center gap-0.5">
      {Array.from({ length: 10 }, (_, i) => (
        <span
          key={i}
          aria-hidden="true"
          className={`h-2.5 w-1.5 rounded-xs ${i < score ? "bg-clinical" : "bg-line"}`}
        />
      ))}
    </span>
  );
}

export function RecommendedFoodsList({ foods, lang }: { foods: RecommendedFood[]; lang: Lang }) {
  const t = L[lang];
  return (
    <ol className="grid gap-x-8 sm:grid-cols-2">
      {foods.map((food, index) => (
        <li
          key={food.food_id}
          className="flex items-baseline gap-3 border-b border-line py-2.5 print:border-line"
        >
          <span className="w-5 shrink-0 text-right text-sm font-semibold text-ink-muted">
            {index + 1}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block font-medium leading-snug text-ink">{nameOf(food, lang)}</span>
            {food.food_group && (
              <span className="block text-sm text-ink-muted">
                {FOOD_GROUPS[lang][food.food_group] ?? food.food_group}
              </span>
            )}
          </span>
          {food.kcal_per_100g != null && (
            <span className="shrink-0 text-right text-sm text-ink-soft">
              {food.kcal_per_100g}
              <span className="block text-xs text-ink-muted">{t.per100g}</span>
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}

/** The same ranking for paper: one line a dish, with the figures in columns
 * a reader can run a finger down. Ingredients and method stay on screen. */
export function RecommendedRecipesTable({ recipes, lang }: { recipes: RecommendedRecipe[]; lang: Lang }) {
  const t = L[lang];
  // assessments from before the recipe dataset carry a name and an energy
  // only; a column with nothing in it is left out rather than printed blank
  const has = {
    type: recipes.some((r) => r.category || r.diet_type),
    cooked: recipes.some((r) => r.weekly_frequency_score != null),
    serving: recipes.some((r) => r.serving_size_g != null),
    time: recipes.some((r) => r.total_time_min != null),
  };
  return (
    <table className="keep-rows hidden w-full text-left text-sm print:table">
      <thead className="border-b border-line-strong text-ink-muted">
        <tr className="align-bottom">
          <th scope="col" className="w-6" />
          <th scope="col" className="py-1.5 pr-3 font-semibold">{t.dish}</th>
          {has.type && <th scope="col" className="px-3 py-1.5 font-semibold">{t.type}</th>}
          {has.cooked && <th scope="col" className="px-3 py-1.5 font-semibold">{t.cooked}</th>}
          {has.serving && (
            <th scope="col" className="whitespace-nowrap px-3 py-1.5 text-right font-semibold">{t.serving}</th>
          )}
          <th scope="col" className="py-1.5 pl-3 text-right font-semibold">
            {t.kcal} {t.perServing}
          </th>
          {has.time && <th scope="col" className="py-1.5 pl-6 text-right font-semibold">{t.time}</th>}
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {recipes.map((recipe, index) => {
          const score = recipe.weekly_frequency_score;
          const meta = [
            recipe.category && local(RECIPE_CATEGORIES_BN, lang, recipe.category),
            recipe.diet_type && local(DIET_TYPES_BN, lang, recipe.diet_type),
          ].filter((m): m is string => Boolean(m));
          return (
            <tr key={recipe.recipe_id}>
              <td className="py-2 pr-3 text-right align-top font-semibold text-ink-muted">{index + 1}</td>
              <td className="py-2 pr-3 align-top font-semibold text-ink">{nameOf(recipe, lang)}</td>
              {has.type && <td className="px-3 py-2 align-top text-ink-soft">{meta.join(", ")}</td>}
              {has.cooked && (
                <td className="px-3 py-2 align-top text-ink-soft">
                  {score != null && (
                    <span className="inline-flex items-center gap-2 whitespace-nowrap">
                      <FrequencyMeter score={score} lang={lang} />
                      {recipe.frequency_tier
                        ? local(FREQUENCY_TIERS_BN, lang, recipe.frequency_tier)
                        : `${score}/10`}
                    </span>
                  )}
                </td>
              )}
              {has.serving && (
                <td className="whitespace-nowrap px-3 py-2 text-right align-top text-ink-soft">
                  {recipe.serving_size_g != null && `${Math.round(recipe.serving_size_g)} g`}
                </td>
              )}
              <td className="py-2 pl-3 text-right align-top font-semibold text-ink">
                {Math.round(recipe.per_serving_kcal)}
              </td>
              {has.time && (
                <td className="whitespace-nowrap py-2 pl-6 text-right align-top text-ink-soft">
                  {recipe.total_time_min != null && `${recipe.total_time_min} ${t.min}`}
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function RecommendedRecipesList({
  recipes,
  lang,
  showDetails = true,
  showNotes = false,
}: {
  recipes: RecommendedRecipe[];
  lang: Lang;
  /** ingredients + method behind a disclosure; off for compact summaries */
  showDetails?: boolean;
  /** the dataset's dish notes, incl. clinical cautions — for the physician */
  showNotes?: boolean;
}) {
  const t = L[lang];
  return (
    <ol className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface print:border-line">
      {recipes.map((recipe, index) => {
        const score = recipe.weekly_frequency_score;
        const meta = [
          recipe.category && local(RECIPE_CATEGORIES_BN, lang, recipe.category),
          recipe.diet_type && local(DIET_TYPES_BN, lang, recipe.diet_type),
        ].filter((m): m is string => Boolean(m));
        return (
          <li key={recipe.recipe_id} className="break-inside-avoid px-4 py-4 sm:px-5">
            <div className="flex items-start gap-3.5">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-line-strong text-sm font-bold text-ink-soft">
                {index + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                  <h3 className="text-lg font-semibold leading-snug text-ink">{nameOf(recipe, lang)}</h3>
                  <p className="text-sm text-ink-soft">
                    <strong className="font-bold text-ink">{Math.round(recipe.per_serving_kcal)}</strong>{" "}
                    {t.kcal} {t.perServing}
                  </p>
                </div>
                {meta.length > 0 && (
                  <p className="mt-0.5 flex flex-wrap gap-x-3 text-sm text-ink-muted">
                    {meta.map((m) => (
                      <span key={m}>{m}</span>
                    ))}
                  </p>
                )}
                {showNotes && recipe.notes && (
                  <p className="mt-1.5 text-sm text-ink-soft">{recipe.notes}</p>
                )}
                <div className="mt-2.5 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-ink-soft">
                  {score != null && (
                    <span className="inline-flex items-center gap-2">
                      <FrequencyMeter score={score} lang={lang} />
                      <span>
                        {recipe.frequency_tier
                          ? local(FREQUENCY_TIERS_BN, lang, recipe.frequency_tier)
                          : `${score}/10`}
                      </span>
                    </span>
                  )}
                  {recipe.serving_size_g != null && (
                    <span>
                      {t.serving} ≈ {Math.round(recipe.serving_size_g)} g
                      {recipe.servings ? `, ${t.serves.toLowerCase()} ${recipe.servings}` : ""}
                    </span>
                  )}
                  {recipe.total_time_min != null && (
                    <span className="inline-flex items-center gap-1">
                      <IconClock className="h-4 w-4" />
                      {recipe.total_time_min} {t.min}
                    </span>
                  )}
                </div>

                {showDetails && (recipe.ingredients?.length || recipe.steps?.length) ? (
                  <details className="group mt-3">
                    <summary
                      className={`inline-flex cursor-pointer list-none items-center gap-1 rounded text-sm font-semibold text-clinical hover:underline print:hidden ${focusRing}`}
                    >
                      <IconChevronRight className="h-4 w-4 transition-transform duration-150 group-open:rotate-90" />
                      {t.details}
                    </summary>
                    <div className="mt-3 grid gap-5 rounded-md bg-surface-soft p-4 sm:grid-cols-5">
                      {recipe.ingredients?.length ? (
                        <div className="sm:col-span-2">
                          <h4 className="text-sm font-semibold text-ink">{t.ingredients}</h4>
                          <ul className="mt-1.5 space-y-1 text-sm text-ink-soft">
                            {recipe.ingredients.map((ing, i) => (
                              <li key={i}>
                                {ing.household_measure || nameOf(ing, lang)}
                                {ing.optional && <span className="text-ink-muted"> ({t.optional})</span>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {recipe.steps?.length ? (
                        <div className="sm:col-span-3">
                          <h4 className="text-sm font-semibold text-ink">{t.method}</h4>
                          <ol className="mt-1.5 list-decimal space-y-1.5 pl-5 text-sm leading-6 text-ink-soft marker:font-semibold marker:text-ink-muted">
                            {recipe.steps.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      ) : null}
                    </div>
                    {t.englishOnly && <p className="mt-2 text-xs text-ink-muted">{t.englishOnly}</p>}
                  </details>
                ) : null}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
