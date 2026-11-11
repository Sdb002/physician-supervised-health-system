/* The Bangla interface text must cover what the screens ask for. Run with
 * `npm test`. */

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { BN, bnDigits, translate } from "./ui-text.ts";

const ROOT = join(import.meta.dirname, "..");

function sources(folder: string): string[] {
  return readdirSync(join(ROOT, folder), { recursive: true, encoding: "utf-8" })
    .filter((name) => /\.tsx?$/.test(name) && !name.endsWith(".test.ts") && !name.endsWith("ui-text.ts"))
    .map((name) => join(ROOT, folder, name));
}

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

test("every sentence a screen passes to t() or rich() has Bangla", () => {
  const call = /\b(?:t|rich)\(\s*"((?:[^"\\]|\\.)*)"/g;
  const missing: string[] = [];
  for (const file of ["app", "components", "lib"].flatMap(sources)) {
    for (const match of readFileSync(file, "utf-8").matchAll(call)) {
      const sentence = JSON.parse(`"${match[1]}"`);
      if (!(sentence in BN)) missing.push(`${file}: ${sentence}`);
    }
  }
  assert.deepEqual(missing, []);
});

test("the options a patient form offers have Bangla", () => {
  const options = readFileSync(join(ROOT, "lib", "patient-options.ts"), "utf-8");
  const words = [...options.matchAll(/\b(?:label|hint): "([^"]+)"/g)].map((m) => m[1]);
  assert.ok(words.length > 30);
  assert.deepEqual(words.filter((word) => !(word in BN)), []);
});

test("a translation keeps the placeholders of its sentence", () => {
  for (const [en, bn] of Object.entries(BN)) {
    assert.deepEqual(placeholders(bn), placeholders(en), en);
  }
});

test("translate fills placeholders, with Bangla digits in Bangla", () => {
  assert.equal(translate("en", "{value} kg", { value: 61.5 }), "61.5 kg");
  assert.equal(translate("bn", "{value} kg", { value: 61.5 }), "৬১.৫ কেজি");
  // a name or an id passed as text is left as it is
  assert.equal(translate("bn", "Welcome back, {name}", { name: "Dr. Rahman 2" }), "স্বাগতম, Dr. Rahman 2");
  assert.equal(bnDigits("1539"), "১৫৩৯");
});

test("a sentence with no Bangla stays English, digits and all", () => {
  assert.equal(translate("bn", "no such sentence {n}", { n: 5 }), "no such sentence 5");
  assert.equal(translate("bn", "incorrect email or password"), "ইমেইল বা পাসওয়ার্ড ভুল");
});
