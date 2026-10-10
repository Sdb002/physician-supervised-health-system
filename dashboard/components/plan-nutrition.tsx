/** The figures behind a meal plan, set out so the plan can be checked rather
 * than taken on trust: carbohydrate meal by meal, each day's energy, fat and
 * sodium against the sodium limit, the cooking salt that sodium figure
 * stands on, the dishes that carry the most fat, and how the energy target
 * was worked out.
 *
 * Every number is the engine's, and so is the sodium limit. The only
 * arithmetic here is adding a meal's lines together. Plans approved before
 * engine 0.5.0 carry day totals but no per-line figures, so they show the
 * days without the meal columns and without the last two blocks. Plans from
 * before 0.6.0 were not fitted to the sodium limit and carry no salt figures:
 * they keep the over-the-limit warning. Each day's own salt is on the plan
 * itself (week-plan.tsx); this table is already as wide as its card. */

import { AssessmentResult, MealItem } from "@/lib/api";
import { MEAL_ORDER, localName, mealName, planDays, portionText, weekdayName } from "@/lib/clinical-terms";
import type { Lang } from "@/lib/use-lang";

type Plan = AssessmentResult["nutrition"]["meal_plan"];
type Anthropometrics = AssessmentResult["anthropometrics"];
type EnergyBasis = NonNullable<Anthropometrics["basis"]>;

/** Rows in the "highest in fat" list: enough to see what drives a day's fat. */
const FATTIEST_DISHES = 6;

const EQUATIONS: Record<string, string> = { mifflin_st_jeor: "Mifflin-St Jeor" };

const ACTIVITY: Record<Lang, Record<string, string>> = {
  en: { sedentary: "a sedentary day", light: "light activity", moderate: "moderate activity", active: "an active day" },
  bn: { sedentary: "কম নড়াচড়া", light: "হালকা কর্মব্যস্ততা", moderate: "মাঝারি কর্মব্যস্ততা", active: "বেশি কর্মব্যস্ততা" },
};

const L = {
  en: {
    byDay: "Nutrition by day",
    carbsByMeal: "Carbohydrate in each meal",
    day: "Day",
    everyDay: "Every day",
    average: "Average day",
    energy: "Energy",
    carbs: "Carbohydrate, g",
    wholeDay: "Whole day",
    fat: "Fat",
    sodium: "Sodium",
    kcal: "kcal",
    g: "g",
    mg: "mg",
    limit: (limit: string) => `mg, limit ${limit}`,
    overLimit: "over the limit",
    sodiumOver: (limit: string, over: string, of: string, average: string) =>
      `Sodium is above the ${limit} mg daily limit on ${over} of ${of} days (average ${average} mg).`,
    sodiumOverOneDay: (limit: string, total: string) =>
      `Sodium is above the ${limit} mg daily limit (${total} mg).`,
    sodiumWithin: (limit: string) => `Sodium stays within the ${limit} mg daily limit on every day.`,
    sodiumWithinSalted: (limit: string, salt: string, recipe: string) =>
      `Sodium stays under the ${limit} mg daily limit on every day when each day's dishes are cooked with the salt shown: ${salt} g a day on average, where their recipes list ${recipe} g.`,
    basis:
      "Portions are cooked weights, as served; fruit is weighed as eaten. The figures are worked out from each recipe's raw ingredients, including its cooking oil and salt.",
    basisSalted:
      "Portions are cooked weights, as served; fruit is weighed as eaten. The figures are worked out from each recipe's raw ingredients, including its cooking oil, with the cooking salt given for each day and none added at the table.",
    fattiest: "Dishes highest in fat this week",
    dish: "Dish",
    portion: "Portion",
    cookingFat: "of which cooking fat",
    noSaturatedFat:
      "Saturated fat is not recorded in the food table, so total fat and the fat each dish is cooked in are shown instead.",
    energyTitle: "How the energy target was worked out",
    person: (b: EnergyBasis) =>
      `${b.sex === "male" ? "Male" : "Female"}, ${b.age} years, ${b.weight_kg} kg, ${b.height_cm} cm.`,
    maintenance: (a: Anthropometrics, b: EnergyBasis, activity: string) =>
      `Resting energy ${a.ree_kcal} kcal (${EQUATIONS[b.equation] ?? b.equation}) × ${b.activity_factor} for ${activity}${
        b.activity_assumed ? ", assumed because no activity level is recorded" : ""
      } = ${a.tdee_kcal} kcal to hold weight steady.`,
    adjustment: (a: Anthropometrics, b: EnergyBasis) =>
      b.adjustment_kcal === 0
        ? `No adjustment at this body mass index (${a.bmi}, ${a.bmi_category}): ${a.target_kcal} kcal a day.`
        : `${b.adjustment_kcal < 0 ? "Less" : "Plus"} ${Math.abs(b.adjustment_kcal)} kcal for weight ${
            b.adjustment_kcal < 0 ? "loss" : "gain"
          } (body mass index ${a.bmi}, ${a.bmi_category}) = ${a.target_kcal} kcal a day.`,
    floor: (b: EnergyBasis) => `Raised to the ${b.floor_kcal} kcal minimum.`,
  },
  bn: {
    byDay: "দিনভিত্তিক পুষ্টি",
    carbsByMeal: "প্রতি বেলার শর্করা",
    day: "দিন",
    everyDay: "প্রতিদিন",
    average: "গড় দিন",
    energy: "শক্তি",
    carbs: "শর্করা, গ্রাম",
    wholeDay: "সারা দিন",
    fat: "চর্বি",
    sodium: "সোডিয়াম",
    kcal: "কিলোক্যালরি",
    g: "গ্রাম",
    mg: "মিলিগ্রাম",
    limit: (limit: string) => `মিলিগ্রাম, সীমা ${limit}`,
    overLimit: "সীমার বেশি",
    sodiumOver: (limit: string, over: string, of: string, average: string) =>
      `${of} দিনের মধ্যে ${over} দিন সোডিয়াম দৈনিক ${limit} মিলিগ্রাম সীমার বেশি (গড় ${average} মিলিগ্রাম)।`,
    sodiumOverOneDay: (limit: string, total: string) =>
      `সোডিয়াম দৈনিক ${limit} মিলিগ্রাম সীমার বেশি (${total} মিলিগ্রাম)।`,
    sodiumWithin: (limit: string) => `প্রতিদিন সোডিয়াম দৈনিক ${limit} মিলিগ্রাম সীমার মধ্যে আছে।`,
    sodiumWithinSalted: (limit: string, salt: string, recipe: string) =>
      `প্রতিদিনের রান্নায় দেখানো পরিমাণ লবণ দিলে সোডিয়াম প্রতিদিন দৈনিক ${limit} মিলিগ্রাম সীমার নিচে থাকে: গড়ে দিনে ${salt} গ্রাম, যেখানে রেসিপিতে লেখা আছে ${recipe} গ্রাম।`,
    basis:
      "পরিমাণগুলো রান্না করা খাবারের ওজন, যেভাবে পরিবেশন করা হয়; ফলের ওজন খাওয়ার অবস্থায়। হিসাবগুলো প্রতিটি রান্নার কাঁচা উপকরণ থেকে করা, রান্নার তেল ও লবণসহ।",
    basisSalted:
      "পরিমাণগুলো রান্না করা খাবারের ওজন, যেভাবে পরিবেশন করা হয়; ফলের ওজন খাওয়ার অবস্থায়। হিসাবগুলো প্রতিটি রান্নার কাঁচা উপকরণ থেকে করা, রান্নার তেলসহ; লবণ ধরা হয়েছে প্রতিদিনের জন্য দেওয়া রান্নার লবণের পরিমাণে, পাতে আলাদা লবণ ছাড়া।",
    fattiest: "এই সপ্তাহে সবচেয়ে বেশি চর্বিযুক্ত রান্না",
    dish: "রান্না",
    portion: "পরিমাণ",
    cookingFat: "এর মধ্যে রান্নার তেল-চর্বি",
    noSaturatedFat:
      "খাদ্য তালিকায় সম্পৃক্ত চর্বির তথ্য নেই, তাই মোট চর্বি এবং প্রতিটি রান্নায় ব্যবহৃত তেল-চর্বি দেখানো হয়েছে।",
    energyTitle: "শক্তির লক্ষ্য যেভাবে হিসাব করা হয়েছে",
    person: (b: EnergyBasis) =>
      `${b.sex === "male" ? "পুরুষ" : "নারী"}, বয়স ${b.age} বছর, ওজন ${b.weight_kg} কেজি, উচ্চতা ${b.height_cm} সেমি।`,
    maintenance: (a: Anthropometrics, b: EnergyBasis, activity: string) =>
      `বিশ্রামকালীন শক্তি ${a.ree_kcal} কিলোক্যালরি (${EQUATIONS[b.equation] ?? b.equation}) × ${b.activity_factor} (${activity}${
        b.activity_assumed ? ", ধরে নেওয়া হয়েছে কারণ কর্মব্যস্ততার মাত্রা নথিভুক্ত নেই" : ""
      }) = ওজন ধরে রাখতে ${a.tdee_kcal} কিলোক্যালরি।`,
    adjustment: (a: Anthropometrics, b: EnergyBasis) =>
      b.adjustment_kcal === 0
        ? `এই বডি মাস ইনডেক্সে (${a.bmi}) কোনো সমন্বয় নেই: দিনে ${a.target_kcal} কিলোক্যালরি।`
        : `ওজন ${b.adjustment_kcal < 0 ? "কমানোর" : "বাড়ানোর"} জন্য ${Math.abs(b.adjustment_kcal)} কিলোক্যালরি ${
            b.adjustment_kcal < 0 ? "কম" : "বেশি"
          } (বডি মাস ইনডেক্স ${a.bmi}) = দিনে ${a.target_kcal} কিলোক্যালরি।`,
    floor: (b: EnergyBasis) => `ন্যূনতম ${b.floor_kcal} কিলোক্যালরিতে তোলা হয়েছে।`,
  },
} as const;

function Heading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-display mb-3 text-lg font-bold leading-7 text-ink print:break-after-avoid">{children}</h2>
  );
}

// figures are right-aligned under right-aligned headers; the row's name leads on the left
const th = "px-2 py-1.5 text-right font-semibold last:pr-0";
const td = "px-2 py-2 text-right text-ink-soft last:pr-0";
const lead = "py-2 pr-2 text-left font-semibold text-ink";

export function PlanNutrition({
  plan,
  limits,
  anthropometrics,
  lang,
  staff = false,
}: {
  plan: Plan;
  /** the engine's hard limits (sodium), to set each day against */
  limits?: Record<string, number>;
  anthropometrics?: Anthropometrics;
  lang: Lang;
  /** physicians also see energy, fat, sodium, the fattiest dishes and the energy working */
  staff?: boolean;
}) {
  const t = L[lang];
  const num = (n: number) => (lang === "bn" ? Math.round(n).toLocaleString("bn-BD") : String(Math.round(n)));
  const grams = (n: number) =>
    n.toLocaleString(lang === "bn" ? "bn-BD" : "en", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  const days = planDays(plan);
  if (days.length === 0 || days.some((d) => d.totals?.carb_g == null)) return null;
  const lines = days.flatMap((d) => Object.values(d.meals).flat());
  const meals = MEAL_ORDER.filter((m) => days.some((d) => d.meals[m]?.length));
  // engine 0.5.0 onwards: every line reports its own carbohydrate, fat and sodium
  const perLine = lines.length > 0 && lines.every((it) => it.carb_g != null && it.fat_g != null);
  const mealCarbs = (items: MealItem[] = []) => items.reduce((sum, it) => sum + (it.carb_g ?? 0), 0);

  const sodiumLimit = limits?.sodium_mg;
  const daysOver = sodiumLimit ? days.filter((d) => (d.totals?.sodium_mg ?? 0) > sodiumLimit) : [];
  const averageSodium = plan.totals?.sodium_mg ?? 0;
  // engine 0.6.0 onwards: the sodium figures count the plan's cooking salt,
  // which can be less than the recipes list
  const salted = plan.salt_g != null && plan.recipe_salt_g != null;
  const averageSalt = plan.salt_g ?? 0;
  const averageRecipeSalt = plan.recipe_salt_g ?? 0;

  const dishes = new Map<string, MealItem>();
  if (perLine) {
    for (const line of lines) {
      const seen = line.recipe_id ? dishes.get(line.recipe_id) : undefined;
      // a dish served in two sizes is listed at its larger portion
      if (line.recipe_id && (!seen || (line.fat_g ?? 0) > (seen.fat_g ?? 0))) dishes.set(line.recipe_id, line);
    }
  }
  const fattiest = [...dishes.values()].sort((a, b) => (b.fat_g ?? 0) - (a.fat_g ?? 0)).slice(0, FATTIEST_DISHES);

  const basis = anthropometrics?.basis;

  return (
    <>
      {/* the tables may run on to the next page (never stranding a row or two:
          .keep-rows) rather than leave the end of this one empty */}
      <section>
        <Heading>{staff ? t.byDay : t.carbsByMeal}</Heading>
        <div className="overflow-x-auto">
          <table className="keep-rows w-full text-left text-sm">
            <thead className="border-b border-line-strong text-ink-muted">
              <tr className="align-bottom">
                <th scope="col" rowSpan={2} className="py-1.5 pr-2 text-left font-semibold">{t.day}</th>
                {staff && <th scope="col" className={`${th} pb-0`}>{t.energy}</th>}
                <th scope="colgroup" colSpan={(perLine ? meals.length : 0) + 1} className="px-2 pb-0 pt-1.5 font-semibold last:pr-0">
                  <span className={perLine ? "block border-b border-line pb-1 text-center" : "block text-right"}>
                    {t.carbs}
                  </span>
                </th>
                {staff && <th scope="col" className={`${th} pb-0`}>{t.fat}</th>}
                {staff && <th scope="col" className={`${th} pb-0`}>{t.sodium}</th>}
              </tr>
              <tr className="align-bottom font-normal">
                {staff && <th scope="col" className={`${th} font-normal`}>{t.kcal}</th>}
                {perLine &&
                  meals.map((meal) => (
                    <th key={meal} scope="col" className={`${th} font-normal`}>{mealName(meal, lang)}</th>
                  ))}
                <th scope="col" className={`${th} font-normal`}>{t.wholeDay}</th>
                {staff && <th scope="col" className={`${th} font-normal`}>{t.g}</th>}
                {staff && (
                  <th scope="col" className={`${th} font-normal`}>
                    {sodiumLimit ? t.limit(num(sodiumLimit)) : t.mg}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {days.map((d) => {
                const over = daysOver.includes(d);
                return (
                  <tr key={d.day}>
                    <th scope="row" className={lead}>
                      {d.weekday ? weekdayName(d.weekday, lang) : t.everyDay}
                    </th>
                    {staff && <td className={td}>{num(d.totals!.kcal)}</td>}
                    {perLine && meals.map((meal) => <td key={meal} className={td}>{num(mealCarbs(d.meals[meal]))}</td>)}
                    <td className={`${td} font-semibold text-ink`}>{num(d.totals!.carb_g)}</td>
                    {staff && <td className={td}>{num(d.totals!.fat_g)}</td>}
                    {staff && (
                      <td className={over ? `${td} font-bold text-watch-ink` : td}>
                        {num(d.totals!.sodium_mg)}
                        {over && <span className="sr-only">, {t.overLimit}</span>}
                      </td>
                    )}
                  </tr>
                );
              })}
              {days.length > 1 && (
                <tr className="border-t border-line-strong">
                  <th scope="row" className={lead}>{t.average}</th>
                  {staff && <td className={`${td} font-semibold text-ink`}>{num(plan.totals.kcal)}</td>}
                  {perLine &&
                    meals.map((meal) => (
                      <td key={meal} className={td}>
                        {num(days.reduce((sum, d) => sum + mealCarbs(d.meals[meal]), 0) / days.length)}
                      </td>
                    ))}
                  <td className={`${td} font-semibold text-ink`}>{num(plan.totals.carb_g)}</td>
                  {staff && <td className={`${td} font-semibold text-ink`}>{num(plan.totals.fat_g)}</td>}
                  {staff && (
                    <td
                      className={
                        sodiumLimit && averageSodium > sodiumLimit
                          ? `${td} font-bold text-watch-ink`
                          : `${td} font-semibold text-ink`
                      }
                    >
                      {num(averageSodium)}
                    </td>
                  )}
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {staff && sodiumLimit ? (
          daysOver.length > 0 ? (
            <p className="mt-3 rounded-md border border-watch-line bg-watch-tint px-4 py-2 text-sm font-semibold text-watch-ink">
              {days.length > 1
                ? t.sodiumOver(num(sodiumLimit), num(daysOver.length), num(days.length), num(averageSodium))
                : t.sodiumOverOneDay(num(sodiumLimit), num(averageSodium))}
            </p>
          ) : (
            <p className="mt-3 text-sm text-ink-soft">
              {salted && averageSalt < averageRecipeSalt
                ? t.sodiumWithinSalted(num(sodiumLimit), grams(averageSalt), grams(averageRecipeSalt))
                : t.sodiumWithin(num(sodiumLimit))}
            </p>
          )
        ) : null}
        <p className="mt-2 text-sm text-ink-muted">{salted ? t.basisSalted : t.basis}</p>
      </section>

      {staff && anthropometrics && basis && (
        <section className="print:break-inside-avoid">
          <Heading>{t.energyTitle}</Heading>
          <p className="text-sm leading-6 text-ink-soft">
            {t.person(basis)} {t.maintenance(anthropometrics, basis, ACTIVITY[lang][basis.activity] ?? basis.activity)}{" "}
            {t.adjustment(anthropometrics, basis)}
            {basis.floor_applied && ` ${t.floor(basis)}`}
          </p>
        </section>
      )}

      {staff && fattiest.length > 0 && (
        <section>
          <Heading>{t.fattiest}</Heading>
          <div className="overflow-x-auto">
            <table className="keep-rows w-full text-left text-sm">
              <thead className="border-b border-line-strong text-ink-muted">
                <tr className="align-bottom">
                  <th scope="col" className="py-1.5 pr-2 text-left font-semibold">{t.dish}</th>
                  <th scope="col" className={`${th} text-left`}>{t.portion}</th>
                  <th scope="col" className={th}>{t.energy}, {t.kcal}</th>
                  <th scope="col" className={th}>{t.fat}, {t.g}</th>
                  <th scope="col" className={th}>{t.cookingFat}, {t.g}</th>
                  <th scope="col" className={th}>{t.sodium}, {t.mg}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {fattiest.map((line) => (
                  <tr key={line.recipe_id}>
                    <th scope="row" className={lead}>{localName(line, lang)}</th>
                    <td className={`${td} whitespace-nowrap text-left`}>{portionText(line, lang)}</td>
                    <td className={td}>{num(line.kcal)}</td>
                    <td className={`${td} font-semibold text-ink`}>{num(line.fat_g ?? 0)}</td>
                    <td className={td}>{line.cooking_fat_g != null ? num(line.cooking_fat_g) : "—"}</td>
                    <td className={td}>{num(line.sodium_mg ?? 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-sm text-ink-muted">{t.noSaturatedFat}</p>
        </section>
      )}
    </>
  );
}
