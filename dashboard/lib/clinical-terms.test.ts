/* Unit tests for the display helpers. Run with `npm test`: Node's own test
 * runner executes the TypeScript directly, so there is no extra tooling. */

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  bmiCategoryName,
  conditionName,
  foodDisplayName,
  mealItemKey,
  planDays,
  portionText,
  saltCutPercent,
  todayIndex,
  weekdayName,
} from "./clinical-terms.ts";
import { byTriage, riskLabel } from "./triage.ts";

const line = (over: object = {}) => ({ name_en: "Dal", name_bn: "ডাল", qty_g: 216, kcal: 169, ...over });

test("a dish portion reads as household servings with its weight", () => {
  assert.equal(portionText({ recipe_id: "BDR-021", servings: 1, qty_g: 216 }), "1 serving, 216 g");
  assert.equal(portionText({ recipe_id: "BDR-001", servings: 1.5, qty_g: 364.4 }), "1½ servings, 364 g");
  assert.equal(portionText({ recipe_id: "BDR-021", servings: 0.75, qty_g: 162 }), "¾ serving, 162 g");
  // a physician's edit by weight rarely lands on a household fraction
  assert.equal(portionText({ recipe_id: "BDR-021", servings: 0.93, qty_g: 200 }), "0.9 serving, 200 g");
});

test("a single food reads by weight alone", () => {
  assert.equal(portionText({ qty_g: 130 }), "130 g");
  assert.equal(portionText({ qty_g: 130 }, "bn"), "১৩০ গ্রাম");
});

test("Bangla portions use Bangla digits and keep the fraction signs", () => {
  assert.equal(portionText({ recipe_id: "BDR-001", servings: 1.5, qty_g: 365 }, "bn"), "১½ পরিবেশন, ৩৬৫ গ্রাম");
});

test("a week plan is read day by day; a one-day plan becomes a single day", () => {
  const week = { days: [{ day: 1, weekday: "saturday", meals: { lunch: [line()] }, totals: { kcal: 1800 } }] };
  assert.equal(planDays(week), week.days);

  const oneDay = planDays({ meals: { lunch: [line()] }, totals: { kcal: 1800 }, salt_g: 4.2, recipe_salt_g: 6.5 });
  assert.equal(oneDay.length, 1);
  assert.equal(oneDay[0].weekday, undefined);
  assert.deepEqual([oneDay[0].salt_g, oneDay[0].recipe_salt_g], [4.2, 6.5]);

  assert.deepEqual(planDays(undefined), []);
  assert.deepEqual(planDays({}), []);
});

test("the salt cut is how much less than the recipes a day takes", () => {
  assert.equal(saltCutPercent({ salt_g: 4.2, recipe_salt_g: 6.5 }), 35);
  // cooked as the recipes say
  assert.equal(saltCutPercent({ salt_g: 4.3, recipe_salt_g: 4.3 }), 0);
  // a plan from before the sodium limit was enforced carries no salt figures
  assert.equal(saltCutPercent({}), 0);
  assert.equal(saltCutPercent({ salt_g: 0, recipe_salt_g: 0 }), 0);
});

test("a plan opens on today's weekday when it has one", () => {
  const days = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"].map((weekday, i) => ({
    day: i + 1,
    weekday,
    meals: {},
  }));
  const today = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][new Date().getDay()];
  assert.equal(days[todayIndex(days)].weekday, today);
  assert.equal(todayIndex([{ day: 1, meals: {} }]), 0);
});

test("food-table names are shown the way people say them", () => {
  assert.equal(foodDisplayName("Guava, green, raw"), "Guava, green");
  assert.equal(foodDisplayName("Milk, cow, whole fat (pasteurized, UTH)"), "Milk, cow, whole fat");
  assert.equal(foodDisplayName("raw"), "raw");
});

test("engine keys read as words in both languages", () => {
  assert.equal(conditionName("chronic_kidney_disease"), "Kidney disease");
  assert.equal(conditionName("hypertension", "bn"), "উচ্চ রক্তচাপ");
  assert.equal(bmiCategoryName("obese", "bn"), "স্থূলতা");
  assert.equal(weekdayName("saturday", "en", true), "Sat");
  // a key nobody has translated yet still reads as language, not an identifier
  assert.equal(conditionName("some_new_condition", "bn"), "Some new condition");
});

test("a plan line is identified by its dish or its food", () => {
  assert.equal(mealItemKey({ recipe_id: "BDR-001" }), "BDR-001");
  assert.equal(mealItemKey({ food_id: "F001" }), "F001");
  assert.equal(mealItemKey({}), "");
});

test("the review queue puts the highest risk first, then the longest wait", () => {
  const item = (risk: string, created: string) =>
    ({ assessment: { result: { overall_risk: risk } }, visit: { created_at: created } }) as Parameters<typeof byTriage>[0];
  const queue = [
    item("low", "2026-10-01T08:00:00Z"),
    item("critical", "2026-10-03T08:00:00Z"),
    item("low", "2026-09-28T08:00:00Z"),
    item("high", "2026-10-02T08:00:00Z"),
  ].sort(byTriage);
  assert.deepEqual(
    queue.map((q) => [q.assessment.result.overall_risk, q.visit.created_at.slice(0, 10)]),
    [["critical", "2026-10-03"], ["high", "2026-10-02"], ["low", "2026-09-28"], ["low", "2026-10-01"]]
  );
  assert.equal(riskLabel("none"), "No risk flags");
  assert.equal(riskLabel("moderate"), "Moderate risk");
});
