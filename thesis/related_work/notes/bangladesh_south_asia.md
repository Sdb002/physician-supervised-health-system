# Bangladesh and South Asia context: digital health for diet-related disease, local food recommenders, and the disease-burden case

Scope and method. Searched PubMed/Europe PMC (REST API), Crossref, OpenAlex, arXiv, publisher pages, WHO, IDF, DHS Program and GSMA between 2026-11-15 and 2026-11-16. Every paper below was opened at a source page (Europe PMC record with abstract, publisher or journal page, arXiv page, or Crossref record) and every burden figure was read from the primary document (BDHS PDFs, the WHO STEPS fact sheet PDF, the IDF factsheet PDF, the GSMA report PDF, or the WHO GHO OData API). Where only bibliographic metadata could be opened, that is said. PMC full-text pages, DBLP and Semantic Scholar were blocked by bot checks or rate limits, so a few full texts could not be read; those cases are in the Gaps lists. Comparison with "the system" means: bilingual (Bangla/English) web app for Bangladeshi patients; inputs weight, fasting glucose, BP, haemoglobin and eight conditions; outputs a weekly plan of Bangladeshi home dishes, local-food rankings and an exercise prescription; physician approval before the patient sees anything; FCTB 2013 + IFCT 2017 + USDA food data; 250 home dishes scored for cooking frequency; sodium capped at 2000 mg/day through cooking salt; WHO Asian BMI cut-offs. The system has had no real-patient evaluation, so outcome numbers from trials below are context, not comparators for its results.

## 1. Ranked list: which regional papers are closest to the system? (objective a)

### Takeaway
No published work found combines what the system combines: Bangladeshi home dishes, a food composition table, several diet-related conditions at once, a weekly plan, exercise, and physician sign-off before release. The closest are (i) meal-plan or diet-decision-support prototypes for other South Asian cuisines (Sri Lanka, India), (ii) Bangladeshi food datasets and a Bangladesh-linked diet recommender, and (iii) clinician-facing decision-support trials for hypertension and diabetes in India and Bangladesh. Most Bangladeshi digital-health trials send one-way SMS or voice messages and have mixed or null results.

### Cited Findings
Ranking is by closeness of function to the system (personalised diet output from local foods, multi-condition logic, clinician role, Bangladesh setting), not by study quality. "Real patients" means people with the condition took part.

**1. Wijekoon WMDH, Harshanath SMB. "Meal Preparation Algorithm for Diabetic Patients Using Machine Learning." Sri Lankan Journal of Applied Sciences 1(2):27–33, 2023 (published 28 Feb 2023). No DOI listed.** — [journal page](https://sljoas.uwu.ac.lk/index.php/sljoas/article/view/51)
- Type: system/prototype paper (university journal, Sri Lanka).
- What it did: built U-HEALTH, a mobile app that gives diabetic patients daily meal plans for three main meals plus an evening snack and tracks eating habits.
- Method: neural-network meal-plan generation; random-forest decision tree using health status, food preferences, allergies, nutrient content, sex, age, BMI and BMR; KNN to categorise foods.
- Data: a food dataset built around "Sri Lankan food styles and availability"; no named food composition table on the page.
- Evaluation: no user or patient study and no accuracy figures on the page. No real patients.
- Similar: daily meal plans from local dishes; uses BMI/BMR, preferences and allergies (cf. the system's excluded-foods picker).
- Different: diabetes only; no physician approval; no weekly plan, sodium cap, exercise prescription or bilingual UI described; no evaluation.

**2. Kumar D, Bhardwaj A, Sharma S, Malhotra B, Amadi-Mgbenka C, Grover A, Joshi A. "Designing and Evaluating a Personalized, Human-Centered Dietary Decision Support System for Use Among People With Diabetes in an Indian Setting: Protocol for a Quasi-Experimental Study." JMIR Research Protocols 11(3):e13635, 2022. DOI 10.2196/13635.** — [DOI](https://doi.org/10.2196/13635); [Europe PMC 35258472](https://europepmc.org/article/MED/35258472)
- Type: study protocol (with baseline data), India.
- What it did: a telephone-linked dietary decision support system: diet capture in English and Hindi, conversion to calorie components, personalised SMS feedback and automated reminders.
- Data/evaluation: 800 randomised participants with diabetes (400 intervention, 400 control), stratified urban/rural; 3- and 6-month follow-up ongoing at publication. Real patients enrolled; no outcomes yet.
- Similar: personalised diet advice for diabetes in a South Asian setting; two-language interface (English plus a national language), urban and rural users.
- Different: analyses what the patient already ate and sends feedback; does not generate a weekly plan of local dishes; no physician gate; single condition; SMS rather than web app.

**3. Roy M, Das S, Protity AT. "OBESEYE: Interpretable Diet Recommender for Obesity Management using Machine Learning and Explainable AI." arXiv:2308.02796 (cs.LG), submitted 5 Aug 2023; page cites IJRAMT 4(6):1–7 (2023).** — [arXiv](https://arxiv.org/abs/2308.02796)
- Type: preprint / minor-journal paper. Co-author Das is a nutritionist at a Dhaka hospital (per search-result author details; the arXiv page itself does not describe the data origin).
- What it did: ML models that predict daily fluid, carbohydrate, protein and fat needs, claimed to account for comorbidities and physical condition.
- Method: linear regression, SVM, decision tree, random forest, XGBoost, LightGBM; best were linear regression (fluid), random forest (carbohydrate), LightGBM (protein, fat).
- Evaluation: the abstract reports "high accuracy" and "low RMSE" with no numbers; data source not described on the page; no patient evaluation reported.
- Similar: multi-condition diet recommendation, ML, Bangladesh link.
- Different: outputs nutrient targets, not dishes; no food composition table or recipes named; no clinician step; weak reporting.

**4. Ahmed BM, Haque ME, Huq AKO, Masud MM, Ali ME, Naznin M. "FoodBD: a polygon-annotated meal image dataset of Bangladeshi cuisines with visual and nutritional labels." BMC Research Notes 19(1), 2025 (record lists vol. 19; PMID 41366460). DOI 10.1186/s13104-025-07583-8.** — [DOI](https://doi.org/10.1186/s13104-025-07583-8); [Europe PMC](https://europepmc.org/article/MED/41366460)
- Type: dataset paper (Bangladesh; authors include BUET-affiliated computer scientists, per author list).
- What it did: 3,523 smartphone photos of Bangladeshi meals, polygon segmentation over 67 food categories; 1,837 images carry expert-estimated carbohydrate, protein, fat, fibre, calories and glycaemic load; train/validation/test splits.
- Evaluation: dataset release; intended for dietary assessment of people with diabetes. No recommender, no patient outcome.
- Similar: Bangladeshi dishes with nutrient labels, diabetes focus; closest local data resource to the system's 250-dish recipe table.
- Different: image recognition/assessment, not recommendation; nutrients expert-estimated per image rather than computed from a food composition table.

**5. Vijayakumar A, Dubasi HB, Awasthi A, Jaacks LM. "Development of an Indian Food Composition Database." Current Developments in Nutrition 8(7):103790, 2024. DOI 10.1016/j.cdnut.2024.103790 (corrigendum: 10.1016/j.cdnut.2025.107450).** — [DOI](https://doi.org/10.1016/j.cdnut.2024.103790); [Europe PMC 39071807](https://europepmc.org/article/MED/39071807)
- Type: database paper (India), open access, code on GitHub.
- What it did: the Indian Nutrient Databank (INDB): 1,095 raw foods and 1,014 recipes. Raw foods mainly from IFCT 2017 (528 items), gaps filled from IFCT 2004 and UK/US databases; recipes mainly from two cookbooks plus 148 food-blog recipes, ingredients matched to raw foods.
- Notable numbers: only 42.62% of recipe ingredients matched a nutrient retention factor, so cooking losses were handled in a USDA-retention sensitivity analysis. IFCT 2017 has no composite dishes (chapatis, curries). Authors list missing packaged foods, yield factors and regional dishes as limitations.
- Similar: the same data problem the system solves (IFCT 2017 plus foreign tables to compute home-dish nutrients).
- Different: database only, no recommender; Indian not Bangladeshi dishes; no household cooking-frequency score.

**6. Agrawal P, Gandhi S, Agarwal M. "DiabChatbot: A Machine Learning Chatbot for Early Diagnosis of Type II/Mellitus Diabetes and Diet Recommendation in an Indian Scenario." 2024 10th International Conference on Advanced Computing and Communication Systems (ICACCS), IEEE, 2024. DOI 10.1109/icaccs60874.2024.10716933.** — [Crossref record](https://api.crossref.org/works/10.1109/icaccs60874.2024.10716933)
- Type: IEEE conference paper (India). Only metadata could be opened (no abstract in Crossref); method, data and evaluation not verified.
- Similar (from title only): diet recommendation for Indian diabetic users. Different: chatbot that also screens for diabetes; no evidence of physician review.

**7. Prabhakaran D, Jha D, Prieto-Merino D, Roy A, Singh K, Ajay VS, et al. "Effectiveness of an mHealth-Based Electronic Decision Support System for Integrated Management of Chronic Conditions in Primary Care: The mWellcare Cluster-Randomized Controlled Trial." Circulation 139(3):380–391, 2019. DOI 10.1161/CIRCULATIONAHA.118.038192.** — [DOI](https://doi.org/10.1161/circulationaha.118.038192); [Europe PMC 30586732](https://europepmc.org/article/MED/30586732)
- Type: cluster RCT, India (40 community health centres). Development paper: Jindal D et al., Global Health Action 11(1):1517930, 2018, [DOI](https://doi.org/10.1080/16549716.2018.1517930).
- What it did: Android EHR plus algorithm-based electronic decision support for hypertension, diabetes, tobacco, alcohol and depression, used by nurses, with SMS reminders.
- Evaluation: 3,698 enrolled, 3,324 completed 12 months; real patients.
- Key numbers: no difference in systolic BP change (−0.98 mmHg, 95% CI −4.64 to 2.67) or HbA1c (0.11%, −0.24 to 0.45); both arms improved (SBP −13.65 vs −12.66 mmHg). The pilot found resistance to the recommended workflow (Jindal 2018).
- Similar: rule-based, multi-condition clinical decision support with a health worker in the loop.
- Different: clinician-facing treatment support, not patient diet plans; no food data.

**8. Xie W, et al. "Enhancing care quality and accessibility through digital technology-supported decentralisation of hypertension and diabetes management in Bangladesh..." (title truncated in record). BMJ Open 13(11):e073743, 2023. DOI 10.1136/bmjopen-2023-073743.** — [DOI](https://doi.org/10.1136/bmjopen-2023-073743); [Europe PMC 37984955](https://europepmc.org/article/MED/37984955)
- Type: single-cohort proof-of-concept, Parbatipur, Bangladesh. Follow-on protocol with baseline: Xie W et al., JMIR Research Protocols 15:e71696, 2026, [DOI](https://doi.org/10.2196/71696).
- What it did: digital care-coordination platform ("Simple" app: records, referrals, follow-up) letting non-physician workers run village clinics instead of the doctor-run subdistrict clinic.
- Evaluation: 624 patients (mean age 59.5, 65.1% female); real patients; no control arm; attrition 36.2% overall.
- Key numbers: uncontrolled BP fell from 60% to 26% at month 3 (adjusted IRR 0.44, 95% CI 0.33–0.57); uncontrolled glucose from 74% to 43%. 2026 baseline (n=6,849, Dinajpur): BP control 10.2% among hypertensive adults, glycaemic control 14.9% among diabetic adults; awareness 35.3% (hypertension), 60.7% (diabetes).
- Similar: Bangladesh, hypertension + diabetes, digital tool supporting supervised care.
- Different: no diet content; task-shifts away from physicians rather than adding a physician gate.

**9. Rahman MJ, Rahman MM, Sarker MHR, Matsuyama R, Kakehashi M, Tsunematsu M, et al. "Impact of mobile health-based nutritional education on hemoglobin levels in anemic adolescent girls in rural Bangladesh: a randomized controlled trial." BMC Public Health 2025. DOI 10.1186/s12889-025-23687-z.** — [DOI](https://doi.org/10.1186/s12889-025-23687-z); [Europe PMC 40722070](https://europepmc.org/article/MED/40722070)
- Type: open-label parallel RCT (NCT05185661), two schools, Chandpur district.
- Evaluation: 121 of 138 anaemic girls analysed (62 vs 59), 8 months; real participants with anaemia.
- Key numbers: haemoglobin rose but not significantly; anaemia recovery 25.8% vs 13.6%; BMI coefficient 1.10 (95% CI 0.44–1.76); anaemia knowledge coefficient 4.11 (3.63–4.58).
- Similar: diet advice for anaemia, Bangladesh, haemoglobin as the measured input.
- Different: education messages, not food rankings; adolescents; no physician gate.

**10. Billah SM, et al. "Effect of nutrition counselling with a digital job aid on child dietary diversity..." (title truncated in record). Maternal & Child Nutrition 18(1):e13267, 2022. DOI 10.1111/mcn.13267.** — [DOI](https://doi.org/10.1111/mcn.13267); [Europe PMC 34467669](https://europepmc.org/article/MED/34467669). Companion feasibility paper: Ferdous TE, Jaman MJ, Siddique AB, Sultana N, Hossain T, Arifeen SE, Billah SM. Nutrients 16(20):3429, 2024, [DOI](https://doi.org/10.3390/nu16203429).
- Type: secondary outcomes of a five-arm cluster RCT, rural Bangladesh.
- What it did: community health workers used a tablet job aid (scheduling, pictorial content) for complementary-feeding counselling in the first 1000 days.
- Key numbers: 855 pooled intervention vs 403 control children 6–23 months; mean dietary diversity +0.09; flesh-food consumption OR 1.32 (1.11–1.57); effect only in mildly/moderately food-insecure households; the record's CIs look inconsistent (check full text). Feasibility: coverage >90% except the perinatal window (51%); charging, battery wear and unstable internet were barriers.
- Similar: digital tool delivering diet advice in Bangladesh through a health worker (a human in the loop).
- Different: child feeding, not adult chronic disease; counselling aid, not generated plans.

**11. Shariful Islam SM, Niessen LW, Ferrari U, Ali L, Seissler J, Lechner A. "Effects of Mobile Phone SMS to Improve Glycemic Control Among Patients With Type 2 Diabetes in Bangladesh: A Prospective, Parallel-Group, Randomized Controlled Trial." Diabetes Care 38(8):e112–e113, 2015. DOI 10.2337/dc15-0505.** — [DOI](https://doi.org/10.2337/dc15-0505); [Europe PMC 26207059](https://europepmc.org/article/MED/26207059); [LSTM repository page](https://research.lstmed.ac.uk/en/publications/effects-of-mobile-phone-sms-to-improve-glycemic-control-among-pat-5/)
- Type: RCT reported as a short letter (no abstract), Dhaka tertiary hospital. Companion: Shariful Islam SM et al. "Mobile phone use and willingness to pay for SMS for diabetes in Bangladesh." J Public Health (Oxf) 38(1):163–169, 2016, [DOI](https://doi.org/10.1093/pubmed/fdv009): 515 adults with T2D; median willingness to pay 20 BDT (about US$0.26); WTP was higher in men (OR 2.4, 95% CI 1.0–5.7), with household income >50,000 BDT (OR 4.6, 1.1–20.4) and with secondary or higher education (OR 5.2, 1.4–19.6).
- Key numbers for the trial: not verifiable (letter, no abstract; PMC blocked). Do not quote an HbA1c effect without opening the full letter.
- Similar: Bangladesh, type 2 diabetes, phone-delivered lifestyle advice, real patients.
- Different: generic one-way SMS; no individual food plan; no clinician review of content.

**12. Jahan Y, Rahman MM, Faruque ASG, Chisti MJ, Kazawa K, Matsuyama R, Moriyama M. "Awareness Development and Usage of Mobile Health Technology Among Individuals With Hypertension in a Rural Community of Bangladesh: Randomized Controlled Trial." Journal of Medical Internet Research 22(12):e19137, 2020. DOI 10.2196/19137.** — [DOI](https://doi.org/10.2196/19137); [Europe PMC 33284129](https://europepmc.org/article/MED/33284129)
- Type: open-label 1:1 RCT, Mirzapur (rural), Aug 2018–Jul 2019; registered NCT03614104.
- What it did: health education for both arms; intervention arm also received periodic SMS for 5 months.
- Evaluation: 420 adults ≥35 with hypertension (209 vs 211); completion 98.0%; real patients.
- Key numbers: salt intake <6 g/day improved in both groups (P<.001); SBP (P=.04) and DBP (P=.02) fell in both groups; the abstract reports the control group with 9% higher adherence for salt intake (P=.04) and physical activity, i.e., no advantage of SMS over education alone.
- Similar: salt reduction and physical activity for hypertension in rural Bangladesh.
- Different: generic messages; the measured salt target was <6 g/day, not a computed sodium cap.

**13. Fottrell E, Ahmed N, Morrison J, Kuddus A, Shaha SK, King C, et al. "Community groups or mobile phone messaging to prevent and control type 2 diabetes and intermediate hyperglycaemia in Bangladesh (DMagic): a cluster-randomised controlled trial." Lancet Diabetes & Endocrinology 7(3):200–212, 2019. DOI 10.1016/S2213-8587(19)30001-4.** — [DOI](https://doi.org/10.1016/S2213-8587(19)30001-4); [Europe PMC 30733182](https://europepmc.org/article/MED/30733182)
- Type: three-arm cluster RCT, 96 rural villages (~125,000 people), Faridpur area, 2015–2018 (ISRCTN41083256).
- What it did: (a) participatory learning and action (PLA) community groups; (b) twice-weekly voice messages for 14 months (per search-result summary of the paper); (c) control.
- Evaluation: 11,454 adults ≥30 at end-line; 2,100 of 2,470 with baseline intermediate hyperglycaemia followed 2 years. Real population.
- Key numbers: PLA cut combined T2D + intermediate hyperglycaemia prevalence (aOR 0.36, 0.27–0.48; absolute −20.7%) and 2-year diabetes incidence (aOR 0.39, 0.24–0.65); mHealth had no effect (aOR 0.93, 0.74–1.16; incidence OR 1.02, 0.73–1.43). PLA cost INT$316 per case prevented.
- Companions: Morrison J et al. Global Public Health 17(7):1299–1313, 2022, [DOI](https://doi.org/10.1080/17441692.2021.1923776) — voice messages raised knowledge but exposure was limited by technical faults, changing phone numbers and message fatigue. Pires M et al. J Epidemiol Community Health 76(6):586–594, 2022, [DOI](https://doi.org/10.1136/jech-2021-217293) — mHealth effect only in the youngest group (incidence ratio 0.53, 0.28–1.00).
- Similar: Bangladesh, diet/activity for diabetes, phone-delivered. Different: population messaging, no personalisation, no clinician.

**14. Kobashi Y, Haque SE, Sakisaka K, Amir I, Kaneko M, Mutahara M, et al. "Community-based intervention for managing hypertension and diabetes in rural Bangladesh." Tropical Medicine and Health 52(1):13, 2024. DOI 10.1186/s41182-023-00574-0.** — [DOI](https://doi.org/10.1186/s41182-023-00574-0); [Europe PMC 38268002](https://europepmc.org/article/MED/38268002)
- Type: pre–post controlled study (randomisation not described), six villages, Narail.
- What it did: delivered by non-health staff; the stronger arm got wall checklists, phone-call messages, personalised advice papers, seminar videos and seminars; the weaker arm a poster only.
- Evaluation: 600 participants completed both surveys.
- Key numbers: SBP −7.3 mmHg (4.6–9.9) stronger arm vs −4.7 (2.4–7.0) control (p=0.001); weaker arm −1.9 (p=0.21 vs control); no between-group glucose difference.
- Similar: personalised written advice for hypertension and diabetes in Bangladesh. Different: paper/phone, not software; not food-level.

**15. Pfammatter A, Spring B, Saligram N, Davé R, Gowda A, Blais L, et al. "mHealth Intervention to Improve Diabetes Risk Behaviors in India: A Prospective, Parallel Group Cohort Study." Journal of Medical Internet Research 18(8):e207, 2016. DOI 10.2196/jmir.5712.** — [DOI](https://doi.org/10.2196/jmir.5712); [Europe PMC 27496271](https://europepmc.org/article/MED/27496271)
- Type: prospective parallel cohort (ACTRN12615000423516), India, Arogya World "mDiabetes".
- What it did: 56 text messages over 6 months in 12 languages to opted-in subscribers.
- Evaluation: 982 intervention / 943 control at baseline; 611 and 632 followed up. General population, not patients.
- Key numbers: larger improvement in a health-behaviour composite (F(1,1238)=30.181, P<.001); fruit, vegetable and fat intake improved (P<.01); exercise did not.
- Similar: diet-behaviour change in many local languages. Different: prevention SMS, no personal plan.
- Follow-ons: Chadwick J et al. "Artificial Intelligence-Enabled Mobile Health Intervention (mDiabetes) to Reduce Diabetes Risk Behaviors in Rural India: Quasi-Experimental Pre-Post Study." JMIR 27:e79283, 2025, [DOI](https://doi.org/10.2196/79283) — reinforcement-learning-selected WhatsApp messages vs static messages, no between-group difference (physical activity aOR 1.0, 0.7–1.3; BMI difference −0.0, −0.6 to 0.5). Rani PK et al. Frontiers in Public Health 12:1470615, 2024, [DOI](https://doi.org/10.3389/fpubh.2024.1470615) — voice calls plus CHW meetings; 545 analysed; awareness 82.75%→97.43%.

**16. Alam M, Banwell C, Lokuge K. "The Effect of Women's Differential Access to Messages on Their Adoption of Mobile Health Services and Pregnancy Behavior in Bangladesh: Retrospective Cross-Sectional Study." JMIR mHealth and uHealth 8(7):e17665, 2020. DOI 10.2196/17665.** — [DOI](https://doi.org/10.2196/17665); [Europe PMC 32706694](https://europepmc.org/article/MED/32706694)
- Type: retrospective cross-sectional survey of 459 female subscribers (2014) of the Aponjon maternal messaging service.
- Key numbers: women with sole access to messages (vs shared with family) more often ate nutritious food five times a day (OR 1.58, 1.04–2.40) and followed water advice (OR 1.90, 1.17–3.09).
- Related Aponjon evaluations: Alam M et al. BMC Health Serv Res 17:434, 2017, [DOI](https://doi.org/10.1186/s12913-017-2361-6) — 476 mothers, no significant effect on skilled birth attendance, breastfeeding or postnatal care; Chowdhury ME, Shiblee SI, Jones HE. BMC Med Inform Decis Mak 19:179, 2019, [DOI](https://doi.org/10.1186/s12911-019-0903-z) — users exposed ≥6 months about 3 times as likely to score high on maternal knowledge/practice (propensity-matched).
- Similar: pregnancy nutrition advice in Bangladesh; shows shared-phone access matters. Different: generic stage-based messages.

**17. Shahid M, Mahar SA, Shaikh S, Shaikh ZU. "Mobile phone intervention to improve diabetes care in rural areas of Pakistan: a randomized controlled trial." Journal of the College of Physicians and Surgeons Pakistan 25(3):166–171, 2015. PMID 25772954 (DOI in the record is malformed; do not cite it).** — [Europe PMC 25772954](https://europepmc.org/article/MED/25772954)
- Type: RCT, 440 adults with T2D and HbA1c ≥8.0%, 4 months.
- What it did: phone calls every 15 days on glucose monitoring, medication, activity and healthy eating.
- Key numbers: following the diet plan rose 17.3%→43.6% (p<0.001) vs 13.6%→15.9% in control; normalised HbA1c RR 2.71 (1.18–6.40).
- Similar: diet adherence for diabetes, staff-led. Different: voice calls by staff, no food recommender.
- Related Pakistan preprint (not peer reviewed): Ali GB et al., Research Square 2019, [DOI](https://doi.org/10.21203/rs.2.11378/v1) — 249 T2D patients, three dietary SMS a week for 3 months, no difference in diet score (OR 1.04, 0.96–1.14).

**18. Bhandari B, Narasimhan P, Jayasuriya R, Vaidya A, Schutte AE. "Effectiveness and Acceptability of a Mobile Phone Text Messaging Intervention to Improve Blood Pressure Control (TEXT4BP) among Patients with Hypertension in Nepal: A Feasibility Randomised Controlled Trial." Global Heart 17(1):13, 2022. DOI 10.5334/gh.1103.** — [DOI](https://doi.org/10.5334/gh.1103); [Europe PMC 35342691](https://europepmc.org/article/MED/35342691)
- Type: feasibility RCT, Kathmandu tertiary hospital, 200 adults, 3 months; co-designed (COM-B) messages three times a week.
- Key numbers: SBP −7.09 vs −0.77 mmHg (adjusted β −6.50, −12.6 to −0.33); DBP β −4.60 (−8.16 to −1.04); BP target 70% vs 48% (p=0.006).
- Similar: hypertension self-management by phone in South Asia. Different: generic SMS, medication adherence focus.
- Other Nepal work (protocols only): Shrestha N et al. PLoS One 20(11):e0335333, 2025, [DOI](https://doi.org/10.1371/journal.pone.0335333) (T2D text-based mHealth RCT, n=154); Berube LT et al. JMIR Res Protoc 13:e59423, 2024, [DOI](https://doi.org/10.2196/59423) (gestational-diabetes app with dietary self-management).

**19. Senarath U, et al. mHENAL protocol (title not fully captured). Contemporary Clinical Trials Communications 16:100453, 2019. DOI 10.1016/j.conctc.2019.100453.** — [DOI](https://doi.org/10.1016/j.conctc.2019.100453); [Europe PMC 31650073](https://europepmc.org/article/MED/31650073)
- Type: RCT protocol, Sri Lanka, 1,200 adults, 12 months; two voice and two text messages a week with diet and lifestyle content; primary outcome 10-year CVD risk. No results paper found in this search.

**20. Jafar TH, Gandhi M, de Silva HA, Jehan I, Naheed A, Finkelstein EA, et al. "A Community-Based Intervention for Managing Hypertension in Rural South Asia." New England Journal of Medicine 382(8):717–726, 2020. DOI 10.1056/NEJMoa1911965.** — [DOI](https://doi.org/10.1056/NEJMoa1911965); [Europe PMC 32074419](https://europepmc.org/article/MED/32074419)
- Type: cluster RCT (COBRA-BPS), 30 rural communities in Bangladesh, Pakistan and Sri Lanka; 2,645 adults with hypertension; >90% follow-up at 24 months.
- What it did: CHW home visits for BP monitoring and counselling, training of government physicians, care coordination. The abstract does not mention a digital component.
- Key numbers: SBP −9.0 vs −3.9 mmHg (difference 5.2, 3.2–7.1); BP control 53.2% vs 43.7% (RR 1.22, 1.10–1.35).
- Relevance: the strongest regional evidence that a human, physician-linked programme lowers BP; a non-digital benchmark.

### Inferences
- The ranking's top half is made of prototypes, datasets and protocols with no outcome data; the bottom half is made of trials with outcome data but no food-level personalisation. The system sits in the empty space between them.
- Personalisation in the regional trials means message timing or selection (mDiabetes RL, TEXT4BP co-design), not choosing dishes for a patient's conditions and lab values.

### Gaps
- No peer-reviewed Bangladeshi diet or meal recommender built on FCTB 2013 was found in Europe PMC, Crossref or OpenAlex; IEEE Xplore and DBLP could not be searched directly (DBLP returned bot-check pages, Semantic Scholar rate-limited). Bangladeshi student/conference recommenders may exist in IEEE ICCIT/ICECE/TENSYMP proceedings but none could be verified. An unpublished GitHub project ("Hybrid diet ML planner" using a Bangladesh food composition table) appeared in search but is not citable.
- Islam SMS 2015 trial HbA1c numbers could not be read (letter without abstract; PMC blocked).
- SriHealth (SLIIT repository) and a Pakistani dish-recognition/nutrient-profiling preprint (preprints.org 202608.0821) were seen in search results but their pages returned no content, so they are not listed.

## 2. Which digital health interventions in Bangladesh target diet, diabetes, hypertension, pregnancy nutrition, anaemia or obesity, and what did evaluations find?

### Takeaway
Bangladeshi evidence is dominated by one-way SMS or voice messaging (diabetes, hypertension, pregnancy) and by health-worker tablet job aids (child nutrition, hypertension/diabetes care coordination). Messaging alone mostly raised knowledge without changing disease outcomes (DMagic) or did no better than education (Jahan 2020); the clearer gains came where people or health workers were in the loop (PLA groups, digitally supported village clinics, personalised advice papers). No Bangladeshi digital intervention for obesity was found.

### Cited Findings
- Diabetes, population level: DMagic voice messaging had no effect on T2D/intermediate hyperglycaemia (aOR 0.93, 0.74–1.16), while community groups did (aOR 0.36, 0.27–0.48) — [Fottrell 2019](https://doi.org/10.1016/S2213-8587(19)30001-4). Exposure was limited by technical faults, number changes and message fatigue — [Morrison 2022](https://doi.org/10.1080/17441692.2021.1923776).
- Diabetes, clinic patients: an SMS RCT in Dhaka was published as a Diabetes Care letter — [Islam 2015](https://doi.org/10.2337/dc15-0505); willingness to pay for diabetes SMS was a median 20 BDT — [Islam 2016](https://doi.org/10.1093/pubmed/fdv009).
- Hypertension: SMS plus education was not better than education alone for salt and activity adherence in 420 rural patients — [Jahan 2020](https://doi.org/10.2196/19137). Personalised advice papers plus phone messages lowered SBP 7.3 mmHg vs 4.7 in controls — [Kobashi 2024](https://doi.org/10.1186/s41182-023-00574-0). Digital-supported village clinics cut uncontrolled BP from 60% to 26% (uncontrolled cohort) — [Xie 2023](https://doi.org/10.1136/bmjopen-2023-073743).
- Pregnancy nutrition: Aponjon messaging associated with nutritious food intake only when women had sole access (OR 1.58) — [Alam 2020](https://doi.org/10.2196/17665); no effect on several birth/postnatal behaviours — [Alam 2017](https://doi.org/10.1186/s12913-017-2361-6); ≥6 months' exposure linked to about 3-fold higher maternal knowledge/practice scores — [Chowdhury 2019](https://doi.org/10.1186/s12911-019-0903-z).
- Child and first-1000-days nutrition: tablet job aid counselling modestly raised dietary diversity (+0.09) — [Billah 2022](https://doi.org/10.1111/mcn.13267); coverage >90% but 51% in the perinatal window, with power and connectivity problems — [Ferdous 2024](https://doi.org/10.3390/nu16203429).
- Anaemia: mHealth nutrition education in anaemic adolescent girls gave anaemia recovery of 25.8% vs 13.6% but no significant haemoglobin change — [Rahman MJ 2025](https://doi.org/10.1186/s12889-025-23687-z).
- Comparators: India mWellcare decision support null on SBP and HbA1c — [Prabhakaran 2019](https://doi.org/10.1161/circulationaha.118.038192); India mDiabetes SMS improved fruit, vegetable and fat intake — [Pfammatter 2016](https://doi.org/10.2196/jmir.5712); AI-selected messages no better than static ones — [Chadwick 2025](https://doi.org/10.2196/79283); Nepal TEXT4BP lowered SBP by 6.5 mmHg (adjusted) — [Bhandari 2022](https://doi.org/10.5334/gh.1103); Pakistan phone calls raised diet-plan adherence 17.3%→43.6% — [Shahid 2015](https://europepmc.org/article/MED/25772954); COBRA-BPS (non-digital, BD/PK/SL) lowered SBP by 5.2 mmHg — [Jafar 2020](https://doi.org/10.1056/NEJMoa1911965).

### Inferences
- A reviewer will know that "an app that sends advice" has a weak track record in Bangladesh; the system should be framed as decision support with a physician gate, not as another messaging intervention.
- The positive regional results share a human element (community groups, CHWs, nurses, physicians), which supports the physician-approval design but also means the system's value cannot be claimed without a clinical study.

### Gaps
- No Bangladeshi digital intervention for obesity or weight management, chronic kidney disease diet, or knee osteoarthritis exercise was found.
- No Bangladeshi trial delivered food-level (dish-level) recommendations.

## 3. Which diet or food recommender systems exist for South Asian cuisines, and which use FCTB, IFCT or local recipe datasets?

### Takeaway
Food recommenders for South Asian cuisines exist mainly as prototypes in small university journals or IEEE conferences (Sri Lanka U-HEALTH, India DiabChatbot) with no user evaluation reported. Local data resources are maturing: India's INDB couples IFCT 2017 with 1,014 recipes, and Bangladesh now has image datasets of local meals (FoodBD). None of the verified recommenders uses FCTB, and none scores dishes by how often households cook them.

### Cited Findings
- U-HEALTH builds daily meal plans for diabetics from a Sri Lankan food dataset using RF/KNN/neural networks; no evaluation reported — [Wijekoon & Harshanath 2023](https://sljoas.uwu.ac.lk/index.php/sljoas/article/view/51).
- An Indian dietary decision support system captures diet in English and Hindi and returns SMS feedback; 800 participants randomised, results pending — [Kumar 2022](https://doi.org/10.2196/13635).
- INDB: 1,095 raw foods and 1,014 recipes; IFCT 2017 lacks composite dishes; only 42.62% of ingredients matched a retention factor — [Vijayakumar 2024](https://doi.org/10.1016/j.cdnut.2024.103790).
- RecipeDB holds ~118,171 recipes from 74 countries with USDA nutrition, not IFCT — [Batra 2020, Database](https://doi.org/10.1093/database/baaa077). (Useful contrast: global recipe resources use USDA, not regional tables.)
- FoodBD: 3,523 Bangladeshi meal images, 67 categories, 1,837 with expert nutrient and glycaemic-load labels, aimed at diabetes dietary assessment — [Ahmed 2025](https://doi.org/10.1186/s13104-025-07583-8). A further Bangladeshi image set, BD-Food33 (1.2K images, 33 local foods), is on Mendeley Data — [DOI 10.17632/8wt48bjmx3](https://doi.org/10.17632/8wt48bjmx3) (seen in OpenAlex metadata only).
- OBESEYE predicts macronutrient and fluid needs with ML and claims to consider comorbidities; no dish-level output and no reported numbers — [Roy 2023](https://arxiv.org/abs/2308.02796).
- DiabChatbot (IEEE ICACCS 2024) addresses diet recommendation "in an Indian scenario" (metadata only) — [Agrawal 2024](https://doi.org/10.1109/icaccs60874.2024.10716933).
- Diet cost work uses national dietary guidelines: the Cost of Recommended Diet in Bangladesh was US$0.87 (83 BDT) per person per day; about 43% of households could not afford it; households overspent on starchy staples and underspent on protein foods, fruit and dairy — [Islam S, Nowar A, Amin MR, Shaheen N. Foods 12(4):790, 2023](https://doi.org/10.3390/foods12040790).

### Inferences
- Combining FCTB 2013 with IFCT 2017 and USDA for 250 Bangladeshi home dishes, with a household cooking-frequency score, appears to have no published counterpart; INDB is the nearest analogue and is worth citing as the Indian equivalent of the same data problem.
- Affordability (CoRD) is a real constraint a reviewer may raise; the system's frequency weighting favours commonly cooked dishes but does not model cost.

### Gaps
- No verified Pakistani or Nepali food recommender paper was found (only a preprint and an IJRAMT-type paper surfaced; not opened).
- IEEE Xplore could not be searched directly; Bangladeshi conference recommenders remain unverified.

## 4. Bangla-language health apps: usability, health literacy, uptake and the digital divide

### Takeaway
Bangladeshi mHealth apps have poor usability, limited health literacy is common among NCD patients, and women are far less likely than men to own a smartphone or use mobile internet; household smartphone access is lower in rural areas. Once women own smartphones, their internet use is close to men's, and shared family phones change who receives health messages.

### Cited Findings
- Usability: of usability problems found in 36 Bangladeshi mHealth apps, 61% were catastrophic or major; aesthetic/minimalist design was the most violated heuristic (21%); 30-user tests agreed with low SUS scores; authors call usability a barrier to adoption — [Islam MN, Karim MM, Inan TT, Islam AKMN. BMC Med Inform Decis Mak 20:19, 2020](https://doi.org/10.1186/s12911-020-1033-3).
- Language and literacy barriers: rural community members named illiteracy, limited English, low trust and technical inability as barriers to mHealth — [Khatun 2016, Int J Med Inform 93:49–56](https://doi.org/10.1016/j.ijmedinf.2016.05.010). Only 37% of phone owners generally read received SMS; knowledge of mHealth services rose steeply with education (11+ years aOR 11.1) — [Khatun 2015, Int J Med Inform 84(10):847–856](https://doi.org/10.1016/j.ijmedinf.2015.06.008).
- Health literacy: 43% of 2,793 NCD service seekers at 11 primary care centres had limited health literacy (HLS-EU-Q); male sex, schooling and urban PHC were linked to adequate literacy — [Salwa M et al. Health Lit Res Pract 2024](https://doi.org/10.3928/24748307-20240119-01). Only 27.3% of 401 T2D patients in Dhaka diabetes centres had adequate functional health literacy (Bengali S-TOFHLA) — [Islam MM et al. Health Lit Res Pract 2026](https://doi.org/10.3928/24748307-20260409-02).
- Gender gap (GSMA, survey 2024, adults 18+, Bangladesh): mobile ownership 85% men vs 68% women; smartphone ownership 40% vs 25% (gender gap 37%); mobile internet use 42% vs 26% (gap 39%); among smartphone owners, 90% of men and 87% of women use mobile internet; feature phones remain common (25% of men, 22% of women own one) — [GSMA Mobile Gender Gap Report 2025](https://www.gsma.com/wp-content/uploads/2025/12/The-Mobile-Gender-Gap-Report-2025.pdf). Pakistan had the widest smartphone gender gap (48%) of the 15 countries.
- Rural/urban (BBS ICT Access and Use Survey 2025–26, July–Sept 2025, as reported by the Financial Express on 21 Dec 2025): 72.4% of households own at least one smartphone (urban 81%, rural 69%); internet use among people aged 5+ 48.9% (men 51.2%, women about 46.3%); personal phone ownership 56.5% (men about 63%, women 53%) — [Financial Express](https://thefinancialexpress.com.bd/home/mobile-internet-access-expand-despite-ownership-gender-gaps-bbs-survey). Note: the reported sex-specific ownership figures do not average to the total; check the BBS release.
- Older rural data: in Chakaria (2012–13), 61.8% of men vs 34.4% of women owned a phone; women more often shared a family phone (19.7% vs 11.6%) — [Khatun 2017, BMC Health Serv Res 17:573](https://doi.org/10.1186/s12913-017-2523-6). Gender moderated mHealth adoption in Dhaka — [Hoque 2016, BMC Med Inform Decis Mak 16:51](https://doi.org/10.1186/s12911-016-0289-0).
- Shared access matters for outcomes: women with sole access to Aponjon messages had higher odds of nutritious eating (OR 1.58) — [Alam 2020](https://doi.org/10.2196/17665).
- Older adults (60+, n=493) in Bangladesh: habit, service quality and price value predicted mHealth use — [Palas 2022, BMC Med Inform Decis Mak 22:191](https://doi.org/10.1186/s12911-022-01917-3).

### Inferences
- A Bangla interface is necessary but not sufficient: literacy and smartphone access limit who can use a patient-facing web app, especially rural women, pregnant women and older patients — the groups with high anaemia, hypertension and diabetes burden. A physician- or clinic-mediated workflow partly offsets this, and printable reports (the system has a print layout) help households sharing one phone.
- The system's Bangla wording has not been reviewed (per project notes); the usability literature suggests a usability study (SUS plus heuristic review) would be expected by reviewers.

### Gaps
- No published usability or uptake study of a Bangla-language diet or NCD self-management app was found.
- The BBS ICT figures above come from a newspaper report of the BBS release; the BBS PDF itself could not be downloaded. Earlier BBS ICT 2022 figures (e.g., 63.3% household smartphone access) appeared only in news snippets and were not verified.

## 5. Disease-burden figures for Bangladesh (each with source and year)

### Takeaway
About one in eight Bangladeshi adults has diabetes (IDF 2024: 13.9 million, age-standardised 13.2%, 39.1% undiagnosed); the 2022 BDHS measured diabetes in 17% of women and 15% of men and hypertension in 23% and 17%, with most cases uncontrolled. Over a third of women of reproductive age and of pregnant women are anaemic; 38% of ever-married women aged 20–49 are overweight or obese even on standard (not Asian) cut-offs; adults eat about 9 g of salt a day, nine in ten eat fewer than five servings of fruit and vegetables, and rice still supplies a large share of the diet.

### Cited Findings
Diabetes
- IDF Diabetes Atlas 11th edition (data year 2024): 13,877.4 thousand adults 20–79 with diabetes; crude prevalence 12.3%; age-standardised 13.2% (second-highest in the IDF South-East Asia region after Mauritius, 20.1%; India 10.5%, Sri Lanka 10.2%, Nepal 7.7%); 39.1% undiagnosed; 31,620 diabetes-related deaths; USD 74.4 spent per person with diabetes; "one in 8" adults; projected 23.0 million (15.4%) by 2050 — [IDF Atlas 11th ed. SEA factsheet, 2025](https://international-diabetes-federation.s3.eu-west-1.amazonaws.com/media/uploads/sites/3/2025/08/IDF_Atlas_11_2025_SEA_Factsheet.pdf). Pakistan is in IDF's MENA region and is not on this sheet.
- BDHS 2022 (fieldwork Jun–Dec 2022; report Jan 2024): diabetes (FPG ≥7.0 mmol/L or medication) in 17% of women and 15% of men aged 18+; 23% and 19% at age 35+; 67% of diabetic women and 72% of diabetic men unaware; only 6% and 5% aware, treated and controlled — [NIPORT & ICF, BDHS 2022 Final Report, ch. 14](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf).
- BDHS 2017–18 (report Oct 2020): diabetes in 10% of women and 11% of men aged 18+ — [NIPORT & ICF, BDHS 2017–18 Final Report](https://www.dhsprogram.com/pubs/pdf/FR344/FR344.pdf).
- WHO STEPS 2018 (n≈7,000 with biochemistry, ages 18–69): raised fasting glucose or on medication 8.3% (7.5–9.3); impaired fasting glycaemia 6.6%; 74.9% had never had blood glucose measured — [WHO/NIPSOM 2018 STEPS Fact Sheet Bangladesh](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf) (page: [WHO Bangladesh](https://www.who.int/bangladesh/about-us/publications/m/item/2018-steps-fact-sheet-bangladesh), posted 14 Dec 2022).
- Conflict: a secondary analysis of the same STEPS 2018 data (n=6,875) reports hypertension 27.3%, diabetes 9.8% and hypercholesterolaemia 30.2% — [Rahman MM et al. Public Health 246:105832, 2025](https://doi.org/10.1016/j.puhe.2025.105832) — differing from the fact sheet (21.0%, 8.3%, 28.4%), presumably because of definitions and sample cleaning. Cite the fact sheet for national figures.

Hypertension
- BDHS 2022: 23% of women and 17% of men aged 18+ (≥140/90 or medication); 36% and 23% at 35+; 43% of hypertensive women and 51% of hypertensive men unaware; 19% and 20% controlled. Prevalence fell from 28% (women) and 26% (men) in 2017–18 — [BDHS 2022](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf); [BDHS 2017–18](https://www.dhsprogram.com/pubs/pdf/FR344/FR344.pdf).
- STEPS 2018: hypertension 21.0% (men 17.9%, women 24.1%); 7.9% newly diagnosed by the survey — [STEPS fact sheet](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf).
- BDHS 2022: hypertension 42% in obese vs 19% in normal-BMI women (men 43% vs 15%) — [BDHS 2022](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf).

Overweight and obesity (note the cut-offs)
- BDHS 2022 (WHO standard cut-offs: overweight 25.0–29.9, obese ≥30): 38% of ever-married women 20–49 overweight or obese (sampling-error table: 38.5%, 95% CI 37.1–39.9), 8% obese; urban 48% vs rural 35%; men 20+: 20% overweight or obese, 2% obese — [BDHS 2022 ch. 11 and Appendix B](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf).
- STEPS 2018 (standard cut-offs): overweight 20.5% (men 16.0%, women 25.1%); obese 5.4% (women 8.6%); mean BMI 22.7 — [STEPS fact sheet](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf).
- Neither national source reports WHO Asian cut-offs (≥23 overweight, ≥27.5 obese), so national figures understate overweight as the system defines it.

Anaemia
- WHO GHO modelled estimates, 2023: women of reproductive age 37.6% (uncertainty 20.9–57.6); pregnant women 38.6% (21.8–56.6); non-pregnant 37.5% — [WHO GHO NUTRITION_ANAEMIA_REPRODUCTIVEAGE_PREV](https://ghoapi.azureedge.net/api/NUTRITION_ANAEMIA_REPRODUCTIVEAGE_PREV?$filter=SpatialDim%20eq%20%27BGD%27).
- WHO GHO, children 6–59 months, 2019 (latest in API): 43.1% (24.4–61.1) — [WHO GHO NUTRITION_ANAEMIA_CHILDREN_PREV](https://ghoapi.azureedge.net/api/NUTRITION_ANAEMIA_CHILDREN_PREV?$filter=SpatialDim%20eq%20%27BGD%27%20and%20TimeDim%20ge%202015).
- Local survey: 38% (95% CI 35–40%) of second/third-trimester pregnant women in Narayanganj were anaemic — [Hasan MI et al. BMC Public Health 2024](https://doi.org/10.1186/s12889-024-20480-2).
- BDHS 2022 trained teams for anaemia testing, but the Final Report contains no anaemia results chapter — [BDHS 2022 p.6](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf).

Chronic kidney disease
- Pooled CKD prevalence 22.48% (9 studies, 225,206 participants; women 25.32%, men 20.31%; high heterogeneity) — [Banik S, Ghosh A. Int Urol Nephrol 53(4):713–718, 2021](https://doi.org/10.1007/s11255-020-02597-6).

Cholesterol
- STEPS 2018: raised total cholesterol (≥5.0 mmol/L or medication) 28.4% (26.8–30.0) — [STEPS fact sheet](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf).

Salt
- STEPS 2018: mean salt intake 9.0 g/day from urinary sodium (men and women 9.0); 48.2% always or often add salt at the table — [STEPS fact sheet](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf); rural 9.0 vs urban 8.9 g/day — [Riaz BK et al. BMJ Open 10(11):e041334, 2020](https://doi.org/10.1136/bmjopen-2020-041334). 9.0 g salt is roughly 3,500 mg sodium (conversion, not a source figure), against the system's 2,000 mg cap.

Diet pattern
- STEPS 2018: 89.6% eat <5 servings of fruit and/or vegetables a day; mean 0.4 servings of fruit and 2.3 of vegetables per day; fruit eaten on 1.6 days a week — [STEPS fact sheet](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf).
- Nutrition Survey of Bangladesh 2017–18 (weighed records, n=1,551): adherence to national food-based dietary guidelines was 4.1% for fruit, 5% for milk and 6–7% for vegetables; most ate more carbohydrate and less fat than recommended — [Islam MH, Halima O, Shaheen N. Food Sci Nutr 13(10):e71056, 2025](https://doi.org/10.1002/fsn3.71056).
- HIES 2022 (BBS), as reported by The Daily Star (12 Apr 2023): rice intake 328.9 g per person per day (367.2 g in 2016; 416 g in 2010); urban 284.7 g, rural 348.1 g; vegetables 201.9 g (from 167.3 g) — [The Daily Star](https://www.thedailystar.net/business/economy/news/capita-rice-intake-keeps-falling-bbs-3295806).

Mortality
- Probability of dying between 30 and 70 from CVD, cancer, diabetes or chronic respiratory disease: 21.7% in 2023 (men 24.6%, women 18.7%; uncertainty 12.0–34.8) — [WHO GHO NCDMORT3070](https://ghoapi.azureedge.net/api/NCDMORT3070?$filter=SpatialDim%20eq%20%27BGD%27%20and%20TimeDim%20ge%202015).
- BDHS 2022 cites a national survey finding that 97% of adults 18–69 had at least one NCD risk factor (WHO 2018) — [BDHS 2022 ch. 14](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf); STEPS-based paper: 3.0% had none, 26.2% had three or more — [Riaz 2020](https://doi.org/10.1136/bmjopen-2020-041334).

### Inferences
- The 2017–18 to 2022 BDHS changes (diabetes up, hypertension down) should be quoted with care: same definitions per the report, but the report itself does not explain the hypertension fall. Quoting both surveys with years avoids over-claiming a trend.
- For the paper, the strongest single sentences: IDF 2024 (13.9 million, 13.2%, 39.1% undiagnosed); BDHS 2022 (diabetes 17%/15%, hypertension 23%/17%, two-thirds of diabetics unaware); STEPS 2018 (9.0 g salt, 89.6% low fruit/veg); WHO GHO 2023 anaemia (37.6% WRA, 38.6% pregnant).

### Gaps
- The IDF Bangladesh country page (gestational diabetes / hyperglycaemia-in-pregnancy figure) could not be opened (redirect loop); not cited.
- No newer national STEPS survey than 2018 was found.
- No measured national anaemia figure newer than the BDHS 2011 era was found (BDHS 2022 did not publish one; the National Micronutrient Survey 2019–20 report was not located). WHO GHO figures are modelled with wide uncertainty.
- No national CKD survey; the meta-analysis pools heterogeneous local studies (95% CI not shown in the record).
- The HIES 2022 rice figure is from a newspaper report of the BBS release; the BBS PDF was not opened.
- No Bangladesh-specific GBD paper was opened; GBD DALY figures are not included.

## 6. Health-system figures: doctors per population and consultation length

### Takeaway
Bangladesh has about 7 medical doctors per 10,000 people and the shortest primary-care consultations recorded in a 67-country review (48 seconds), while BP and glucose control are low. A physician-approval step must therefore be quick to perform, and reviewers will ask whether it scales.

### Cited Findings
- Medical doctors per 10,000 population: 7.22 (2023), 7.17 (2022), 6.30 (2019), 4.76 (2015) — [WHO GHO HWF_0001, NHWA data, Dec 2025 update](https://ghoapi.azureedge.net/api/HWF_0001?$filter=SpatialDim%20eq%20%27BGD%27%20and%20TimeDim%20ge%202015) (indicator name confirmed in the [GHO indicator list](https://ghoapi.azureedge.net/api/Indicator?$filter=IndicatorCode%20eq%20%27HWF_0001%27)).
- Average primary-care consultation in Bangladesh: 48 seconds, the shortest of 67 countries (Sweden 22.5 minutes); 18 countries with about half the world's population have consultations of 5 minutes or less — [Irving G et al. BMJ Open 7(10):e017902, 2017](https://doi.org/10.1136/bmjopen-2017-017902).
- Care-cascade gaps: only 19–20% of hypertensive adults and 5–6% of diabetic adults are aware, treated and controlled (BDHS 2022) — [BDHS 2022](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf); BP control 10.2% and glycaemic control 14.9% at baseline in Dinajpur — [Xie 2026](https://doi.org/10.2196/71696).
- Scale-up costing: hypertension-only primary care cost US$8.9 per eligible patient per year and integrated hypertension/diabetes/cholesterol care US$40.2; authors argue task-sharing with nurses and CHWs is needed — [Husain MJ et al. BMJ Open 12(6):e061467, 2022](https://doi.org/10.1136/bmjopen-2022-061467).
- Village doctors linked to physicians via mHealth valued decision support but faced call-centre access, fees and unfamiliarity — [Khan NUZ et al. BMC Med Inform Decis Mak 15:62, 2015](https://doi.org/10.1186/s12911-015-0188-9).

### Inferences
- With under a minute per consultation, physicians cannot write diet plans themselves; a pre-built plan they approve or reject is a plausible fit, but the review time per plan should be measured before claiming feasibility.
- Regional programmes are moving toward task-shifting (Xie 2023, Husain 2022); a reviewer may ask why approval rests with physicians rather than nurses or nutritionists.

### Gaps
- No Bangladeshi figure was found for dietitians/nutritionists per population or for time physicians spend on diet counselling.
- World Bank physician-density API timed out; WHO GHO was used instead.

## 7. Which gaps do these sources name, and which venues publish this regional work?

### Takeaway
The sources name: one-way messaging that raises knowledge but not outcomes; message fatigue and technical failure; poor app usability; limited English and literacy; women's limited and shared phone access; missing nutrient data for composite local dishes; dataset scarcity for offline evaluation of food recommenders; and large untreated hypertension and diabetes populations. The work appears in global-health and mHealth journals rather than recommender-systems venues.

### Cited Findings
- mHealth raised knowledge but "did not change disease outcomes" — [Fottrell 2019](https://doi.org/10.1016/S2213-8587(19)30001-4); technical faults, number changes and message fatigue — [Morrison 2022](https://doi.org/10.1080/17441692.2021.1923776).
- Unsatisfactory usability is a possible barrier to wider mHealth adoption in Bangladesh — [Islam MN 2020](https://doi.org/10.1186/s12911-020-1033-3).
- Illiteracy and limited English as barriers — [Khatun 2016](https://doi.org/10.1016/j.ijmedinf.2016.05.010).
- IFCT 2017 lacks composite dishes; regional dishes, yield factors and packaged foods missing — [Vijayakumar 2024](https://doi.org/10.1016/j.cdnut.2024.103790).
- Evidence reporting in developing-country mHealth studies is weak, most failing the WHO mERA checklist — [Hoque MR et al. Health Informatics J 26(4):2792–2810, 2020](https://doi.org/10.1177/1460458220937102).
- Power cuts, battery wear and unstable internet limit tablet tools — [Ferdous 2024](https://doi.org/10.3390/nu16203429).
- Venues observed: The Lancet Diabetes & Endocrinology; NEJM; Circulation; Diabetes Care; JMIR, JMIR mHealth and uHealth, JMIR Research Protocols; BMC Medical Informatics and Decision Making; BMC Public Health; BMC Health Services Research; BMC Research Notes; BMJ Open; Global Heart; Maternal & Child Nutrition; Nutrients; Foods; Food Science & Nutrition; Current Developments in Nutrition; Tropical Medicine and Health; Global Public Health; Journal of Epidemiology & Community Health; International Journal of Medical Informatics; Health Informatics Journal; Health Literacy Research and Practice; Frontiers in Public Health; Journal of the College of Physicians and Surgeons Pakistan; Sri Lankan Journal of Applied Sciences; IEEE ICACCS; arXiv. The Lancet Regional Health – Southeast Asia publishes regional diet-quality commentary (e.g., Richi & Alam 2025, "From hidden hunger to double burden...", [DOI](https://doi.org/10.1016/j.lansea.2025.100673), seen in OpenAlex metadata only).

### Inferences
- For a system paper, JMIR mHealth and uHealth, JMIR Formative Research, BMC Medical Informatics and Decision Making and Digital Health-type venues match the regional literature; recommender-systems venues have little South Asian clinical work to cite.

### Gaps
- No source explicitly names "physician approval of generated diet plans" as a gap; that framing would be the paper's own.

## 8. Synthesis: the burden case, the gap the system fills, and what a reviewer could say is already covered

### Takeaway
The burden case is strong and citable; the gap (dish-level, multi-condition, physician-gated recommendations from Bangladeshi food data) is real in the verified literature; but reviewers can point out that messaging and decision-support trials already exist in the region, that most showed small or null effects, and that the system has no patient evaluation of its own.

### Cited Findings
Burden case in five sentences (ready to adapt):
1. In 2024 an estimated 13.9 million Bangladeshi adults aged 20–79 had diabetes (age-standardised prevalence 13.2%), 39.1% of them undiagnosed ([IDF Diabetes Atlas, 11th ed., 2025](https://international-diabetes-federation.s3.eu-west-1.amazonaws.com/media/uploads/sites/3/2025/08/IDF_Atlas_11_2025_SEA_Factsheet.pdf)).
2. The 2022 Bangladesh Demographic and Health Survey measured diabetes in 17% of women and 15% of men and hypertension in 23% and 17%, and only 5–6% of people with diabetes and 19–20% of people with hypertension had their condition controlled ([NIPORT & ICF, 2024](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf)).
3. Adults consumed a mean 9.0 g of salt a day and 89.6% ate fewer than five servings of fruit and vegetables daily in the 2018 national STEPS survey ([WHO/NIPSOM, 2018](https://cdn.who.int/media/docs/default-source/searo/bangladesh/publications/2018-steps-fact-sheet-bangladesh.pdf)).
4. Anaemia affected an estimated 37.6% of women of reproductive age and 38.6% of pregnant women in 2023 ([WHO GHO](https://ghoapi.azureedge.net/api/NUTRITION_ANAEMIA_REPRODUCTIVEAGE_PREV?$filter=SpatialDim%20eq%20%27BGD%27)), and 38% of ever-married women aged 20–49 were overweight or obese by standard cut-offs in 2022 ([NIPORT & ICF, 2024](https://www.dhsprogram.com/pubs/pdf/FR386/FR386.pdf)).
5. With about 7 doctors per 10,000 people ([WHO GHO, 2023](https://ghoapi.azureedge.net/api/HWF_0001?$filter=SpatialDim%20eq%20%27BGD%27%20and%20TimeDim%20ge%202015)) and primary-care consultations averaging 48 seconds ([Irving et al., 2017](https://doi.org/10.1136/bmjopen-2017-017902)), individual dietary counselling is rarely possible in routine care.

Gap the system fills (each element tied to evidence above):
- Dish-level recommendations from Bangladeshi home dishes with computed nutrients (FCTB/IFCT/USDA) — no verified Bangladeshi counterpart; nearest are FoodBD (assessment dataset) and INDB (Indian database).
- Several co-occurring conditions handled together (diabetes, hypertension, anaemia, cholesterol, CKD, pregnancy, obesity, knee OA) — regional tools are single-condition (U-HEALTH, Kumar 2022, TEXT4BP, Jahan 2020).
- Sodium handled as a quantified cap through cooking salt, against a measured 9.0 g/day salt intake — regional trials gave generic salt advice.
- Physician approval before release — regional digital tools either bypass clinicians (SMS) or support clinicians' own treatment decisions (mWellcare, Simple app), not patient diet plans.
- Bangla interface — app usability and language barriers are documented, but no Bangla diet app study exists.

What a reviewer could say is already covered:
- Phone-delivered diet and lifestyle advice for diabetes, hypertension and pregnancy has been tested in Bangladesh several times (DMagic, Islam 2015, Jahan 2020, Aponjon) with mostly null or knowledge-only results — so "a digital tool" is not new, and the burden of proof is on outcomes.
- Clinician-in-the-loop decision support for hypertension and diabetes exists (mWellcare in India, null; Simple-app decentralisation in Bangladesh) — physician involvement alone is not novel.
- Personalised diet decision support in a South Asian language exists (Kumar 2022, India, English/Hindi, 800 participants) and meal planners from local foods exist (U-HEALTH, Sri Lanka).
- Local food datasets exist (FoodBD; INDB for India).
- Unlike most of the above, the system has no real-patient data, no physician-agreement study and synthetic model labels; reviewers will compare it with trials that enrolled hundreds to thousands of patients.

### Inferences
- The defensible novelty claim is the combination (Bangladeshi dish-level data + multi-condition rule gate + physician approval + Bangla), not any single element.
- The weakest point relative to regional work is evaluation; framing the paper as a system and dataset description with a planned physician study matches what regional prototypes (U-HEALTH, Kumar 2022 protocol) have published.

### Gaps
- No direct evidence on how long physicians in Bangladesh would take to review a generated plan.
- No study measured whether Bangladeshi patients follow dish-level plans versus generic advice.
