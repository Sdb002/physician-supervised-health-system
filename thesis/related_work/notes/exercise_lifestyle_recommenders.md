# Automated exercise prescription, combined diet-and-exercise recommenders, and adherence features: related work for the physician-supervised diet app

How this was checked (searched and verified 2026-11-15/16): every paper below was checked against PubMed (E-utilities record: title, authors, journal, year, DOI, abstract), the Crossref DOI record, the arXiv API, or DOAJ/Semantic Scholar for IEEE Access, which PubMed does not index. Where a detail comes from the full text rather than the abstract, the full-text page is cited. One paper (Yang et al., JMIR 2026) was checked through its Crossref DOI record because jmir.org returned HTTP 403. FITTER is an arXiv **preprint** (v1, posted 2026-11-02) and is labelled as one. Full-text details for FITTER and P3-EX were pulled from the HTML pages by a summarising fetch, so recheck those numbers against the PDFs before submission.

The system's own features, used to judge closeness: (F1) FITT-VP prescription with aerobic, strength and flexibility work, plus balance from age 65; (F2) a cited per-exercise safety dataset rated safe/modify/avoid per condition; (F3) a hard rule gate before any ranking; (F4) a gradient-boosted ranker trained on synthetic patient types with guideline-derived labels; (F5) a Saturday–Friday week with no consecutive strength days; (F6) integration with a meal plan; (F7) a daily checklist and streak; (F8) physician approval before release; (F9) no real-patient evaluation yet.

## Which 12–20 published papers are closest to this system, ranked by closeness?

### Takeaway
No paper found combines all nine features. The closest are guideline-grounded, clinician-facing exercise prescription generators that apply explicit safety rules: FITTER (preprint), the EXPERT tool and P3-EX. Next come combined diet-and-physical-activity knowledge bases or apps, led by PROTEIN, the only one found that covers iron-deficiency anaemia. Ranking criteria: the number of features F1–F9 shared, with extra weight on F1–F3 and F8.

### Cited Findings

#### 1. FITTER: guideline-grounded multi-agent FITT-VP prescription (closest; **preprint**)
- **Citation:** Li X, Lin Y, Wu Y, Wang F, Wang M, Gary RA, Kariuki J, Smith J, Billinger SA, Xiao C, Hu X, Yan R. "A Guideline-Grounded Multi-Agent Framework for Personalized Exercise Prescription from Clinical and Wearable Data." arXiv:2611.03983v1, posted 2026-11-02. Type: preprint (not peer-reviewed). Venue: arXiv. Verified via the arXiv API — [arXiv](https://arxiv.org/abs/2611.03983)
- **What it built:** FITTER, a multi-agent framework that combines clinical and wearable data with condition-specific guidance to produce personalised FITT-VP prescriptions. A deterministic safety audit-and-repair step corrects rule-checkable violations — [arXiv abstract](https://arxiv.org/abs/2611.03983)
- **Method:** Pre-generation screening has three parts: a profile screen, a medication screen against an FDA-label-derived knowledge base, and an LLM safety review that may add concerns but cannot remove those from the first two screens. Five LLM agents then run in sequence: Type (aerobic, resistance, flexibility, neuromotor), Frequency, Intensity & Time (RPE ranges, talk test, durations, stop criteria), Volume (weekly minutes) and Progression (six two-week blocks with progression and regression rules). A rule-based (non-LLM) audit-and-repair loop follows — [arXiv full text](https://arxiv.org/html/2611.03983)
- **Constraint classes in the audit:** intensity limits (for example a ban on vigorous exercise), activity restrictions, frequency/time/volume limits, progression restrictions and stop criteria. Example mappings: no high-fall-risk activities when fall risk is present; intensity capped at RPE 6 under a non-vigorous restriction; balance-demanding activities excluded under medication-related peripheral neuropathy. The paper does not mention PAR-Q+ or ACSM pre-participation screening — [arXiv full text](https://arxiv.org/html/2611.03983)
- **Guidance and data:** Four guidance sources: the ACSM position stand (Garber 2011), the AHA/ASA statement for stroke survivors (Billinger 2014), the ACS guideline (Rock 2020) and the ADA position statement (Colberg 2016). They were split into 289 passages and indexed with bge-base-en-v1.5 and FAISS. Patient data came from All of Us Registered Tier v8: 4,554 eligible (3,764 cancer, 790 stroke), with 400 evaluated (300 cancer, 100 stroke). Inputs included Fitbit weekly steps and activity minutes. Goals, readiness, stress, social setting and equipment access were **simulated**. The backbone was Qwen3.5-9B with temperature 0, and safety was judged by a GPT-5-family model — [arXiv full text](https://arxiv.org/html/2611.03983)
- **Evaluation:** computational evaluation against five LLM baselines, ablation, and structured clinician review. The study was retrospective: no prescription was given to any participant — [arXiv full text](https://arxiv.org/html/2611.03983)
- **Key numbers:**
  - Model-assessed safety-constraint compliance was 98.5% (394/400) for FITTER versus 75.8–85.8% for the comparators (Vanilla 75.8%, CoT 84.2%, ReAct 82.8%, Self-Refine 85.8%, Multi-Agent Collaboration 77.8%).
  - In the cancer-cohort ablation, compliance was 99.0% with the full system, 82.0% without retrieval, 76.3% without the model safety review and 62.0% without audit-and-repair.
  - Clinician review covered 80 prescriptions, rated by 4 reviewers with **one reviewer per prescription** and no inter-rater agreement estimated. Safety was 80.6% (95% CI 74.4–86.2), clinical acceptability 68.1% (37 accepted as written, 35 with modification, 8 not accepted), and anticipated effectiveness 95.3% for cancer and 62.5% for stroke.
  - Stroke reviewers noted missing components such as strength exercise.
  - Source: [arXiv full text](https://arxiv.org/html/2611.03983)
- **Similarities:** FITT-VP output with all four exercise components; explicit, rule-checkable safety constraints that override the generative or learned part; clinician-facing design; evaluation on retrospective or simulated data with no prospective patient use (the same as F9).
- **Differences:** the generator is an LLM; this system uses a rule gate plus a GBM ranker over a fixed, cited exercise catalogue. FITTER's safety check runs *after* generation (audit and repair); this system's gate runs *before* ranking. FITTER covers cancer and stroke, not pregnancy, anaemia or knee OA. It has no diet plan, no weekly calendar (it uses two-week progression blocks instead), no checklist or streak, and no approval gate. The authors themselves note the gap between model-assessed safety (98.5%) and clinician-rated safety (80.6%) — [arXiv full text](https://arxiv.org/html/2611.03983)

#### 2. EXPERT tool: rule-based digital decision support for exercise prescription in CVD and CVD risk factors
- **Citation (primary):** Hansen D, Dendale P, Coninx K, Vanhees L, Piepoli MF, Niebauer J, Cornelissen V, Pedretti R, Geurts E, Ruiz GR, Corrà U, Schmid JP, et al. (36 authors). "The European Association of Preventive Cardiology Exercise Prescription in Everyday Practice and Rehabilitative Training (EXPERT) tool: A digital training and decision support system for optimized exercise prescription in cardiovascular disease. Concept, definitions and construction methodology." *Eur J Prev Cardiol* 2017;24(10):1017–1031. doi:10.1177/2047487317702042. PMID 28420250. Type: methods paper / practice guideline — [PubMed](https://pubmed.ncbi.nlm.nih.gov/28420250/)
- **Companion:** Hansen D, Niebauer J, Cornelissen V, et al. (35 authors). "Exercise Prescription in Patients with Different Combinations of Cardiovascular Disease Risk Factors: A Consensus Statement from the EXPERT Working Group." *Sports Med* 2018;48(8):1781–1797. doi:10.1007/s40279-018-0930-4. PMID 29729003 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/29729003/)
- **What it built:** an algorithm behind an interactive tool that "automatically provides an exercise prescription according to the variables provided." Expert-defined rules give diagnostic criteria, primary exercise goals, disease-specific prescriptions (intensity, frequency, volume, type, session and programme duration) and exercise safety advice — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/)
- **Conditions covered:** 10 cardiovascular diseases; 5 CVD risk factors (type 1 and 2 diabetes, obesity, hypertension, hypercholesterolaemia); 3 non-cardiovascular conditions (lung failure, renal failure, sarcopaenia). The rules also account for baseline exercise tolerance, common cardiovascular medications and adverse events during exercise testing — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/)
- **Method and data:** working-group members systematically reviewed meta-analyses, systematic reviews and clinical studies per risk factor and wrote the recommendations and safety precautions. Hasselt University built the algorithm. The 2018 paper reports *simulations* of tool outputs — [PubMed 29729003](https://pubmed.ncbi.nlm.nih.gov/29729003/)
- **Evaluation:** expert consensus and simulated cases only, as reported in these papers; neither abstract reports a patient or clinician study. A 2021 editorial by the same group is titled "Computerized decision support for exercise prescription in cardiovascular rehabilitation: high hopes…but still a long way to go" (*Eur J Prev Cardiol* 2021;28(5):569–571, doi:10.1093/eurjpc/zwaa105; only the title and metadata were checked, as there is no abstract) — [PubMed 33624079](https://pubmed.ncbi.nlm.nih.gov/33624079/)
- **Similarities:** the closest match in *knowledge content*. It encodes literature-derived, condition-specific prescription rules and safety advice for diabetes, hypertension and obesity, handles combinations of conditions, and serves as a clinician decision aid. It is fully rule-based and deterministic, like this system's gate.
- **Differences:** safety and dosing rules sit at the condition/prescription level, not as per-exercise safe/modify/avoid labels; there is no ML ranking, no pregnancy, anaemia or knee OA, no diet, no patient checklist and no weekly calendar. It targets European cardiac rehabilitation clinicians.

#### 3. P3-EX (Prioritize Personalize Prescribe Exercise): evidence-based exercise prescription algorithm for clinicians
- **Citation:** Chen S, Wu Y, Kennedy J, Panza G, Guidry MZ, Pescatello LS. "An exercise prescription algorithm for clinicians to use with their patients with cardiovascular disease risk factors." *Digit Health* 2025;11:20552076251360884. doi:10.1177/20552076251360884. PMID 40677518. Type: development plus feasibility/usability survey study — [PubMed](https://pubmed.ncbi.nlm.nih.gov/40677518/)
- **What it built and method:** a web-based tool. The clinician first enters age, sex, signs and symptoms of CVD, metabolic or renal disease, and desired intensity, and the tool decides whether **medical clearance** is needed according to ACSM pre-participation guidance. The clinician then enters BMI, waist circumference, blood pressure, glucose, lipids and CVD medications. Each risk factor is scored with a modified AHA Life's Essential 8, the ACSM multiple-risk-factor strategy picks the priority, and the tool outputs a FITT prescription for that factor. The article describes FITT only; it does not mention FITT-VP, resistance, flexibility or balance components, PAR-Q+ or contraindication lists — [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/)
- **Data and evaluation:** 844 recruited and 309 completed (143 healthcare providers, 166 other professionals). Each completed a timed **hypothetical case** and an adapted Mobile Application Rating Scale. No real patients took part — [PubMed](https://pubmed.ncbi.nlm.nih.gov/40677518/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/)
- **Key numbers:** 86.9% agreed P3-EX will make patients healthier; 83.5% were satisfied; 79.2% agreed the prescription is safe (the Results section reports 79.8%, a discrepancy within the article); 34.4% said fault tolerance could be improved; 88.8% produced a prescription for the same prioritised risk factor; mean time 4.6 min. The corresponding author owns P3-EX LLC — [PubMed](https://pubmed.ncbi.nlm.nih.gov/40677518/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/)
- **Similarities:** deterministic, guideline-derived (ACSM) prescription for hypertension, diabetes, dyslipidaemia and obesity; a safety step before prescribing (medical clearance); clinician in the loop; no patient outcome data (the same as F9).
- **Differences:** one prioritised risk factor per prescription rather than a joint plan; no exercise catalogue, ranking, ML, week schedule, diet or patient checklist; US practitioner users. Its evaluation is a usability survey, which this system lacks.

#### 4. PROTEIN project: expert nutrition-and-PA knowledge base, NAct ontology and a personalised meal-and-exercise app
- **Citation (knowledge base):** Wilson-Barnes SL, Pagkalos I, Patra E, Kokkinopoulou A, Hassapidou M, Lalama E, Csanalosi M, Kabisch S, Pfeiffer AFH, DeCorte E, Cornelissen V, Bacelar P, et al. (24 authors). "The development of an EU-wide nutrition and physical activity expert knowledge base to support a personalised mobile application across various EU population groups." *Nutr Bull* 2024;49(2):220–234. doi:10.1111/nbu.12673. PMID 38773712 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38773712/)
- **Citation (pilot RCT):** Lalama E, Csanalosi M, Kabisch S, Wilson-Barnes S, Gymnopoulos LP, Dimitropoulos K, Rouskas K, Anagnostis A, Oikonomidis I, Hadjileontiadis L, et al. (16 authors). "Effect of a Personalized Mobile App on Glucose Control in Adults With Prediabetes and Type 2 Diabetes: Exploratory Pilot Randomized Controlled Trial." *JMIR Hum Factors* 2026;13:e87692. doi:10.2196/87692. PMID 42342244 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42342244/)
- **Citation (ontology):** Tsatsou D, Lalama E, Wilson-Barnes SL, Hart K, Cornelissen V, Buys R, Pagkalos I, Balula Dias S, Dimitropoulos K, Daras P. "NAct: The Nutrition & Activity Ontology for Healthy Living." *Formal Ontology in Information Systems (FOIS 2021)*, Frontiers in Artificial Intelligence and Applications. doi:10.3233/FAIA210377. Verified via Crossref — [DOI](https://doi.org/10.3233/FAIA210377)
- **What it built:** a smartphone app giving "tailored and dynamic nutrition and physical activity advice". Behind it are an expert knowledge base of reference ranges (macro/micronutrients, anthropometry, biochemical, physiological and sleep parameters) for **10 EU population groups**, including healthy adults, T2D, CVD, excess weight, obesity and **iron-deficiency anaemia**. There is also a library of 24-hour meal plans covering dietary preferences and allergies, in 7 languages — [PubMed 38773712](https://pubmed.ncbi.nlm.nih.gov/38773712/)
- **Method:** NAct links nutritional, medical, behavioural and lifestyle indicators to dietary and PA directives to drive "a reasoning-based AI decision support system" — [Crossref/FOIS](https://doi.org/10.3233/FAIA210377)
- **Evaluation:** an exploratory pilot RCT with **21** adults with T2D or prediabetes. They used CGM and the app for "personalized meals and exercise recommendations based on their glucose levels and physical activity" — [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/)
- **Key numbers:** time in range rose from 71.8% (SD 27.3) to 76% (SD 28.1) (P<.05) but missed the 5% target. HbA1c, fasting glucose and weight did not change. Dropout was high, with mean app use of 42 days (range 5–84), and COVID-19 hindered recruitment — [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/)
- **Similarities:** the closest *combined diet-and-exercise* system. Expert, guideline-derived reference knowledge per population group; condition coverage that overlaps on T2D, CVD/hypertension, obesity and **anaemia**; a curated meal-plan library; joint meal and exercise recommendations; real-user pilot data.
- **Differences:** no per-exercise safety ratings, no pregnancy or knee OA group, no FITT-VP prescription form reported in the abstracts, no physician approval gate, and wearable/CGM-driven adaptation. It is EU-focused, whereas this system serves Bangladesh.

#### 5. Sun et al. 2021: intelligent personalised exercise prescription in an eHealth promotion system (China)
- **Citation:** Sun T, Xu Y, Xie H, Ma Z, Wang Y. "Intelligent Personalized Exercise Prescription Based on an eHealth Promotion System to Improve Health Outcomes of Middle-Aged and Older Adult Community Dwellers: Pretest-Posttest Study." *J Med Internet Res* 2021;23(5):e28221. doi:10.2196/28221. PMID 34028359. Type: single-group pretest-posttest study — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- **What it built and method:** a cloud platform assessed PA, lifestyle, chronic disease and drug history, family history, cardiovascular function, body composition, bone density and fitness. An "intelligent system" then routed each participant: those **with relative contraindications for exercise** received a "health care exercise mode", and those without contraindications who exercised regularly received a "scientific fitness mode" — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- **Data and evaluation:** 177 real participants aged 52–85 (mean 67.93), from 2 community health centres in Anhui, over 12 months, analysed with paired t-tests. 97 were in health care mode and 80 in fitness mode — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- **Key numbers:** in health care mode, heart rate, subendocardial viability ratio, weight, BMI, body fat and baPWV changed significantly (for example baPWV MD −0.72). Blood pressure, muscle mass, bone density and balance did not change. Both groups declined in handgrip, vital capacity and agility. The authors state they are "unable to recommend such a program given the existing limitations" — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- **Similarities:** a contraindication-driven rule split before prescribing, which resembles the gate; older adults; chronic-disease history as input; an automated system issues the prescription.
- **Differences:** the routing algorithm is not described in the abstract; there is no per-exercise dataset, ML ranking, diet or adherence features; and it was evaluated with real users but without a control group.

#### 6. HyperRecSysPA: physical activity recommender for hypertensive patients
- **Citation:** Ferretto LR, Bellei EA, Biduski D, Bin LCP, Moro MM, Cervi CR, De Marchi ACB. "A Physical Activity Recommender System for Patients With Arterial Hypertension." *IEEE Access* 2020;8:61656–61664. doi:10.1109/ACCESS.2020.2983564. Type: system development plus physician validation. Verified via Crossref and DOAJ (not indexed in PubMed) — [DOI](https://doi.org/10.1109/ACCESS.2020.2983564); [DOAJ record](https://doaj.org/article/2ebc11afb9f9481bb8c6aac0fa37876c)
- **Built and method:** a hypertensive user-profile model (HyperModel2PAR, 32 elements in three groups) and a PA recommender (HyperRecSysPA) that uses it — [Semantic Scholar/DOAJ abstract](https://doi.org/10.1109/ACCESS.2020.2983564)
- **Evaluation and numbers:** physicians answered a questionnaire about the generated recommendations and approved "~75%" of them. No patient study is reported — [DOI abstract](https://doi.org/10.1109/ACCESS.2020.2983564)
- **Similar:** condition-specific (hypertension) PA recommendation with physicians reviewing the output.
- **Different:** physician review was a one-off validation, not a release gate per patient; a single condition; no FITT-VP structure or diet reported; the algorithm type is not given in the abstract.

#### 7. HeNuALs: ontology-based telehealth system for healthy nutrition and active lifestyle in older adults
- **Citation:** Spoladore D, Colombo V, Arlati S, Mahroo A, Trombetta A, Sacco M. "An Ontology-Based Framework for a Telehealthcare System to Foster Healthy Nutrition and Active Lifestyle in Older Adults." *Electronics* 2021;10:2129. doi:10.3390/electronics10172129. Verified via Crossref (MDPI; not in PubMed) — [DOI](https://doi.org/10.3390/electronics10172129)
- **Built:** an ontological layer storing patients, foods and PA data that infers suggestions "based on the effects of foods and exercises on specific health conditions". It has separate patient and clinician apps with different permissions, and wearable sensors to monitor exercise and "ensure patients' safety" — [DOI abstract](https://doi.org/10.3390/electronics10172129)
- **Evaluation:** inferences were validated on **two use cases**, one patient with respiratory disease and one with diabetes mellitus. Validation with target users is listed as future work — [DOI abstract](https://doi.org/10.3390/electronics10172129)
- **Similar:** combined diet and exercise; health-condition-driven knowledge; clinician access to patient data; older adults; no real-user evaluation (the same as F9).
- **Different:** symbolic inference only (no ranking model), dish labels of healthy/adequate/unhealthy, and no FITT-VP week plan, approval gate or checklist reported.

#### 8. HeLiS ontology and persuasive explanations (Key to Health / PerKApp line of work)
- **Citations:** Dragoni M, Bailoni T, Maimone R, Eccher C. "HeLiS: An Ontology for Supporting Healthy Lifestyles." *The Semantic Web – ISWC 2018*, LNCS, pp. 53–69. doi:10.1007/978-3-030-00668-6_4 (verified via Crossref and Semantic Scholar) — [DOI](https://doi.org/10.1007/978-3-030-00668-6_4). Dragoni M, Donadello I, Eccher C. "Explainable AI meets persuasiveness: Translating reasoning results into behavioral change advice." *Artif Intell Med* 2020;105:101840. doi:10.1016/j.artmed.2020.101840. PMID 32505427 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/32505427/)
- **Built:** HeLiS represents "both the food and physical activity domains" and concepts for monitoring users' actions and unhealthy behaviours. It was used in a real-world system, "Key to Health", which promotes healthy lifestyles at workplaces — [Semantic Scholar record](https://doi.org/10.1007/978-3-030-00668-6_4)
- **Method:** a reasoner checks logged intake against rules and detects violations. Natural-language generation turns violations into persuasive explanations, which the authors report "are able to reduce the unhealthy users' behaviors" — [PubMed 32505427](https://pubmed.ncbi.nlm.nih.gov/32505427/)
- **Similar:** a combined food-and-PA knowledge model, deterministic rule reasoning, and explanation of rule outcomes to users.
- **Different:** monitors behaviour after the fact rather than prescribing; workplace and healthy-population focus; no FITT-VP prescription, ranking or physician gate. The size of the user evaluation is not in the abstract.

#### 9. MyBehavior: bandit-based personalised suggestions for physical activity and diet
- **Citations:** Rabbi M, Pfammatter A, Zhang M, Spring B, Choudhury T. "Automated personalized feedback for physical activity and dietary behavior change with mobile phones: a randomized controlled trial on adults." *JMIR mHealth uHealth* 2015;3(2):e42. doi:10.2196/mhealth.4160. PMID 25977197 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/25977197/). Companion: Rabbi M, Aung MH, Zhang M, Choudhury T. "MyBehavior: automatic personalized health feedback from user behaviors and preferences using smartphones." *UbiComp 2015*, pp. 707–718. doi:10.1145/2750858.2805840 (Crossref) — [DOI](https://doi.org/10.1145/2750858.2805840)
- **Built and method:** combined automatic and manual logging of activity, location and food. A multi-armed bandit generates suggestions to continue, avoid or slightly change existing behaviours — [PubMed](https://pubmed.ncbi.nlm.nih.gov/25977197/)
- **Evaluation and numbers:** a 3-week randomised pilot with 17 participants (9 personalised, 8 generic suggestions written by professionals). The intervention group walked more (P=.05); calorie choices did not differ significantly (P=.15); users rated personalised suggestions higher (P<.001) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/25977197/)
- **Similar:** joint diet and PA suggestions with ML personalisation.
- **Different:** learns online from a single user's own logs (bandit) rather than an offline-trained ranker; healthy motivated adults; no safety gate, FITT-VP or physician.

#### 10. Zaleski et al. 2024: ChatGPT exercise recommendations scored against ACSM FITT-VP categories
- **Citation:** Zaleski AL, Berkowsky R, Craig KJT, Pescatello LS. "Comprehensiveness, Accuracy, and Readability of Exercise Recommendations Provided by an AI-Based Chatbot: Mixed Methods Study." *JMIR Med Educ* 2024;10:e51308. doi:10.2196/51308. PMID 38206661 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38206661/)
- **Method and data:** the chatbot was prompted through an API for **26 clinical populations**. Two reviewers coded 10 categories: condition-specific benefits, **pre-participation health screening**, frequency, intensity, time, type, volume, progression, special considerations and references — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38206661/)
- **Key numbers:** 41.2% (107/260) comprehensive; 90.7% (146/161) accurate; **8/15 (53%) of inaccuracies concerned pre-participation medical clearance**; readability at college level (FK 13.7). Observed themes included a preference for aerobic exercise and possible bias against age-based groups and people with disabilities — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38206661/)
- **Similar:** uses the same FITT-VP frame and clinical populations, and gives a ready coding scheme that could be used to audit this system's prescriptions.
- **Different:** an evaluation of a general LLM, not a built system.

#### 11. Dergaa et al. 2024: expert evaluation of GPT-4 exercise prescriptions
- **Citation:** Dergaa I, Saad HB, El Omri A, Glenn JM, Clark CCT, Washif JA, et al. (32 authors). "Using artificial intelligence for exercise prescription in personalised health promotion: A critical evaluation of OpenAI's GPT-4 model." *Biol Sport* 2024;41(2):221–241. doi:10.5114/biolsport.2024.133661. PMID 38524814 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38524814/)
- **Method and evaluation:** GPT-4 wrote 30-day programmes for 5 hypothetical profiles with health conditions. Exercise-prescription experts judged FITT adherence, RPE, medication and condition handling, and individualisation — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38524814/)
- **Findings:** the programmes were "general safety-conscious" but "lacked precision in addressing individual health conditions", "often prioritizing excessive safety over the effectiveness of training". The authors do not recommend AI as a substitute for professionals — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38524814/)
- **Similar/different:** an LLM baseline that motivates a deterministic gate and catalogue; it is qualitative only.

#### 12. Yang et al. 2026: predictive-model-tailored PA recommendations for adults with high blood pressure
- **Citation:** Yang Y, Chen M, Hu W, Fu Y, Li X, Liao Z, Feng H, Zhao Y, Pei L, Mi B, Chen F. "Physical Activity Recommendations Tailored by a Predictive Model for Adults With High Blood Pressure: Observational Study." *J Med Internet Res* 2026;28:e78492. doi:10.2196/78492. Verified via the Crossref DOI record; jmir.org returned 403 — [DOI](https://doi.org/10.2196/78492)
- **Built and method:** an ML model, trained in UK Biobank and externally validated in NHANES, predicts which of four accelerometer-derived PA patterns (active weekend warrior, active regular, active light, baseline) gives the highest predicted survival for each individual. It was integrated into a web application — [DOI abstract](https://doi.org/10.2196/78492)
- **Numbers:** 71,637 UK Biobank and 5,104 NHANES participants; external AUC 86.4% (95% CI 85.1–87.7) for 10-year mortality. A current pattern inconsistent with the predicted optimum was associated with HR 1.28 (1.20–1.38). Key drivers were stroke history, age, sex, BP class and antihypertensive medication — [DOI abstract](https://doi.org/10.2196/78492)
- **Similar:** an ML-ranked PA choice for hypertension, with medication and age among the inputs.
- **Different:** labels are observed mortality in cohort data, not a guideline function; it chooses a pattern, not a FITT-VP prescription; observational, with no safety gate.

#### 13. Cavallo & Toumazou 2023: personalised lifestyle recommender for T2D designed and simulated on UK Biobank
- **Citation:** Cavallo FR, Toumazou C. "Personalised lifestyle recommendations for type 2 diabetes: Design and simulation of a recommender system on UK Biobank Data." *PLOS Digit Health* 2023;2(8):e0000333. doi:10.1371/journal.pdig.0000333. PMID 37647301 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37647301/)
- **Built and method:** an adaptive knowledge-based system guided by the Behaviour Change Wheel and COM-B. It assigns each user to one of four diabetes clusters, recommends PA and sedentary levels from genotype and activity history, shows CVD risk, and uses leptin as a feedback signal — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37647301/)
- **Evaluation:** "trained and simulated" on UK Biobank diabetic participants, showing the system "could help increase activity over time". A human study is planned — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37647301/)
- **Similar:** a knowledge-based design with evaluation only by simulation, so it is a peer-reviewed precedent for publishing without patients.
- **Different:** activity levels rather than exercise items; needs genotype and hormone data; no diet, safety gate or physician.

#### 14. Yom-Tov et al. 2017: reinforcement learning to encourage PA in type 2 diabetes
- **Citation:** Yom-Tov E, Feraru G, Kozdoba M, Mannor S, Tennenholtz M, Hochberg I. "Encouraging Physical Activity in Patients With Diabetes: Intervention Using a Reinforcement Learning System." *J Med Internet Res* 2017;19(10):e338. doi:10.2196/jmir.7994. PMID 29017988 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/29017988/)
- **Built, data and evaluation:** 27 sedentary T2D patients received a smartphone pedometer and a personal PA plan. An RL algorithm personalised SMS messages (sent between once a day and once a week) and was compared with a static policy plus weekly reminders. The learning group increased activity and walking pace and had a "superior reduction" in HbA1c; the abstract gives no effect sizes — [PubMed](https://pubmed.ncbi.nlm.nih.gov/29017988/)
- **Similar:** diabetes, real patients, ML personalisation for exercise adherence.
- **Different:** personalises *messages*, not the prescription; no safety logic.

#### 15. StandingTall: app-delivered, self-managed balance exercise for fall prevention (age 70+)
- **Citation:** Delbaere K, Valenzuela T, Lord SR, Clemson L, Zijlstra GAR, Close JCT, Lung T, Woodbury A, Chow J, McInerney G, Miles L, Toson B, Briggs N, van Schooten KS. "E-health StandingTall balance exercise for fall prevention in older people: results of a two year randomised controlled trial." *BMJ* 2021;373:n740. doi:10.1136/bmj.n740. PMID 33824131 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33824131/)
- **Design and data:** an assessor-blinded RCT with 503 people aged 70+, independent and without unstable or acute conditions precluding exercise. The intervention was 2 h/week of StandingTall plus education (n=254) versus education alone (n=249), for 2 years — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33824131/)
- **Numbers:** 12-month primary outcomes were not significant (IRR 0.84, 0.62–1.13). Over 24 months the fall rate was 16% lower (IRR 0.84, 0.72–0.98) and injurious falls 20% lower (RR 0.80, 0.66–0.98). 68.1% exercised a median 114.0 min/week at 12 months and 52.0% exercised 120.4 min/week at 24 months. No serious training-related adverse events occurred — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33824131/)
- **Similar:** the strongest real-world evidence for the system's balance/falls-prevention component in older adults (Otago-style home balance work delivered digitally).
- **Different:** a balance-only programme, not a multi-condition recommender; no diet or physician gate.

#### 16. re.flex: fully automated app-based exercise for knee osteoarthritis
- **Citation:** Dieter V, Janssen P, Krauss I. "Efficacy of the mHealth-Based Exercise Intervention re.flex for Patients With Knee Osteoarthritis: Pilot Randomized Controlled Trial." *JMIR mHealth uHealth* 2024;12:e54356. doi:10.2196/54356. PMID 39250181 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39250181/)
- **Design:** a 12-week **fully automated** app-based home programme with 3 sessions/week, monitored by two accelerometers placed above and below the knee, with or without a brace, versus usual care. 61 participants (mean age 62.9) were analysed per protocol — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39250181/)
- **Numbers:** pain ES 0.76, function ES 0.64, knee-related QoL ES 0.76; adherence 92.5% (899/972) of scheduled sessions; no effect on psychological or performance measures — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39250181/)
- **Similar:** automated knee-OA exercise delivery on a fixed weekly session pattern, with adherence tracked per scheduled session (close to the daily checklist).
- **Different:** a single condition, sensor-guided, with no recommender, OARSI rule encoding or physician gate reported.

#### 17. HealthyMoms: smartphone app for weight gain, diet and physical activity in pregnancy
- **Citation:** Sandborg J, Söderström E, Henriksson P, Bendtsen M, Henström M, Leppänen MH, Maddison R, Migueles JH, Blomberg M, Löf M. "Effectiveness of a Smartphone App to Promote Healthy Weight Gain, Diet, and Physical Activity During Pregnancy (HealthyMoms): Randomized Controlled Trial." *JMIR mHealth uHealth* 2021;9(3):e26091. doi:10.2196/26091. PMID 33704075 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33704075/)
- **Design:** a 2-arm RCT (n=305; 152 vs 153) in Sweden. The 6-month app offered information, push notifications, self-monitoring and feedback on weight gain, diet and PA — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33704075/)
- **Numbers:** no overall effect on gestational weight gain (P=.62); among women with overweight or obesity, completers gained 1.67 kg less (95% CI −3.26 to −0.09). Diet quality (Swedish HEI) was higher (+0.27, 0.05–0.50); MVPA did not differ (P≥.21) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33704075/)
- **Companion (engagement):** in the intervention group (n=134), more self-monitoring registrations went with lower weight gain (β −0.18, P=.043) and better diet quality (β 0.17, P=.019), driven mainly by PA registrations. App sessions and page views were not associated with outcomes. Henriksson P, et al. *Sci Rep* 2022;12:13793. doi:10.1038/s41598-022-17554-9. PMID 35963935 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35963935/)
- **Similar:** pregnancy, combined diet and PA, and self-monitoring (closest to tick-off logging).
- **Different:** generic recommendations with feedback, not a prescription; no condition-specific safety ratings or physician approval.

### Inferences
- Positions 1–3 share this system's architecture idea (explicit guideline rules that bound what the patient receives) but none ranks items from a per-exercise safety dataset. Positions 4, 7, 8, 9 and 17 share the diet-plus-exercise scope but not the prescription form. No paper found pairs a FITT-VP prescription with a meal plan, physician approval and a daily checklist.
- The ranking would change if the paper emphasised the ML component. On that view Yang 2026 (12) and the LightGBM-based exercise prescription framework of Mo et al. 2026 (see the methods question below) move up.

### Gaps
- No exercise recommender was found that encodes pregnancy-specific (for example ACOG) safety rules or OARSI knee-OA rules per exercise, and no Bangladesh or South Asian exercise recommender was found. The nearest South Asian work is a pregnancy diet/PA coaching app protocol from Karachi (Nuruddin et al. 2021; see the diet-and-exercise question), which has no results.
- The algorithm types in Ferretto 2020 and Sun 2021 are not described in their abstracts; the full texts were not read.
- EXPERT: no published clinician or patient evaluation of the tool was found in this search.

## Which systems automate exercise prescription (FITT/FITT-VP/ACSM) for diabetes, hypertension, knee OA, obesity, pregnancy or older adults, and are they rule-based, knowledge-based, ML or RL?

### Takeaway
Clinical exercise-prescription automation is mostly **rule- or knowledge-based**: EXPERT, P3-EX, Sun 2021, and the ontologies HeNuALs, NAct and EXMO. Newer work adds **LLMs constrained by deterministic rules** (FITTER) or **supervised ML** that chooses among a few activity patterns (Yang 2026, Mo 2026). **RL/bandits** have been used mainly to time or personalise nudges, not to set the prescription (Yom-Tov 2017, HeartSteps, MyBehavior).

### Cited Findings
- **Rule-based / expert algorithm:**
  - EXPERT covers diabetes, obesity, hypertension, hypercholesterolaemia and 10 CVDs — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/)
  - P3-EX covers hypertension, diabetes, dyslipidaemia and obesity, with ACSM clearance and FITT — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/)
  - Sun 2021 routes people with or without relative contraindications into two prescription modes — [PubMed 34028359](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- **Knowledge bases and ontologies:**
  - EXMO (Exercise Medicine Ontology) has 434 classes and 9,732 axioms built from guidelines, databases and articles. It was expert-evaluated and checked with the ELK/JFact reasoners, and the authors propose it to support recommendation systems. Liu X, et al. *Sci Data* 2024;11:1349. doi:10.1038/s41597-024-04217-9 — [PubMed 39695140](https://pubmed.ncbi.nlm.nih.gov/39695140/)
  - PAHFKB is a heart-failure exercise-prescription knowledge base mined from 357 studies (1989–2021; over 900,000 subjects) with 1,010 items including 357 training protocols. Zhang K, et al. *Digit Health* 2024;10:20552076241299083. doi:10.1177/20552076241299083 — [PubMed 39569397](https://pubmed.ncbi.nlm.nih.gov/39569397/)
  - COPPER is an OBO-compliant ontology for PA action and coping plans (288 classes), checked with competency questions and use cases. Braun M, et al. *Int J Behav Nutr Phys Act* 2025;22:52. doi:10.1186/s12966-025-01744-5 — [PubMed 40325420](https://pubmed.ncbi.nlm.nih.gov/40325420/)
- **Literature-to-rules automation:** Gemini 1.5 extracted evidence from PubMed abstracts into **six executable decision rules** linking shoulder range-of-motion deficits to exercises. The rules were applied to secondary range-of-motion data from 35 patients with shoulder impingement. Kim JH. *Musculoskelet Sci Pract* 2026;82:103520. doi:10.1016/j.msksp.2026.103520 — [PubMed 41707384](https://pubmed.ncbi.nlm.nih.gov/41707384/)
- **LLM plus deterministic rules:** FITTER (preprint) — [arXiv](https://arxiv.org/html/2611.03983)
- **Supervised ML:**
  - Yang 2026 picks the PA pattern with the highest predicted survival for hypertension — [DOI](https://doi.org/10.2196/78492)
  - Mo et al. 2026 use 1D-CNN with multi-head attention plus **LightGBM**, trained on 6,698 male students aged 18–20, to classify BMI from fitness tests (accuracy 94.5%, κ 0.91, F1 0.93) and drive SHAP-guided prescriptions. A 12-week randomised trial reported a 23.5% fall in overweight/obesity prevalence. Mo M, et al. *Sci Rep* 2026;16. doi:10.1038/s41598-026-42405-2 — [PubMed 41826482](https://pubmed.ncbi.nlm.nih.gov/41826482/)
- **RL/bandits for nudges:**
  - Yom-Tov 2017 personalised SMS by RL in T2D — [PubMed 29017988](https://pubmed.ncbi.nlm.nih.gov/29017988/)
  - MyBehavior used a multi-armed bandit — [PubMed 25977197](https://pubmed.ncbi.nlm.nih.gov/25977197/)
  - HeartSteps V2 uses an RL algorithm that decides "five times per day, whether to deliver a context-tailored activity suggestion". Liao P, Greenewald K, Klasnja P, Murphy S. *Proc ACM IMWUT* 2020;4(1):18. doi:10.1145/3381007 — [PubMed 34527853](https://pubmed.ncbi.nlm.nih.gov/34527853/)
- **Older adults:**
  - StandingTall (balance, age 70+) — [PubMed 33824131](https://pubmed.ncbi.nlm.nih.gov/33824131/)
  - A protocol for a smartphone-delivered *personalised multicomponent* programme (upper/lower body, flexibility, strength and dynamic/static/vestibular balance) for people aged 65+, compared with WHO guideline counselling (planned n=300). Netz Y, et al. *BMC Geriatr* 2021;21:605. doi:10.1186/s12877-021-02559-2 — [PubMed 34702168](https://pubmed.ncbi.nlm.nih.gov/34702168/)
- **Knee OA apps:**
  - re.flex was fully automated — [PubMed 39250181](https://pubmed.ncbi.nlm.nih.gov/39250181/)
  - Im et al. 2025 delivered a 6-week app programme for people aged 60+ with knee OA, *tailored by physiotherapists* from remotely monitored symptoms (n=29, randomised 2:1). 69% exercised at least 5 days/week, the WOMAC median change was −11.00 and no adverse events occurred. Im YJ, et al. *JMIR mHealth uHealth* 2025;13:e71073. doi:10.2196/71073 — [PubMed 41401375](https://pubmed.ncbi.nlm.nih.gov/41401375/)

### Inferences
- No paper found trains an exercise *ranker* on synthetic patient types with labels from a guideline function. Mo 2026 uses gradient boosting but for BMI classification on real student data, and Yang 2026 learns from observed mortality. This system's "rule gate, then GBM re-ranking of permitted items" design looks unreported in this literature, though the search was not exhaustive.
- FITT-VP with all four components (aerobic, resistance, flexibility, neuromotor) appears explicitly only in FITTER and in Zaleski's coding scheme. EXPERT and P3-EX describe FITT and its dosing variables.

### Gaps
- Pregnancy: no exercise-prescription *recommender* was found. The pregnancy hits were diet/PA apps (HealthyMoms) and counselling interventions, for example Fit for Two: 17 pregnant women with type 2 or gestational diabetes, counselling plus Fitbit step goals. Larsen B, et al. *JMIR mHealth uHealth* 2020;8(10):e18915. doi:10.2196/18915 — [PubMed 33084584](https://pubmed.ncbi.nlm.nih.gov/33084584/)
- Anaemia: no exercise recommender with anaemia-specific exercise rules was found. PROTEIN's knowledge base includes iron-deficiency anaemia as a population group, but its abstract does not describe exercise-level rules for anaemia — [PubMed 38773712](https://pubmed.ncbi.nlm.nih.gov/38773712/)
- No RecSys/HealthRecSys workshop paper on exercise prescription was identified and verified in this pass.

## How do these systems handle safety: pre-participation screening (e.g., PAR-Q+), contraindications, condition-specific exclusions, intensity limits?

### Takeaway
Safety is handled in four ways: an ACSM medical-clearance decision before prescribing (P3-EX), condition-level safety advice in expert rules (EXPERT), contraindication-based routing (Sun 2021), and post-generation rule audits that cap intensity and forbid activities (FITTER). No verified system implements PAR-Q+, and LLM-only prescriptions are weakest exactly on pre-participation screening.

### Cited Findings
- P3-EX determines whether medical clearance is needed from age, sex, signs and symptoms, known CVD/metabolic/renal disease and desired intensity, per ACSM guidance; 79.2% of users agreed its prescriptions were safe — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/); [PubMed](https://pubmed.ncbi.nlm.nih.gov/40677518/)
- EXPERT gives "exercise training safety advices" per disease and adjusts for medications, exercise tolerance and adverse events during exercise testing — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/); [PubMed 29729003](https://pubmed.ncbi.nlm.nih.gov/29729003/)
- Sun 2021 gives people with relative contraindications a separate "health care" mode — [PubMed 34028359](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- FITTER:
  - It uses pre-generation profile and medication screens (FDA-label knowledge base), then a deterministic audit over intensity limits, activity restrictions, F/T/volume limits, progression restrictions and stop criteria — [arXiv](https://arxiv.org/html/2611.03983)
  - Removing audit-and-repair cut safety-constraint compliance from 99.0% to 62.0% (cancer ablation), but clinicians rated only 80.6% of the reviewed prescriptions safe — [arXiv](https://arxiv.org/html/2611.03983)
  - It does not mention PAR-Q+ or ACSM screening — [arXiv](https://arxiv.org/html/2611.03983)
- ChatGPT exercise advice was 90.7% accurate, but 53% (8/15) of inaccuracies concerned pre-participation medical clearance — [PubMed 38206661](https://pubmed.ncbi.nlm.nih.gov/38206661/). GPT-4 programmes erred towards "excessive safety over the effectiveness of training" — [PubMed 38524814](https://pubmed.ncbi.nlm.nih.gov/38524814/)
- HeNuALs uses wearable sensors during prescribed exercise "to ensure patients' safety" — [DOI](https://doi.org/10.3390/electronics10172129)
- Trial-based safety: StandingTall excluded people with unstable or acute conditions precluding exercise and reported no serious training-related adverse events over 2 years — [PubMed 33824131](https://pubmed.ncbi.nlm.nih.gov/33824131/). Im 2025 reported no adverse events in its knee-OA app trial — [PubMed 41401375](https://pubmed.ncbi.nlm.nih.gov/41401375/)

### Inferences
- FITTER's ablation is the only quantitative evidence found that a deterministic rule layer matters more than retrieval or an LLM self-check. It supports the paper's claim that safety should not depend on the learned or generative component. The 98.5% versus 80.6% gap also warns that rule compliance is not clinical safety, and the paper should say so about its own gate.
- Per-exercise contraindication labels for named conditions (safe/modify/avoid) were not found in any system. EXPERT and FITTER hold constraints at the prescription level, and the knowledge bases (EXMO, PAHFKB) hold protocols and terms, not per-exercise safety ratings — [PubMed 39695140](https://pubmed.ncbi.nlm.nih.gov/39695140/); [PubMed 39569397](https://pubmed.ncbi.nlm.nih.gov/39569397/)

### Gaps
- No peer-reviewed system implementing PAR-Q+ or the 2015 ACSM pre-participation algorithm as an automated gate was verified, apart from P3-EX's clearance step. A web search surfaced only a patent application, which was not reviewed.
- Intensity limits for pregnancy, anaemia (low haemoglobin) or uncontrolled blood pressure as automated rules were not found in any verified system.

## Which systems combine diet and exercise recommendations in one lifestyle plan or coaching app, especially for chronic disease or pregnancy?

### Takeaway
Combined diet-and-PA systems exist in three forms. There are ontology/knowledge-based recommenders (PROTEIN/NAct, HeNuALs, HeLiS), learning-based suggestion apps (MyBehavior, CGM-driven programmes) and self-monitoring apps (HealthyMoms). Evaluations range from use cases to small pilots and one 305-person pregnancy RCT. None couples a physician-approved exercise prescription with a meal plan.

### Cited Findings
- PROTEIN: joint meal and exercise recommendations; knowledge base for 10 groups including T2D, CVD, obesity and iron-deficiency anaemia; pilot RCT with 21 participants — [PubMed 38773712](https://pubmed.ncbi.nlm.nih.gov/38773712/); [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/); [DOI NAct](https://doi.org/10.3233/FAIA210377)
- HeNuALs: diet and active lifestyle for older adults with chronic disease; patient and clinician apps; validated on 2 use cases — [DOI](https://doi.org/10.3390/electronics10172129)
- HeLiS: food plus PA ontology used in the "Key to Health" workplace programme — [DOI](https://doi.org/10.1007/978-3-030-00668-6_4); persuasive explanations — [PubMed 32505427](https://pubmed.ncbi.nlm.nih.gov/32505427/)
- MyBehavior: bandit-generated PA and food suggestions; 17-person 3-week RCT — [PubMed 25977197](https://pubmed.ncbi.nlm.nih.gov/25977197/)
- CGM and wearable programme: 2,217 participants (normoglycaemia, prediabetes and T2D) used CGM for 28 days, logged food, PA and weight, and got personalised recommendations from glycaemic patterns. The authors report improvements in hyperglycaemia, glucose variability and weight. Zahedani AD, et al. *NPJ Digit Med* 2023;6:216. doi:10.1038/s41746-023-00956-y — [PubMed 38001287](https://pubmed.ncbi.nlm.nih.gov/38001287/)
- Livongo: ML on member engagement estimated per-member treatment effects of five action types, including PA tracking and nutrition monitoring. Coach interaction and glucose self-monitoring showed the largest average estimated-A1c decreases (1.7% and 1.4%). Retrospective. Kamath S, et al. *JMIR Form Res* 2022;6(3):e33329. doi:10.2196/33329 — [PubMed 35311691](https://pubmed.ncbi.nlm.nih.gov/35311691/)
- ML diabetes prediction plus "food and exercise recommender" (Random Forest, SVM, XGBoost for prediction), reporting an error rate below 30% on over 100 million user-rated foods. The exercise component is not quantified in the abstract. Sajid M, et al. *PLoS One* 2025;20(1):e0307718. doi:10.1371/journal.pone.0307718 — [PubMed 39775570](https://pubmed.ncbi.nlm.nih.gov/39775570/)
- HealthyW8 Healthy Lifestyle Recommender System: tailored PA and meal recommendations for people aged 65+ with overweight; protocol for 7 European pilots (about 240 participants, 3 months). No results yet. Vahid F, et al. *BMJ Open* 2026;16(3):e108771. doi:10.1136/bmjopen-2025-108771 — [PubMed 41881526](https://pubmed.ncbi.nlm.nih.gov/41881526/)
- Pregnancy:
  - HealthyMoms RCT (n=305) — [PubMed 33704075](https://pubmed.ncbi.nlm.nih.gov/33704075/)
  - PurUmeed Aaghaz app (Karachi, Pakistan): personalised diet, supplement and PA advice plus 3 weekly push reminders, versus face-to-face counselling; protocol for 300 first-trimester women without comorbidities. Nuruddin R, et al. *JMIR Res Protoc* 2021;10(11):e31611. doi:10.2196/31611 — [PubMed 34783675](https://pubmed.ncbi.nlm.nih.gov/34783675/)

### Inferences
- Combined systems usually pair diet rules with generic PA targets (steps, MVPA minutes, "activity levels"). They rarely produce a structured exercise prescription. This system's pairing of a weekly meal plan with a FITT-VP week is uncommon in what was found.
- PurUmeed Aaghaz (Pakistan) and the PROTEIN anaemia group are the closest in setting and condition to a Bangladesh deployment, and both lack exercise safety rules.

### Gaps
- Results of the PurUmeed Aaghaz trial were not located. Pregnancy-specific combined *recommenders* (as opposed to self-monitoring apps) were not found.

## What evidence exists on adherence features (daily task checklists, streaks, gamification, reminders), with effect sizes?

### Takeaway
Gamification and digital adjuncts have **small** positive effects on physical activity, with SMD/g around 0.2–0.45, and the effects shrink after the intervention ends. Self-monitoring of diet and PA, the mechanism behind a tick-off checklist, has meta-analytic support, especially when advice is tailored. Evidence on **streak counters specifically** is thin: one large observational usage study, consumer-psychology experiments, a qualitative study and a completed but unpublished RCT.

### Cited Findings
- **Gamification:**
  - Mazeas 2022 pooled 16 RCTs (n=2,407): Hedges g=0.42 (95% CI 0.14–0.69); g=0.58 versus inactive and 0.23 (0.05–0.41) versus active non-gamified controls; long-term g=0.15 (0.07–0.23). There was no subgroup difference between healthy people and adults with chronic disease. Mazeas A, Duclos M, Pereira B, Chalabaev A. *J Med Internet Res* 2022;24(1):e26779. doi:10.2196/26779 — [PubMed 34982715](https://pubmed.ncbi.nlm.nih.gov/34982715/)
  - Nishi 2024 compared gamified with **non-gamified apps** (36 trials, 49 comparisons, n=10,079): +489 steps/day (64 to 914; high certainty, judged "trivial"); BMI −0.28 kg/m² and weight −0.70 kg (moderate); body fat −1.92% (high); waist −1.16 cm (moderate). Nishi SK, et al. *eClinicalMedicine* 2024;76:102798. doi:10.1016/j.eclinm.2024.102798 — [PubMed 39764571](https://pubmed.ncbi.nlm.nih.gov/39764571/)
- **Apps and trackers overall:** 28 RCTs in the meta-analysis (n=7,454; adults 18–65 *without chronic illness*): SDM 0.350 (0.236–0.465), I²=69%, about 1,850 steps/day. Interventions with text messaging and personalisation features were significantly more effective. Laranjo L, et al. *Br J Sports Med* 2021;55(8):422–432. doi:10.1136/bjsports-2020-102892 — [PubMed 33355160](https://pubmed.ncbi.nlm.nih.gov/33355160/)
- **Reminders and prompts:**
  - One-way text messages increased objectively measured steps (Cohen's d=0.38, 0.19–0.58; 10 studies); the effect on MVPA was not significant (d=0.31, −0.01 to 0.63). Smith DM, et al. *Am J Prev Med* 2020;58(1):142–151. doi:10.1016/j.amepre.2019.08.014 — [PubMed 31759805](https://pubmed.ncbi.nlm.nih.gov/31759805/)
  - In the HeartSteps micro-randomised trial (44 adults, 6 weeks), any suggestion versus none raised 30-min step counts by 14% (35 steps, p=.06); walking suggestions raised them by 24% (59 steps, p=.02). Effects were largest early and declined over time. Klasnja P, et al. *Ann Behav Med* 2019;53(6):573–582. doi:10.1093/abm/kay067 — [PubMed 30192907](https://pubmed.ncbi.nlm.nih.gov/30192907/)
- **Digital adjuncts to *prescribed* home exercise:** 10 RCTs (n=1,117); 7 favoured the digital addition, and the 3 null trials had longer follow-up. Heterogeneity prevented meta-analysis, and quality was low to moderate. Lang S, McLelland C, MacDonald D, Hamilton DF. *Arch Physiother* 2022;12:24. doi:10.1186/s40945-022-00148-z — [PubMed 36184611](https://pubmed.ncbi.nlm.nih.gov/36184611/)
- **Self-monitoring (checklist-like logging):**
  - Digital self-monitoring of diet *and* PA in adults with overweight or obesity (12 RCTs): weight MD −2.87 kg (−3.78 to −1.96), moderate PA SMD 0.44 (0.26–0.62), energy intake −181.71 kcal; tailored interventions were more effective than non-tailored ones. Berry R, Kassavou A, Sutton S. *Obes Rev* 2021;22(10):e13306. doi:10.1111/obr.13306 — [PubMed 34192411](https://pubmed.ncbi.nlm.nih.gov/34192411/)
  - In hypertension (15 RCTs, 7,415 patients), app-based behavioural self-monitoring lowered SBP by 1.64 mmHg (95% CI reported as 2.73–0.55). Kassavou A, et al. *JMIR mHealth uHealth* 2022;10(7):e34767. doi:10.2196/34767 — [PubMed 35819830](https://pubmed.ncbi.nlm.nih.gov/35819830/)
  - In pregnancy, the number of self-monitoring registrations (not sessions or page views) was associated with outcomes — [PubMed 35963935](https://pubmed.ncbi.nlm.nih.gov/35963935/)
- **Streaks:**
  - Carrot Rewards (41,207 users, 12 months): over 60% used the app for at least 6 months and 29% for 12 months. The mean streak was 20.22 weeks and the mean break 16.14 weeks; the median time to first break was 18 weeks. Breaks and re-engagement were common. Lau EY, Mitchell MS, Faulkner G. *Front Public Health* 2022;10:914433. doi:10.3389/fpubh.2022.914433 — [PubMed 36438245](https://pubmed.ncbi.nlm.nih.gov/36438245/)
  - In seven studies, highlighting **intact** (versus broken) logged streaks increased later engagement. The effect grew when people blamed themselves for the break and shrank when a broken streak could be "repaired". Silverman J, Barasch A. *J Consum Res* 2022;49(6):1095–1117. doi:10.1093/jcr/ucac029 (Crossref) — [DOI](https://doi.org/10.1093/jcr/ucac029)
  - Run streakers (qualitative, n=21, streaks of 100 to over 4,500 days) described habit automaticity, but "many run streakers reported running through injuries and lack of recovery". Curran M, et al. *Health Psychol Behav Med* 2024;12(1):2416505. doi:10.1080/21642850.2024.2416505 — [PubMed 39439910](https://pubmed.ncbi.nlm.nih.gov/39439910/)
  - A University of Pennsylvania RCT of streak-based versus tally-based feedback in a 30-day digital health challenge (enrolment 7,004; primary outcome lessons completed) is registered as COMPLETED (2026-01-21) with no results posted — [ClinicalTrials.gov NCT07220044](https://clinicaltrials.gov/study/NCT07220044)
- **Adherence observed in exercise-app trials:** re.flex 92.5% of scheduled sessions — [PubMed 39250181](https://pubmed.ncbi.nlm.nih.gov/39250181/); StandingTall 68.1% exercising a median 114 min/week at 12 months — [PubMed 33824131](https://pubmed.ncbi.nlm.nih.gov/33824131/); PROTEIN mean use 42 days with high dropout — [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/)

### Inferences
- A daily checklist of meals and exercise is a form of self-monitoring, so the paper can cite Berry 2021 and Henriksson 2022 for the mechanism. It should not claim an effect, because the system has not been tested with users.
- Streak design implications: Silverman and Barasch suggest broken streaks can lower engagement and that a "repair" option softens this. Curran warns streaks can push people to exercise through injury. A streak counted over *scheduled* tasks, with planned rest and non-consecutive strength days not counted as breaks, would fit both findings; this is an inference, not tested.
- Gamification effects decay (Mazeas long-term g=0.15; HeartSteps effects fall over weeks), so claims about a streak's contribution should be framed as an untested design choice.

### Gaps
- No RCT isolating a daily *checklist* feature, or a streak counter in a health app, has published results. NCT07220044 is the most direct test and is unpublished.
- Laranjo 2021 excluded people with chronic illness, so the pooled effect may not transfer to this system's patients.

## How were these systems evaluated: offline, expert review, user studies or patient trials?

### Takeaway
Evaluation splits into four tiers. (1) Simulation or offline evaluation on cohort or synthetic data: FITTER, Cavallo 2023, Yang 2026, HeNuALs use cases, EXPERT simulations. (2) Expert or clinician review: FITTER with 80 prescriptions and 4 clinicians, Ferretto (~75% approved), Zaleski, Dergaa, and the P3-EX usability survey with 309 professionals. (3) Small pilots with real users: MyBehavior 17, PROTEIN 21, Yom-Tov 27, HeartSteps 44, re.flex 61, Sun 177 without a control. (4) Larger RCTs: StandingTall 503, HealthyMoms 305. Few recommender-style systems reach tier 3 or 4.

### Cited Findings
- Simulation or offline:
  - FITTER: retrospective, simulated scenario variables, no delivery to participants — [arXiv](https://arxiv.org/html/2611.03983)
  - Cavallo 2023: trained and simulated on UK Biobank — [PubMed 37647301](https://pubmed.ncbi.nlm.nih.gov/37647301/)
  - Yang 2026: observational cohorts with external validation — [DOI](https://doi.org/10.2196/78492)
  - HeNuALs: two use cases — [DOI](https://doi.org/10.3390/electronics10172129)
  - EXPERT: simulations — [PubMed 29729003](https://pubmed.ncbi.nlm.nih.gov/29729003/)
- Expert or clinician review:
  - FITTER: one clinician per prescription, no agreement statistic — [arXiv](https://arxiv.org/html/2611.03983)
  - Ferretto: physicians approved ~75% — [DOI](https://doi.org/10.1109/ACCESS.2020.2983564)
  - Zaleski: two coders over 10 FITT-VP-based categories — [PubMed 38206661](https://pubmed.ncbi.nlm.nih.gov/38206661/)
  - Dergaa: expert panel review — [PubMed 38524814](https://pubmed.ncbi.nlm.nih.gov/38524814/)
  - P3-EX: practitioners worked a hypothetical case — [PubMed 40677518](https://pubmed.ncbi.nlm.nih.gov/40677518/)
- Pilots: [PubMed 25977197](https://pubmed.ncbi.nlm.nih.gov/25977197/); [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/); [PubMed 29017988](https://pubmed.ncbi.nlm.nih.gov/29017988/); [PubMed 30192907](https://pubmed.ncbi.nlm.nih.gov/30192907/); [PubMed 39250181](https://pubmed.ncbi.nlm.nih.gov/39250181/); [PubMed 34028359](https://pubmed.ncbi.nlm.nih.gov/34028359/)
- RCTs: [PubMed 33824131](https://pubmed.ncbi.nlm.nih.gov/33824131/); [PubMed 33704075](https://pubmed.ncbi.nlm.nih.gov/33704075/)

### Inferences
- An offline evaluation on synthetic data, as here, has peer-reviewed precedent (Cavallo 2023 in PLOS Digital Health; EXPERT simulations). However, the closest comparators add *at least* a clinician review (FITTER, Ferretto, P3-EX), and a reviewer will expect one.
- A cheap next step matching the field: have physicians rate a sample of generated prescriptions with Zaleski's 10-category coding scheme or FITTER's five review dimensions, and report inter-rater agreement. FITTER did not report agreement.

### Gaps
- No exercise recommender was found with a head-to-head comparison against clinician-written prescriptions on the same patients.
- Results across papers are not comparable. Tasks, populations and metrics differ (compliance with constraints, approval rates, steps, falls), so numbers should not be set against this system's metrics.

## Which venues publish this work?

### Takeaway
Clinical-informatics journals (the JMIR family, Digital Health, PLOS Digital Health, AIIM) dominate. Sports and cardiology journals carry the guideline-encoding tools (EJPC, Sports Med, Biol Sport, BJSM). CS venues (IEEE Access, ACM UbiComp/IMWUT, ISWC/LNCS, FOIS, MDPI Electronics, arXiv) carry the engineering papers.

### Cited Findings
- **JMIR family:**
  - J Med Internet Res: Sun 2021 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34028359/); Yom-Tov 2017 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/29017988/); Mazeas 2022 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34982715/); Yang 2026 — [DOI](https://doi.org/10.2196/78492)
  - JMIR mHealth uHealth: MyBehavior — [PubMed](https://pubmed.ncbi.nlm.nih.gov/25977197/); re.flex — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39250181/); HealthyMoms — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33704075/); Im 2025 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41401375/)
  - JMIR Med Educ: Zaleski — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38206661/)
  - JMIR Hum Factors: PROTEIN pilot — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42342244/)
- **Digital Health (SAGE):** P3-EX — [PubMed](https://pubmed.ncbi.nlm.nih.gov/40677518/); PAHFKB — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39569397/)
- **PLOS Digital Health:** Cavallo — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37647301/). **Artif Intell Med:** Dragoni 2020 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/32505427/). **Sci Data:** EXMO — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39695140/). **Sci Rep:** Mo 2026 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41826482/)
- **Cardiology and sport:** Eur J Prev Cardiol (EXPERT) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/28420250/); Sports Med (EXPERT consensus) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/29729003/); Biol Sport (Dergaa) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38524814/); BJSM (Laranjo) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33355160/); BMJ (StandingTall) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/33824131/); Arch Physiother (Lang) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36184611/); IJBNPA (COPPER) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/40325420/); Musculoskelet Sci Pract (Kim) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41707384/)
- **CS and engineering:** IEEE Access (Ferretto) — [DOI](https://doi.org/10.1109/ACCESS.2020.2983564); ACM UbiComp 2015 (MyBehavior) — [DOI](https://doi.org/10.1145/2750858.2805840); Proc ACM IMWUT (HeartSteps RL) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34527853/); ISWC 2018 LNCS (HeLiS) — [DOI](https://doi.org/10.1007/978-3-030-00668-6_4); FOIS 2021 FAIA (NAct) — [DOI](https://doi.org/10.3233/FAIA210377); MDPI Electronics (HeNuALs) — [DOI](https://doi.org/10.3390/electronics10172129); arXiv (FITTER, preprint) — [arXiv](https://arxiv.org/abs/2611.03983)
- **Nutrition, obesity, behaviour and public health:** Nutr Bull (PROTEIN knowledge base) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38773712/); Obes Rev (Berry) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34192411/); eClinicalMedicine (Nishi) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39764571/); Am J Prev Med (Smith) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/31759805/); Ann Behav Med (HeartSteps MRT) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/30192907/); Front Public Health (Lau) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36438245/); J Consum Res (Silverman) — [DOI](https://doi.org/10.1093/jcr/ucac029); Health Psychol Behav Med (Curran) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39439910/)

### Inferences
- A paper whose contribution is a safety-gated, physician-supervised recommender with synthetic-data evaluation fits *Digital Health*, *PLOS Digital Health*, *JMIR Formative Research/JMIR Medical Informatics* or *IEEE Access*. These venues have published comparable development-stage work with no patient outcomes (P3-EX, Cavallo, Ferretto).

### Gaps
- No RecSys HealthRecSys workshop paper on exercise or lifestyle recommendation was verified in this pass, so that venue's coverage is unknown here.

## Synthesis: what is common, what this system adds, and what a reviewer would criticise

### Takeaway
The field agrees that deterministic guideline rules should bound what patients receive (EXPERT, P3-EX, FITTER) and that diet and PA work better advised together (PROTEIN, HeNuALs, HealthyMoms). Against the papers found, this system's distinct elements are: a cited per-exercise safety dataset with three-level ratings per condition; a gate *before* ranking rather than an audit after generation; physician approval as a release gate per patient; an explicit week calendar with strength-spacing rules; and a daily checklist and streak, all in one Bangladesh-facing app. A reviewer's main objections will be the absence of any clinician or patient evaluation, synthetic labels that make the ranker's metrics circular, and the lack of pre-participation screening evidence.

### Cited Findings
- **Common:**
  - Prescriptions follow ACSM-style dosing (FITT or FITT-VP) — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/); [PMC P3-EX](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/); [arXiv FITTER](https://arxiv.org/html/2611.03983)
  - Rules are derived from literature or guidelines by experts — [PubMed 29729003](https://pubmed.ncbi.nlm.nih.gov/29729003/); [PubMed 38773712](https://pubmed.ncbi.nlm.nih.gov/38773712/)
  - Learned components are restricted to personalisation within or after rules — [arXiv FITTER](https://arxiv.org/html/2611.03983)
  - Evaluation is mostly offline or expert-based — see the evaluation question above
- **What the system adds (relative to the papers found, not an exhaustive claim):**
  1. Per-exercise safe/modify/avoid ratings across pregnancy, hypertension, diabetes, anaemia and knee OA, built from 88 cited sources. EXPERT's safety advice is per condition and prescription — [PubMed 28420250](https://pubmed.ncbi.nlm.nih.gov/28420250/). EXMO and PAHFKB store terms and protocols, not exercise-level contraindication ratings — [PubMed 39695140](https://pubmed.ncbi.nlm.nih.gov/39695140/); [PubMed 39569397](https://pubmed.ncbi.nlm.nih.gov/39569397/).
  2. A gate before ranking. FITTER repairs violations *after* LLM generation, and its ablation shows how much the rule layer matters (99.0% versus 62.0%) — [arXiv](https://arxiv.org/html/2611.03983).
  3. A GBM ranker trained on synthetic patient types with guideline-derived labels. No verified paper uses this approach. The nearest are Mo 2026 (LightGBM for BMI classification) and Yang 2026 (survival-based choice of PA pattern) — [PubMed 41826482](https://pubmed.ncbi.nlm.nih.gov/41826482/); [DOI](https://doi.org/10.2196/78492).
  4. Physician approval per patient before release. Comparators are clinician-facing tools (P3-EX, EXPERT, FITTER) or used physicians only for one-off validation (Ferretto) — [PubMed 40677518](https://pubmed.ncbi.nlm.nih.gov/40677518/); [DOI](https://doi.org/10.1109/ACCESS.2020.2983564).
  5. A Saturday–Friday calendar with no strength work on consecutive days, against FITTER's two-week progression blocks and the fixed weekly session counts in re.flex and StandingTall — [arXiv](https://arxiv.org/html/2611.03983); [PubMed 39250181](https://pubmed.ncbi.nlm.nih.gov/39250181/); [PubMed 33824131](https://pubmed.ncbi.nlm.nih.gov/33824131/).
  6. Meal plan, exercise prescription, daily checklist and streak in one patient view. Combined systems found do not include a prescription-grade exercise component — [PubMed 42342244](https://pubmed.ncbi.nlm.nih.gov/42342244/); [PubMed 33704075](https://pubmed.ncbi.nlm.nih.gov/33704075/).
  7. Pregnancy and anaemia coverage plus a South Asian setting. Only PROTEIN covers anaemia as a population group, and only a Pakistani protocol is in the region — [PubMed 38773712](https://pubmed.ncbi.nlm.nih.gov/38773712/); [PubMed 34783675](https://pubmed.ncbi.nlm.nih.gov/34783675/).
- **What a reviewer would criticise:**
  - **No clinician or patient evaluation.** Even the development-stage comparators report physician approval rates (~75%), clinician safety ratings (80.6%) or practitioner usability (n=309) — [DOI](https://doi.org/10.1109/ACCESS.2020.2983564); [arXiv](https://arxiv.org/html/2611.03983); [PubMed 40677518](https://pubmed.ncbi.nlm.nih.gov/40677518/)
  - **Rule compliance is not safety.** FITTER's model-assessed compliance was 98.5% while clinicians rated only 80.6% of reviewed prescriptions safe — [arXiv](https://arxiv.org/html/2611.03983)
  - **Pre-participation screening.** LLM advice failed most often on medical clearance, and P3-EX builds ACSM clearance in. A reviewer will ask whether this system screens before prescribing (for example PAR-Q+ or the ACSM algorithm) or relies on the physician — [PubMed 38206661](https://pubmed.ncbi.nlm.nih.gov/38206661/); [PMC P3-EX](https://pmc.ncbi.nlm.nih.gov/articles/PMC12268123/)
  - **Adherence claims.** Effects of gamification and reminders are small and fade, and the streak evidence is mostly observational or experimental outside health. Streaks can also push people to exercise through injury — [PubMed 34982715](https://pubmed.ncbi.nlm.nih.gov/34982715/); [PubMed 39764571](https://pubmed.ncbi.nlm.nih.gov/39764571/); [PubMed 39439910](https://pubmed.ncbi.nlm.nih.gov/39439910/)

### Inferences
- The ranker's held-out agreement with the hand-written labelling function measures how faithfully it reproduces that function, not prescription quality. The paper should state this plainly, because FITTER's 98.5% versus 80.6% gap is exactly the kind of evidence a reviewer will cite.
- The strongest defensible framing: "a safety-first architecture in which a cited, per-exercise rule gate bounds a learned re-ranker, under physician approval", positioned against FITTER's post-hoc audit, EXPERT and P3-EX's condition-level rules, and PROTEIN's combined knowledge base. Physician approval is a workflow gate, not a validation of the engine.
- Planned evaluation that would answer the main criticisms:
  - physician rating of a sample of synthetic-patient prescriptions on Zaleski's 10 categories or FITTER's 5 dimensions, with two raters per item and an agreement statistic;
  - a check that no "avoid" exercise ever passes the gate (a deterministic test);
  - a usability or feasibility pilot measuring checklist completion, the outcome re.flex and StandingTall report.

### Gaps
- This was not a systematic search (PubMed, Crossref, arXiv and general web search, about 2 days of effort). A systematic search of IEEE Xplore, ACM DL and Scopus might surface more exercise recommenders, especially conference papers.
- Full texts were not read for Ferretto 2020, HeLiS/AIIM 2020, HeNuALs, the EXPERT papers or Sun 2021; details beyond their abstracts are unverified.
- FITTER is a v1 preprint posted two weeks before this search, so its numbers may change in revision.
