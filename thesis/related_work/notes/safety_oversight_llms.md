# Safety architecture, human oversight and LLM risks in diet and lifestyle clinical decision support: related-work notes

How these notes were verified: on 2026-11-15 every paper below was checked against at least one primary metadata source: its PubMed record (NCBI E-utilities), its Crossref DOI record, its Europe PMC record, its Semantic Scholar record or the arXiv API. I read the abstract of every paper. I read the full text only for Hoang 2023 and Chen 2024 (open access via Europe PMC). For the rest, the key numbers come from the abstracts, and a number that is not in an abstract is listed as a gap. The regulatory texts were read on the official pages: the EUR-Lex HTML of Regulation (EU) 2024/1689, Regulation (EU) 2026/1744 and Regulation (EU) 2017/745; the FDA guidance PDF; and the WHO publication and news pages. Preprints are labelled "preprint".

Reminder for the report writer: the system's own evaluation uses synthetic patients and synthetic labels. The numbers from the LLM studies below come from different tasks and data, so they must not be compared head-to-head with the system's numbers. They support the design rationale only.

---

## Q0. Ranked list of verified papers by closeness to the system, with the five closest in depth

### Takeaway
No published system combines all four elements of this design: a deterministic guideline rule engine, a rule-based contraindication gate placed before ML ranking, mandatory physician approval with an audit log, and an LLM used only for phrasing. The closest analogues each match one or two elements. MAI-DIET (2026) has rules computing the meal plan, an LLM as a supervised helper and clinician supervision. PROTEIN AI Advisor (2022) has an expert-rule layer gating an optimisation layer. Ponzo 2024 and Papastratis 2024 benchmark LLM diet advice against guidelines or a knowledge-based recommender. Zaretsky 2024 and Chen 2024 study LLM-generated patient-facing text under physician review.

### Cited Findings

#### Deep dives: the five closest

**#1 (closest). MAI-DIET: clinician-supervised, rule-computed meal plans with an LLM as a supervised helper.**
Divanis K, Foscolou A, Prosalentis G, Mylonas C, Antoniou MI, Krokou A, et al. "Clinician-Artificial Intelligence Collaboration for Mediterranean Meal-Plan Generation: Development, Technical Feasibility, and Professional Acceptability of the MAI-DIET Framework." *Nutrients*. 2026;18(16). doi:10.3390/nu18162661. PMID 42654242. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/); [DOI](https://doi.org/10.3390/nu18162661)
- Type: peer-reviewed development and feasibility study (MDPI *Nutrients*). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- What it did: built a "clinician-supervised, data-driven, AI-assisted programmatic framework" that generates Greek-Mediterranean recipe-based meal plans for apparently healthy community-dwelling adults. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- Method: standardised food-composition and recipe libraries feed "a rule-based module that performs meal-plan generation and nutrient calculations". Claude Opus 4.7 "supported predefined operator-supervised transformation tasks, and provided the interface for launching the rule-based module". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- Data and evaluation: six 28-day plans for hypothetical adults at 1600-2600 kcal/day, scored with MedDietScore, the dietary phytochemical index and GR-UPFAST. Acceptability was rated by 103 healthcare professionals on a five-point Likert questionnaire. The plans "were not tested in the intended population", so no real patients took part; clinicians rated acceptability only. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- Key numbers: all plans met the energy criteria. Sodium deviated by up to +36.3% in the higher-energy plans. Calcium was 17.5% below the EFSA population reference intake in the 1600 kcal plan. MedDietScore was 35-36/55. Acceptability was 3.84 ± 0.59, with Cronbach's alpha 0.838-0.952. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- Similarities: numbers come from deterministic rules rather than the LLM (Guarantee 1); the same LLM family (Claude) is confined to supervised supporting tasks; clinicians stay in the loop; plans are recipe-based and multi-week.
- Differences: healthy adults rather than chronic disease, so no contraindication gate is described; no ML ranking; the abstract describes no per-patient physician approval and no audit log; Greek cuisine rather than Bangladeshi; the LLM also acts as the user interface, which goes further than phrasing alone.

**#2. PROTEIN AI Advisor: an expert-rule layer that gates an optimisation layer.**
Stefanidis K, Tsatsou D, Konstantinidis D, Gymnopoulos L, Daras P, Wilson-Barnes S, et al. (23 authors). "PROTEIN AI Advisor: A Knowledge-Based Recommendation Framework Using Expert-Validated Meals for Healthy Diets." *Nutrients*. 2022;14(20):4435. doi:10.3390/nu14204435. PMID 36297118; PMCID PMC9612332. — [Europe PMC/PubMed](https://pubmed.ncbi.nlm.nih.gov/36297118/); [DOI](https://doi.org/10.3390/nu14204435)
- Type: peer-reviewed system paper (EU-funded PROTEIN project consortium; MDPI *Nutrients*). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- What it did and method: a knowledge-based recommender built on "an explicit dataset of expert-validated meals" covering ten user groups of healthy people and people with health conditions. It has two layers: "(a) a qualitative layer for verifying ingredient appropriateness", implemented as "an expert system for fuzzy inference relying on an ontology of rules acquired by experts in Nutrition", and "(b) a quantitative layer for synthesizing meal plans", an optimisation method that works to target nutrient values and ranges. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- Data and evaluation: synthetic only, with 3000 virtual user profiles and their weekly meal plans. No real patients or clinicians took part in the evaluation. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- Key numbers: "high precision and recall for recommending appropriate ingredients in most user categories", and the meal-plan generator "achieved a total recommendation accuracy of 92% for all nutrient recommendations". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- Similarities: this is the closest published architecture to Guarantee 2. Expert rules decide which items are appropriate before a quantitative layer composes or ranks them, the plans are weekly, and the meals are expert-validated.
- Differences: the rule layer uses fuzzy inference rather than hard exclusion; the second layer is an optimiser rather than trained rankers; there is no physician approval step, audit log or LLM; the setting is European with a different set of conditions; the evaluation is synthetic, as in the present system.
- Note: three of its authors (Konstantinidis, Daras, Dimitropoulos) also wrote Papastratis 2024 (#6), which used "a state-of-the-art knowledge-based recommendation system" as its reference. That this reference is PROTEIN AI Advisor is my inference and is not verified.

**#3. Ponzo 2024: ChatGPT dietary advice for NCDs breaks down with overlapping conditions.**
Ponzo V, Goitre I, Favaro E, Merlo FD, Mancino MV, Riso S, et al. "Is ChatGPT an Effective Tool for Providing Dietary Advice?" *Nutrients*. 2024;16(4):469. doi:10.3390/nu16040469. PMID 38398794. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38398794/); [DOI](https://doi.org/10.3390/nu16040469)
- Type: peer-reviewed empirical evaluation. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38398794/)
- What it did and method: in November 2023 the authors compared ChatGPT (GPT-3.5) dietary advice for several non-communicable diseases (NCDs) with guidelines, then tested "a complex case with several diseases". A panel of nutrition experts rated the responses. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38398794/)
- Evaluation: an expert panel and no real patients. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38398794/)
- Key numbers: appropriateness ranged from 55.5% (sarcopenia) to 73.3% (NAFLD). Two recommendations (one for obesity, one for NAFLD) contradicted guidelines, and one type 2 diabetes suggestion was "unsupported". Many were "not fully matched". "When the chatbot handled overlapping conditions, limitations emerged, resulting in some contradictory or inappropriate advice", and the authors concluded it "is currently unable to replace a healthcare professional's consultation". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38398794/)
- Similarities: the conditions overlap with the system's (diabetes, obesity), and the paper documents the failure mode the deterministic multi-condition engine is designed to avoid, namely advice for overlapping conditions.
- Differences: it evaluates a general chatbot rather than a system; it uses one older model version; it is not a Bangladeshi context.

**#4. Zaretsky 2024: an LLM rewrites physician-written summaries into patient-friendly language.**
Zaretsky J, Kim JM, Baskharoun S, Zhao Y, Austrian J, Aphinyanaphongs Y, et al. "Generative Artificial Intelligence to Transform Inpatient Discharge Summaries to Patient-Friendly Language and Format." *JAMA Network Open*. 2024;7(3):e240357. doi:10.1001/jamanetworkopen.2024.0357. PMID 38466307. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38466307/); [DOI](https://doi.org/10.1001/jamanetworkopen.2024.0357)
- Type: peer-reviewed cross-sectional study. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- What it did and method: used an LLM on a "secure Health Insurance Portability and Accountability Act-compliant platform, Microsoft Azure OpenAI" to transform the real discharge summaries of 50 adult General Internal Medicine patients at NYU Langone (June 2023) into a patient-friendly format. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- Evaluation: the input was real patient documents. Readability was measured with Flesch-Kincaid and understandability with PEMAT. Two physicians reviewed each output for accuracy and completeness. No patients rated the outputs. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- Key numbers: grade level fell from 11.0 to 6.2 and PEMAT understandability rose from 13% to 81% (P < .001). Of 100 reviews, 54 gave the best accuracy rating and 56 rated the output entirely complete. "Eighteen reviews noted safety concerns, mostly involving omissions, but also several inaccurate statements (termed hallucinations)." The authors concluded that "initial implementation will require physician review." — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- Similarities: this is exactly the "LLM rephrases clinician-approved content for patients" step of the system, and it argues for physician review of the rephrased text.
- Differences: free-text discharge summaries rather than a structured diet and exercise report; English only; no deterministic template fallback is compared.

**#5. Chen 2024: physicians editing LLM drafts adopt the LLM's assessment (automation bias), and some drafts are dangerous.**
Chen S, Guevara M, Moningi S, Hoebers F, Elhalawani H, Kann BH, Chipidza FE, Leeman J, Aerts HJWL, Miller T, Savova GK, Gallifant J, Celi LA, Mak RH, Lustberg M, Afshar M, Bitterman DS. "The effect of using a large language model to respond to patient messages." *The Lancet Digital Health*. 2024;6(6):e379-e381. doi:10.1016/S2589-7500(24)00060-8. PMID 38664108; PMCID PMC11829255. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38664108/); [DOI](https://doi.org/10.1016/S2589-7500(24)00060-8)
- Type: short (three-page) observational study in *The Lancet Digital Health*. Full text read via Europe PMC. — [Europe PMC full text](https://europepmc.org/article/PMC/PMC11829255)
- Method: a two-stage study at Brigham and Women's Hospital in 2023. GPT-4 generated 100 cancer-patient scenario and question pairs, which an oncologist edited, and GPT-4 drafted replies. Six attending radiation oncologists first wrote manual replies, then edited the GPT-4 drafts until they were "clinically acceptable" (LLM-assisted replies), and completed surveys on quality, safety and helpfulness. The content was then annotated. — [Europe PMC full text](https://europepmc.org/article/PMC/PMC11829255)
- Evaluation: real clinicians and simulated patients, with no real patients. — [Europe PMC full text](https://europepmc.org/article/PMC/PMC11829255)
- Key numbers: assessing physicians judged that LLM drafts "posed a risk of severe harm in 11 (7·1%) of 156 survey responses, and death in one (0·6%)", mostly because acuity was judged or conveyed wrongly. Drafts improved subjective efficiency in 120 of 156 cases (76.9%). Inter-physician agreement on content rose from a mean kappa of 0.10 (manual) to 0.52 (LLM-assisted). LLM-assisted replies were closer in content to the LLM drafts (p = 0.81) than to the manual replies (p < 0.0001). Mean length was 34 words manual, 169 words LLM draft and 160 words LLM-assisted. The authors wrote that this suggests "automation bias and anchoring", and that physicians "might not simply use LLMs to better phrase their own assessment, but instead adopt the assessment by the LLM." — [Europe PMC full text](https://europepmc.org/article/PMC/PMC11829255)
- Similarities: the closest evidence on what physician review of AI output does in practice; it supports both the need for Guarantee 3 and the critique that review alone is not sufficient.
- Differences: here the LLM made the clinical assessment, whereas in this system the LLM only phrases; oncology portal messages, not diet.

#### Ranked list, #6-#25

**#6. Papastratis I, Stergioulas A, Konstantinidis D, Daras P, Dimitropoulos K.** "Can ChatGPT provide appropriate meal plans for NCD patients?" *Nutrition*. 2024;121:112291. doi:10.1016/j.nut.2023.112291. PMID 38359704. A corrigendum appeared in *Nutrition* 2024;128:112532 (doi:10.1016/j.nut.2024.112532). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38359704/); [Corrigendum](https://pubmed.ncbi.nlm.nih.gov/39304456/)
- Type: peer-reviewed evaluation. It assessed meal plans from two LLMs (ChatGPT models) for obesity, cardiovascular disease and type 2 diabetes profiles against "a state-of-the-art knowledge-based recommendation system as a reference", covering energy intake, nutrient accuracy and meal variability. Patient profiles were simulated; the abstract does not mention real patients. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38359704/)
- Key conclusion: "Additional supervision and guidance by nutrition experts or knowledge-based systems are required to ensure meal appropriateness for users with NCDs." — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38359704/)
- Similarities: the only verified head-to-head of an LLM against a knowledge-based diet recommender; it directly motivates Guarantee 1. Differences: the abstract reports no numbers (see Gaps), and there is no oversight workflow.

**#7. Göz B, Dikilitaş Y, Göz F, Sayar A.** "Large Language Model Dietary Recommendations for Multimorbidity with Conflicting Guidelines in Turkish and English." *Nutrients*. 2026;18(21). doi:10.3390/nu18213674. PMID 43030301 (published 5 Nov 2026). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/43030301/)
- Nine LLMs, two of them Turkish-adapted, answered 76 synthetic vignettes in Turkish and English. The vignettes combined type 2 diabetes, CKD, hypertension, obesity, gout and coeliac disease as single conditions, conflicting pairs, concordant pairs and triples. "An LLM judge panel" graded the responses against dietitian-approved key-feature checklists; the dietitian's blinded ratings agreed with the panel on 90% of items for a subset. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/43030301/)
- Numbers: proprietary models covered 81-92% of the weighted checklist and "fully resolved 57% to 89% of the guideline conflicts". Turkish responses covered 2 percentage points less overall, mainly in conflicting-pair vignettes and in open-weight models. "The GPT and Claude models had the fewest safety-critical flags, 5% to 8% in both languages." — [PubMed](https://pubmed.ncbi.nlm.nih.gov/43030301/)
- Similarities: it covers the system's own condition mix (diabetes, CKD, hypertension, obesity) and non-English output. Differences: scoring is mostly by LLM judge; the vignettes are synthetic; the language is Turkish, not Bangla.

**#8. Karakas PE, Calik A, Bilen AB, Kandemir K, Alphan ME.** "Large Language Models as Clinical Nutrition Decision Tools: Quantitative Bias and Guideline Deviation in Type 2 Diabetes Meal Planning." *Healthcare (Basel)*. 2026;14(6). doi:10.3390/healthcare14060739. PMID 41897193. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41897193/)
- Six widely used LLMs produced 3-day, 1800 kcal type 2 diabetes plans (n = 18 days). These were compared with a dietitian-designed reference diet based on ADA, EASD and IDF guidelines, using professional nutrition software, Bland-Altman analysis and ICC; registered dietitians scored guideline adherence (inter-rater ICC = 0.806). Most LLM diets had lower energy, carbohydrate and fibre, with "significant bias and wide limits of agreement", and "only one model" was relatively consistent. The authors conclude the plans "may pose clinical risks if used without professional oversight". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41897193/)
- Similarities: diabetes, and the explicit framing of LLMs as "decision tools", which is what Guarantee 1 rejects. The abstract does not name the six models.

**#9. Wang LC, Zhang H, Ginsberg N, Nandorine Ban A, Kooman JP, Kotanko P.** "Application of ChatGPT to Support Nutritional Recommendations for Dialysis Patients - A Qualitative and Quantitative Evaluation." *Journal of Renal Nutrition*. 2024;34(6):477-481. doi:10.1053/j.jrn.2024.09.001. PMID 39278578. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39278578/)
- GPT-4 received a Monte Carlo-simulated dialysis patient (demographics, food preferences, labs, budget) and generated a one-day menu with five recipes. An experienced renal dietitian rated it, and it was compared with USDA-approved nutrient software. The output was also translated into five languages. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39278578/)
- Numbers: dietitian ratings (median) were 3/5 for recipes, 5/5 for cooking instructions and 2/5 for nutritional analysis. ChatGPT's own analysis underestimated calories by 36%, protein by 28%, fat by 48%, phosphorus by 54%, potassium by 49% and sodium by 53%. Native speakers rated the translations as reliable (4/5). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39278578/)
- Similarities: kidney disease, lab-driven input, multilingual output. This is the strongest single "hallucinated nutrient values" citation for kidney disease.

**#10. Niszczota P, Rybicka I.** "The credibility of dietary advice formulated by ChatGPT: Robo-diets for people with food allergies." *Nutrition*. 2023;112:112076. doi:10.1016/j.nut.2023.112076. PMID 37269717. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37269717/)
- Assessed 56 diets for hypothetical people with food allergies at four prompting levels: baseline, two allergens, and low-calorie. ChatGPT, "although generally accurate, has the potential to produce harmful diets"; "more common errors involve inaccuracies in portions or calories". The paper was followed by a published commentary exchange (Ray 2024; the authors' reply). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37269717/); [Commentary](https://pubmed.ncbi.nlm.nih.gov/38071176/)
- Similarity: allergen and exclusion handling, the analogue of the system's excluded-foods filter and contraindication gate. The abstract gives no count of harmful diets (see Gaps).

**#11. Qarajeh A, Tangpanithandee S, Thongprayoon C, Suppadungsuk S, Krisanapan P, Aiumtrakul N, et al.** "AI-Powered Renal Diet Support: Performance of ChatGPT, Bard AI, and Bing Chat." *Clinics and Practice*. 2023;13(5):1160-1172. doi:10.3390/clinpract13050104. PMID 37887080. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37887080/)
- 240 foods from the Mayo Clinic Renal Diet Handbook (149 potassium items, 91 phosphorus items) were classified by four chatbots. Potassium accuracy: GPT-4 81% (60% of low-potassium foods, 99% of high-potassium foods), GPT-3.5 66%, Bard 79%, Bing 81%. High-phosphorus accuracy: Bard 100%, Bing 89%, GPT-3.5 85%, GPT-4 77%. Consistency across repeated sessions was also measured. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37887080/)
- Similarity: this is the item-level classification a contraindication gate performs deterministically. Even the best potassium classifier missed 40% of low-potassium foods, mislabelling them.

**#12. Garcia P, Ma SP, Shah S, Smith M, Jeong Y, Devon-Sand A, et al.** "Artificial Intelligence-Generated Draft Replies to Patient Inbox Messages." *JAMA Network Open*. 2024;7(3):e243201. doi:10.1001/jamanetworkopen.2024.3201. PMID 38506805. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38506805/)
- A 5-week prospective single-group quality-improvement study (July-August 2023) at Stanford Health Care, with LLM drafts integrated into the EHR. 162 clinicians were analysed, all real clinicians answering real patient messages. Mean draft utilisation was 20%. There was "no change in reply action time, write time, or read time". The task-load score fell from 61.31 to 47.26 (P < .001) and work exhaustion from 1.95 to 1.62 (P < .001). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38506805/)

**#13. Tai-Seale M, Baxter SL, Vaida F, Walker A, Sitapati AM, Osborne C, et al.** "AI-Generated Draft Replies Integrated Into Health Records and Physicians' Electronic Communication." *JAMA Network Open*. 2024;7(4):e246565. doi:10.1001/jamanetworkopen.2024.6565. PMID 38619840. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38619840/)
- A randomised waiting-list QI study: 52 primary care physicians (25 immediate, 27 delayed activation) plus 70 contemporary controls. GenAI drafts were associated with "a 21.8% increase in read time (95% CI, 5.2% to 41.0%)", a non-significant -5.9% change in reply time, and a 17.9% increase in reply length. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38619840/)
- Relevance: reviewing AI output can add reading time. This is the workload critique of Guarantee 3.

**#14. Yera Toledo R, Alzahrani AA, Martínez L.** "A Food Recommender System Considering Nutritional Information and User Preferences." *IEEE Access*. 2019;7:96695-96711. doi:10.1109/ACCESS.2019.2929413. — [Crossref DOI](https://doi.org/10.1109/ACCESS.2019.2929413)
- A daily meal-plan recommender that "incorporates a pre-filtering stage that uses AHPSort as multi-criteria decision analysis tool for filtering out foods which are not appropriate to the current user characteristics", followed by "an optimization-based stage". It was evaluated with a case study only. — [Semantic Scholar record](https://www.semanticscholar.org/search?q=A%20Food%20Recommender%20System%20Considering%20Nutritional%20Information%20and%20User%20Preferences); abstract verified via [DOI](https://doi.org/10.1109/ACCESS.2019.2929413)
- Similarity: a filter-then-optimise pipeline, structurally like Guarantee 2. Difference: the filter is multi-criteria sorting rather than hard clinical contraindication rules.

**#15. Chen Y, Subburathinam A, Chen C-H, Zaki MJ.** "Personalized Food Recommendation as Constrained Question Answering over a Large-scale Food Knowledge Graph." *Proceedings of the 14th ACM International Conference on Web Search and Data Mining (WSDM '21)*. 2021:544-552. doi:10.1145/3437963.3441816; arXiv:2101.01775. — [DOI](https://doi.org/10.1145/3437963.3441816); [arXiv](https://arxiv.org/abs/2101.01775)
- Models food recommendation as knowledge-graph question answering in which "personalized requirements from the user's dietary preferences and health guidelines are handled in a unified way as additional constraints", with techniques "for handling negations and numerical comparisons". It reports an "average 59.7% absolute improvement" over non-personalised baselines on a benchmark built from a food knowledge graph and health guidelines. Evaluation was offline, with no clinicians or patients. — [arXiv](https://arxiv.org/abs/2101.01775)
- Similarity: guideline constraints, including allergies, applied to a learned recommender. Difference: the constraints sit inside the QA model rather than in a separate auditable gate.

**#16. Spoladore D, Tosi M, Lorenzini EC.** "Ontology-based decision support systems for diabetes nutrition therapy: A systematic literature review." *Artificial Intelligence in Medicine*. 2024;151:102859. doi:10.1016/j.artmed.2024.102859. PMID 38564880. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38564880/)
- A systematic review of the domain ontologies used in diabetes nutrition recommender and decision support systems. These "deliver a computable representation of experts' knowledge". The review examines "the role of clinical experts in developing domain ontologies" and calls for "a preeminent role for clinical experts and clinical guidelines" and better interoperability. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38564880/)
- Similarity: it situates the guideline-cited rule engine in the knowledge-based nutrition CDSS tradition. The abstract gives no counts (see Gaps).

**#17. (Preprint) Wu J, Yan R, Luo H, Liu D, Wang M, Townsend KL, et al.** "NutriOrion: A Hierarchical Multi-Agent Framework for Personalized Nutrition Intervention Grounded in Clinical Guidelines." arXiv:2602.18650, 20 Feb 2026. Not peer reviewed. — [arXiv](https://arxiv.org/abs/2602.18650)
- A multi-agent LLM planner for multimorbidity with "a safety constraint mechanism that injects pharmacological contraindications as hard negative constraints during synthesis, ensuring clinical validity by construction rather than post-hoc filtering". Outputs map to ADIME and FHIR R4. It was evaluated on 330 stroke patients with multimorbidity and achieved "a 12.1 percent drug-food interaction violation rate". — [arXiv](https://arxiv.org/abs/2602.18650)
- Similarity: it shares the idea that contraindications must be hard constraints. Difference: the constraints are injected into LLM generation, and a 12.1% violation rate remained. A deterministic pre-ranking gate is designed so that this rate is zero by construction, and the system's gate test checks this.

**#18. Hager P, Jungmann F, Holland R, Bhagat K, Hubrecht I, Knauer M, et al.** "Evaluation and mitigation of the limitations of large language models in clinical decision-making." *Nature Medicine*. 2024;30(9):2613-2622. doi:10.1038/s41591-024-03097-1. PMID 38965432. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38965432/)
- Built a MIMIC-based dataset of 2,400 real patient cases across four abdominal pathologies and a simulated clinical workflow. State-of-the-art LLMs "do not accurately diagnose patients across all pathologies (performing significantly worse than physicians), follow neither diagnostic nor treatment guidelines, and cannot interpret laboratory results", and were "sensitive to both the quantity and order of information". The authors conclude that LLMs "are currently not ready for autonomous clinical decision-making". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38965432/)
- Relevance: the strongest general, high-impact citation for Guarantee 1, since the system's clinical logic depends on lab values and guideline adherence. It is not a diet study.

**#19. Hoang YN, Chen YL, Ho DKN, Chiu WC, Cheah KJ, Mayasari NR, Chang JS.** "Consistency and Accuracy of Artificial Intelligence for Providing Nutritional Information." *JAMA Network Open*. 2023;6(12):e2350367. doi:10.1001/jamanetworkopen.2023.50367. PMID 38150258. Research letter; full text read. — [Europe PMC full text](https://europepmc.org/article/PMC/PMC10753390)
- ChatGPT-3.5 and ChatGPT-4 gave energy and macronutrients for 222 food items (8 menus), five repeats each, in English and Traditional Chinese, compared with the Taiwan FDA food composition database. "Both chatbots provided accurate energy contents for approximately 35% to 48% of the 222 food items within ±10%". In the table, energy within ±10% was 39.2-46.8%, and fat within ±10% was 35.5-48.3%. GPT-4 overestimated protein, and coefficients of variation differed by input language for carbohydrate. — [Europe PMC full text](https://europepmc.org/article/PMC/PMC10753390)

**#20. Kim DW, Park JS, Sharma K, Velazquez A, Li L, Ostrominski JW, et al.** "Qualitative evaluation of artificial intelligence-generated weight management diet plans." *Frontiers in Nutrition*. 2024;11:1374834. doi:10.3389/fnut.2024.1374834. PMID 38577160. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38577160/)
- Obesity-medicine and nutrition experts (67 of 95 completed) blindly rated ChatGPT-4 weight-loss plans against two plans from tertiary centres and found "no significant differences". Of 14 experts who thought they could spot the AI plan, only 5 did. Limitations they named included "conflicting dietary considerations, lack of affordability, and insufficient specificity... such as exact portion sizes". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38577160/)
- Relevance: this is the counter-evidence a reviewer may raise, that LLM plans can look indistinguishable from clinical ones. Indistinguishability is also why plausible errors may pass review unnoticed.

**#21. You Q, Zhou L, Ma Y, Guo J, Wang Y, Shi L, et al.** "Comparison of ChatGPT-3.5, ChatGPT-4.0 and DeepSeek in generating dietary plans for patients with chronic kidney disease: A focus on nutritional accuracy and dietary inflammation." *Nutrition*. 2026;142:112957. doi:10.1016/j.nut.2025.112957. PMID 41135437. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41135437/)
- Standardised prompts set an 1800 kcal target at five protein levels (30-70 g) for CKD stages; 20 participants entered them, giving 300 plans. "All three LLMs failed to meet the 1800 kcal energy target, with values ranging from 1165 to 1548 kcal (P < 0.001)". DeepSeek's plans were pro-inflammatory (DII 2.25). The authors conclude "human oversight remains crucial". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41135437/)

**#22. Dratsch T, Chen X, Rezazade Mehrizi M, Kloeckner R, Mähringer-Kunz A, Püsken M, et al.** "Automation Bias in Mammography: The Impact of Artificial Intelligence BI-RADS Suggestions on Reader Performance." *Radiology*. 2023;307(4):e222176. doi:10.1148/radiol.222176. PMID 37129490. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37129490/)
- 27 radiologists read 50 mammograms; a purported AI suggested an incorrect category for 12 of 40 test cases. With correct versus incorrect AI suggestions, accuracy was 79.7% vs 19.8% for inexperienced readers, 81.3% vs 24.8% for moderately experienced readers and 82.3% vs 45.5% for very experienced readers. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37129490/)
- Relevance: even expert reviewers follow wrong automated suggestions, which is the rubber-stamping risk for Guarantee 3.

**#23. Rajashekar NC, Shin YE, Pu Y, Chung S, You K, Giuffre M, et al.** "Human-Algorithmic Interaction Using a Large Language Model-Augmented Artificial Intelligence Clinical Decision Support System." *Proceedings of the CHI Conference on Human Factors in Computing Systems (CHI '24)*. 2024:1-20. doi:10.1145/3613904.3642024. — [DOI](https://doi.org/10.1145/3613904.3642024)
- A randomised controlled trial of an AI-CDSS for upper GI bleeding with and without an LLM interface, run in realistic clinical simulations with physicians and medical students. The authors found "evidence that LLM augmentation improves ease-of-use, that LLM-generated responses with citations improve trust", and that "HCI varies based on clinical expertise". — [Semantic Scholar abstract via API, DOI 10.1145/3613904.3642024](https://doi.org/10.1145/3613904.3642024)
- Similarity: the LLM is a layer over an existing decision algorithm rather than the decision-maker, which is the nearest design to "LLM only explains". Difference: the LLM converses with clinicians, not patients.

**#24. Kabir M, Islam MS, Laskar MTR, Nayeem MT, Bari MS, Hoque E.** "BenLLM-Eval: A Comprehensive Evaluation into the Potentials and Pitfalls of Large Language Models on Bengali NLP." *Proceedings of LREC-COLING 2024*. 2024:2238-2252. Crossref DOI 10.63317/5i2sb9uio9fs (resolves to https://lrec.elra.info/lrec2024-main-0201); preprint arXiv:2309.13173. — [Proceedings page](https://lrec.elra.info/lrec2024-main-0201); [arXiv](https://arxiv.org/abs/2309.13173)
- Zero-shot evaluation of GPT-3.5, LLaMA-2-13b-chat and Claude-2 on Bengali summarisation, QA, paraphrasing, NLI, transliteration, classification and sentiment. On some tasks the models were on par with or better than fine-tuned SOTA, but "in most tasks, their performance is quite poor", and open-source LLaMA-2 was "significantly bad". — [arXiv](https://arxiv.org/abs/2309.13173)
- Relevance: the only verified peer-reviewed general Bengali LLM benchmark that includes a Claude model. It tested older models, and none of the tasks is health communication.

**#25. Brewster RCL, Gonzalez P, Khazanchi R, Butler A, Selcer R, Chu D, et al.** "Performance of ChatGPT and Google Translate for Pediatric Discharge Instruction Translation." *Pediatrics*. 2024;154(1):e2023065573. doi:10.1542/peds.2023-065573. PMID 38860299. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38860299/)
- 20 standardised discharge instructions were translated into Spanish, Brazilian Portuguese and Haitian Creole by professionals, Google Translate and ChatGPT-4.0, then rated for adequacy, fluency, meaning and clinical-harm severity. Machine output was comparable to professional translation for Spanish and Portuguese. For the low-resource Haitian Creole, potentially clinically significant errors occurred in 33.3% of ChatGPT translations, 23.3% of Google translations and 8.3% of professional ones. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38860299/)
- Relevance: patient-facing clinical text in a low-resource language carries a higher clinical-error risk. This is directly relevant to Bangla phrasing.

#### Authoritative documents (detail in Q5)
- WHO (2021) *Ethics and governance of artificial intelligence for health: WHO guidance*, ISBN 9789240029200. — [WHO](https://www.who.int/publications/i/item/9789240029200)
- WHO (2024) *Ethics and governance of artificial intelligence for health: Guidance on large multi-modal models*, ISBN 978-92-4-008475-9. — [WHO](https://www.who.int/publications/i/item/9789240084759)
- US FDA, *Clinical Decision Support Software: Guidance for Industry and FDA Staff* (2022 guidance, revised January 2026; current version issued 29 January 2026). — [FDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)
- Regulation (EU) 2024/1689 (AI Act) as amended by Regulation (EU) 2026/1744 (Digital Omnibus on AI), read with Regulation (EU) 2017/745 (MDR). — [EUR-Lex AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng); [EUR-Lex Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng)

### Inferences
- Ranking logic: #1-#2 share architecture (rules compute or gate, then a secondary step); #3, #6-#11 supply the empirical case against LLM clinical logic in the system's own conditions; #4-#5, #12-#13 and #22 cover physician review of AI output; #14-#17 are gate-like hybrids; #24-#25 cover the language risk.
- The literature splits into two camps with little overlap. Recommender-systems work (#2, #14, #15, #17) does constrain ML with rules but rarely includes clinician approval. Clinical informatics work (#4, #5, #12, #13) studies clinician review of LLM drafts but not rule-gated diet engines. The system's novelty claim can rest on combining the two, but it should be stated cautiously ("we found no system that...") with the search scope given.

### Gaps
- Papastratis 2024 (#6): the abstract has no numbers, and the full text is paywalled and was not read. Its quantitative results (energy and nutrient error versus the knowledge-based reference) are unverified.
- Niszczota 2023 (#10): the number or share of harmful diets is not in the abstract; the full text was not read.
- Spoladore 2024 (#16): the number of included studies is not in the abstract.
- Karakas 2026 (#8): the six LLMs are not named in the abstract.
- The Yera Toledo 2019 abstract was obtained from the Semantic Scholar API, not from the IEEE page (which was not opened).

---

## Q1. Which systems put a clinician in the loop to approve, edit or reject AI-generated diet, lifestyle or patient-facing output, and what did they find about workload, trust and errors caught?

### Takeaway
No verified study evaluates a physician approve/edit/reject gate on AI-generated diet plans with real patients. The best evidence comes from clinicians reviewing LLM drafts of patient messages and patient-friendly documents. There, review reduces perceived burden but not time (Garcia 2024), can increase reading time (Tai-Seale 2024), and catches some errors. Reviewers also anchor on the AI's content (Chen 2024), and automation bias affects experts too (Dratsch 2023; Goddard 2012).

### Cited Findings
- Stanford EHR-integrated LLM drafts (162 clinicians, 5 weeks): 20% utilisation, no change in read, write or reply time, lower task load (61.31 to 47.26) and lower exhaustion (1.95 to 1.62). — [Garcia 2024, JAMA Netw Open](https://pubmed.ncbi.nlm.nih.gov/38506805/)
- In a randomised waiting-list study of 52 PCPs, drafts were associated with +21.8% read time, a non-significant -5.9% reply time and +17.9% reply length. — [Tai-Seale 2024, JAMA Netw Open](https://pubmed.ncbi.nlm.nih.gov/38619840/)
- With six radiation oncologists editing GPT-4 drafts, unedited drafts carried a risk of severe harm in 7.1% and of death in 0.6% of 156 survey responses. Edited replies stayed close to the drafts' content (p = 0.81 versus drafts, p < 0.0001 versus manual), and the authors flag "automation bias and anchoring". — [Chen 2024, Lancet Digit Health](https://europepmc.org/article/PMC/PMC11829255)
- When two physicians reviewed LLM patient-friendly discharge summaries, 18 of 100 reviews noted safety concerns, mostly omissions plus some hallucinations; the authors say "initial implementation will require physician review." — [Zaretsky 2024, JAMA Netw Open](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- In GPT-4 patient-facing instructions for incidental radiology findings (430 test reports), no findings were hallucinated outright, but "2.8% of cases included generated text about recommendations that were inferred without specific reference". The authors say "active clinician oversight via 'human-in-the-loop' workflows remains critical". — [Woo KC, et al. JAMIA 2024;31(9):1983-1993, doi:10.1093/jamia/ocae117](https://pubmed.ncbi.nlm.nih.gov/38778578/)
- For Chinese surgical consent forms from nine hospitals, the LLM-simplified version improved readability but "reduced content quality, particularly risk information"; "clinician revision restored accuracy while maintaining clarity and achieved the highest comprehension scores." — [Luo J, et al. npj Digit Med 2026;9(1), doi:10.1038/s41746-026-02591-9](https://pubmed.ncbi.nlm.nih.gov/41922537/)
- A diet-specific clinician-supervised framework (MAI-DIET) had a rule-based module compute plans and Claude Opus 4.7 do operator-supervised tasks; 103 HCPs rated acceptability at 3.84 ± 0.59. No patient outcomes were measured. — [Divanis 2026, Nutrients](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- Real patients with human feedback after the fact: 20 of 88 peritoneal-dialysis patients shared ChatGPT query screenshots with nurses and received feedback, and sharing was associated with lower serum phosphorus (mean difference 0.687 mg/dL at T2; p = 0.006). The study is observational and the nurse review came after the patient had seen the AI output. — [Wang HC, et al. Ther Apher Dial 2026, doi:10.1002/1744-9987.70234](https://pubmed.ncbi.nlm.nih.gov/42963867/)
- On 2000 real Medicaid patient messages (three-physician blinded adjudication), "no configuration met the autonomous benchmark". The two configurations that met the sensitivity target relied on clinician review of flagged messages; the best, a disagreement-stratified clinician-review workflow, reached sensitivity 0.939 with 878 alerts per 1,000 messages. — [Basu S, et al. BMC Med Inform Decis Mak 2026;26(1), doi:10.1186/s12911-026-03763-z](https://pubmed.ncbi.nlm.nih.gov/43026589/)
- Automation bias evidence:
  - Accuracy fell to 19.8-45.5% when the AI suggestion was wrong, against 79.7-82.3% when it was right, across experience levels. — [Dratsch 2023, Radiology](https://pubmed.ncbi.nlm.nih.gov/37129490/)
  - A systematic review of 74 studies found that automation bias is mediated by trust, workload, task complexity and time pressure. Mitigators include "emphasizing user accountability" and "the provision of information versus recommendation". — [Goddard K, Roudsari A, Wyatt JC. JAMIA 2012;19(1):121-127, doi:10.1136/amiajnl-2011-000089](https://pubmed.ncbi.nlm.nih.gov/21685142/)
  - Automation bias appears even in single tasks with "high verification complexity", and "strategies to minimize AB might focus on cognitive load reduction". — [Lyell D, Coiera E. JAMIA 2017;24(2):423-431, doi:10.1093/jamia/ocw105](https://pubmed.ncbi.nlm.nih.gov/27516495/)
  - JAMA Viewpoint "Automation Bias and Assistive AI: Risk of Harm From AI-Driven Clinical Decision Support" (Khera R, Simon MA, Ross JS. JAMA 2023;330(23):2255-2257, doi:10.1001/jama.2023.22557). The page is paywalled; only the title and opening were verified. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38112824/)
- Alert fatigue (the workload analogue): reminder acceptance "dropped by 30% for each additional reminder received per encounter" and by 10% for each 5-point rise in repeated reminders (112 primary care clinicians). — [Ancker JS, et al. BMC Med Inform Decis Mak 2017;17(1):36, doi:10.1186/s12911-017-0430-8](https://pubmed.ncbi.nlm.nih.gov/28395667/)

### Inferences
- In the system, the physician reviews deterministic, guideline-traceable output rather than an LLM's clinical judgement. This is the "information versus recommendation" and "verification complexity" lever that Goddard 2012 and Lyell & Coiera 2017 identify. Showing the cited threshold and rule behind each exclusion should make verification easier than reviewing free-text LLM drafts. This is an argument, not a measured result.
- The anchoring finding in Chen 2024 implies that an approval rate near 100% would not by itself show that review is meaningful. Edit and reject rates, time per review and seeded-error detection would be the evidence.
- The evidence that review catches errors comes from document-rewriting tasks (Zaretsky 2024, Luo 2026). The evidence that review misses errors comes from decision tasks (Chen 2024, Dratsch 2023).

### Gaps
- I found no study of physician approve/edit/reject of AI-generated diet or exercise plans with real patients, and no study reporting physician edit or reject rates for diet plans.
- No study measured how long physicians take to review a weekly meal plan.
- Bangladesh-specific evidence on physician workload with digital CDS was not found in this scope; it belongs to the Bangladesh-context notes.

---

## Q2. Which guideline-based or rule-based CDSS exist for nutrition or lifestyle in chronic disease, and which hybrid designs let rules gate or constrain ML output?

### Takeaway
Knowledge-based nutrition recommenders are well established. They include ontology or expert-rule systems for diabetes nutrition (Spoladore 2024 review) and two-layer designs in which an expert-rule layer screens items before an optimiser builds plans (PROTEIN AI Advisor 2022; Yera Toledo 2019). Hybrid ML or LLM designs constrain learned output with guideline rules (Chen 2021; NutriOrion preprint 2026). None of them pairs the gate with physician approval and an audit log. Systematic reviews also find that most health recommenders are evaluated offline and rarely reach practice.

### Cited Findings
- PROTEIN AI Advisor: a qualitative layer (fuzzy expert system over an ontology of nutrition-expert rules) verifies ingredient appropriateness before a quantitative optimisation layer synthesises plans; 92% total recommendation accuracy on 3000 synthetic users. — [Stefanidis 2022, Nutrients](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- An AHPSort pre-filtering stage removes "foods which are not appropriate to the current user characteristics" before optimisation. — [Yera Toledo 2019, IEEE Access](https://doi.org/10.1109/ACCESS.2019.2929413)
- Health guidelines and preferences act as constraints, including negations, in KBQA food recommendation; 59.7% average absolute improvement over non-personalised baselines. — [Chen 2021, WSDM](https://arxiv.org/abs/2101.01775)
- (Preprint) Contraindications are injected "as hard negative constraints during synthesis... rather than post-hoc filtering"; 12.1% drug-food interaction violation rate remained. — [NutriOrion, arXiv 2026](https://arxiv.org/abs/2602.18650)
- MAI-DIET: a rule-based module performs plan generation and nutrient calculation, with the LLM supervised. — [Divanis 2026](https://pubmed.ncbi.nlm.nih.gov/42654242/)
- An ontology-based diabetes nutrition DSS review emphasises clinical experts and guidelines as the knowledge source and interoperability as a barrier. — [Spoladore 2024, AIIM](https://pubmed.ncbi.nlm.nih.gov/38564880/)
- An LLM-centred alternative, for contrast: ChatDiet uses an LLM orchestrator over a causal personal model and a population nutrition model and reports "a 92% effectiveness rate" in a case-study food recommendation test. — [Yang Z, et al. Smart Health 2024;32:100465, doi:10.1016/j.smhl.2024.100465](https://doi.org/10.1016/j.smhl.2024.100465)
- Health recommender systems (HRS) reviews:
  - Of 73 HRS studies for laypersons, nutrition was a major category, most used hybrid algorithms, and "half of the studies only evaluated the algorithm". — [De Croon R, et al. J Med Internet Res 2021;23(6):e18035, doi:10.2196/18035](https://pubmed.ncbi.nlm.nih.gov/34185014/)
  - Of 51 HRS, 62.7% used offline evaluation only and 33.3% included end users. — [Sun Y, et al. J Med Internet Res 2023;25:e38184, doi:10.2196/38184](https://pubmed.ncbi.nlm.nih.gov/36656630/)
  - Across 136 HRS articles (2014-2025), "limited clinical adoption is not primarily driven by algorithmic immaturity but by persistent misalignment between intended use, evaluation design, and integration pathways". — [El Miayar O, Berrado A. iScience 2026;29(6):116220, doi:10.1016/j.isci.2026.116220](https://pubmed.ncbi.nlm.nih.gov/42317741/)
  - Earlier overviews (metadata verified; abstracts not retrieved): Tran TNT, Atas M, Felfernig A, Stettinger M. "An overview of recommender systems in the healthy food domain." J Intell Inf Syst 2018;50:501-526, doi:10.1007/s10844-017-0469-0 — [DOI](https://doi.org/10.1007/s10844-017-0469-0). Tran TNT, Felfernig A, Trattner C, Holzinger A. "Recommender systems in the healthcare domain: state-of-the-art and research issues." J Intell Inf Syst 2021;57:171-201, doi:10.1007/s10844-020-00633-6 — [DOI](https://doi.org/10.1007/s10844-020-00633-6). Schäfer H, et al. "Towards Health (Aware) Recommender Systems." DH '17:157-161, doi:10.1145/3079452.3079499 — [DOI](https://doi.org/10.1145/3079452.3079499).
- General CDSS: an npj Digital Medicine overview of CDSS types (knowledge-based versus non-knowledge-based), benefits, pitfalls and harms, with recommendations for design, implementation, evaluation and maintenance. — [Sutton RT, et al. npj Digit Med 2020;3:17, doi:10.1038/s41746-020-0221-y](https://pubmed.ncbi.nlm.nih.gov/32047862/)
- An ML-personalised diet with clinical evidence (no rule gate): in an RCT of 225 adults with prediabetes, a machine-learning postprandial-targeting diet reduced "time above 140" by 1.3 h/day versus 0.3 h/day for a Mediterranean diet, and HbA1c by 0.16% versus 0.08%. — [Ben-Yacov O, et al. Diabetes Care 2021;44(9):1980-1991, doi:10.2337/dc21-0162](https://pubmed.ncbi.nlm.nih.gov/34301736/)
- Maintaining rule bases with LLM help: Claude Sonnet 4 supported local ontology updates to a dietary lifestyle ontology, but "global optimization of ontology... required systematic examination by human experts." — [Jung J, Taira R, Kim H. JAMIA 2026;33(5):1037-1042, doi:10.1093/jamia/ocag015](https://pubmed.ncbi.nlm.nih.gov/41719167/)

### Inferences
- The system's gate-then-rank design follows the PROTEIN and Yera Toledo pattern (rule or MCDA filter, then a quantitative stage) but with hard, guideline-cited exclusions. NutriOrion's leftover 12.1% violation rate shows why the exclusion should be deterministic and placed outside the generator.
- NutriOrion explicitly argues against "post-hoc filtering". The system's gate runs before ranking, so the rankers never see excluded items. That is closer to "by construction" than to post-hoc filtering, and the paper should state this clearly to pre-empt that critique.
- The HRS reviews (De Croon, Sun, El Miayar) mean the system's synthetic-only evaluation is typical of the field. They also give a reviewer grounds to ask for a clinical-integration plan.

### Gaps
- I found no verified rule-gated diet CDSS for Bangladesh or South Asia (left to the Bangladesh-context notes) and none covering anaemia, pregnancy and knee osteoarthritis together.
- No paper found reports a formal test (unit or property test) that contraindicated items never appear. Safety is usually evaluated by error rates, not guaranteed by tests.

---

## Q3. What do empirical studies find when LLMs give diet plans or nutrition advice for diabetes, CKD, hypertension, allergies, pregnancy or weight loss?

### Takeaway
Across 2023-2026, LLM diet output is often fluent and broadly guideline-like. It is quantitatively unreliable, though: systematic energy shortfalls of hundreds of kcal, large errors on potassium, phosphorus and sodium, and poor micronutrient agreement. It degrades with comorbidity or conflicting guidelines and varies between runs. Nearly all studies use hypothetical cases. Almost every set of authors concludes that professional supervision or knowledge-based systems are needed.

### Cited Findings
- Scope of the field: a scoping review of 40 studies (2022-2024) found tasks of dietary advice (n = 21), food composition (n = 9), meal plans (n = 7) and data extraction (n = 5); "most studies (n = 38) focused on evaluating the models in hypothetical situations". — [O'Hara C, et al. Am J Clin Nutr 2026;123(2):101127, doi:10.1016/j.ajcnut.2025.101127](https://pubmed.ncbi.nlm.nih.gov/41317995/)

**Diabetes**
- Six LLMs on type 2 diabetes plans showed significant bias and wide limits of agreement versus a dietitian reference, with lower energy, carbohydrate and fibre. — [Karakas 2026](https://pubmed.ncbi.nlm.nih.gov/41897193/)
- 24 virtual type 2 diabetes profiles, prompted in Turkish: energy alignment was 70.9% for ChatGPT-4.1 and 83.1% for Grok-3; "frequent hallucinations and lack of clinical contextualization were noted." — [Bayram HM, Arslan S, Ozturkcan A. J Eval Clin Pract 2025;31(7):e70295, doi:10.1111/jep.70295](https://pubmed.ncbi.nlm.nih.gov/41055593/)
- For type 2 diabetes and metabolic syndrome (63 prompts, two dietitians), 1500 kcal menus were discordant for carbohydrate, fat, vitamin D and calcium, with gaps in physical-activity advice. — [Naja F, et al. Eur J Clin Nutr 2024;78(10):887-896, doi:10.1038/s41430-024-01476-y](https://pubmed.ncbi.nlm.nih.gov/39060542/)
- Across 52 simulated diabetes cases, Gemini 1.5 Flash scored 4.34 and GPT-4 3.79 on AHP (p < 0.001), and Gemini was better in CKD cases. — [Ben Lafqih M, et al. Diabetes Metab Syndr 2025;19(12):103355, doi:10.1016/j.dsx.2025.103355](https://pubmed.ncbi.nlm.nih.gov/41386168/)
- ChatGPT and GPT-4 passed the Chinese Registered Dietitian exam, and dietitians rated 162 of 168 responses favourably. Recommendations deviated for some foods (root vegetables, dry beans), and the program was declared "ready for a supervised pilot study". — [Sun H, et al. J Med Internet Res 2023;25:e51300, doi:10.2196/51300](https://pubmed.ncbi.nlm.nih.gov/37943581/)
- (Preprint) NutriBench has 11,857 meal descriptions; 12 LLMs were tested on carbohydrate estimation, with a nutritionist comparison and a simulated blood-glucose risk assessment. — [Hua A, et al. arXiv:2407.12843](https://arxiv.org/abs/2407.12843)

**Chronic kidney disease**
- GPT-4's dialysis menu underestimated potassium by 49%, phosphorus by 54% and sodium by 53%, and the renal dietitian rated its nutritional analysis 2/5. — [Wang LC 2024](https://pubmed.ncbi.nlm.nih.gov/39278578/)
- In 300 CKD plans, energy was 1165-1548 kcal against an 1800 kcal target. — [You 2026](https://pubmed.ncbi.nlm.nih.gov/41135437/)
- Potassium classification accuracy was 66-81% across chatbots, and GPT-4 identified only 60% of low-potassium foods. — [Qarajeh 2023](https://pubmed.ncbi.nlm.nih.gov/37887080/)
- Stage-specific CKD plans (GPT-4, Gemini, Copilot; three physicians) showed "discrepancies between GPT-4's internal estimations and manual values", with deviations "most notably for sodium and potassium". — [Kairat M, et al. J Clin Med 2025;14(22):8033, doi:10.3390/jcm14228033](https://pubmed.ncbi.nlm.nih.gov/41303069/)
- On KDIGO- and KDOQI-derived lifestyle and nutrition questions reviewed by nephrologists, "some answers remained potentially misleading". — [Acharya PC, et al. Diseases 2024;12(8):185, doi:10.3390/diseases12080185](https://pubmed.ncbi.nlm.nih.gov/39195184/)

**Multimorbidity and conflicting guidelines (diabetes, CKD, hypertension, obesity, gout, coeliac)**
- Conflicts were fully resolved in 57-89% of cases; safety-critical flags were 5-8% for the GPT and Claude models; Turkish output scored 2 percentage points below English. — [Göz 2026](https://pubmed.ncbi.nlm.nih.gov/43030301/)
- Overlapping conditions produced "contradictory or inappropriate advice". — [Ponzo 2024](https://pubmed.ncbi.nlm.nih.gov/38398794/)

**Hypertension (lifestyle education)**
- Diet and exercise brochures for diabetes, hypertension and obesity from five LLMs: Claude Sonnet 4 and Gemini had the highest reliability (modified DISCERN 3.0) at about a 9th-grade reading level; Perplexity had the lowest reliability (1.3). The authors say "human editing... and human supervision will be needed". The venue is Cureus, a lower-rigour journal. — [Aenuginti CS, et al. Cureus 2026;18(3):e106221, doi:10.7759/cureus.106221](https://pubmed.ncbi.nlm.nih.gov/42077671/)

**Food allergy**
- Of 56 robo-diets, some were potentially harmful, and the common errors involved portions and calories. — [Niszczota & Rybicka 2023](https://pubmed.ncbi.nlm.nih.gov/37269717/)

**Pregnancy**
- DeepSeek-R1 and ChatGPT-4.0 pregnancy plans all scored DQI-I ≥ 70. Adequacy was 35.8 vs 33.9 and moderation 22.3 vs 17.0 (ChatGPT higher on moderation). Plans were checked for calories and cost, with no clinician safety review reported in the abstract. — [Gao Z, Li J, Fang W. Front Public Health 2026;14:1728954, doi:10.3389/fpubh.2026.1728954](https://pubmed.ncbi.nlm.nih.gov/41710315/)
- A bilingual GPT-3.5 nutrition chatbot was embedded in an RCT (N = 200) of high-risk pregnant women; engagement was the main problem. Of the low users interviewed (n = 32), 90% preferred Spanish. — [Macias-Navarro L, et al. JMIR Form Res 2026;10:e85292, doi:10.2196/85292](https://pubmed.ncbi.nlm.nih.gov/42066287/)

**Weight loss and general meal plans**
- Experts could not distinguish ChatGPT-4 weight-loss plans from tertiary-centre plans (5 of 14 identified correctly). — [Kim 2024](https://pubmed.ncbi.nlm.nih.gov/38577160/)
- 108 ChatGPT and Bard plans contained less energy and carbohydrate than the DRI; vitamin D and fluoride were below the DRI for all plans; vegan plans lacked B12. — [Hieronimus B, Hammann S, Podszun MC. Nutr Res 2024;128:105-114, doi:10.1016/j.nutres.2024.07.002](https://pubmed.ncbi.nlm.nih.gov/39102765/)
- Five LLMs, including Claude 4.1, produced adolescent diet plans that "systematically undercalculate energy (bias: +695 kcal)" (sign as reported) relative to dietitian plans. "No model showed consistent proximity to the dietitian across all nutrients." — [Bilen AB, Kalkan GE, Önal HY. Front Nutr 2026;13:1765598, doi:10.3389/fnut.2026.1765598](https://pubmed.ncbi.nlm.nih.gov/41909033/)
- Real-case PCOS/PMOS plans from four LLMs, including Claude Sonnet 4.6 (216 menus): no model had consistently low error, Gemini 2.5 Flash had an energy bias of +531.1 kcal and 28 red flags, and reproducibility was generally poor. The findings "do not support their independent or unsupervised use". — [Çalık A, et al. Nutrients 2026;18(19):3205, doi:10.3390/nu18193205](https://pubmed.ncbi.nlm.nih.gov/42884656/)

**Hallucinated or inaccurate nutrient values**
- Only about 35-48% of energy values were within ±10% of a food composition database. — [Hoang 2023](https://europepmc.org/article/PMC/PMC10753390)
- "97% of the artificial intelligence values fall within a 40% difference from United States Department of Agriculture data", a loose tolerance. — [Haman M, Školník M, Lošťák M. Nutrition 2024;119:112325, doi:10.1016/j.nut.2023.112325](https://pubmed.ncbi.nlm.nih.gov/38194819/)
- In 2026 models (ChatGPT 5.2, Claude Opus 4.5, Gemini 3 Pro Preview, Llama 4 Maverick), agreement was "high for energy and macronutrients" but variable "particularly [for] vitamin D, folate, and iron". Claude Opus 4.5 had no nutrient rated poor. — [Lawabni R, et al. J Nutr 2026;156(9):101712, doi:10.1016/j.tjnut.2026.101712](https://pubmed.ncbi.nlm.nih.gov/42401322/)

**Counter-evidence**
- ChatGPT answers to common nutrition questions scored higher than dieticians' answers on 5 of 8 questions (graded by 18 dieticians and 9 experts). — [Kirk D, van Eijnatten E, Camps G. J Nutr Metab 2023;2023:5548684, doi:10.1155/2023/5548684](https://pubmed.ncbi.nlm.nih.gov/38025546/)

**General clinical decision-making (not diet)**
- LLMs "follow neither diagnostic nor treatment guidelines, and cannot interpret laboratory results". — [Hager 2024, Nat Med](https://pubmed.ncbi.nlm.nih.gov/38965432/)

### Inferences
- The failure modes concentrate exactly where the system's rules operate: potassium, phosphorus and sodium for CKD and hypertension, energy targets, overlapping conditions, allergen and exclusion handling, and iron and folate (relevant to anaemia and pregnancy; Lawabni 2026). This is the specific case for Guarantee 1.
- The newest models (Lawabni 2026, Göz 2026) are much better on energy and macronutrients and on single conditions. The case for Guarantee 1 should therefore rest on determinism, reproducibility (Çalık 2026: poor reproducibility), auditability and residual safety-critical error rates (5-8% even for the best models in Göz 2026), not on "LLMs are inaccurate" alone.

### Gaps
- No verified study evaluates LLM diet advice for Bangladeshi foods or in Bangla, for anaemia diets, or for knee osteoarthritis exercise.
- Exercise prescription by LLMs was not searched in this scope (the exercise notes may cover it).
- Most abstracts do not report harmful-item rates per plan in a comparable way, so no pooled error rate can be stated.

---

## Q4. Which systems use an LLM only to explain or phrase deterministic output or to write patient-friendly reports, and what is known about LLM quality in Bengali or other low-resource languages for health communication?

### Takeaway
LLM rewriting of clinician-authored content into lay language is well studied. It improves readability strongly, but introduces omissions and occasional hallucinations in about 1 in 5 physician reviews (Zaretsky 2024). It also loses risk information unless a clinician revises the output (Luo 2026). Designs where an LLM only sits on top of a deterministic algorithm exist but are rare (Rajashekar 2024; MAI-DIET 2026). Evidence for Bengali is thin: general benchmarks show weak zero-shot performance on most tasks for older models, and Bangla medical QA lacks clinician-validated benchmarks. Low-resource-language clinical translation carries markedly more clinically significant errors.

### Cited Findings
- Patient-friendly rewriting:
  - Reading grade fell from 11.0 to 6.2 and PEMAT rose from 13% to 81%; 18 of 100 reviews noted safety concerns. — [Zaretsky 2024](https://pubmed.ncbi.nlm.nih.gov/38466307/)
  - 15 radiologists rated ChatGPT-simplified reports. Most found them correct and complete, but "instances of incorrect statements, missed relevant medical information, and potentially harmful passages were reported." — [Jeblick K, et al. Eur Radiol 2024;34(5):2817-2825, doi:10.1007/s00330-023-10213-1](https://pubmed.ncbi.nlm.nih.gov/37794249/)
  - Related (metadata verified, abstract not read): Lyu Q, et al. "Translating radiology reports into plain language using ChatGPT and GPT-4 with prompt learning: results, limitations, and potential." Vis Comput Ind Biomed Art 2023;6(1):9, doi:10.1186/s42492-023-00136-5. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37198498/)
- Non-English simplification with clinician revision (Chinese consent forms): the LLM reduced risk-information quality, and clinician revision restored it with the best comprehension. — [Luo 2026, npj Digit Med](https://pubmed.ncbi.nlm.nih.gov/41922537/)
- An LLM layered on a deterministic or validated algorithm:
  - An LLM interface over a UGIB AI-CDSS improved ease of use, and citations improved trust (RCT in simulation). — [Rajashekar 2024, CHI](https://doi.org/10.1145/3613904.3642024)
  - MAI-DIET used an LLM as the interface to a rule-based module. — [Divanis 2026](https://pubmed.ncbi.nlm.nih.gov/42654242/)
  - Registered dietitians validated GPT-4 nutrition outputs and produced "dietitian-reviewed template instructions" that improved the generated food product descriptions. — [Szymanski A, Wimer B, Anuyah O, Eicher-Miller H, Metoyer R. CHI '24, doi:10.1145/3613904.3641924](https://doi.org/10.1145/3613904.3641924)
- Lab-result explanation for lay patients: on 53 Yahoo! Answers lab questions, GPT-4 outperformed four other LLMs and human answers, but "there were cases in which GPT-4 responses were inaccurate and not individualized." — [He Z, et al. J Med Internet Res 2024;26:e56655, doi:10.2196/56655](https://pubmed.ncbi.nlm.nih.gov/38630520/)
- Low-resource languages:
  - Clinically significant translation errors in Haitian Creole were 33.3% for ChatGPT versus 8.3% for professionals. — [Brewster 2024, Pediatrics](https://pubmed.ncbi.nlm.nih.gov/38860299/)
  - GPT-4's translations of a dialysis menu into five languages were rated 4/5. — [Wang LC 2024](https://pubmed.ncbi.nlm.nih.gov/39278578/)
  - "A pronounced disparity in LLM responses across these languages" (English, Spanish, Chinese, Hindi) for health questions, with the XLingHealth benchmark. — [Jin Y, Chandra M, Verma G, Hu Y, De Choudhury M, Kumar S. WWW '24:2627-2638, doi:10.1145/3589334.3645643](https://doi.org/10.1145/3589334.3645643)
  - ChatGPT was evaluated on 7 tasks in 37 languages, with "worse performance... for different NLP tasks and languages" than previous models. — [Lai VD, et al. Findings of EMNLP 2023:13171-13189, doi:10.18653/v1/2023.findings-emnlp.878](https://doi.org/10.18653/v1/2023.findings-emnlp.878)
- Bengali specifically:
  - GPT-3.5, LLaMA-2-13b-chat and Claude-2 performed poorly on most Bengali tasks. — [Kabir 2024, LREC-COLING (BenLLM-Eval)](https://arxiv.org/abs/2309.13173)
  - (Preprint) Nine LLMs, including Claude-3.5-Sonnet, summarised 2,350 Bangla consumer health queries zero-shot. Mixtral-8x22b was best on ROUGE-1/L and fine-tuned Bangla T5 best on ROUGE-2; "zero-shot LLMs can rival fine-tuned models". The evaluation was ROUGE only, with no clinical safety rating. — [Abrar A, Tabassum F, Ahmed S. arXiv:2505.05070](https://arxiv.org/abs/2505.05070)
  - A mini-review of 15 studies on Bangla medical QA found "dataset scarcity, heavy reliance on translated corpora, inconsistent evaluation practices, and a lack of clinician-validated benchmarks". — [Mahmud JS, et al. Front Digit Health 2026;8:1856734, doi:10.3389/fdgth.2026.1856734](https://pubmed.ncbi.nlm.nih.gov/42953604/)
  - The BanglaHealth paraphrase dataset (200,000 sentences, built by round-trip machine translation) shows how scarce native Bangla health resources are. — [Aziz F, Islam MN. Data Brief 2025;61:111699, doi:10.1016/j.dib.2025.111699](https://pubmed.ncbi.nlm.nih.gov/40521140/)

### Inferences
- The system's "LLM only phrases; a deterministic template is the fallback" design is supported by Zaretsky, Jeblick, Luo and Woo, but those same studies show that phrasing alone can omit or alter content. If the LLM rephrases after the physician has approved the structured report, the patient-facing text is not what the physician saw. A reviewer will likely ask either that the physician sees the final phrased text, or that an automated check confirms every approved item and number survives phrasing. I did not check which order the system uses; the writer should confirm this against the repository README.
- For Bangla, the absence of clinician-validated benchmarks (Mahmud 2026) and the low-resource error gap (Brewster 2024) argue for keeping the deterministic template as the reference and treating LLM Bangla phrasing as unvalidated. This matches the system's own stated limitation that its Bangla wording has not been reviewed by a clinician.

### Gaps
- No verified study evaluates LLM-generated Bangla patient health text for clinical accuracy or harm.
- No study compares template NLG with LLM phrasing for diet reports.
- Classic deterministic clinical data-to-text work (for example BabyTalk) was not verified in this pass, so it is not cited.

---

## Q5. What do authoritative bodies say about oversight and auditability of AI in health, and where does a physician-approval workflow fit?

### Takeaway
All four sources point the same way. Humans should stay in control of medical decisions (WHO 2021); LMMs risk inaccurate statements and automation bias and need post-release auditing (WHO 2024). Clinician-facing CDS whose basis clinicians can independently review is treated differently from patient-facing software, and automation bias is the stated reason (FDA 2026). High-risk medical AI must allow human oversight with override and must keep automatic logs (EU AI Act Articles 12, 14 and 26). A physician gate with an append-only audit log maps directly onto these requirements. None of these bodies governs Bangladesh, so they serve as benchmarks.

### Cited Findings
- **WHO 2021**, *Ethics and governance of artificial intelligence for health: WHO guidance* (28 June 2021; ISBN 9789240029200). — [WHO publication page](https://www.who.int/publications/i/item/9789240029200)
  - Six principles: protecting human autonomy; promoting human well-being and safety and the public interest; ensuring transparency, explainability and intelligibility; fostering responsibility and accountability; ensuring inclusiveness and equity; promoting AI that is responsive and sustainable. — [WHO news release, 28 June 2021](https://www.who.int/news/item/28-06-2021-who-issues-first-global-report-on-ai-in-health-and-six-guiding-principles-for-its-design-and-use)
  - On autonomy: "humans should remain in control of health-care systems and medical decisions". On accountability: "Effective mechanisms should be available for questioning and for redress". On responsiveness: "Designers, developers and users should continuously and transparently assess AI applications during actual use." — [WHO news release](https://www.who.int/news/item/28-06-2021-who-issues-first-global-report-on-ai-in-health-and-six-guiding-principles-for-its-design-and-use)
- **WHO 2024**, *Ethics and governance of artificial intelligence for health: Guidance on large multi-modal models* (ISBN 978-92-4-008475-9; 98 pp). The news release is dated 18 January 2024, but the publication page now shows 25 March 2025, probably a later edition (not confirmed). — [WHO publication page](https://www.who.int/publications/i/item/9789240084759); [WHO news release](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
  - Risks named: LMMs can produce "false, inaccurate, biased, or incomplete statements" and can encourage "automation bias" among health professionals and patients. — [WHO news release](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
  - Recommendations: governments should "introduce mandatory post-release auditing and impact assessments" for LMMs deployed at scale; developers should engage stakeholders "including medical providers" from the early stages and design LMMs for well-defined tasks with the needed accuracy and reliability. — [WHO news release](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
- **US FDA**, *Clinical Decision Support Software: Guidance for Industry and FDA Staff*, docket FDA-2017-D-6569, final. The current document was "issued on January 29, 2026. This document supersedes 'Clinical Decision Support Software' issued on January 6, 2026." — [FDA guidance PDF](https://www.fda.gov/media/109618/download); [FDA page](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)
  - Law-firm summaries state that the January 2026 revision superseded the September 2022 guidance. This is a secondary source. — [Covington, Jan 2026](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)
  - The four criteria of section 520(o)(1)(E) for Non-Device CDS are restated: (1) no image or signal analysis; (2) displays or analyses medical information; (3) supports or provides recommendations "to a health care professional"; (4) enables the HCP "to independently review the basis for such recommendations" so the HCP does not "rely primarily" on them. — [FDA guidance PDF](https://www.fda.gov/media/109618/download)
  - "Software functions that support or provide recommendations to patients or caregivers – not HCPs – meet the definition of a device." — [FDA guidance PDF](https://www.fda.gov/media/109618/download)
  - On automation bias: "Automation bias is the propensity of humans to over-rely on a suggestion from an automated system... can result in errors of commission (following incorrect advice) or omission". It "increases" in urgent situations, and this informs FDA's interpretation. — [FDA guidance PDF](https://www.fda.gov/media/109618/download)
  - Criterion 4 labelling expectations include that "the intended use is not time-critical", that the inputs are clearly identified, and "a plain language description of the underlying algorithm development and validation". — [FDA guidance PDF](https://www.fda.gov/media/109618/download)
  - New in 2026: software that otherwise meets all criteria but provides "only one recommendation that is clinically appropriate" falls under enforcement discretion. The guidance still states that a "specific preventive, diagnostic or treatment output or directive" fails Criterion 3. — [FDA guidance PDF](https://www.fda.gov/media/109618/download)
  - The guidance is reported to be silent on AI specifically. — [Covington](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)
- **EU AI Act**, Regulation (EU) 2024/1689 of 13 June 2024. — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Definition: an "AI system" is a machine-based system that "infers, from the input it receives, how to generate outputs such as predictions, content, recommendations, or decisions" (Art 3(1)). Recital 12 says the definition "should not cover systems that are based on the rules defined solely by natural persons to automatically execute operations". — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Art 6(1): an AI system is high-risk where it is a product, or a safety component of a product, covered by Annex I legislation and that product must undergo third-party conformity assessment. Annex I item 11 is the Medical Devices Regulation (EU) 2017/745 and item 12 is the IVDR (EU) 2017/746. — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Art 12: high-risk systems "shall technically allow for the automatic recording of events (logs) over the lifetime of the system". — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Art 14 (human oversight): systems must be "effectively overseen by natural persons". Overseers must be able "to remain aware of the possible tendency of automatically relying or over-relying on the output... (automation bias)", to correctly interpret the output, "to decide... not to use the high-risk AI system or to otherwise disregard, override or reverse the output", and to intervene or stop the system. — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Art 26(2): deployers must "assign human oversight to natural persons who have the necessary competence, training and authority". Art 26(6): they must keep the automatically generated logs "for a period... of at least six months". — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
  - Timing: the original Art 113 applied Art 6(1) obligations from 2 August 2027. Regulation (EU) 2026/1744 (Digital Omnibus on AI, 8 July 2026) amended Art 113 so that Chapter III Sections 1-3 apply from "2 December 2027 as regards AI systems classified as high-risk pursuant to Article 6(2) and Annex III; and... 2 August 2028 as regards AI systems classified as high-risk pursuant to Article 6(1) and Annex I". — [EUR-Lex AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng); [EUR-Lex Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng)
- **EU MDR**, Annex VIII Rule 11: "Software intended to provide information which is used to take decisions with diagnosis or therapeutic purposes is classified as class IIa", or class IIb or III if a decision could cause serious deterioration or death. — [EUR-Lex Regulation (EU) 2017/745](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32017R0745)

### Inferences
- Where the physician-approval workflow fits:
  - It operationalises WHO's "humans remain in control" principle and the EU Art 14 abilities to "disregard, override or reverse": the approve, edit and reject actions.
  - The append-only audit log matches the Art 12 and Art 26(6) logging duties and WHO's call for accountability and redress.
  - Under the FDA framing, routing recommendations to a physician who can see the cited threshold behind each rule is the Criterion 3/4 pattern. Once the output reaches patients, however, the FDA treats patient-facing functions as devices. The approval gate means the patient receives the physician's decision rather than the software's, which is the paper's argument, but this has not been tested against any regulator.
- EU AI Act scope: by Recital 12, a deterministic engine of human-written rules may fall outside the "AI system" definition. The trained rankers and the LLM do infer, so they would be AI systems. If the product qualified as an MDR class IIa+ device under Rule 11 (needing notified-body assessment, which I did not verify in this pass), the AI components would be high-risk under Art 6(1), with obligations from 2 August 2028 after the Omnibus. This is my reading, not legal advice.
- These are foreign frameworks. The system targets Bangladesh, so the paper should present them as reference standards, not as compliance claims.

### Gaps
- I did not read the full WHO 2021 and 2024 PDFs, so the oversight recommendations come from the WHO news releases.
- I did not read the September 2022 FDA guidance text itself; the changes from 2022 come from the 2026 PDF plus secondary summaries.
- MDCG guidance on qualifying software and on the MDR-AI Act interplay was not verified.
- Bangladesh's own regulatory position on AI or software as a medical device was not searched; it belongs to the Bangladesh-context notes.

---

## Q6. Which venues publish this work?

### Takeaway
LLM-nutrition evaluations cluster in nutrition journals, especially MDPI *Nutrients*, Elsevier *Nutrition* and *Frontiers in Nutrition*. Oversight and deployment studies appear in JAMA Network Open, The Lancet Digital Health, JAMIA, npj Digital Medicine and Radiology. Recommender and LLM-system work appears at ACM venues (WSDM, CHI, WWW), in IEEE Access and AIIM, and in ACL/LREC venues for language evaluation.

### Cited Findings
- **Clinical informatics / general medicine:** JAMA Network Open (Garcia 2024; Tai-Seale 2024; Zaretsky 2024; Hoang 2023); The Lancet Digital Health (Chen 2024); Nature Medicine (Hager 2024); JAMA (Khera 2023); JAMIA (Goddard 2012; Lyell & Coiera 2017; Woo 2024; Jung 2026); npj Digital Medicine (Sutton 2020; Luo 2026); Radiology (Dratsch 2023); European Radiology (Jeblick 2024); Pediatrics (Brewster 2024); JMIR (De Croon 2021; Sun Y 2023; Sun H 2023; He 2024); BMC Medical Informatics and Decision Making (Ancker 2017; Basu 2026). — sources as cited in Q0-Q5
- **Nutrition:** Nutrients (Ponzo 2024; Stefanidis 2022; Divanis 2026; Göz 2026; Çalık 2026); Nutrition (Papastratis 2024; Niszczota 2023; Haman 2024; You 2026); American Journal of Clinical Nutrition (O'Hara 2026); Journal of Nutrition (Lawabni 2026); Journal of Renal Nutrition (Wang LC 2024); Nutrition Research (Hieronimus 2024); European Journal of Clinical Nutrition (Naja 2024); Frontiers in Nutrition (Kim 2024; Bilen 2026); Journal of Nutrition and Metabolism (Kirk 2023). — sources as cited in Q0-Q3
- **Other clinical (variable rigour):** Clinics and Practice (Qarajeh 2023); Healthcare (Basel) (Karakas 2026); J Clin Med (Kairat 2025); Diseases (Acharya 2024); Diabetes & Metabolic Syndrome (Ben Lafqih 2025); J Eval Clin Pract (Bayram 2025); Frontiers in Public Health (Gao 2026); JMIR Formative Research (Macias-Navarro 2026); Therapeutic Apheresis and Dialysis (Wang HC 2026); Cureus (Aenuginti 2026). — sources as cited in Q1 and Q3
- **CS / AI venues:** WSDM (Chen 2021); CHI (Rajashekar 2024; Szymanski 2024); WWW (Jin 2024); Findings of EMNLP (Lai 2023); LREC-COLING (Kabir 2024); IEEE Access (Yera Toledo 2019); Artificial Intelligence in Medicine (Spoladore 2024); J Intelligent Information Systems (Tran 2018, 2021); Smart Health (ChatDiet 2024); iScience (El Miayar 2026); arXiv preprints (NutriOrion 2026; NutriBench 2024; Abrar 2025). — sources as cited in Q2 and Q4

### Inferences
- For a paper combining a rule-engine architecture with an oversight workflow, the closest-fit venues are those that published both the CDSS reviews and the oversight evidence: JAMIA, npj Digital Medicine, JMIR (including JMIR Medical Informatics), Artificial Intelligence in Medicine and the Journal of Biomedical Informatics. Nutrients publishes much of the LLM-diet comparison work. The venue choice is still open for the author.

### Gaps
- Journal acceptance rates and impact metrics were not collected.

---

## Q7. Synthesis: the three guarantees against the literature, the strongest citations for each, and critiques a reviewer could raise

### Takeaway
Each guarantee has direct support. Guarantee 1 (no LLM in clinical logic) is supported by consistent evidence of quantitative and multimorbidity failures and by regulators' warnings about inaccuracy. Guarantee 2 (rule gate before ML) follows an established knowledge-based recommender pattern and avoids the residual violations seen when constraints are soft. Guarantee 3 (physician approval plus audit log) matches WHO, FDA and EU oversight and logging expectations. The literature does not support treating physician approval as proof of safety, because of automation bias, anchoring and added workload. The LLM-phrasing step reintroduces a smaller version of the risk Guarantee 1 removes.

### Cited Findings

**Guarantee 1: clinical logic never depends on an LLM.**
What the literature does: most LLM diet studies end by recommending supervision or knowledge-based systems; few build systems that exclude LLMs from computation. MAI-DIET is the clearest example that does.
Strongest citations:
- LLMs "follow neither diagnostic nor treatment guidelines, and cannot interpret laboratory results". — [Hager 2024, Nat Med](https://pubmed.ncbi.nlm.nih.gov/38965432/)
- ChatGPT meal plans need "supervision and guidance by nutrition experts or knowledge-based systems". — [Papastratis 2024](https://pubmed.ncbi.nlm.nih.gov/38359704/)
- Advice degrades with overlapping conditions. — [Ponzo 2024](https://pubmed.ncbi.nlm.nih.gov/38398794/)
- Potassium, phosphorus and sodium were underestimated by 49-54% for dialysis. — [Wang LC 2024](https://pubmed.ncbi.nlm.nih.gov/39278578/)
- Energy fell 250-635 kcal short of the 1800 kcal CKD target (my arithmetic from the reported 1165-1548 kcal). — [You 2026](https://pubmed.ncbi.nlm.nih.gov/41135437/)
- Systematic bias for type 2 diabetes. — [Karakas 2026](https://pubmed.ncbi.nlm.nih.gov/41897193/)
- Guideline conflicts were only 57-89% resolved, and safety flags remained at 5-8% even for the best models. — [Göz 2026](https://pubmed.ncbi.nlm.nih.gov/43030301/)
- Poor reproducibility. — [Çalık 2026](https://pubmed.ncbi.nlm.nih.gov/42884656/)
- LMMs make "false, inaccurate, biased, or incomplete statements". — [WHO 2024 news release](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
- Positive precedent: rules compute while the LLM is supervised. — [MAI-DIET 2026](https://pubmed.ncbi.nlm.nih.gov/42654242/)

**Guarantee 2: contraindicated items never reach recommendations (gate before ranking).**
What the literature does: two-stage designs are common (PROTEIN, Yera Toledo); constraint-aware learned recommenders exist (Chen 2021); LLM systems inject constraints into generation (NutriOrion). None reports a test-enforced zero-violation property.
Strongest citations:
- Expert-rule qualitative layer before an optimisation layer. — [PROTEIN AI Advisor 2022](https://pubmed.ncbi.nlm.nih.gov/36297118/)
- Pre-filtering of inappropriate foods before optimisation. — [Yera Toledo 2019](https://doi.org/10.1109/ACCESS.2019.2929413)
- Guideline constraints in recommendation. — [Chen 2021](https://arxiv.org/abs/2101.01775)
- Even "hard" constraints inside an LLM planner left a 12.1% drug-food violation rate. — [NutriOrion preprint](https://arxiv.org/abs/2602.18650)
- Item-level LLM classification of renal-diet foods is error-prone, with GPT-4 identifying 60% of low-potassium foods. — [Qarajeh 2023](https://pubmed.ncbi.nlm.nih.gov/37887080/)
- Allergen-restricted LLM diets were potentially harmful. — [Niszczota 2023](https://pubmed.ncbi.nlm.nih.gov/37269717/)

**Guarantee 3: no patient sees a report until a physician approves it, with every decision logged append-only.**
What the literature does and recommends: regulators expect oversight that can override and expect logging. Deployment studies place clinicians between the LLM and the patient. Diet-specific evaluations of such a gate do not exist.
Strongest citations:
- Humans "should remain in control of health-care systems and medical decisions". — [WHO 2021 news release](https://www.who.int/news/item/28-06-2021-who-issues-first-global-report-on-ai-in-health-and-six-guiding-principles-for-its-design-and-use)
- Human oversight with the ability to "disregard, override or reverse", and awareness of automation bias. — [EU AI Act Art 14](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
- Automatic logs (Art 12), kept at least six months (Art 26(6)). — [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
- HCP-facing recommendations with an independently reviewable basis; patient-facing functions are devices; automation bias is defined. — [FDA 2026 CDS guidance](https://www.fda.gov/media/109618/download)
- "Initial implementation will require physician review". — [Zaretsky 2024](https://pubmed.ncbi.nlm.nih.gov/38466307/)
- Clinician revision restored accuracy lost in LLM simplification. — [Luo 2026](https://pubmed.ncbi.nlm.nih.gov/41922537/)
- Mitigators include accountability and information rather than recommendation. — [Goddard 2012](https://pubmed.ncbi.nlm.nih.gov/21685142/)

**Critiques a reviewer could raise, with the evidence behind each**
1. **Automation bias and rubber-stamping.**
   - Physicians edited LLM drafts but kept their content (p = 0.81 similarity), and the authors raised "automation bias and anchoring". — [Chen 2024](https://europepmc.org/article/PMC/PMC11829255)
   - Experts' accuracy fell to 19.8-45.5% with wrong AI suggestions. — [Dratsch 2023](https://pubmed.ncbi.nlm.nih.gov/37129490/)
   - Both the FDA and the EU AI Act name automation bias explicitly. — [FDA 2026](https://www.fda.gov/media/109618/download); [EU AI Act Art 14](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
   - Expected question: what stops approval becoming a click-through? The system has no measured edit or reject rates.
2. **Physician workload.**
   - Drafts did not save time. — [Garcia 2024](https://pubmed.ncbi.nlm.nih.gov/38506805/)
   - Read time rose 21.8%. — [Tai-Seale 2024](https://pubmed.ncbi.nlm.nih.gov/38619840/)
   - Acceptance falls as items per encounter rise. — [Ancker 2017](https://pubmed.ncbi.nlm.nih.gov/28395667/)
   - A weekly plan, rankings and an exercise prescription per patient is a lot to review in a doctor-scarce setting.
3. **Rule brittleness and maintenance.**
   - Knowledge-based CDSS need ongoing content maintenance. — [Sutton 2020](https://pubmed.ncbi.nlm.nih.gov/32047862/)
   - Ontology upkeep still needed human experts for global consistency. — [Jung 2026](https://pubmed.ncbi.nlm.nih.gov/41719167/)
   - Clinical experts and guidelines are central but hard to keep interoperable. — [Spoladore 2024](https://pubmed.ncbi.nlm.nih.gov/38564880/)
   - Rules only cover what their data encodes. For example, the system's food table has no saturated-fat values, so the high-cholesterol plan excludes solid-fat dishes instead of counting them, a limitation recorded in the project.
4. **LLMs are getting better, so is excluding them overcautious?**
   - High energy and macronutrient agreement in 2026 models. — [Lawabni 2026](https://pubmed.ncbi.nlm.nih.gov/42401322/)
   - Expert-indistinguishable weight-loss plans. — [Kim 2024](https://pubmed.ncbi.nlm.nih.gov/38577160/)
   - ChatGPT outscored dieticians on general questions. — [Kirk 2023](https://pubmed.ncbi.nlm.nih.gov/38025546/)
   - Response: determinism, reproducibility and auditability, plus residual safety-critical rates (Göz 2026: 5-8%; Çalık 2026: poor reproducibility). The argument is not that LLMs are simply inaccurate.
5. **The phrasing step may change approved content.**
   - Omissions and hallucinations appeared in 18 of 100 reviews. — [Zaretsky 2024](https://pubmed.ncbi.nlm.nih.gov/38466307/)
   - Inferred recommendations appeared in 2.8% of cases. — [Woo 2024](https://pubmed.ncbi.nlm.nih.gov/38778578/)
   - Risk information was lost. — [Luo 2026](https://pubmed.ncbi.nlm.nih.gov/41922537/)
   - Low-resource-language errors were 33.3% versus 8.3%. — [Brewster 2024](https://pubmed.ncbi.nlm.nih.gov/38860299/)
   - Weak Bengali performance and no clinician-validated Bangla benchmarks. — [Kabir 2024](https://arxiv.org/abs/2309.13173); [Mahmud 2026](https://pubmed.ncbi.nlm.nih.gov/42953604/)
   - Expected question: is the phrased Bangla text itself reviewed or checked against the approved content?
6. **No real patients or clinicians.** The system is evaluated on synthetic data, though the field is mostly the same: 38 of 40 studies used hypothetical cases, and health recommenders are rarely evaluated with users. A reviewer will still ask for a physician agreement study. — [O'Hara 2026](https://pubmed.ncbi.nlm.nih.gov/41317995/); [Sun Y 2023](https://pubmed.ncbi.nlm.nih.gov/36656630/); [De Croon 2021](https://pubmed.ncbi.nlm.nih.gov/34185014/)
7. **Regulatory fit is asserted, not shown.**
   - The FDA says patient-facing CDS functions are devices; US rules do not apply in Bangladesh; and EU high-risk status depends on MDR classification. — [FDA 2026](https://www.fda.gov/media/109618/download); [EU AI Act Art 6(1), Annex I](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng); [MDR Rule 11](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32017R0745)

### Inferences
- Positioning sentence the evidence supports: "Prior diet systems either constrain ML with expert rules without clinician sign-off (PROTEIN, Yera Toledo, Chen 2021) or place clinicians over LLM-generated content without deterministic clinical logic (Garcia, Tai-Seale, Chen 2024, Zaretsky). The present system combines a test-enforced rule gate, deterministic guideline logic and a logged physician gate, and restricts the LLM to phrasing."
- Strongest single citation per guarantee: G1 Hager 2024 (Nat Med), with Ponzo 2024 or Wang LC 2024 for diet specifically; G2 PROTEIN AI Advisor 2022, with NutriOrion as the contrast; G3 EU AI Act Art 14 plus FDA 2026 for the requirement, with Chen 2024 for the automation-bias caveat.
- Mitigations the literature suggests, which could go in limitations and future work rather than be claimed:
  - Present each recommendation with its rule and threshold (information, not recommendation; Goddard 2012).
  - Measure edit and reject rates and time per review.
  - Seed known errors to test reviewer vigilance (Dratsch 2023 design).
  - Show the physician the final phrased text, or automatically check it against the approved structured report (Zaretsky 2024; Luo 2026).
  - Keep the deterministic template as the default for Bangla until clinicians review the LLM wording.

### Gaps
- No study was found that measures automation bias specifically in reviewing deterministic, rule-based diet output as opposed to ML or LLM output.
- No evidence was found on audit-log use in practice, such as whether logs are reviewed or support redress.
- No head-to-head comparison of template versus LLM phrasing in Bangla was found.
