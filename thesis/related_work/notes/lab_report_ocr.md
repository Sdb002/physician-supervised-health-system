# Related work: reading lab test results from photographed or scanned lab reports (OCR and information extraction)

*How these notes were checked: every paper listed was checked against at least one primary record: the Crossref DOI registry, the DOI resolver, PubMed (E-utilities), an arXiv abstract page or the arXiv API, or the full text on PMC or arXiv. Each entry says whether it is peer-reviewed; arXiv-only items are labelled "preprint". A number is quoted only if I read it in the abstract or the full text. Where only the abstract was reachable, the missing numbers are listed under Gaps. "The system" means the diet-app lab-slip reader described in the assignment brief. Facts about the system come from that brief, not from a source.*

---

## 1. Which 12–20 published papers are closest to the system, ranked by closeness?

### Takeaway
The closest prior work is Ma et al. 2023 (BMC Med Inform Decis Mak). It runs **PP-OCR on a CPU**, rebuilds table rows with layout rules, and uses a CRF, with a regex-rule baseline, to extract test name, value, unit and reference range from **real** Chinese paper lab reports captured by phone and scanner. After it come Xue et al.'s 2018 and 2020 papers on lab-report images, two Chinese benchmarks of medical-report images (MedRepBench, a preprint, and RJUA-MedDQA at KDD 2024), and Neveditsin et al. at EACL 2026, who compare Tesseract, PaddleOCR (PP-OCRv5), docTR and Surya with compact multimodal LLMs on real smartphone photos of Indian clinical reports, all run on-premise. None of the reviewed papers combines targeted analytes, look-alike exclusion, unit conversion, plausibility rejection, abstention and mandatory physician confirmation. None reports a field-level benchmark of lab slips with controlled synthetic damage.

### Cited Findings

**How the papers were ranked** (my own judgement): document type (lab report) first, then capture (phone photo, scan or PDF), then pipeline (local OCR plus rules), then evaluation (field-level, with photo damage), then setting (low- and middle-income country, on-premise).

| # | Paper | Venue / type | Documents | Pipeline | Headline number | Source |
|---|---|---|---|---|---|---|
| 1 | Ma et al. 2023 | BMC Med Inform Decis Mak (journal) | 153 real Chinese lab reports, scanner and phone | PP-OCR + layout rules + CRF (regex baseline) | entity F1 0.86 (rules 0.78); 0.78 s/report on CPU | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/) |
| 2 | Xue et al. 2020; Xue et al. 2018 | IEEE Access (journal); IEEE DASC/PiCom/DataCom/CyberSciTech 2018 (conference) | scanned and camera-captured lab reports | custom deep-learning text detection and recognition; top-down table segmentation | detection recall 99.5% | [S2 abstract 2020](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ACCESS.2019.2961964?fields=title,venue,year,abstract); [S2 abstract 2018](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043?fields=title,venue,year,abstract) |
| 3 | Shang et al. 2025, MedRepBench | arXiv preprint (authors' comment: ECCV 2026) | 1,925 real Chinese report images (photos, PDFs, screenshots) | OCR + LLM vs end-to-end VLM | best OCR+LLM value recall 88.83%; without OCR, recall drops about 10–20% | [arXiv HTML](https://arxiv.org/html/2508.16674v2) |
| 4 | Neveditsin et al. 2026 | EACL 2026 Industry Track (peer-reviewed) | real smartphone photos of Indian obstetric ultrasound reports | 5 OCR systems vs 3 compact MLLMs, all local | numeric accuracy from 0.674 (PaddleOCR) to 0.950 (Qwen2.5-VL) | [arXiv HTML](https://arxiv.org/html/2511.13523v1) |
| 5 | Jin et al. 2024, RJUA-MedDQA | KDD 2024 (peer-reviewed) | 2,000 Chinese report images, 979 of them patient photos | LMMs (GPT-4V and others) vs OCR-style text + LLM | GPT-4V wrong on 54 of 84 unanswerable entity questions | [arXiv HTML](https://arxiv.org/html/2402.14840v1) |
| 6 | Batra et al. 2024, OCR-MRD | Int J Inf Technol (journal) | medical lab reports | Tesseract vs EasyOCR vs docTR × 6 preprocessing steps | numbers not obtained | [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s41870-023-01610-2?fields=title,venue,year,abstract) |
| 7 | Hsu et al. 2022 | JAMIA Open (journal) | 955 real scanned sleep-study reports | Tesseract + preprocessing + ClinicalBERT | document accuracy 94.76% (AHI), 91.61% (SaO2) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/) |
| 8 | Li et al. 2024, MSIE-Net | Applied Sciences, MDPI (journal) | Chinese medical examination reports (CMERD) | OCR + RVI-LayoutXLM + table-item detection + coordinate aggregation | numbers not obtained | [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/app14041668?fields=title,venue,year,abstract) |
| 9 | Soeno et al. 2024 | PLOS ONE (journal) | 6 sample pictures, 38 clinical staff, Japan | OCR vs manual typing on a smartphone | errors 0% vs 1.32% (vital signs) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/) |
| 10 | Laique et al. 2021 | Gastrointestinal Endoscopy (journal) | real scanned colonoscopy and pathology reports, USA | commercial OCR/NLP hybrid | 95.8–99.3% accuracy vs manual extraction | [PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/) |
| 11 | Folks et al. 2024 | BMC Bioinformatics (journal) | smartphone photos of paper anaesthesia charts, Kigali | perspective and shadow correction + YOLOv8 + DNNs | BP mean average error 1.0 / 1.36 mmHg | [PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/) |
| 12 | Katebi et al. 2024 | PLOS Digital Health (journal) | photos of BP-monitor screens, rural Guatemala and Georgia (USA) | YOLO + CNN digit reader | MAE about 1 mmHg | [PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/) |
| 13 | Hegghammer 2022 | J Comput Soc Sci (journal) | 18,568 page images with artificial noise (English, Arabic) | Tesseract vs Textract vs Document AI | cloud engines more robust to noise | [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract) |

That is 13 ranked entries and 14 papers; entry 2 covers two companion papers. The supporting references below, also verified, back specific key questions: the PP-OCR family, Tesseract, data-entry error and automation bias, local LLMs, and Bangla OCR.

#### Top five in depth

**1. Ma et al. 2023: the closest match**
- **Citation:** Ma M-W, Gao X-S, Zhang Z-Y, Shang S-Y, Jin L, Liu P-L, Lv F, Ni W, Han Y-C, Zong H. "Extracting laboratory test information from paper-based reports." *BMC Medical Informatics and Decision Making* 2023;23(1):251. doi:10.1186/s12911-023-02346-6. PMID 37932733; PMC10629084. — [Crossref](https://api.crossref.org/works/10.1186/s12911-023-02346-6); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37932733/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Type:** peer-reviewed open-access journal article. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **What they built:** an OCR module followed by an information-extraction module for paper lab reports. A web application built on the pipeline was used by physicians at Peking University First Hospital; the paper gives no quantitative clinical outcome data from that use. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **OCR method:** PP-OCR, with a DB text detector, a text-direction classifier and a CRNN recogniser on a MobileNetV3 backbone. Text items are grouped into lines by similar vertical coordinates. The paper does not compare OCR engines. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Layout and table rules:** a keyword regex finds header rows (e.g., "name", "result", "value"). Line normalisation merges or splits lines by comparison with the average line length. "Step detection" handles multi-column layouts: a second occurrence of the test-name entity marks a second column, and the columns are merged into one table. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Extraction:** a conditional random field (L-BFGS, elastic-net) using word identity, suffix, shape and part-of-speech features. It extracts LabName, LabResult, LabUnit and LabRefRange, plus the report time (the earliest datetime). A regex rule system is the baseline. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Data:** a public training set of 238 images of Chinese lab reports from 119 paper files, captured by scanners and smartphones under varying lighting, from an open-source GitHub repository. Validation used 196 real reports from Peking University First Hospital; after excluding incomplete scans and reports with OCR accuracy below 30%, 153 remained. By type: complete blood count 49, PSA 27, biochemical 26, tumour marker 12, urinalysis 9, viral 7, other 23. The reports came from various outside hospitals and had diverse layouts. Two annotators labelled with IOB tags (Cohen's κ 0.89). — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Evaluation:** real documents, OCR and IE scored separately. An entity counts as correct only if both its text and its category match. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Key numbers:** OCR character accuracy 0.95, detection-box accuracy 0.93, line formation 0.90, overall 0.93. Rule baseline P 0.84 / R 0.73 / F1 0.78. CRF P 0.90 / R 0.83 / F1 0.86. Per-entity CRF F1: name 0.89, result 0.87, unit 0.84, reference range 0.80. 6,965 of 8,442 gold entities correct. 0.78 s per report on one CPU (Xeon Silver 4116, 2.10 GHz, 32 GB RAM). — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Errors and limitations they state:** the main causes were poor scan quality, lines misplaced by skew, and multi-column layouts; one example report scored an average precision of 0.59. Accuracy depends on scan quality and handwritten markups, "which often require manual correction by physicians". The CRF was chosen over BERT for speed. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Similarities to the system (my analysis):** the same OCR model family (PP-OCR), CPU-only inference at about a second per document, rules that rebuild table rows from coordinates, input from both phones and scanners, and physicians correcting values in a web application.
- **Differences (my analysis):** Ma extracts every test generically, not three targeted analytes, and uses a learned CRF. It reports no look-alike exclusion, unit conversion, plausibility check or abstention. It is Chinese-language and tested on real reports, and it excluded the worst images (OCR below 30%), whereas the system uses synthetic slips with controlled damage. There is no PDF text-layer path.

**2. Xue et al. 2020 and Xue et al. 2018: early work on lab-report images**
- **Citation (2020):** Xue W, Li Q, Xue Q. "Text Detection and Recognition for Images of Medical Laboratory Reports With a Deep Learning Approach." *IEEE Access* 2020;8:407–416. doi:10.1109/ACCESS.2019.2961964. — [Crossref](https://api.crossref.org/works/10.1109/ACCESS.2019.2961964); [DOI resolves to IEEE Xplore 8941040](https://doi.org/10.1109/ACCESS.2019.2961964)
- **Citation (2018):** Xue W, Li Q, Zhang Z, Zhao Y, Wang H. "Table Analysis and Information Extraction for Medical Laboratory Reports." In: *2018 IEEE 16th Intl Conf on Dependable, Autonomic and Secure Computing / 16th Intl Conf on Pervasive Intelligence and Computing / 4th Intl Conf on Big Data Intelligence and Computing / Cyber Science and Technology Congress (DASC/PiCom/DataCom/CyberSciTech)*, Aug 2018, pp. 193–199. doi:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043. — [Crossref title search result](https://api.crossref.org/works?rows=3&query.bibliographic=Table%20analysis%20and%20information%20extraction%20for%20medical%20laboratory%20reports)
- **Type:** a peer-reviewed open-access journal article (2020) and an IEEE conference paper (2018). — [Crossref](https://api.crossref.org/works/10.1109/ACCESS.2019.2961964)
- **What they built (2018):** a document-image system for lab reports. Table areas and text are segmented top-down, then text containing Arabic numerals, mathematical symbols and multilingual characters is recognised. It was evaluated on a new public dataset of scanned and camera-captured reports, explicitly to support "remote healthcare in developing countries". — [S2 abstract 2018](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043?fields=title,venue,year,abstract)
- **What they built (2020):** a two-module deep-learning system. Detection uses a patch-based training strategy that reaches **99.5% recall**. Recognition uses a "concatenation structure" that combines shallow and deep features and improves multilingual recognition. The motivation is EHR data sharing and integrating historical records. — [S2 abstract 2020](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ACCESS.2019.2961964?fields=title,venue,year,abstract)
- **Evaluation:** text detection and recognition, not field extraction. Dataset size and recognition accuracy are not in the abstracts (see Gaps). — [S2 abstract 2020](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ACCESS.2019.2961964?fields=title,venue,year,abstract)
- **Similarities (my analysis):** the same document type, capture by camera and scanner, table-aware segmentation, and a developing-country motivation.
- **Differences (my analysis):** custom-trained detection and recognition networks rather than an off-the-shelf PP-OCR; they measure OCR quality, not the correctness of specific clinical values; no safety rules or confirmation step is described.

**3. Shang et al. 2025, MedRepBench: field-level extraction from report images (preprint)**
- **Citation:** Shang F, Xia Y, Yang D, Wang Y, Yang B. "MedRepBench: A Comprehensive Benchmark for Medical Report Interpretation." arXiv:2508.16674 (v2), first submitted 21 Aug 2025. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2508.16674); [arXiv HTML v2](https://arxiv.org/html/2508.16674v2)
- **Type:** **preprint**. The arXiv comment field says "ECCV 2026 (main conference)"; I did not confirm this against the proceedings. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2508.16674)
- **What they built:** a benchmark of 1,925 de-identified, real Chinese medical report images (exam and lab reports) from a private online medical service, captured as handheld photos, PDFs or e-documents, and mobile screenshots. To annotate it, a proprietary OCR system extracted the text, DeepSeek-R1 parsed it into JSON, and humans verified the output. An audit of 200 reports found more than 97% field-level agreement, and 12.3% of images were removed as near-duplicates. — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Task and metric:** each lab item has five fields: name, value, unit, reference range and abnormality flag. The flag must be inferred from the value and range, not copied. The score is field-level recall averaged over the five fields. An item matches only on an exact normalised name; the reference range is fuzzy-matched and the other fields need exact equivalence. Outputs are cut to the top K, where K is the number of ground-truth items, so spurious items take up slots. — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Models:** open-source only (InternVL2.5/3, Qwen2.5-VL, LLaMA-4 Scout and Maverick as VLMs; Qwen3, DeepSeek-R1-Distill and DeepSeek-V3 as LLMs reading OCR text). GPT, Gemini and Claude were **excluded "for reproducibility and privacy"**. — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Key numbers:** LLaMA-4-Maverick without OCR scored 88.51 / 72.26 / 78.83 / 77.58 / 75.83 recall on name / value / unit / range / abnormal. The best OCR+LLM, DeepSeek-V3, scored 96.48 / 88.83 / 90.75 / 92.60 / 89.06. Qwen2.5-VL-32B's abnormal-flag recall was 59.66 without OCR and 83.95 with it. Removing OCR cuts field-level recall by about 10–20%. The authors' GRPO-tuned InternVL3-8B reached 79.45% average recall without OCR (SFT 73.31%). — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Error analysis:** VLMs make character-level errors on fine-print numbers and units, misalign rows in nested or multi-column tables, and miss abnormality flags. In OCR+LLM pipelines, recognition errors propagate and can produce hallucinations such as marking normal findings as abnormal. — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Limitations they state:** Chinese only, open-source models only, DeepSeek-R1 as both annotator and judge, and a human study of only 60 samples. — [arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Similarities (my analysis):** field-level scoring of value, unit and range on real phone photos and PDFs, and evidence that an explicit OCR stage helps value extraction. Its privacy-based exclusion of cloud models matches the system's on-premise default.
- **Differences (my analysis):** it extracts every item generically using GPU-scale LLMs and VLMs; it has no abstention metric (recall only); it is in Chinese; it does not report unit conversion or plausibility checks.

**4. Neveditsin et al. 2026: OCR engines vs compact MLLMs on real phone photos, run on-premise**
- **Citation:** Neveditsin N, Lingras P, Patil S, Patil S, Mago VK. "Compact Multimodal Language Models as Robust OCR Alternatives for Noisy Textual Clinical Reports." In: *Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (Volume 5: Industry Track)*, 2026, pp. 48–59. doi:10.18653/v1/2026.eacl-industry.4. Also arXiv:2511.13523. — [Crossref title search result](https://api.crossref.org/works?rows=3&query.bibliographic=Compact%20Multimodal%20Language%20Models%20as%20Robust%20OCR%20Alternatives%20for%20Noisy%20Textual%20Clinical%20Reports); [ACL Anthology PDF](https://aclanthology.org/2026.eacl-industry.4.pdf); [arXiv](https://arxiv.org/abs/2511.13523)
- **Type:** peer-reviewed conference paper (industry track). The numbers below come from arXiv v1 and may differ slightly from the camera-ready version. — [arXiv HTML v1](https://arxiv.org/html/2511.13523v1)
- **Data:** 340 anonymised obstetric ultrasound reports, all **real smartphone photos of printed reports** from a clinical partner in India, in "regionally inflected medical English". A random 60 were transcribed by hand and rated for noise. The noise types were blur, rotation, uneven illumination and shadows, bleed-through from the reverse side, background texture and compression artefacts. Annotator agreement on noise, Krippendorff's α, ranged from 0.62 for blur to 0.85 for illumination. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Systems compared:** Tesseract 4.1.1, PaddleOCR 3.3.0 (PP-OCRv5), docTR 1.0.0, Surya 0.17.0, GOT-OCR 2.0, Qwen2.5-VL-7B-Instruct, Phi-4-multimodal-instruct and InternVL3.5-4B. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Metrics:** CER and WER (computed with jiwer after normalisation), plus numeric accuracy N_acc: the share of reference numeric spans that appear identically in the output, matched by an order-preserving aligner. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Key numbers (CER / WER / N_acc):** Tesseract 0.189 / 0.276 / 0.756; PaddleOCR 0.111 / 0.183 / **0.674**; docTR 0.108 / 0.173 / 0.884; Surya 0.135 / 0.220 / 0.821; GOT-OCR 2.0 0.101 / 0.395 / 0.832; InternVL3.5-4B 0.040 / 0.096 / 0.927; Phi-4-MM 0.035 / 0.075 / 0.944; Qwen2.5-VL 0.031 / 0.078 / **0.950**. Runtime per image: Tesseract 0.63 s, docTR 0.81 s, Surya 1.66 s, GOT-OCR 4.87 s, InternVL 11.13 s, **PaddleOCR 14.14 s (CPU only, 1.00 GB RAM)**, Qwen2.5-VL 54.89 s, Phi-4-MM 66.79 s, on an A100 80 GB with dual EPYC 7552 CPUs. Tesseract was most sensitive to blur and shadows, docTR to rotation, and Surya to bleed-through. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Hallucination:** the MLLMs were not reported to fabricate digits, but they sometimes transcribed background text from other documents visible in the photo. GOT-OCR "may remain prone to hallucination"; this is a caution, not a measurement. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Privacy:** everything ran on local hardware, and no cloud OCR APIs were used. The authors present the approach as suited to on-premise healthcare digitisation and aligned with privacy rules analogous to HIPAA and GDPR. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Limitations they state:** one domain and one region; page-level transcription only, with layout and table extraction not the goal; a single hardware setup. — [arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **Similarities (my analysis):** almost the same engine shortlist the authors compared (Tesseract, PaddleOCR/PP-OCR, docTR, Surya), real phone photos of printed clinical reports in South Asia, on-premise processing, and a numbers-focused metric.
- **Differences (my analysis):** this is transcription, not extraction of named fields, and there is no rule layer. In their configuration PP-OCRv5 had the *lowest* numeric accuracy and was slow on CPU (14 s), while the system reports about 1.5 s per photo with RapidOCR on ONNX. The configurations differ, so the figures cannot be compared directly.

**5. Jin et al. 2024, RJUA-MedDQA: medical report images and hallucination in GPT-4V**
- **Citation:** Jin C, Zhang M, Ma W, Li Y, Wang Y, Jia Y, Du Y, Sun T, Wang H, Fan C, Gu J, Chi C, Lv X, Li F, Xue W, Huang Y. "RJUA-MedDQA: A Multimodal Benchmark for Medical Document Question Answering and Clinical Reasoning." In: *Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '24)*, 2024, pp. 5218–5229. doi:10.1145/3637528.3671644. arXiv:2402.14840. — [Crossref title search result](https://api.crossref.org/works?rows=3&query.bibliographic=RJUA-MedDQA%20multimodal%20benchmark%20medical%20document%20question%20answering%20clinical%20reasoning); [arXiv](https://arxiv.org/abs/2402.14840)
- **Type:** peer-reviewed conference paper. — [DOI](https://doi.org/10.1145/3637528.3671644)
- **Data:** 2,000 Chinese medical report images from the urology department of Shanghai Renji Hospital: 402 screenshots, 619 scanned PDFs and **979 photos taken by patients** (593 high quality; 386 low quality with **rotation, skew, blur or missing corners**). The lab reports include complete blood count, liver function, urinalysis and PSA, mostly as tables. The abstract calls the images "real-world", but the full text also calls the data "synthetic multi-modal clinical data for virtual patients", so the provenance is ambiguous. — [arXiv HTML](https://arxiv.org/html/2402.14840v1); [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3637528.3671644?fields=title,venue,year,abstract)
- **Method:** it evaluates LMMs (LLaVA-v1.5-7B, mPLUG-Owl2, Qwen-VL-Chat, Qwen-VL-Plus, GPT-4V) reading the images directly, against LLMs (Qwen, GPT-4) reading text restored by the authors' ESRA annotation method. ESRA doubled annotator productivity and improved accuracy by 26.8%. — [arXiv HTML](https://arxiv.org/html/2402.14840v1)
- **Key numbers:** GPT-4V entity accuracy 0.38 and table accuracy 0.47; Qwen-VL-Plus 0.51 and 0.53; ESRA+GPT-4 0.76 and 0.72; ESRA+Qwen 0.80 and 0.73. On **unanswerable** questions, GPT-4V gave incorrect answers to **54 of 84 entity questions and 35 of 50 table questions**, i.e. it answered when it should have abstained. Reference-range errors arise when a model fails to find the right item name. GPT-4V also changed output formats such as decimal places. — [arXiv HTML](https://arxiv.org/html/2402.14840v1)
- **Similarities (my analysis):** lab tables photographed by patients, with the same kinds of damage (rotation, skew, blur) the system's benchmark simulates. The unanswerable-question test parallels the system's "leave empty rather than guess" rule, and the reference-range confusion parallels the system's rule to skip reference ranges.
- **Differences (my analysis):** a question-answering format rather than form prefill; Chinese; no rule-based pipeline; it measures LMMs rather than proposing a deployable extractor.

#### Entries 6–13 (compact)

**6. Batra et al. 2024, OCR-MRD**
- Citation: Batra P, Phalnikar N, Kurmi D, Tembhurne J, Sahare P, Diwan T. "OCR-MRD: performance analysis of different optical character recognition engines for medical report digitization." *International Journal of Information Technology* 2024;16(1):447–455 (online 24 Nov 2023). doi:10.1007/s41870-023-01610-2. Peer-reviewed journal (Springer). — [Crossref](https://api.crossref.org/works/10.1007/s41870-023-01610-2)
- Built and method: a comparison of **Tesseract, EasyOCR and docTR** under six preprocessing techniques (binarisation, brightness transformation, gamma correction, sigmoid stretching, bilateral filtering, sharpening) and their combinations, for digitising medical lab records. — [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s41870-023-01610-2?fields=title,venue,year,abstract)
- Data, evaluation and numbers: not available from the abstract (paywalled; see Gaps).
- Similar (my analysis): an engine-selection study on lab reports, close to the authors' own comparison before choosing RapidOCR. Different: no PaddleOCR/PP-OCR, and (going by the abstract) OCR accuracy only, with no field extraction.

**7. Hsu et al. 2022**
- Citation: Hsu E, Malagaris I, Kuo Y-F, Sultana R, Roberts K. "Deep learning-based NLP data pipeline for EHR-scanned document information extraction." *JAMIA Open* 2022;5(2):ooac045. doi:10.1093/jamiaopen/ooac045. PMID 35702624. Peer-reviewed journal (an arXiv preprint, 2110.11864, exists). — [Crossref](https://api.crossref.org/works/10.1093/jamiaopen/ooac045); [PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- Built and method: extraction of two targeted numeric indicators, apnoea-hypopnoea index (AHI) and oxygen saturation (SaO2), from **955 real scanned sleep-study reports**. Preprocessing (grey-scaling, dilating, eroding, contrast) is followed by Tesseract OCR, then 7 traditional ML and 3 deep-learning models, with and without layout input. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- Numbers: ClinicalBERT reached AUROC 0.9743 and **document accuracy 94.76%** for AHI, and AUROC 0.9523 and **91.61%** for SaO2. The authors conclude that preprocessing and document layout both matter. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- Similar (my analysis): a few targeted numeric values from scanned reports, scored per document. Different: a learned classifier, Tesseract, US sleep reports, real scans only.

**8. Li et al. 2024, MSIE-Net**
- Citation: Li Q, Sheng H, Sheng M, Wan H. "MSIE-Net: Associative Entity-Based Multi-Stage Network for Structured Information Extraction from Reports." *Applied Sciences* 2024;14(4):1668. doi:10.3390/app14041668. Peer-reviewed open-access journal (MDPI). — [Crossref](https://api.crossref.org/works/10.3390/app14041668); [publisher page](https://www.mdpi.com/2076-3417/14/4/1668)
- Built and method: three stages. (1) RVI-LayoutXLM, a refined-attention variant of LayoutXLM, does key-information extraction. (2) RIFD-Net locates each test item in the table body. (3) Coordinate-aggregation post-processing links the outputs. They argue that earlier methods reconstruct table bodies but overlook table headers. Data: the Chinese Medical Examination Report Dataset (CMERD), "based on real medical scenarios". — [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/app14041668?fields=title,venue,year,abstract)
- Numbers: not obtained (the MDPI page returned HTTP 403; see Gaps).
- Similar (my analysis): coordinate-based reconstruction of table rows, like the system's row rebuilding. Different: a trained layout transformer that needs annotated data; Chinese.

**9. Soeno et al. 2024**
- Citation: Soeno S, Liu K, Watanabe S, Sonoo T, Goto T. "Development of novel optical character recognition system to reduce recording time for vital signs and prescriptions: A simulation-based study." *PLOS ONE* 2024;19(1):e0296319. doi:10.1371/journal.pone.0296319. PMID 38241403. Peer-reviewed journal. — [Crossref](https://api.crossref.org/works/10.1371/journal.pone.0296319); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/)
- Method and data: a within-subject experiment at three community hospitals and two fire departments in Japan, with 38 volunteers (15 paramedics, 10 nurses, 13 physicians). Participants recorded data from 6 sample pictures (3 ambulance monitors, 3 pharmacy notebooks), either by OCR or by typing on a smartphone. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/)
- Numbers: character-level errors were **0/1056 (0%) with OCR vs 14/1056 (1.32%) typed for vital signs** (p<0.001), and 30/4814 (0.62%) vs 53/4814 (1.10%) for prescriptions. Time was similar for vital signs (21 vs 23 s) but much shorter by OCR for a six-drug prescription (18 vs 144 s). — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/)
- Similar (my analysis): OCR prefill of vital signs (including blood pressure) with a human in the loop, measured against manual entry. Different: a simulation with six pictures; not lab reports.

**10. Laique et al. 2021**
- Citation: Laique SN, Hayat U, Sarvepalli S, Vaughn B, Ibrahim M, McMichael J, Qaiser KN, Burke C, Bhatt A, Rhodes C, Rizk MK. "Application of optical character recognition with natural language processing for large-scale quality metric data extraction in colonoscopy reports." *Gastrointestinal Endoscopy* 2021;93(3):750–757. doi:10.1016/j.gie.2020.08.038. PMID 32891620. Peer-reviewed journal. — [Crossref](https://api.crossref.org/works/10.1016/j.gie.2020.08.038); [PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/)
- Method and data: a commercial OCR/NLP hybrid, co-developed by Cleveland Clinic and eHealth Technologies, applied to real scanned colonoscopy and pathology reports from three EHR systems at Cleveland Clinic and the University of Minnesota, and compared against manual extraction by two researchers. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/)
- Numbers: accuracy of 95.8% for polyps, 98.5% adenomas, 99.3% sessile serrated polyps, 98% advanced adenomas, 98.4% inadequate preparation and 99% failed caecal intubation; agreement with NLP alone was above 99%. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/)
- Similar (my analysis): variable-level accuracy on real scans against a manual gold standard. Different: categorical findings, not lab values; proprietary method.

**11. Folks et al. 2024**
- Citation: Folks RD, Naik BI, Brown DE, Durieux ME. "Computer vision digitization of smartphone images of anesthesia paper health records from low-middle income countries." *BMC Bioinformatics* 2024;25(1):178. doi:10.1186/s12859-024-05785-8. PMID 38714921. Peer-reviewed journal. — [Crossref](https://api.crossref.org/works/10.1186/s12859-024-05785-8); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/)
- Method and data: smartphone photos of paper anaesthesia charts from the University Teaching Hospital of Kigali. The pipeline removes perspective distortion and shadows, applies morphological clean-up, uses YOLOv8 to locate chart sections, and uses DNNs to read handwritten BP symbols and physiological values. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/)
- Numbers: section boxes precision 0.99, recall 0.99, mAP0.5–95 0.97; checkboxes above 99% accuracy; **BP mean average error 1.0 mmHg (systolic) and 1.36 mmHg (diastolic)**; physiological data 85.2% accuracy; "within human accuracy when provided legible handwriting". — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/)
- Similar (my analysis): a low-income-country hospital, phone photos, perspective correction, blood pressure. Different: handwritten chart symbols, trained detectors, no printed lab tables.

**12. Katebi et al. 2024**
- Citation: Katebi N, Bremer W, Nguyen T, Phan D, Jeff J, Armstrong K, Phabian-Millbrook P, Platner M, Carroll K, Shoai B, Rohloff P, Boulet SL, Franklin CG, Clifford GD. "Automated image transcription for perinatal blood pressure monitoring using mobile health technology." *PLOS Digital Health* 2024;3(10):e0000588. doi:10.1371/journal.pdig.0000588. PMID 39356720. Peer-reviewed journal (an earlier medRxiv preprint exists). — [Crossref](https://api.crossref.org/works/10.1371/journal.pdig.0000588); [PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- Method and data: photos of oscillometric BP-monitor screens from four studies in two countries. In rural Guatemala, 49 lay midwives captured readings from 1,697 and 584 pregnant women; in Georgia (USA), 23 and 49 postpartum participants did so. YOLO localises the LCD, a multi-digit CNN reads it, and colour correction and thresholding handle reflections. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- Numbers: device-independent model MAE 1.1 / 1.1 mmHg (Georgia IMPROVE) and 1 / 0.6 mmHg (Guatemala Set 2), below the FDA's 5 mmHg requirement. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- Similar (my analysis): blood pressure read from real photos in low-resource settings. Different: seven-segment LCD digits, not printed reports.

**13. Hegghammer 2022**
- Citation: Hegghammer T. "OCR with Tesseract, Amazon Textract, and Google Document AI: a benchmarking experiment." *Journal of Computational Social Science* 2022;5(1):861–882 (online 22 Nov 2021). doi:10.1007/s42001-021-00149-1. Peer-reviewed journal. — [Crossref](https://api.crossref.org/works/10.1007/s42001-021-00149-1)
- Method and data: 322 English book scans and 100 Arabic article scans, each **replicated 43 times with different artificial noise**: 18,568 documents and 51,304 process requests. The test images are released as the "Noisy OCR Dataset" (NOD). — [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)
- Findings: Document AI was best; the server-based engines beat Tesseract substantially, especially on noisy documents; English was more accurate than Arabic. — [S2 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)
- Similar (my analysis): the same benchmark design as the system's, with clean pages plus controlled synthetic damage, released for reuse. Different: not medical, page-level text, includes cloud engines.

#### Supporting references (verified; cited for specific key questions, not ranked by closeness)
- **PP-OCR family (technical reports, preprints):** Du Y, Li C, Guo R, Yin X, Liu W, Zhou J, Bai Y, Yu Z, Yang Y, Dang Q, Wang H. "PP-OCR: A Practical Ultra Lightweight OCR System." arXiv:2009.09941, 2020. Du Y, Li C, Guo R, Cui C, Liu W, Zhou J, Lu B, Yang Y, Liu Q, Hu X, Yu D, Ma Y. "PP-OCRv2: Bag of Tricks for Ultra Lightweight OCR System." arXiv:2109.03144, 2021. Li C, Liu W, Guo R, Yin X, Jiang K, Du Y, Du Y, Zhu L, Lai B, Hu X, Yu D, Ma Y. "PP-OCRv3: More Attempts for the Improvement of Ultra Lightweight OCR System." arXiv:2206.03001, 2022. Cui C, Sun T, Lin M, Gao T, Zhang Y, Liu J, Wang X, Zhang Z, Zhou C, Liu H, Zhang Y, Lv W, Huang K, Zhang Y, Zhang J, Zhang J, Liu Y, Yu D, Ma Y. "PaddleOCR 3.0 Technical Report." arXiv:2507.05595, 2025. — [arXiv API records](http://export.arxiv.org/api/query?id_list=2009.09941,2109.03144,2206.03001,2507.05595)
- **Tesseract (canonical citation, outside the 2017–2026 window):** Smith R. "An Overview of the Tesseract OCR Engine." *Ninth International Conference on Document Analysis and Recognition (ICDAR 2007)*, vol. 2, pp. 629–633. doi:10.1109/ICDAR.2007.4376991. Peer-reviewed conference paper. — [Crossref](https://api.crossref.org/works/10.1109/ICDAR.2007.4376991)
- **Mays JA, Mathias PC.** "Measuring the rate of manual transcription error in outpatient point-of-care testing." *JAMIA* 2019;26(3):269–272. doi:10.1093/jamia/ocy170. PMID 30649499. Peer-reviewed journal. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/30649499/); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6351970/)
- **Zhou L, Blackley SV, Kowalski L, Doan R, Acker WW, Landman AB, Kontrient E, Mack D, Meteer M, Bates DW, Goss FR.** "Analysis of Errors in Dictated Clinical Documents Assisted by Speech Recognition Software and Professional Transcriptionists." *JAMA Network Open* 2018;1(3):e180530. doi:10.1001/jamanetworkopen.2018.0530. PMID 30370424. Peer-reviewed journal. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/30370424/)
- **Lyell D, Coiera E.** "Automation bias and verification complexity: a systematic review." *JAMIA* 2017;24(2):423–431. doi:10.1093/jamia/ocw105. PMID 27516495. Peer-reviewed systematic review. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/27516495/)
- **Wiest IC, Ferber D, Zhu J, van Treeck M, Meyer SK, Juglan R, Carrero ZI, Paech D, Kleesiek J, Ebert MP, Truhn D, Kather JN.** "Privacy-preserving large language models for structured medical information retrieval." *npj Digital Medicine* 2024;7:257. doi:10.1038/s41746-024-01233-2. PMID 39304709. Peer-reviewed journal. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39304709/)
- **Wiest IC, Wolf F, Leßmann M-E, van Treeck M, Ferber D, Zhu J, Boehme H, Bressem KK, Ulrich H, Ebert MP, Kather JN.** "A software pipeline for medical information extraction with large language models, open source and suitable for oncology." *npj Precision Oncology* 2025;9:313. doi:10.1038/s41698-025-01103-4. PMID 40962856. Peer-reviewed protocol. — [Crossref](https://api.crossref.org/works/10.1038/s41698-025-01103-4); [PubMed](https://pubmed.ncbi.nlm.nih.gov/40962856/)
- **Tabassum S, Abedin N, Rahman MM, Rahman MM, Ahmed MT, Islam R, Ahmed A.** "An online cursive handwritten medical words recognition system for busy doctors in developing countries for ensuring efficient healthcare service delivery." *Scientific Reports* 2022;12:3601. doi:10.1038/s41598-022-07571-z. PMID 35246576. Peer-reviewed journal. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35246576/); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8897401/)
- **Zulkarnain IM, Islam SB, Farabe MZAZ, Shawon MMH, Abedin JM, Hasan BR, Haque M, Shihab I, Mobassir S, Ansary MN, Sushmit A, Sadeque F.** "bbOCR: An Open-source Multi-domain OCR Pipeline for Bengali Documents." arXiv:2308.10647, 2023. **Preprint.** — [arXiv](https://arxiv.org/abs/2308.10647)
- **Paul D, Chaudhuri BB.** "A BLSTM Network for Printed Bengali OCR System with High Accuracy." arXiv:1908.08674, 2019. **Preprint.** — [arXiv](https://arxiv.org/abs/1908.08674)

### Inferences
- Ma et al. is the natural baseline to cite and contrast. It is the same OCR family, on CPU, with layout rules and physician correction, but it extracts every item generically and is evaluated on real data. The system is a different design point: narrow, safety-first and abstaining.
- A reviewer will ask for at least one test on real documents, because every close paper used one: Ma (153 reports), MedRepBench (1,925 images), RJUA (979 patient photos), Neveditsin (60 annotated real photos), Hsu (955 scans), Folks and Katebi (field photos).
- Three entries (Folks, Katebi, Soeno) read blood pressure from photos or screens. They give comparison points for the system's BP field, reported as MAE in mmHg or as character errors.

### Gaps
- I could not get the dataset sizes or recognition accuracy for Xue 2018 and Xue 2020: the IEEE Xplore page came back empty (it renders in the browser), and the abstracts give only the 99.5% detection recall.
- I could not get numbers for OCR-MRD (paywalled) or MSIE-Net (MDPI returned HTTP 403), so their results are uncharacterised here.
- MedRepBench's ECCV 2026 acceptance rests on the authors' arXiv comment; I did not confirm it in the proceedings.
- I found no peer-reviewed paper that applies LayoutLM (v1–v3) specifically to lab reports; the nearest is MSIE-Net's LayoutXLM variant.

---

## 2. Which papers extract lab test values from photographed or scanned lab reports, and how (OCR + rules, NER/CRF, layout models, VLMs/LLMs)?

### Takeaway
Four families appear. They are (a) OCR followed by hand-written rules, (b) OCR followed by sequence labelling (CRF or BERT), (c) layout-aware transformers (LayoutXLM), and (d) multimodal LLMs or VLMs, either end-to-end or reading OCR text. On real lab reports, rules alone were weaker than CRF (F1 0.78 vs 0.86), and OCR-assisted LLMs beat end-to-end VLMs by about 10–20 points of field recall. Diabetes- or anaemia-specific extraction from report photos was not found as a distinct paper; the closest papers extract all items from general chemistry and CBC reports.

### Cited Findings
- **OCR + rules:** Ma et al.'s regex rule baseline reached P 0.84 / R 0.73 / F1 0.78 on 153 real reports. Their layout rules (line grouping by y-coordinate, header-row regex, multi-column "step detection") feed both the rules and the CRF. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **OCR + rules (table-first):** Xue et al. 2018 segment table areas and text top-down before recognition. — [Xue 2018 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043?fields=title,venue,year,abstract)
- **OCR + CRF:** Ma et al.'s CRF (L-BFGS, elastic-net; lexical, shape and POS features) reached F1 0.86, versus 0.78 for rules. The CRF was preferred over BERT for speed, at 0.78 s per report on CPU. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **OCR + transformer classifier:** Hsu et al. ran Tesseract and then ClinicalBERT on 955 scanned sleep reports: 94.76% document accuracy for AHI and 91.61% for SaO2. Layout-structured input and preprocessing choices both affected end-to-end results. — [Hsu 2022, PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- **Layout transformer:** MSIE-Net uses RVI-LayoutXLM for key-information extraction, a detector for test items in the table body, and coordinate-aggregation post-processing, on Chinese medical examination reports. — [MSIE-Net abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/app14041668?fields=title,venue,year,abstract)
- **OCR + LLM vs end-to-end VLM:** in MedRepBench the best OCR+LLM (DeepSeek-V3) reached 88.83% value recall and 90.75% unit recall, against 72.26% and 78.83% for the best no-OCR VLM (LLaMA-4-Maverick). Removing OCR cut field recall by about 10–20%. — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **The same pattern in RJUA-MedDQA:** ESRA text + GPT-4 scored entity accuracy 0.76, against 0.38 for GPT-4V on the image, although LMMs were more robust to low-quality images. — [RJUA-MedDQA, arXiv HTML](https://arxiv.org/html/2402.14840v1)
- **Custom deep OCR:** Xue et al. 2020 use patch-based detection (99.5% recall) and a recogniser with concatenated shallow and deep features for multilingual text. — [Xue 2020 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ACCESS.2019.2961964?fields=title,venue,year,abstract)
- **Commercial OCR/NLP on scanned clinical reports:** Laique et al. reached 95.8–99.3% variable accuracy against manual extraction. — [Laique 2021, PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/)
- **Values from other photographed medical media:** Folks et al. used perspective and shadow removal, YOLOv8 and DNNs for BP on paper charts (MAE 1.0 / 1.36 mmHg). Katebi et al. used YOLO and a CNN for BP-monitor LCDs (MAE about 1 mmHg). — [Folks 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/); [Katebi 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)

### Inferences
- The system belongs to family (a), but its scope is narrowed to three analytes and it adds safety rules. Narrowing the targets is what makes rules competitive: Ma's rules were scored across all items and all layouts. The system should state this trade-off explicitly.
- The published failure modes match the system's rules closely. Skew-induced line misplacement and multi-column layouts appear in Ma; fine-print numbers and units and nested-table misalignment in MedRepBench; rotation, skew, blur and missing corners, plus reference-range confusion, in RJUA. This can be used to justify each rule (deskewing, orientation detection, row rebuilding, skipping reference ranges).

### Gaps
- I found no peer-reviewed paper on extracting only fasting glucose, haemoglobin or blood pressure from lab-report photos, and none that handles look-alike tests (2-hour or random glucose vs fasting, HbA1c, MCH, haemoglobin electrophoresis fractions) or mmol/L to mg/dL conversion as explicit steps.
- I found no LayoutLM/LayoutLMv3 or Donut study on lab reports (searched, nothing found).

---

## 3. How was accuracy measured (field vs character level, real vs synthetic, damage types), and what numbers were reported?

### Takeaway
The close papers measure on **real** documents. Their metrics range from entity- or field-level P/R/F1 or recall (Ma, MedRepBench), through document accuracy (Hsu) and QA accuracy (RJUA), to character, word and numeric-span accuracy (Neveditsin, Ma's OCR module, Soeno) and MAE in mmHg (Folks, Katebi). Synthetic damage at scale appears only in a non-medical OCR benchmark (Hegghammer). Apart from RJUA's unanswerable-question test, no paper reports abstention, i.e. empty versus wrong.

### Cited Findings
- **Entity level, exact text and category match, real data:** Ma reports CRF F1 0.86 overall and per-entity F1 of 0.87 for LabResult and 0.84 for LabUnit. Their OCR module, scored separately, reached character accuracy 0.95, detection 0.93 and line formation 0.90. The validation set excluded reports with OCR accuracy below 30%. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **Field-level recall over name, value, unit, range and abnormal, real images:** MedRepBench requires an exact normalised name match, fuzzy-matches ranges, and truncates output to the top K. Best OCR+LLM: 96.48 / 88.83 / 90.75 / 92.60 / 89.06. — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)
- **Character and word level plus numeric spans, real photos with rated noise:** in Neveditsin et al., N_acc ranged from 0.674 (PaddleOCR) to 0.950 (Qwen2.5-VL), and CER from 0.189 (Tesseract) to 0.031 (Qwen2.5-VL). The noise types were blur, rotation, illumination and shadow, bleed-through, background texture and compression. — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)
- **QA accuracy on photo quality strata:** RJUA-MedDQA split 979 patient photos into 593 high-quality and 386 low-quality (rotation, skew, blur, missing corners). It reports entity and table accuracy, plus incorrect answers on unanswerable questions (GPT-4V: 54/84 and 35/50). — [RJUA-MedDQA, arXiv HTML](https://arxiv.org/html/2402.14840v1)
- **Document-level accuracy, real scans:** Hsu reports 94.76% (AHI) and 91.61% (SaO2) with AUROC 0.9743 and 0.9523. — [Hsu 2022, PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- **Character error rate, OCR vs human typing:** Soeno reports 0% vs 1.32% (vital signs) and 0.62% vs 1.10% (prescriptions), on 6 simulated pictures. — [Soeno 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/)
- **MAE in mmHg on real photos:** Folks reports 1.0 / 1.36 mmHg (systolic and diastolic); Katebi reports 1.1 / 1.1 and 1 / 0.6 mmHg, against the FDA's 5 mmHg requirement. — [Folks 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/); [Katebi 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- **Synthetic damage at scale (non-medical):** Hegghammer replicated 422 real scans 43 times with artificial noise (18,568 documents). Tesseract degraded most with noise. — [Hegghammer abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)
- **Synthetic training data for a low-resource script:** bbOCR uses two novel synthetic datasets plus a "diversified evaluation dataset" for Bengali document OCR. — [bbOCR, arXiv](https://arxiv.org/abs/2308.10647)

### Inferences
- The system's 99.7% is 350 of 351 fields, and its 73.8% is about 259 of 351. My own calculation of a Wilson 95% interval for 350/351 gives roughly 98.4–99.95%, which the paper should report. The figure cannot be compared directly with Ma's 0.86 F1, MedRepBench's 88.83% value recall or Hsu's 91–95%: those cover broader targets on real documents, while the system's are three analytes on synthetic slips.
- The system's abstention-first design ("the one miss was left empty, not wrong") suits a selective-prediction framing: report coverage, accuracy on answered fields, and the wrong-value rate separately. RJUA's unanswerable-question counts are the closest published analogue and show that a VLM (GPT-4V) does not abstain reliably.
- The nine damage types should be mapped onto the noise categories used by Neveditsin (blur, rotation, shadows, bleed-through, texture, compression) and RJUA (rotation, skew, blur, missing corners), so the coverage is comparable.

### Gaps
- I found no published synthetic lab-slip benchmark with controlled photo damage and field-level scoring. Hegghammer's NOD is the nearest methodological precedent but is not medical.
- None of the close papers reports confidence intervals for field accuracy (not seen in the parts I read).

---

## 4. Which papers compare open-source OCR engines on medical or table-heavy documents, and what are the PP-OCR technical reports?

### Takeaway
The most directly comparable engine study is Neveditsin et al. (EACL 2026). They compare Tesseract, PaddleOCR (PP-OCRv5), docTR, Surya and GOT-OCR with three compact MLLMs on real phone photos of clinical reports. PaddleOCR there had good CER but the *lowest* numeric accuracy (0.674). OCR-MRD compares Tesseract, EasyOCR and docTR with preprocessing on lab reports. Hegghammer and Hsu show how much noise and preprocessing affect Tesseract. The PP-OCR model family is documented in four arXiv technical reports (2020–2025).

### Cited Findings
- Neveditsin et al.: Tesseract 4.1.1, PaddleOCR 3.3.0 (PP-OCRv5), docTR 1.0.0, Surya 0.17.0 and GOT-OCR 2.0, against Qwen2.5-VL-7B, Phi-4-multimodal and InternVL3.5-4B. CER / N_acc: Tesseract 0.189 / 0.756; PaddleOCR 0.111 / 0.674; docTR 0.108 / 0.884; Surya 0.135 / 0.821. PaddleOCR ran CPU-only at 14.14 s per image. Tesseract was most sensitive to blur and shadows, docTR to rotation, Surya to bleed-through. **EasyOCR was not included.** — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)
- OCR-MRD compares Tesseract, EasyOCR and docTR across six preprocessing techniques and their combinations for digitising medical reports. It notes that preprocessing effects for medical reports had not been studied before. — [OCR-MRD abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s41870-023-01610-2?fields=title,venue,year,abstract)
- Hsu et al. evaluated Tesseract with combinations of grey-scaling, dilating, eroding and contrast, and concluded that preprocessing and layout both matter. — [Hsu 2022, PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/)
- Hegghammer: server-based processors (Textract, Document AI) were substantially better than Tesseract, especially on noisy documents; Arabic was less accurate than English. — [Hegghammer abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)
- Ma et al. used PP-OCR (DB detector, direction classifier, CRNN with MobileNetV3) without comparing engines, at 0.78 s per report on CPU. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- **PP-OCR (2020):** a 3.5M-parameter model for 6,622 Chinese characters and a 2.8M model for 63 alphanumeric symbols. Training used about 97K images (detector), 600K (direction classifier) and 17.9M (recogniser). It was also verified on French, Korean, Japanese and German. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2009.09941)
- **PP-OCRv2 (2021):** 7% higher precision than PP-OCR at the same inference cost on real data, comparable to the ResNet-backbone server models. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2109.03144)
- **PP-OCRv3 (2022):** nine upgrades; the recogniser moves from CRNN to SVTR; hmean 5% higher than PP-OCRv2 at comparable speed. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2206.03001)
- **PaddleOCR 3.0 (2025):** PP-OCRv5 (multilingual recognition), PP-StructureV3 (document parsing) and PP-ChatOCRv4 (key-information extraction). Models under 100M parameters are reported as competitive with billion-parameter VLMs. Apache-licensed. — [arXiv API record](http://export.arxiv.org/api/query?id_list=2507.05595)
- Tesseract's canonical description is Smith, ICDAR 2007, vol. 2, pp. 629–633. — [Crossref](https://api.crossref.org/works/10.1109/ICDAR.2007.4376991)

### Inferences
- Neveditsin's low numeric accuracy for PaddleOCR (0.674), despite good CER, is directly relevant. It suggests the system's gain from 73.8% to 99.7% comes largely from post-OCR rules, not from the engine alone. Reporting raw OCR numeric accuracy before the rules would make the paper stronger.
- The authors' own comparison (PaddleOCR, Tesseract, EasyOCR, docTR, Surya) would add something new if published with numbers: no peer-reviewed study I found covers all five on lab reports, and EasyOCR is missing from Neveditsin while PaddleOCR is missing from OCR-MRD.

### Gaps
- I found no peer-reviewed paper describing RapidOCR, EasyOCR, docTR or Surya themselves; they appear to be cited by software repository. I did not verify absence exhaustively.
- I did not verify whether the PP-OCR or RapidOCR models cover Bengali script.
- I did not obtain OCR-MRD's per-engine numbers.

---

## 5. What does the literature say about errors in automated medical data entry, and about the value of human confirmation of extracted values?

### Takeaway
Manual transcription of lab values is itself error-prone (3.7% of point-of-care glucose entries discrepant). OCR prefill can reduce character errors compared with typing (0% vs 1.32% for vital signs in one simulation). Human review of automated output removes most errors but not all: a 7.4% error rate in speech-recognised drafts fell to 0.3% in physician-signed notes. Automation bias is strongest when verification is complex, so the confirmation step must make checking easy.

### Cited Findings
- Mays and Mathias: 260 of 6,930 (3.7%) manually entered point-of-care glucose results differed from the interfaced result. 37 of the 260 (14.2%) were off by more than 20%, including potentially dangerous errors, and another 37 (14.2%) were due to non-numeric characters. Staff-entered result flags deviated from the laboratory system's flag in 5,121 of 6,930 pairs (73.9%). Clinically significant discrepancies occurred at about 5 per 1,000 results. — [Mays 2019, PubMed](https://pubmed.ncbi.nlm.nih.gov/30649499/)
- Soeno et al.: OCR had fewer character errors than manual smartphone typing for vital signs (0/1056 vs 14/1056, p<0.001) and prescriptions (30/4814 vs 53/4814). — [Soeno 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/)
- Zhou et al.: in 217 notes from two organisations, the error rate was 7.4% in speech-recognition drafts, 0.4% after transcriptionist review and 0.3% in physician-signed notes. Of the errors at each stage, 5.7%, 8.9% and 6.4% were clinically significant. The authors conclude that manual editing and review are important. — [Zhou 2018, PubMed](https://pubmed.ncbi.nlm.nih.gov/30370424/)
- Lyell and Coiera: of 890 papers, 40 met the criteria (6 in health care). Automation bias was found in single tasks, typically diagnostic, with **high verification complexity**, contrary to the human-factors view that it needs multitasking. It appears tied to cognitive load, and mitigation should aim at reducing cognitive load. — [Lyell 2017, PubMed](https://pubmed.ncbi.nlm.nih.gov/27516495/)
- Ma et al. note that poor scans and handwritten markups "often require manual correction by physicians" in their deployed web application. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- Even benchmark construction relies on human verification of machine extraction: MedRepBench's OCR + LLM annotations were human-checked, with more than 97% field agreement on a 200-report audit. — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)

### Inferences
- Mays' finding that manual entry is not error-free (3.7%, with 14.2% of errors large) supports the system's claim that prefill plus confirmation can beat typing. Zhou and Lyell and Coiera warn that confirmation is not a guarantee.
- Lyell and Coiera imply a concrete design recommendation: show the source crop or row next to each prefilled value, so checking is a glance rather than a search. The system's abstention (empty fields) also avoids the riskiest case, a confidently wrong value that the reviewer must notice.
- A reviewer may ask for a user study with seeded errors, to measure whether physicians actually catch wrong prefills.

### Gaps
- I found no study that measures how often clinicians catch OCR errors in prefilled lab values (catch rate for seeded errors).
- I found no study of transcription error rates for lab values in Bangladesh or South Asia.

---

## 6. Which work comes from low- and middle-income settings, or covers Bangla or other multilingual medical documents?

### Takeaway
Work on medical documents from low- and middle-income countries exists for Rwanda (anaesthesia charts), Guatemala (BP monitors), India (photos of clinical reports) and Bangladesh (handwritten prescription terms). Lab-report papers mostly come from China and are motivated in part by developing-country needs. No paper reads **Bangla lab reports**; Bangla OCR work covers general printed documents and handwritten medical terms.

### Cited Findings
- Folks et al. digitised smartphone photos of paper anaesthesia charts at the University Teaching Hospital of Kigali. They note that paper records predominate in low- and middle-income countries because automated capture and EMRs cost too much. — [Folks 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/)
- Katebi et al. transcribed BP-monitor photos taken by 49 lay midwives in rural Guatemala, aiming at "low-resource settings". — [Katebi 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- Neveditsin et al. used real smartphone photos of printed obstetric ultrasound reports from India, in "regionally inflected medical English". — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)
- Xue et al. 2018 present lab-report extraction as benefiting "remote healthcare in developing countries", and recognise text with multilingual characters. — [Xue 2018 abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043?fields=title,venue,year,abstract)
- Tabassum et al.: "Ninety-seven percent of Bangladeshi doctors write handwritten prescriptions", and multilingual prescriptions are harder to read. On a 17,431-sample corpus of 480 medical terms, a BiLSTM with rotate-shift-stretch augmentation reached 93.0% average accuracy, 19.6 points above the unaugmented model, for online (smart-pen) recognition. — [Tabassum 2022, PubMed](https://pubmed.ncbi.nlm.nih.gov/35246576/)
- bbOCR is an open-source pipeline for Bengali document OCR (printed and scanned), with a novel Bengali recogniser and synthetic datasets. The authors cite a lack of datasets for word-level OCR, layout extraction and distortion correction in Bengali. — [bbOCR, arXiv](https://arxiv.org/abs/2308.10647)
- Paul and Chaudhuri's printed Bengali and English BLSTM-CTC OCR reached 99.32% character and 96.65% word accuracy across 20 Bengali fonts. They report that Google's Indic OCR sometimes confuses Bengali characters with Assamese ones. — [Paul & Chaudhuri 2019, arXiv](https://arxiv.org/abs/1908.08674)
- PP-OCR was validated on French, Korean, Japanese and German, and PaddleOCR 3.0's PP-OCRv5 targets multilingual recognition. — [arXiv API records](http://export.arxiv.org/api/query?id_list=2009.09941,2507.05595)
- Hegghammer found accuracy considerably lower for Arabic than for English, a reminder that non-Latin scripts degrade OCR. — [Hegghammer abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)

### Inferences
- The system would be among the first lab-report readers framed for Bangladeshi primary care. The untested Bangla and handwriting conditions are exactly where the regional literature (Tabassum, bbOCR) says difficulty lies.

### Gaps
- I found no paper on OCR of lab reports from Bangladesh, nor any dataset of Bangla or bilingual lab slips.
- I found no evaluation of PP-OCR or RapidOCR on Bengali script.

---

## 7. Which papers argue for on-premise or on-device processing of medical images for privacy, compared with cloud APIs?

### Takeaway
The privacy argument appears in three forms. Some studies run open models locally (Neveditsin; Wiest et al. 2024 and 2025). One benchmark leaves cloud models out on privacy and reproducibility grounds (MedRepBench). And the benchmark evidence shows cloud OCR can be more robust to noise (Hegghammer), which is the trade-off the system's optional Claude path brings back.

### Cited Findings
- Neveditsin et al. ran every system on local hardware, with no clinical data or weights leaving the institution and no cloud OCR APIs. They present compact MLLMs as privacy-preserving options for on-premise digitisation, but these needed 16–47 GiB of GPU memory and 11–67 s per image. — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)
- Wiest et al. 2024: a local Llama 2 pipeline found liver cirrhosis with 100% sensitivity and 96% specificity in 500 MIMIC-IV histories, showing local LLMs can extract clinical information "with low hardware requirements". — [Wiest 2024, PubMed](https://pubmed.ncbi.nlm.nih.gov/39304709/)
- Wiest et al. 2025 (LLM-AIx) runs on local hospital infrastructure, "eliminating the need to transfer patient data externally", and was demonstrated on 100 TCGA pathology reports. — [Wiest 2025, PubMed](https://pubmed.ncbi.nlm.nih.gov/40962856/)
- MedRepBench excluded GPT, Gemini and Claude "for reproducibility and privacy". — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)
- Hegghammer: the remote engines (Textract, Document AI) outperformed local Tesseract, especially on noisy documents. — [Hegghammer abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)
- Ma et al.'s CPU-only pipeline (0.78 s per report) shows that lab-report OCR can run without a GPU. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)

### Inferences
- The system's CPU-only, about-1.5 s-per-photo design matches Ma's operating point and is far lighter than the local MLLMs Neveditsin tested. That is a practical advantage for clinic servers in Bangladesh. The optional Claude path needs a stated consent and data-handling policy, because the same literature treats cloud models as a privacy exception.

### Gaps
- I found no paper that measures privacy risk or compares on-device and cloud OCR for medical documents with explicit threat models. The arguments are mostly design rationale.

---

## 8. Which papers use multimodal LLMs (GPT-4V, Gemini, Claude) to read lab reports, and what accuracy and hallucination rates did they report?

### Takeaway
Only one peer-reviewed paper found tests a commercial MLLM on lab-report images. That is RJUA-MedDQA (KDD 2024), where GPT-4V had entity accuracy 0.38 and answered 54 of 84 unanswerable entity questions incorrectly. Open-source VLMs were benchmarked in MedRepBench (preprint) and Neveditsin et al. (EACL 2026). **No peer-reviewed evaluation of Claude or Gemini reading lab reports was found.**

### Cited Findings
- RJUA-MedDQA: GPT-4V scored entity accuracy 0.38, table accuracy 0.47 and clinical multiple-choice accuracy 0.46, against ESRA text + GPT-4 at 0.76, 0.72 and 0.79. On unanswerable questions GPT-4V was wrong on 54 of 84 (entity) and 35 of 50 (table). The authors say hallucination affects all models, with LMMs more severely; GPT-4V also changed decimal places. — [RJUA-MedDQA, arXiv HTML](https://arxiv.org/html/2402.14840v1)
- MedRepBench: the best no-OCR VLM (LLaMA-4-Maverick) reached 72.26% value recall and 75.83% abnormal-flag recall. VLM errors were fine-print numbers and units, table misalignment and missed flags. OCR+LLM errors can propagate into hallucinated abnormal findings. No quantified rate of fabricated fields was reported. — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)
- Neveditsin: the compact MLLMs (Qwen2.5-VL-7B, Phi-4-MM, InternVL3.5-4B) had the best numeric accuracy (0.927–0.950) and lowest CER (0.031–0.040) on real phone photos. Fabricated digits were not reported, but the models sometimes transcribed background text from other documents. — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)

### Inferences
- If the paper mentions the optional Claude reader, a reviewer will expect it to be measured on the same 351-field benchmark, including how often it fills a field that should stay empty (RJUA-style unanswerable cases), because the published hallucination evidence for GPT-4V is poor.

### Gaps
- I found no peer-reviewed study evaluating Claude, Gemini or GPT-4o on photographed or scanned lab reports. Searches turned up only general medical-VQA studies, blogs and vendor benchmarks, which I excluded.
- I found no hallucination rate per lab value for any commercial MLLM.

---

## 9. Which venues publish this work?

### Takeaway
The work is spread across medical-informatics journals (BMC MIDM, JAMIA, JAMIA Open, npj Digital Medicine, PLOS Digital Health), general and engineering journals (IEEE Access, Applied Sciences, Int J Inf Technol, PLOS ONE, Scientific Reports, BMC Bioinformatics), clinical journals (Gastrointestinal Endoscopy, JAMA Network Open), and CS conferences (KDD, EACL, IEEE DASC; ECCV per one preprint). OCR model reports are arXiv technical reports.

### Cited Findings
- BMC Medical Informatics and Decision Making: Ma 2023 — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- IEEE Access: Xue 2020 — [Crossref](https://api.crossref.org/works/10.1109/ACCESS.2019.2961964). IEEE DASC/PiCom/DataCom/CyberSciTech 2018 (conference): Xue 2018 — [S2 record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/DASC/PiCom/DataCom/CyberSciTec.2018.00043?fields=title,venue,year,abstract)
- ACM SIGKDD 2024: RJUA-MedDQA — [DOI](https://doi.org/10.1145/3637528.3671644)
- EACL 2026 Industry Track (ACL Anthology): Neveditsin — [ACL Anthology PDF](https://aclanthology.org/2026.eacl-industry.4.pdf)
- arXiv (preprint; authors claim ECCV 2026): MedRepBench — [arXiv API record](http://export.arxiv.org/api/query?id_list=2508.16674)
- International Journal of Information Technology (Springer): OCR-MRD — [Crossref](https://api.crossref.org/works/10.1007/s41870-023-01610-2)
- Applied Sciences (MDPI): MSIE-Net — [Crossref](https://api.crossref.org/works/10.3390/app14041668)
- JAMIA Open: Hsu 2022 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35702624/). JAMIA: Mays 2019 and Lyell 2017 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/30649499/); [PubMed](https://pubmed.ncbi.nlm.nih.gov/27516495/)
- PLOS ONE: Soeno 2024 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38241403/). PLOS Digital Health: Katebi 2024 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39356720/)
- BMC Bioinformatics: Folks 2024 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38714921/). Gastrointestinal Endoscopy: Laique 2021 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/32891620/)
- JAMA Network Open: Zhou 2018 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/30370424/). npj Digital Medicine and npj Precision Oncology: Wiest 2024 and 2025 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39304709/); [PubMed](https://pubmed.ncbi.nlm.nih.gov/40962856/)
- Scientific Reports: Tabassum 2022 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35246576/). Journal of Computational Social Science: Hegghammer — [Crossref](https://api.crossref.org/works/10.1007/s42001-021-00149-1)
- ICDAR 2007: Tesseract — [Crossref](https://api.crossref.org/works/10.1109/ICDAR.2007.4376991). arXiv technical reports: PP-OCR v1–v3 and PaddleOCR 3.0 — [arXiv API records](http://export.arxiv.org/api/query?id_list=2009.09941,2109.03144,2206.03001,2507.05595)

### Inferences
- Good targets for the system's paper are JMIR Medical Informatics, BMC MIDM, JAMIA Open or PLOS Digital Health, where applied, safety-focused pipelines with modest benchmarks appear. CS venues (KDD, EACL Industry, ECCV) publish benchmark-scale or model-comparison work.

### Gaps
- I found no lab-report OCR paper in ICDAR or in JMIR Medical Informatics in this search. That does not prove none exists.

---

## 10. Synthesis: how does the system compare with the literature, what does it add, and what would a reviewer criticise?

### Takeaway
The system is a modern, safety-first instance of the "OCR + rules" approach. It uses the same PP-OCR family and the same CPU-only operating point as the closest paper (Ma 2023). It adds targeted extraction for three analytes, look-alike exclusion, unit conversion, plausibility rejection, abstention, a PDF text-layer path, mandatory physician confirmation, and a reproducible field-level benchmark with controlled damage. Its main weakness against the literature is evidence: every close paper evaluated on real documents, while the system has only synthetic slips, three analytes and 351 fields.

### Cited Findings
- On real documents, Ma's generic rules reached F1 0.78 and the CRF 0.86 at 0.78 s per report on CPU. The main errors were scan quality, skew and multi-column layouts. — [Ma 2023, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10629084/)
- OCR-assisted pipelines beat end-to-end VLMs on field recall by about 10–20 points, but depend on OCR quality. — [MedRepBench, arXiv HTML](https://arxiv.org/html/2508.16674v2)
- On real Indian phone photos, PaddleOCR (PP-OCRv5) had CER 0.111 but numeric accuracy only 0.674; compact MLLMs reached 0.95 at 11–67 s per image on an A100. — [Neveditsin, arXiv HTML](https://arxiv.org/html/2511.13523v1)
- GPT-4V answered most unanswerable entity questions on report images incorrectly (54/84). — [RJUA-MedDQA, arXiv HTML](https://arxiv.org/html/2402.14840v1)
- Manual entry errors run at about 3.7%, with about 5 per 1,000 clinically significant. Human review cut automated-documentation errors from 7.4% to 0.3%, and automation bias rises with verification complexity. — [Mays 2019, PubMed](https://pubmed.ncbi.nlm.nih.gov/30649499/); [Zhou 2018, PubMed](https://pubmed.ncbi.nlm.nih.gov/30370424/); [Lyell 2017, PubMed](https://pubmed.ncbi.nlm.nih.gov/27516495/)
- Synthetic noise benchmarks are an accepted OCR evaluation method (Hegghammer's NOD). — [Hegghammer abstract](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s42001-021-00149-1?fields=title,venue,year,abstract)

### Inferences
**What the system adds (relative to the papers reviewed here):**
1. **Safety-oriented extraction rules.** It skips look-alike tests (2-hour and random glucose, HbA1c, MCH, reference ranges, haemoglobin electrophoresis fractions), converts mmol/L to mg/dL, rejects impossible values, and leaves a field empty rather than guess. None of the reviewed lab-report papers describes these steps. RJUA's reference-range confusion and MedRepBench's unit and number errors are exactly the failures these rules target.
2. **Abstention as a design goal, with physician confirmation before scoring.** It turns "empty, not wrong" into a measurable property. The literature measures recall or F1, but not the wrong-value rate separately from abstention.
3. **A reproducible synthetic benchmark with controlled damage for lab slips:** five layouts, three fonts and nine damage types, scored per field. This applies Hegghammer's noise-replication idea to medical forms, which I found no precedent for.
4. **An operating point.** CPU-only, about 1.5 s per photo, images never leave the clinic. That is comparable to Ma (0.78 s, CPU) and far lighter than local MLLMs (Neveditsin). Text-layer PDFs are read directly, avoiding OCR error entirely; I did not see this path discussed in the close papers.
5. **The setting.** No lab-report OCR paper from Bangladesh was found. The regional literature covers prescriptions and general Bengali OCR (Tabassum, bbOCR).

**What a reviewer would criticise:**
1. **Synthetic slips only.** Every close paper used real documents (Ma, MedRepBench, RJUA, Neveditsin, Hsu, Folks, Katebi). Real phone photos, Bangla text and handwriting are all untested, and Tabassum shows handwriting dominates Bangladeshi prescriptions.
2. **Possible overfitting to the generator.** If the rules were developed against the same 351-field benchmark that shows the gain from 73.8% to 99.7%, that is a development-set result. Reviewers will want held-out layouts, fonts or damage types, or a separate real set.
3. **Narrow scope and small n.** Three analytes and 351 fields, against Ma's 8,442 entities and MedRepBench's 1,925 images. By my calculation, 350/351 has a Wilson 95% CI of about 98.4–99.95%, which should be reported.
4. **No baselines on the same benchmark.** The engine comparison (PaddleOCR, Tesseract, EasyOCR, docTR, Surya) should be published with numbers. A learned extractor (CRF, as in Ma) or a compact VLM (as in Neveditsin), plus the optional Claude path, should be scored on the same fields, including false fills on fields that should stay empty.
5. **Human confirmation is asserted, not tested.** Given automation bias (Lyell and Coiera) and residual post-review errors (Zhou, 0.3%), a seeded-error study measuring physician catch rates would be expected, as would an interface that keeps verification simple, such as showing the source crop.
6. **Metric framing.** Report coverage (fields filled), accuracy on filled fields and wrong-value rate separately, by damage type. Raw OCR numeric accuracy before the rules would show where the gain comes from, given PaddleOCR's low N_acc in Neveditsin.
7. **Privacy inconsistency.** The optional cloud LLM path cuts against the on-premise argument that MedRepBench, Neveditsin and Wiest make. The paper should state when it is used, with what consent, and whether images are de-identified first.

### Gaps
- I could not find a direct published comparison between a rule-based targeted extractor and LLM or VLM extractors for specific analytes (glucose, haemoglobin, BP) on the same lab-report images, so the claim that targeted rules are competitive is untested in the literature.
- I found no real-world dataset of lab slips from Bangladesh that the system could be validated against. Building one, even 50–100 consented real photos, appears to be the single most valuable addition.
