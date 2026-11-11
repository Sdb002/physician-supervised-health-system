import type { Lang } from "./use-lang";

/* The interface in Bangla, for the screens that are written in English in
 * their own files: staff (doctor, admin), sign-in and registration, and the
 * components they share. The English sentence is the key, so a screen reads
 * as it always did and a sentence with no entry here simply stays English.
 * The patient's own pages keep their two languages side by side in each file.
 *
 * Display wording only. Clinical terms follow lib/clinical-terms.ts and
 * src/api/report_template.py so every screen says a thing the same way.
 * What the engine writes for the physician (cautions, rationales, exercise
 * instructions, recipe notes) comes from the API in English and is not
 * translated here. lib/ui-text.test.ts fails when a sentence a screen asks
 * for is missing, or when a {placeholder} differs between the two languages. */

export type Vars = Record<string, string | number>;

const BN_DIGITS = "০১২৩৪৫৬৭৮৯";

/** 1539 -> ১৫৩৯. Decimal points and signs are left as they are. */
export const bnDigits = (text: string) => text.replace(/\d/g, (d) => BN_DIGITS[Number(d)]);

/** The sentence in `lang`, placeholders still in it. */
export function template(lang: Lang, en: string): string {
  return lang === "bn" ? BN[en] ?? en : en;
}

/** The sentence in `lang` with its {placeholders} filled. Numbers take Bangla
 * digits when the sentence itself is in Bangla. */
export function translate(lang: Lang, en: string, vars?: Vars): string {
  const translated = lang === "bn" && en in BN;
  const text = translated ? BN[en] : en;
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (placeholder, name: string) => {
    const value = vars[name];
    if (value === undefined) return placeholder;
    return translated && typeof value === "number" ? bnDigits(String(value)) : String(value);
  });
}

export const BN: Record<string, string> = {
  // ---- words used on many screens
  Search: "খুঁজুন",
  "Search…": "খুঁজুন…",
  Cancel: "বাতিল",
  Close: "বন্ধ করুন",
  Dialog: "ডায়ালগ",
  Edit: "সম্পাদনা",
  None: "নেই",
  none: "নেই",
  Notes: "নোট",
  "Notes (optional)": "নোট (ঐচ্ছিক)",
  "Saving…": "সংরক্ষণ হচ্ছে…",
  "Save changes": "পরিবর্তন সংরক্ষণ করুন",
  Reject: "প্রত্যাখ্যান",
  Approve: "অনুমোদন",
  Status: "অবস্থা",
  Actions: "কাজ",
  Date: "তারিখ",
  Report: "রিপোর্ট",
  Review: "পর্যালোচনা",
  Patient: "রোগী",
  Patients: "রোগী",
  Doctor: "চিকিৎসক",
  Doctors: "চিকিৎসক",
  Admin: "অ্যাডমিন",
  Administrator: "অ্যাডমিন",
  Sex: "লিঙ্গ",
  Female: "নারী",
  Male: "পুরুষ",
  Age: "বয়স",
  "{age} y": "{age} বছর",
  Height: "উচ্চতা",
  "{value} cm": "{value} সেমি",
  Weight: "ওজন",
  "{value} kg": "{value} কেজি",
  "Sex, age": "লিঙ্গ, বয়স",
  Pregnant: "গর্ভবতী",
  "Known conditions": "জানা রোগ",
  Conditions: "রোগ",
  Registered: "নিবন্ধনের তারিখ",
  "Dark screen": "গাঢ় পর্দা",
  "Light screen": "হালকা পর্দা",
  "Toggle dark mode": "গাঢ় পর্দা চালু বা বন্ধ করুন",
  "{title} across {count} visits": "{count}টি ভিজিটে {title}",

  // ---- statuses, roles, risk
  Pending: "অপেক্ষমাণ",
  Waiting: "অপেক্ষমাণ",
  Approved: "অনুমোদিত",
  Rejected: "প্রত্যাখ্যাত",
  Active: "সক্রিয়",
  All: "সব",
  "No risk flags": "ঝুঁকির চিহ্ন নেই",
  "Low risk": "কম ঝুঁকি",
  "Moderate risk": "মাঝারি ঝুঁকি",
  "High risk": "উচ্চ ঝুঁকি",
  "Critical risk": "গুরুতর ঝুঁকি",

  // ---- portal chooser and sign in
  "Your doctor records your check-up": "চিকিৎসক আপনার স্বাস্থ্য পরীক্ষার তথ্য লেখেন",
  "They review the plan the system drafts": "সিস্টেমের তৈরি খসড়া পরিকল্পনা তিনি যাচাই করেন",
  "You get the plan once they approve it": "তিনি অনুমোদন করলে পরিকল্পনাটি আপনি পান",
  "Sign in as": "যে হিসেবে সাইন ইন করবেন",
  "Read the plan your doctor approved for you.": "চিকিৎসকের অনুমোদিত আপনার পরিকল্পনা পড়ুন।",
  "Record check-ups, review plans and approve them.":
    "স্বাস্থ্য পরীক্ষার তথ্য লিখুন, পরিকল্পনা যাচাই করে অনুমোদন দিন।",
  "Approve doctor accounts and oversee the service.": "চিকিৎসকের অ্যাকাউন্ট অনুমোদন করুন এবং সেবাটি তদারক করুন।",
  "New patient?": "নতুন রোগী?",
  "Create an account": "অ্যাকাউন্ট খুলুন",
  "Doctor?": "চিকিৎসক?",
  "Apply for an account": "অ্যাকাউন্টের জন্য আবেদন করুন",
  "Plans come from a rule engine that cites clinical guidelines (ADA, ACC/AHA, WHO, ACSM). They support a consultation and do not replace one.":
    "পরিকল্পনাগুলো তৈরি হয় একটি নিয়মভিত্তিক ইঞ্জিন থেকে, যা চিকিৎসা নির্দেশিকা (ADA, ACC/AHA, WHO, ACSM) অনুসরণ করে। এগুলো চিকিৎসকের পরামর্শে সহায়তা করে, পরামর্শের বিকল্প নয়।",
  "Administrator sign in": "অ্যাডমিন হিসেবে সাইন ইন",
  "Doctor sign in": "চিকিৎসক হিসেবে সাইন ইন",
  "Patient sign in": "রোগী হিসেবে সাইন ইন",
  "New here?": "এখানে নতুন?",
  "Apply for a doctor account": "চিকিৎসকের অ্যাকাউন্টের জন্য আবেদন করুন",
  "Create a patient account": "রোগীর অ্যাকাউন্ট খুলুন",
  "Your registration is still {waiting}. You can sign in as soon as an admin approves your account.":
    "আপনার নিবন্ধন এখনও {waiting}। অ্যাডমিন আপনার অ্যাকাউন্ট অনুমোদন করলেই সাইন ইন করতে পারবেন।",
  "waiting for admin approval": "অ্যাডমিনের অনুমোদনের অপেক্ষায় আছে",
  Email: "ইমেইল",
  Password: "পাসওয়ার্ড",
  "Signing in…": "সাইন ইন হচ্ছে…",
  "Sign in": "সাইন ইন",
  "Choose a different portal": "অন্য পোর্টাল বেছে নিন",

  // ---- messages from the API on the sign-in and registration screens
  "incorrect email or password": "ইমেইল বা পাসওয়ার্ড ভুল",
  "an account with this email already exists": "এই ইমেইলে আগে থেকেই একটি অ্যাকাউন্ট আছে",
  "too many failed sign-in attempts — try again in a few minutes":
    "অনেকবার ভুল চেষ্টা হয়েছে — কয়েক মিনিট পরে আবার চেষ্টা করুন",
  "your registration is awaiting admin approval — try again later":
    "আপনার নিবন্ধন অ্যাডমিনের অনুমোদনের অপেক্ষায় আছে — পরে আবার চেষ্টা করুন",
  "your registration was declined by the admin": "অ্যাডমিন আপনার নিবন্ধন প্রত্যাখ্যান করেছেন",
  "this is a patient account — use the patient sign-in page":
    "এটি রোগীর অ্যাকাউন্ট — রোগীর সাইন-ইন পাতা ব্যবহার করুন",
  "this is a doctor account — use the doctor sign-in page":
    "এটি চিকিৎসকের অ্যাকাউন্ট — চিকিৎসকের সাইন-ইন পাতা ব্যবহার করুন",
  "this is a admin account — use the admin sign-in page":
    "এটি অ্যাডমিনের অ্যাকাউন্ট — অ্যাডমিনের সাইন-ইন পাতা ব্যবহার করুন",
  "not authenticated — sign in first": "আগে সাইন ইন করুন",
  "session expired or invalid — please sign in again": "সেশনের মেয়াদ শেষ — আবার সাইন ইন করুন",
  "account not found or no longer active": "অ্যাকাউন্টটি পাওয়া যায়নি বা আর সক্রিয় নেই",

  // ---- doctor registration
  "Application sent": "আবেদন পাঠানো হয়েছে",
  "An admin will check your registration. You can sign in as soon as it is approved.":
    "একজন অ্যাডমিন আপনার নিবন্ধন যাচাই করবেন। অনুমোদন হলেই সাইন ইন করতে পারবেন।",
  "Go to doctor sign in": "চিকিৎসকের সাইন ইনে যান",
  "An admin checks every application before the account can sign in.":
    "অ্যাকাউন্টে সাইন ইন করার আগে একজন অ্যাডমিন প্রতিটি আবেদন যাচাই করেন।",
  "Already approved?": "আগেই অনুমোদন পেয়েছেন?",
  "Full name": "পুরো নাম",
  "Dr. …": "ডা. …",
  "At least 8 characters.": "কমপক্ষে ৮ অক্ষর।",
  Specialty: "বিশেষত্ব",
  "e.g. Endocrinology": "যেমন: এন্ডোক্রাইনোলজি",
  "BMDC registration no.": "বিএমডিসি নিবন্ধন নম্বর",
  "e.g. A-12345": "যেমন: A-12345",
  "Sending…": "পাঠানো হচ্ছে…",
  "Send application": "আবেদন পাঠান",

  // ---- patient registration
  "Create your patient account": "আপনার রোগীর অ্যাকাউন্ট খুলুন",
  "Your doctor uses these details at your visits. You see a plan only after your doctor approves it.":
    "আপনার ভিজিটের সময় চিকিৎসক এই তথ্যগুলো ব্যবহার করেন। চিকিৎসক অনুমোদন করার পরেই আপনি পরিকল্পনা দেখতে পাবেন।",
  "Already have an account?": "আগে থেকেই অ্যাকাউন্ট আছে?",
  "Your account": "আপনার অ্যাকাউন্ট",
  "e.g. Ayesha Rahman": "যেমন: আয়েশা রহমান",
  "About you": "আপনার সম্পর্কে",
  "Year of birth": "জন্মসাল",
  "Height (cm)": "উচ্চতা (সেমি)",
  "What is a usual day like?": "আপনার সাধারণ দিন কেমন কাটে?",
  "Used to work out how much energy your meals should give you.":
    "আপনার খাবার থেকে কতটা শক্তি পাওয়া দরকার, তা হিসাব করতে এটি লাগে।",
  "I'm not sure": "আমি নিশ্চিত নই",
  "How used to exercise are you?": "ব্যায়ামে আপনি কতটা অভ্যস্ত?",
  "Used to set a safe starting point for exercise.": "নিরাপদভাবে ব্যায়াম শুরু করার মাত্রা ঠিক করতে এটি লাগে।",
  "I rarely exercise": "আমি খুব কম ব্যায়াম করি",
  "I exercise some weeks": "আমি কোনো কোনো সপ্তাহে ব্যায়াম করি",
  "I exercise most days": "আমি প্রায় প্রতিদিন ব্যায়াম করি",
  "I am currently pregnant": "আমি এখন গর্ভবতী",
  "Which trimester?": "কোন ত্রৈমাসিক?",
  "Conditions a doctor has diagnosed": "চিকিৎসক যে রোগগুলো নির্ণয় করেছেন",
  "Tick any that apply. Leave all unticked if none.": "যেগুলো প্রযোজ্য সেগুলোতে টিক দিন। কোনোটি না থাকলে সব ফাঁকা রাখুন।",
  "Food you do not eat": "যে খাবার আপনি খান না",
  "For faith, choice or allergy. Your meal plan will leave these out. Leave all unticked if none.":
    "ধর্মীয় কারণে, নিজের পছন্দে বা অ্যালার্জির জন্য। আপনার খাবার পরিকল্পনায় এগুলো রাখা হবে না। কোনোটি না থাকলে সব ফাঁকা রাখুন।",
  "Any other food or dish you do not eat": "আর কোনো খাবার বা রান্না যা আপনি খান না",
  "Search for it and pick it from the list. It is left out however it is cooked, with every dish that uses it.":
    "খুঁজে তালিকা থেকে বেছে নিন। যেভাবেই রান্না হোক এটি বাদ থাকবে, এটি দিয়ে তৈরি সব রান্নাসহ।",
  "Search a food or dish you do not eat": "যে খাবার বা রান্না আপনি খান না তা খুঁজুন",
  "Creating account…": "অ্যাকাউন্ট খোলা হচ্ছে…",
  "Create account": "অ্যাকাউন্ট খুলুন",

  // ---- what a patient record can hold (lib/patient-options.ts)
  Hypertension: "উচ্চ রক্তচাপ",
  "High blood pressure": "উচ্চ রক্তচাপ",
  Diabetes: "ডায়াবেটিস",
  "High cholesterol": "উচ্চ কোলেস্টেরল",
  Anaemia: "রক্তস্বল্পতা",
  "Chronic kidney disease": "দীর্ঘমেয়াদি কিডনি রোগ",
  "Kidney disease": "কিডনি রোগ",
  "Knee osteoarthritis": "হাঁটুর অস্টিওআর্থ্রাইটিস",
  Vegetarian: "নিরামিষভোজী",
  "No meat or fish; eggs and dairy eaten": "মাছ-মাংস খান না; ডিম ও দুধ খান",
  Vegan: "সম্পূর্ণ নিরামিষভোজী",
  "No animal foods": "কোনো প্রাণিজ খাবার খান না",
  "No beef": "গরুর মাংস নয়",
  "No pork": "শূকরের মাংস নয়",
  "No eggs": "ডিম নয়",
  "No milk or dairy": "দুধ বা দুগ্ধজাত খাবার নয়",
  "No fish": "মাছ নয়",
  "No prawn, crab or shellfish": "চিংড়ি, কাঁকড়া বা খোলসযুক্ত মাছ নয়",
  "No nuts or peanuts": "বাদাম বা চিনাবাদাম নয়",
  "No wheat or gluten": "গম বা গ্লুটেন নয়",
  Sedentary: "কম নড়াচড়া",
  "Mostly sitting; little walking": "বেশিরভাগ সময় বসে থাকা; অল্প হাঁটা",
  Light: "হালকা",
  "On the feet part of the day; housework, short walks": "দিনের কিছু সময় দাঁড়িয়ে বা হেঁটে; ঘরের কাজ, অল্প হাঁটা",
  Moderate: "মাঝারি",
  "Walking or manual work most of the day": "দিনের বেশিরভাগ সময় হাঁটা বা কায়িক কাজ",
  "Heavy manual work or daily sport": "ভারী কায়িক কাজ বা প্রতিদিন খেলাধুলা",
  "First (to week 13)": "প্রথম (১৩ সপ্তাহ পর্যন্ত)",
  "Second (weeks 14 to 27)": "দ্বিতীয় (১৪ থেকে ২৭ সপ্তাহ)",
  "Third (week 28 on)": "তৃতীয় (২৮ সপ্তাহ থেকে)",
  "Not recorded": "নথিভুক্ত নেই",
  "No restrictions": "কোনো বিধিনিষেধ নেই",
  Trimester: "ত্রৈমাসিক",
  "Sets the extra energy the plan adds; none is added until it is recorded.":
    "এর ওপর নির্ভর করে পরিকল্পনায় বাড়তি শক্তি যোগ হয়; নথিভুক্ত না হওয়া পর্যন্ত কিছু যোগ হয় না।",
  "Daily activity": "দৈনন্দিন কর্মব্যস্ততা",
  "Sets the energy target. Left unrecorded, light activity is assumed and the report says so.":
    "এটি শক্তির লক্ষ্য ঠিক করে। নথিভুক্ত না থাকলে হালকা কর্মব্যস্ততা ধরে নেওয়া হয় এবং রিপোর্টে তা লেখা থাকে।",
  "Fitness level": "ব্যায়ামের অভ্যাস",
  "Scales the starting exercise volume.": "এর ওপর নির্ভর করে শুরুর ব্যায়ামের পরিমাণ ঠিক হয়।",
  Beginner: "নতুন",
  Intermediate: "মাঝামাঝি",
  Advanced: "অভ্যস্ত",

  // ---- the food and dish pickers
  dish: "রান্না",
  "in no dish": "কোনো রান্নায় নেই",
  "in 1 dish": "১টি রান্নায় আছে",
  "in {count} dishes": "{count}টি রান্নায় আছে",
  "1 dish": "১টি রান্না",
  "{count} dishes": "{count}টি রান্না",
  "The food list could not be loaded, so nothing can be added here just now. Reload the page to try again.":
    "খাবারের তালিকা আনা যায়নি, তাই এখন এখানে কিছু যোগ করা যাচ্ছে না। পাতাটি আবার লোড করে চেষ্টা করুন।",
  "Search a food or dish the patient does not eat": "রোগী যে খাবার বা রান্না খান না তা খুঁজুন",
  "Search foods and dishes…": "খাবার ও রান্না খুঁজুন…",
  "Loading the food list…": "খাবারের তালিকা আনা হচ্ছে…",
  "Left out for this patient": "এই রোগীর জন্য বাদ দেওয়া",
  "Stop leaving out {name}": "{name} আর বাদ দেবেন না",
  "{kcal} kcal per {grams} g serving": "প্রতি {grams} গ্রাম পরিবেশনে {kcal} কিলোক্যালরি",
  "{kcal} kcal/100g": "{kcal} কিলোক্যালরি/১০০ গ্রাম",
  "recommended for this patient": "এই রোগীর জন্য সুপারিশকৃত",
  "Recommended for this patient": "এই রোগীর জন্য সুপারিশকৃত",
  "Search dishes and foods": "রান্না ও খাবার খুঁজুন",
  "Search dishes and foods (safety-filtered)…": "রান্না ও খাবার খুঁজুন (নিরাপত্তা যাচাই করা)…",
  "Nothing matches “{query}”": "“{query}” এর সঙ্গে কিছু মেলেনি",
  "1 item available": "১টি পাওয়া গেছে",
  "{count} items available": "{count}টি পাওয়া গেছে",
  "Dishes and foods": "রান্না ও খাবার",

  // ---- doctor: today
  "Welcome back, {name}": "স্বাগতম, {name}",
  "Welcome back": "স্বাগতম",
  "New patient": "নতুন রোগী",
  "Awaiting your review": "আপনার পর্যালোচনার অপেক্ষায়",
  "Queue is clear": "তালিকা ফাঁকা",
  "High or critical risk": "উচ্চ বা গুরুতর ঝুঁকি",
  "Open these first": "এগুলো আগে খুলুন",
  "None waiting": "কেউ অপেক্ষায় নেই",
  "Registered patients": "নিবন্ধিত রোগী",
  "View patients": "রোগীদের দেখুন",
  "Highest risk first. Nothing reaches a patient until you approve it.":
    "সবচেয়ে বেশি ঝুঁকি আগে। আপনি অনুমোদন না করা পর্যন্ত রোগীর কাছে কিছুই পৌঁছায় না।",
  "Open review queue": "পর্যালোচনার তালিকা খুলুন",
  "Waiting for your approval": "আপনার অনুমোদনের অপেক্ষায়",
  "You're all caught up": "সব কাজ শেষ",
  "New assessments appear here as soon as an intake is submitted.":
    "ভিজিটের তথ্য জমা হলেই নতুন মূল্যায়ন এখানে দেখা যাবে।",
  "Lab-report reading is on, on this server: a photo of a lab slip can prefill the intake form, and the photo never leaves the clinic. You confirm every value.":
    "এই সার্ভারেই ল্যাব রিপোর্ট পড়া চালু আছে: ল্যাব রিপোর্টের ছবি থেকে ভিজিটের ফর্ম আগে থেকে পূরণ করা যায়, আর ছবিটি ক্লিনিকের বাইরে যায় না। প্রতিটি মান আপনি নিজে নিশ্চিত করেন।",
  "Lab-report reading is on (Claude): a photo of a lab slip can prefill the intake form. You confirm every value.":
    "ল্যাব রিপোর্ট পড়া চালু আছে (Claude): ল্যাব রিপোর্টের ছবি থেকে ভিজিটের ফর্ম আগে থেকে পূরণ করা যায়। প্রতিটি মান আপনি নিজে নিশ্চিত করেন।",
  "Lab-report reading is off on this server. Typing values into the intake form works the same.":
    "এই সার্ভারে ল্যাব রিপোর্ট পড়া বন্ধ আছে। ভিজিটের ফর্মে মান টাইপ করলেও একই কাজ হয়।",

  // ---- doctor: review queue
  "Review queue": "পর্যালোচনার তালিকা",
  "Assessments waiting for your decision, highest risk first. Nothing reaches a patient until you approve it.":
    "আপনার সিদ্ধান্তের অপেক্ষায় থাকা মূল্যায়ন, সবচেয়ে বেশি ঝুঁকি আগে। আপনি অনুমোদন না করা পর্যন্ত রোগীর কাছে কিছুই পৌঁছায় না।",
  "The queue is empty": "তালিকা ফাঁকা",
  "Every assessment has a decision. New ones appear here when an intake is submitted.":
    "সব মূল্যায়নের সিদ্ধান্ত হয়ে গেছে। ভিজিটের তথ্য জমা হলে নতুনগুলো এখানে দেখা যাবে।",
  "Visit {date}": "ভিজিট {date}",

  // ---- doctor: patients
  "{count} registered": "{count} জন নিবন্ধিত",
  "Search by name, PID or condition": "নাম, PID বা রোগ দিয়ে খুঁজুন",
  "No patients match your search": "আপনার খোঁজার সঙ্গে কোনো রোগী মেলেনি",
  "No patients yet": "এখনও কোনো রোগী নেই",
  "Try a different name, PID or condition.": "অন্য নাম, PID বা রোগ দিয়ে চেষ্টা করুন।",
  "Register your first patient to start an intake.": "ভিজিট শুরু করতে আপনার প্রথম রোগীকে নিবন্ধন করুন।",
  "New visit": "নতুন ভিজিট",

  // ---- doctor: new patient and edit patient
  "After saving, you go straight to their first visit.": "সংরক্ষণের পর সরাসরি রোগীর প্রথম ভিজিটে যাবেন।",
  Identity: "পরিচয়",
  "Sex, age and pregnancy change clinical cutoffs.": "লিঙ্গ, বয়স ও গর্ভাবস্থার ওপর রোগ নির্ণয়ের সীমা নির্ভর করে।",
  "Currently pregnant": "বর্তমানে গর্ভবতী",
  "Changes anaemia cutoffs, nutrient targets, excluded foods and exercises; no weight-loss deficit is applied.":
    "এতে রক্তস্বল্পতার সীমা, পুষ্টির লক্ষ্য এবং বাদ দেওয়া খাবার ও ব্যায়াম বদলায়; ওজন কমানোর জন্য শক্তি কমানো হয় না।",
  "Clinical background": "রোগের পটভূমি",
  "The engine also derives conditions from lab values. Tick what is already diagnosed.":
    "ইঞ্জিন ল্যাবের মান থেকেও রোগ নির্ণয় করে। যা আগে থেকেই নির্ণীত, তাতে টিক দিন।",
  "Diagnosed conditions": "নির্ণীত রোগ",
  "Food the patient does not eat": "রোগী যে খাবার খান না",
  "For faith, choice or allergy. These foods and any dish containing them are never planned or offered.":
    "ধর্মীয় কারণে, নিজের পছন্দে বা অ্যালার্জির জন্য। এই খাবারগুলো এবং এগুলো দিয়ে তৈরি কোনো রান্না পরিকল্পনায় রাখা বা প্রস্তাব করা হয় না।",
  "Other foods and dishes to leave out": "আর যে খাবার ও রান্না বাদ থাকবে",
  "A single food the patient is allergic to or will not eat, or a dish. A food is left out in every form, with every dish that uses it.":
    "রোগীর অ্যালার্জি আছে বা তিনি খান না এমন একটি খাবার, অথবা একটি রান্না। একটি খাবার তার সব রূপে বাদ যায়, এটি দিয়ে তৈরি সব রান্নাসহ।",
  "Patient login": "রোগীর লগইন",
  "Optional. Lets the patient read approved reports online.":
    "ঐচ্ছিক। এতে রোগী অনুমোদিত রিপোর্ট অনলাইনে পড়তে পারেন।",
  "Create a login for this patient": "এই রোগীর জন্য লগইন তৈরি করুন",
  "Patient email": "রোগীর ইমেইল",
  "Temporary password": "সাময়িক পাসওয়ার্ড",
  "At least 8 characters. Give it to the patient.": "কমপক্ষে ৮ অক্ষর। এটি রোগীকে জানিয়ে দিন।",
  "Save and start visit": "সংরক্ষণ করে ভিজিট শুরু করুন",
  "The patient was saved, but the login could not be created: {reason}. Fix the email or password and save again, or untick the login option to continue.":
    "রোগীর তথ্য সংরক্ষণ হয়েছে, কিন্তু লগইন তৈরি করা যায়নি: {reason}। ইমেইল বা পাসওয়ার্ড ঠিক করে আবার সংরক্ষণ করুন, অথবা লগইনের টিক তুলে দিয়ে এগিয়ে যান।",
  "Edit patient": "রোগীর তথ্য সম্পাদনা",
  "A plan still awaiting review is rebuilt from the saved record. Approved plans stay as signed off.":
    "পর্যালোচনার অপেক্ষায় থাকা পরিকল্পনা সংরক্ষিত তথ্য থেকে নতুন করে তৈরি হয়। অনুমোদিত পরিকল্পনা যেমন স্বাক্ষরিত তেমনই থাকে।",
  "Sex and year of birth cannot be changed: past visits were scored on them.":
    "লিঙ্গ ও জন্মসাল বদলানো যায় না: আগের ভিজিটগুলোর মূল্যায়ন এগুলোর ভিত্তিতে হয়েছে।",
  "A recorded condition shapes the plan even when that day's values are normal.":
    "নথিভুক্ত রোগ পরিকল্পনায় প্রভাব ফেলে, সেদিনের মান স্বাভাবিক থাকলেও।",

  // ---- doctor: new visit
  "Enter today's measurements. Leave a field empty if it wasn't measured; the assessment scores only what you enter.":
    "আজকের মাপগুলো লিখুন। যা মাপা হয়নি সেই ঘর ফাঁকা রাখুন; আপনি যা লিখবেন শুধু তারই মূল্যায়ন হবে।",
  "Patient record": "রোগীর নথি",
  Measurements: "মাপ",
  "(required)": "(আবশ্যক)",
  "Not measured": "মাপা হয়নি",
  "Fasting glucose": "খালি পেটে গ্লুকোজ",
  "70–99 normal, 100–125 prediabetes, 126+ diabetes range (ADA)":
    "৭০–৯৯ স্বাভাবিক, ১০০–১২৫ প্রি-ডায়াবেটিস, ১২৬+ ডায়াবেটিসের মাত্রা (ADA)",
  "Systolic blood pressure": "সিস্টোলিক রক্তচাপ (উপরের)",
  "Under 120 normal, 130–139 stage 1, 140+ stage 2 (ACC/AHA)":
    "১২০-এর নিচে স্বাভাবিক, ১৩০–১৩৯ ধাপ ১, ১৪০+ ধাপ ২ (ACC/AHA)",
  "Diastolic blood pressure": "ডায়াস্টোলিক রক্তচাপ (নিচের)",
  "Under 80 normal, 80–89 stage 1, 90+ stage 2 (ACC/AHA)": "৮০-এর নিচে স্বাভাবিক, ৮০–৮৯ ধাপ ১, ৯০+ ধাপ ২ (ACC/AHA)",
  Haemoglobin: "হিমোগ্লোবিন",
  "Normal from 13 (men), 12 (women), 11 (pregnancy) (WHO)":
    "স্বাভাবিক: ১৩ থেকে (পুরুষ), ১২ থেকে (নারী), ১১ থেকে (গর্ভাবস্থা) (WHO)",
  "The assessment is created instantly and waits for your review. The patient sees nothing until you approve it.":
    "মূল্যায়ন সঙ্গে সঙ্গে তৈরি হয়ে আপনার পর্যালোচনার অপেক্ষায় থাকে। আপনি অনুমোদন না করা পর্যন্ত রোগী কিছুই দেখেন না।",
  "Creating assessment…": "মূল্যায়ন তৈরি হচ্ছে…",
  "Create assessment": "মূল্যায়ন তৈরি করুন",
  "Fill from a lab slip": "ল্যাব রিপোর্ট থেকে পূরণ করুন",
  "Upload a photo of the lab report, or the PDF the lab sent, and the values are read into the form. Check each one against the slip before you submit.":
    "ল্যাব রিপোর্টের ছবি বা ল্যাবের পাঠানো PDF আপলোড করুন, মানগুলো ফর্মে বসে যাবে। জমা দেওয়ার আগে প্রতিটি মান রিপোর্টের সঙ্গে মিলিয়ে নিন।",
  "Reading the slip…": "রিপোর্ট পড়া হচ্ছে…",
  "Upload lab slip photo or PDF": "ল্যাব রিপোর্টের ছবি বা PDF আপলোড করুন",
  "Values filled in and highlighted. Check each one against the slip.":
    "মানগুলো বসানো ও চিহ্নিত করা হয়েছে। প্রতিটি মান রিপোর্টের সঙ্গে মিলিয়ে নিন।",
  "No values could be read from this photo. Type them in from the slip.":
    "এই ছবি থেকে কোনো মান পড়া যায়নি। রিপোর্ট দেখে টাইপ করুন।",
  "Reader notes: {notes}": "পাঠকের মন্তব্য: {notes}",
  "Read from the PDF's own text, on this server.": "এই সার্ভারেই PDF-এর নিজের লেখা থেকে পড়া হয়েছে।",
  "Read by RapidOCR, on this server.": "এই সার্ভারেই RapidOCR দিয়ে পড়া হয়েছে।",
  "Read by {engine}.": "{engine} দিয়ে পড়া হয়েছে।",
  "Lab-slip reading isn't set up on this server. Typing the values works the same.":
    "এই সার্ভারে ল্যাব রিপোর্ট পড়ার ব্যবস্থা নেই। মান টাইপ করলেও একই কাজ হয়।",

  // ---- doctor: patient record
  Visits: "ভিজিট",
  "Newest first. Open a visit's report to read or print it.":
    "নতুনগুলো আগে। পড়তে বা ছাপতে কোনো ভিজিটের রিপোর্ট খুলুন।",
  "No visits yet": "এখনও কোনো ভিজিট নেই",
  "Start an intake to record measurements and generate an assessment.":
    "মাপ লিখে মূল্যায়ন তৈরি করতে একটি ভিজিট শুরু করুন।",
  "Start intake": "ভিজিট শুরু করুন",
  Glucose: "গ্লুকোজ",
  Systolic: "সিস্টোলিক",
  Diastolic: "ডায়াস্টোলিক",
  Hb: "হিমোগ্লোবিন",
  "Appears after a second visit.": "দ্বিতীয় ভিজিটের পর দেখা যাবে।",
  BMI: "বিএমআই",
  "Blood pressure": "রক্তচাপ",
  "Appears once recorded at two or more visits.": "দুই বা তার বেশি ভিজিটে মাপা হলে দেখা যাবে।",
  "Signs in as {email} to read approved reports.": "অনুমোদিত রিপোর্ট পড়তে {email} দিয়ে সাইন ইন করেন।",
  "Creating…": "তৈরি হচ্ছে…",
  "Create login": "লগইন তৈরি করুন",
  "No login yet, so this patient can't read their reports online.":
    "এখনও লগইন নেই, তাই এই রোগী অনলাইনে নিজের রিপোর্ট পড়তে পারেন না।",
  Profile: "প্রোফাইল",
  "Does not eat": "যা খান না",

  // ---- doctor: reviewing one assessment
  "Assessment {id}": "মূল্যায়ন {id}",
  "Visit on {date}, engine v{version}": "ভিজিট {date}, ইঞ্জিন v{version}",
  "Plan edited": "পরিকল্পনা সম্পাদিত",
  Findings: "ফলাফল",
  "BMI (Asian cutoffs)": "বিএমআই (এশীয় সীমা)",
  "Energy target": "শক্তির লক্ষ্য",
  "kcal/day": "কিলোক্যালরি/দিন",
  "No biomarkers recorded.": "কোনো পরীক্ষার মান নথিভুক্ত নেই।",
  "Check before approving": "অনুমোদনের আগে দেখে নিন",
  "The engine writes these notes in English.": "ইঞ্জিন এই নোটগুলো ইংরেজিতে লেখে।",
  "Why this plan": "এই পরিকল্পনা কেন",
  "Derived conditions": "নির্ণীত অবস্থা",
  "Safety exclusions applied": "নিরাপত্তার জন্য যা বাদ দেওয়া হয়েছে",
  "Removed before ranking: foods tagged {foodTags}; exercises tagged {exerciseTags}.":
    "ক্রম সাজানোর আগে বাদ দেওয়া হয়েছে: {foodTags} চিহ্নিত খাবার; {exerciseTags} চিহ্নিত ব্যায়াম।",
  "Also removed: what the patient does not eat, with {dishes} that use it.":
    "আরও বাদ দেওয়া হয়েছে: রোগী যা খান না, এবং তা দিয়ে তৈরি {dishes}।",
  "rated avoid in pregnancy": "গর্ভাবস্থায় বর্জনীয়",
  "rated avoid with high blood pressure": "উচ্চ রক্তচাপে বর্জনীয়",
  "rated avoid with diabetes": "ডায়াবেটিসে বর্জনীয়",
  "rated avoid with anaemia": "রক্তস্বল্পতায় বর্জনীয়",
  "rated avoid with knee osteoarthritis": "হাঁটুর অস্টিওআর্থ্রাইটিসে বর্জনীয়",
  "done lying on the back": "চিত হয়ে শুয়ে করা হয়",
  "not for 65 and over": "৬৫ বা তার বেশি বয়সে নয়",
  "for women only": "শুধু নারীদের জন্য",
  "for men only": "শুধু পুরুষদের জন্য",
  "Diet plan": "খাবার পরিকল্পনা",
  "Seven days, Saturday to Friday.": "সাত দিন, শনিবার থেকে শুক্রবার।",
  "Target {target} kcal/day": "লক্ষ্য দিনে {target} কিলোক্যালরি",
  "Target {target} kcal/day, planned {planned} kcal on an average day":
    "লক্ষ্য দিনে {target} কিলোক্যালরি, পরিকল্পনায় গড়ে দিনে {planned} কিলোক্যালরি",
  "Target {target} kcal/day, planned {planned} kcal": "লক্ষ্য দিনে {target} কিলোক্যালরি, পরিকল্পনায় {planned} কিলোক্যালরি",
  "Discard edits": "সম্পাদনা বাতিল করুন",
  "Edit again": "আবার সম্পাদনা করুন",
  "Edit plan": "পরিকল্পনা সম্পাদনা",
  "Editing {day}": "{day} সম্পাদনা করা হচ্ছে",
  "≈{kcal} kcal": "≈{kcal} কিলোক্যালরি",
  "{kcal} kcal": "{kcal} কিলোক্যালরি",
  "From an older database. Remove it and add its replacement.":
    "পুরোনো ডেটাবেস থেকে আসা। এটি সরিয়ে এর বদলিটি যোগ করুন।",
  "Grams of {name}": "{name} কত গ্রাম",
  g: "গ্রাম",
  "Remove {name}": "{name} সরান",
  "No items. Add one below.": "কিছু নেই। নিচে থেকে যোগ করুন।",
  "{day}: planned ≈{planned} kcal of a {target} kcal target":
    "{day}: লক্ষ্য {target} কিলোক্যালরির মধ্যে পরিকল্পনায় ≈{planned} কিলোক্যালরি",
  "Planned ≈{planned} kcal of a {target} kcal target": "লক্ষ্য {target} কিলোক্যালরির মধ্যে পরিকল্পনায় ≈{planned} কিলোক্যালরি",
  "Week average ≈{kcal} kcal a day. Each day is edited on its own; pick a day above.":
    "সপ্তাহের গড় দিনে ≈{kcal} কিলোক্যালরি। প্রতিটি দিন আলাদাভাবে সম্পাদনা হয়; ওপরে একটি দিন বেছে নিন।",
  "Live estimates from the recipe and food data. Exact totals and nutrient coverage are recomputed when you apply the changes.":
    "রান্না ও খাবারের তথ্য থেকে তাৎক্ষণিক আনুমানিক হিসাব। পরিবর্তন প্রয়োগ করলে সঠিক মোট পরিমাণ ও পুষ্টির হিসাব নতুন করে করা হয়।",
  "An average day of this plan totals {total}, {percent}% of the {target} kcal target. Adjust quantities before approving if this is unintended.":
    "এই পরিকল্পনার একটি গড় দিনে মোট {total}, যা {target} কিলোক্যালরি লক্ষ্যের {percent}%। এটি অনিচ্ছাকৃত হলে অনুমোদনের আগে পরিমাণ ঠিক করুন।",
  "This plan totals {total}, {percent}% of the {target} kcal target. Adjust quantities before approving if this is unintended.":
    "এই পরিকল্পনায় মোট {total}, যা {target} কিলোক্যালরি লক্ষ্যের {percent}%। এটি অনিচ্ছাকৃত হলে অনুমোদনের আগে পরিমাণ ঠিক করুন।",
  "Exercise plan": "ব্যায়াম পরিকল্পনা",
  "ACSM FITT-VP prescription": "ACSM FITT-VP ব্যবস্থাপত্র",
  "ACSM FITT-VP prescription, each group ranked after the safety gate by the trained exercise model":
    "ACSM FITT-VP ব্যবস্থাপত্র; নিরাপত্তা যাচাইয়ের পর প্রতিটি দলের ক্রম সাজিয়েছে প্রশিক্ষিত ব্যায়াম মডেল",
  "ACSM FITT-VP prescription, each group ranked after the safety gate by the deterministic formula":
    "ACSM FITT-VP ব্যবস্থাপত্র; নিরাপত্তা যাচাইয়ের পর প্রতিটি দলের ক্রম সাজিয়েছে নির্ধারিত সূত্র",
  Aerobic: "অ্যারোবিক",
  Strength: "শক্তি",
  Flexibility: "নমনীয়তা",
  Balance: "ভারসাম্য",
  "Aerobic days/week": "অ্যারোবিক, সপ্তাহে দিন",
  "Minutes/session": "প্রতিবারে মিনিট",
  "Strength days/week": "শক্তি, সপ্তাহে দিন",
  "Flexibility days/week": "নমনীয়তা, সপ্তাহে দিন",
  "Balance days/week": "ভারসাম্য, সপ্তাহে দিন",
  "Weekly volume (MET-min and kcal) is recomputed when you apply the changes. Target heart rate stays as the engine prescribed.":
    "পরিবর্তন প্রয়োগ করলে সাপ্তাহিক পরিমাণ (MET-মিনিট ও কিলোক্যালরি) নতুন করে হিসাব হয়। লক্ষ্য হৃদস্পন্দন ইঞ্জিনের নির্ধারিত মতোই থাকে।",
  "{minutes} min/week": "সপ্তাহে {minutes} মিনিট",
  "{days} × {minutes} min": "{days} × {minutes} মিনিট",
  Intensity: "তীব্রতা",
  Vigorous: "তীব্র",
  "{low}–{high} bpm": "মিনিটে {low}–{high} স্পন্দন",
  "Strength, flexibility, balance": "শক্তি, নমনীয়তা, ভারসাম্য",
  "Strength, flexibility": "শক্তি, নমনীয়তা",
  "{times} a week": "সপ্তাহে {times}",
  Volume: "পরিমাণ",
  "≈{value} MET-min": "≈{value} MET-মিনিট",
  "{kcal} kcal/week, start ×{factor}": "সপ্তাহে {kcal} কিলোক্যালরি, শুরু ×{factor}",
  "{value} MET": "{value} MET",
  "Applying re-checks every item against this patient's safety exclusions and recomputes all derived numbers on the server.":
    "প্রয়োগ করলে প্রতিটি খাবার ও ব্যায়াম এই রোগীর নিরাপত্তা-বিধির সঙ্গে আবার মিলিয়ে দেখা হয় এবং সব হিসাব সার্ভারে নতুন করে করা হয়।",
  "Recomputing…": "নতুন করে হিসাব হচ্ছে…",
  "Apply changes": "পরিবর্তন প্রয়োগ করুন",
  "Recommended foods": "সুপারিশকৃত খাবার",
  "Everyday foods ranked by what a usual portion supplies, at most three per food group, after the safety gate.":
    "নিরাপত্তা যাচাইয়ের পর, প্রতিদিনের খাবারগুলো একটি সাধারণ পরিমাণে কী পুষ্টি দেয় তার ভিত্তিতে সাজানো; প্রতি খাদ্যদল থেকে সর্বোচ্চ তিনটি।",
  "Ranked per 100 g after the safety gate.": "নিরাপত্তা যাচাইয়ের পর প্রতি ১০০ গ্রামের ভিত্তিতে সাজানো।",
  "Trained food model.": "প্রশিক্ষিত খাবার মডেল।",
  "Deterministic formula.": "নির্ধারিত সূত্র।",
  "No foods ranked.": "কোনো খাবার সাজানো হয়নি।",
  "Foods by condition": "রোগ অনুযায়ী খাবার",
  "What the patient will see for each condition: foods that are an EU-threshold source of its nutrients (most often eaten first, after the whole safety gate), and the foods and dishes its contraindication rule leaves out.":
    "প্রতিটি রোগের জন্য রোগী যা দেখবেন: যে খাবারগুলো ইইউ মানদণ্ডে ওই রোগের প্রয়োজনীয় পুষ্টির উৎস (পুরো নিরাপত্তা যাচাইয়ের পর, যা বেশি খাওয়া হয় তা আগে), এবং ওই রোগের নিষেধের নিয়মে যে খাবার ও রান্না বাদ যায়।",
  "Recommended recipes": "সুপারিশকৃত রান্না",
  "Ranked per serving after the safety gate; among suitable dishes the most commonly cooked at home rank first.":
    "নিরাপত্তা যাচাইয়ের পর প্রতি পরিবেশনের ভিত্তিতে সাজানো; উপযুক্ত রান্নার মধ্যে ঘরে যা বেশি রান্না হয় তা আগে।",
  "Sweets, drinks and dishes over the vitamin A upper limit are left out; you can still add them to the plan.":
    "মিষ্টি, পানীয় এবং ভিটামিন এ-র সর্বোচ্চ সীমা ছাড়ানো রান্না বাদ রাখা হয়েছে; তবু আপনি এগুলো পরিকল্পনায় যোগ করতে পারেন।",
  "Trained recipe model.": "প্রশিক্ষিত রান্না মডেল।",
  "No recipes ranked.": "কোনো রান্না সাজানো হয়নি।",
  "This assessment was {status}": "এই মূল্যায়নের অবস্থা: {status}",
  "View report": "রিপোর্ট দেখুন",
  "You are approving the edited plan. Your changes go on the audit trail and into the patient's report.":
    "আপনি সম্পাদিত পরিকল্পনাটি অনুমোদন করছেন। আপনার পরিবর্তনগুলো অডিট লগে এবং রোগীর রিপোর্টে যাবে।",
  "Signing as": "স্বাক্ষরকারী",
  "Comment for the patient (optional)": "রোগীর জন্য মন্তব্য (ঐচ্ছিক)",
  "Comment for the patient (optional), e.g. re-check haemoglobin in 4 weeks":
    "রোগীর জন্য মন্তব্য (ঐচ্ছিক), যেমন: ৪ সপ্তাহ পর আবার হিমোগ্লোবিন পরীক্ষা করুন",
  "Approve and release": "অনুমোদন করে রোগীকে দিন",
  "Apply or cancel your plan edits before recording a decision.":
    "সিদ্ধান্ত দেওয়ার আগে পরিকল্পনার সম্পাদনা প্রয়োগ বা বাতিল করুন।",

  // ---- admin
  Overview: "সারসংক্ষেপ",
  "Doctor registrations and the state of the service.": "চিকিৎসকদের নিবন্ধন এবং সেবার বর্তমান অবস্থা।",
  "{count} visits recorded": "{count}টি ভিজিট নথিভুক্ত",
  "Active doctors": "সক্রিয় চিকিৎসক",
  "Doctors waiting for approval": "অনুমোদনের অপেক্ষায় থাকা চিকিৎসক",
  "Decide below": "নিচে সিদ্ধান্ত দিন",
  "All caught up": "সব কাজ শেষ",
  "Assessments awaiting review": "পর্যালোচনার অপেক্ষায় থাকা মূল্যায়ন",
  "{approved} approved, {rejected} rejected": "{approved}টি অনুমোদিত, {rejected}টি প্রত্যাখ্যাত",
  "Doctor applications": "চিকিৎসকদের আবেদন",
  "Check the BMDC number before approving.": "অনুমোদনের আগে বিএমডিসি নম্বর যাচাই করুন।",
  "All doctors": "সব চিকিৎসক",
  "No applications waiting": "কোনো আবেদন অপেক্ষায় নেই",
  "New doctor registrations appear here for your decision.":
    "চিকিৎসকদের নতুন নিবন্ধন আপনার সিদ্ধান্তের জন্য এখানে দেখা যাবে।",
  "BMDC {number}": "বিএমডিসি {number}",
  "No specialty or licence given": "বিশেষত্ব বা নিবন্ধন নম্বর দেওয়া হয়নি",
  "{email}, applied {date}": "{email}, আবেদন {date}",
  "Recent activity": "সাম্প্রতিক কার্যক্রম",
  "From the append-only audit log.": "অপরিবর্তনীয় অডিট লগ থেকে।",
  "No activity yet.": "এখনও কোনো কার্যক্রম নেই।",
  "Assessment create": "মূল্যায়ন তৈরি",
  "Assessment approved": "মূল্যায়ন অনুমোদিত",
  "Assessment rejected": "মূল্যায়ন প্রত্যাখ্যাত",
  "Doctor approved": "চিকিৎসক অনুমোদিত",
  "Doctor rejected": "চিকিৎসক প্রত্যাখ্যাত",
  "Note created": "নোট লেখা হয়েছে",
  "Note edited": "নোট সম্পাদিত",
  "Patient account create": "রোগীর লগইন তৈরি",
  "Patient create": "রোগী নিবন্ধন",
  "Patient update": "রোগীর তথ্য হালনাগাদ",
  "Visit create": "ভিজিট নথিভুক্ত",
  "User register doctor": "চিকিৎসকের নিবন্ধন আবেদন",
  "User register patient": "রোগীর অ্যাকাউন্ট খোলা",
  "{count} registered, {pending} waiting for approval": "{count} জন নিবন্ধিত, {pending} জন অনুমোদনের অপেক্ষায়",
  "Filter by status": "অবস্থা অনুযায়ী বাছুন",
  "Search name, DID, specialty": "নাম, DID বা বিশেষত্ব দিয়ে খুঁজুন",
  "No doctors yet": "এখনও কোনো চিকিৎসক নেই",
  "No waiting doctors": "অপেক্ষমাণ কোনো চিকিৎসক নেই",
  "No active doctors": "সক্রিয় কোনো চিকিৎসক নেই",
  "No rejected doctors": "প্রত্যাখ্যাত কোনো চিকিৎসক নেই",
  "Applications from the doctor registration page appear here.":
    "চিকিৎসক নিবন্ধনের পাতা থেকে আসা আবেদন এখানে দেখা যাবে।",
  "BMDC no.": "বিএমডিসি নম্বর",
  Applied: "আবেদনের তারিখ",
  Decision: "সিদ্ধান্ত",
  "{count} registered patients": "{count} জন নিবন্ধিত রোগী",
  "Search name, PID, email": "নাম, PID বা ইমেইল দিয়ে খুঁজুন",
  "Try a different name, PID, or email.": "অন্য নাম, PID বা ইমেইল দিয়ে চেষ্টা করুন।",
  Login: "লগইন",
  "No login": "লগইন নেই",
  Users: "ব্যবহারকারী",
  "{count} accounts across all roles": "সব ভূমিকা মিলিয়ে {count}টি অ্যাকাউন্ট",
  "Search name, email, PID or DID": "নাম, ইমেইল, PID বা DID দিয়ে খুঁজুন",
  "No users match your search": "আপনার খোঁজার সঙ্গে কোনো ব্যবহারকারী মেলেনি",
  "No users yet": "এখনও কোনো ব্যবহারকারী নেই",
  User: "ব্যবহারকারী",
  Role: "ভূমিকা",
  Joined: "যোগদানের তারিখ",
};
