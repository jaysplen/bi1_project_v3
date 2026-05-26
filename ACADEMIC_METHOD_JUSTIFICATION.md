# Academic Method Justification — VacuTech W1 / W2 / W3

This document supports the **DLMDSEBA02** presentation and tutor review. It maps each CRM-aligned work package (W pain point) to the **methods actually implemented** in [`bi_pipeline.py`](bi_pipeline.py) and the CRISP-DM notebooks, and cites **peer-reviewed and arXiv literature** to justify those choices.

The project deliberately uses **one transparent algorithm per work package** with fixed, documented hyperparameters—not because they are state-of-the-art in accuracy, but because they are **scientifically established**, **auditable for stakeholders**, and **appropriate for operational decision support**.

---

## 1. Introduction

**VacuTech** (Phase 2 analytics) addresses three business questions:

| Work package | Pain point | Stakeholder | Method in codebase |
|--------------|------------|-------------|-------------------|
| **W1** | Which PM add-on parts should we pre-stock or bundle? | Spare-parts planner | Apriori association rules + Pareto demand concentration |
| **W2** | How long will this repair take at intake? | Service planner | Decision Tree regression |
| **W3** | Which jobs are likely to fail QA before release? | QA supervisor | Decision Tree classification + fixed probability threshold |

Each question is developed in a dedicated notebook (`notebooks/W1_Inventory.ipynb`, `W2_Repair_Duration.ipynb`, `W3_QA_Failure_Risk.ipynb`) following the same five CRISP-DM phases: Business Understanding → Data Understanding → Data Preparation → Modeling + Evaluation → Conclusion / implications. Full business narrative: [`PROJECT_HANDBOOK.md`](PROJECT_HANDBOOK.md).

---

## 2. Cross-cutting methodology — CRISP-DM

### 2.1 Pain point

Analytics must be **reproducible**, **documented**, and **separated from tooling hype**—suitable for academic assessment and operational handover.

### 2.2 Method

Structured data-mining lifecycle (CRISP-DM), mirrored in notebook section headings.

### 2.3 Scientific justification

**[1] Shearer, C. (2000).** *The CRISP-DM model: The new blueprint for data mining.* Journal of Data Warehousing, 5(4), 13–22.  
Shearer introduced CRISP-DM as an industry-neutral process model that separates business understanding from data preparation and modeling. VacuTech notebooks follow this structure so each W can be assessed on both **business fit** and **technical correctness**, not only on model metrics.

**[2] CRISP-DM Consortium (2000).** *CRISP-DM 1.0.*  
The official guide defines six phases (including deployment and evaluation) and emphasises iterative refinement. Using CRISP-DM aligns the project with a **de facto standard** cited across data-mining curricula and practice, which tutors expect when asking for justified analytical process—not ad hoc notebook cells.

**[14] Ngai, E. W. T., Xiu, L., & Chau, D. C. K. (2009).** *Application of data mining techniques in customer relationship management: A literature review and classification.* Expert Systems with Applications, 36(2), 2592–2602.  
[DOI](https://doi.org/10.1016/j.eswa.2008.02.021)

Ngai et al. systematically map CRM tasks (customer identification, attraction, retention, development) to the families of data-mining techniques typically applied to each: clustering and classification for identification, classification and association rules for attraction and retention, association rules and regression for development. This reference anchors the **CRM-task → algorithm** narrative on slide 2 of the presentation and justifies why VacuTech’s three work packages naturally land in *customer retention* (W2, W3) and *customer development* (W1).

### 2.4 Limitations

CRISP-DM describes *process*, not algorithm choice; W-specific methods below complete the scientific argument.

---

## 3. W1 — Inventory optimisation (Apriori + Pareto)

### 3.1 Pain point

During preventive maintenance (PM), technicians often consume **add-on parts** not in the standard kit, causing delays and extra visits. The planner needs (a) **bundle rules** (`A → B`) and (b) a **short SKU list** covering most add-on demand.

### 3.2 Method and implementation

| Element | Implementation |
|---------|----------------|
| Data | PM cases (`maintenance_kit_applied == 1`); add-on lines (`kit_part_flag == 0`); boolean basket matrix (case × part) |
| Algorithm | Apriori + association rules (`mlxtend`) |
| Rule filter | `min_support = 0.05`, `min_lift = 1.2` |
| Complement | Pareto analysis on part frequency (80% / 90% coverage SKUs) |
| Code | `run_w1()` in [`bi_pipeline.py`](bi_pipeline.py); notebook cells 7–13 in `W1_Inventory.ipynb` |

### 3.3 Scientific justification

**[3] Agrawal, R., & Srikant, R. (1994).** *Fast algorithms for mining association rules in large databases.* Proceedings of the 20th International Conference on Very Large Data Bases (VLDB), 487–499.  
[PDF](https://snap.stanford.edu/class/cs224w-readings/Agrawal94AssosiationRule.pdf)

Agrawal and Srikant formalised association-rule mining on transactional data and introduced the **Apriori** level-wise search with pruning. W1 treats each PM visit as a transaction and each add-on part as an item—the same **market-basket** abstraction the paper was designed for. This is the canonical academic basis for choosing Apriori over ad hoc co-occurrence counts.

**[4] Brin, S., Motwani, R., Ullman, J. D., & Tsur, S. (1997).** *Dynamic itemset counting and implication rules for market basket data.* Proceedings of ACM SIGMOD, 255–276.  
[ACM Digital Library](https://dl.acm.org/doi/10.1145/253260.253325)

Brin et al. established the **support–confidence** framework for interestingness of rules. VacuTech’s `min_support = 0.05` suppresses ultra-rare itemsets (noise at ~500 PM baskets); ranking and filtering by **lift** (`min_lift = 1.2`) follows standard practice of requiring co-occurrence **stronger than independence**—a measure widely discussed in the association-rule literature following this work.

**[5] Mündler, N. (2019).** *Association rule mining and itemset-correlation based variants.* arXiv:1907.09535.  
[arXiv](https://arxiv.org/abs/1907.09535) · [PDF](https://arxiv.org/pdf/1907.09535)

This survey reiterates the Apriori foundation, the role of minimum support/confidence, and **downward closure** for efficient pruning. It supports presenting W1 as part of a well-documented research line (not a bespoke script), and justifies reporting **support, confidence, and lift** together so planners can audit rules.

**[6] Wang, J., Pan, X., Wang, L., & Wei, W. (2018).** *Method of spare parts prediction models evaluation based on grey comprehensive correlation degree and association rules mining: A case study in aviation.* Mathematical Problems in Engineering, 2018, Article 2643405.  
[DOI](https://doi.org/10.1155/2018/2643405)

Wang et al. apply **association rule mining** in an **aviation spare-parts** context to relate part types to prediction models and improve inventory decisions. Although their outcome differs from VacuTech’s bundle rules, the paper demonstrates that ARM is an accepted method in **maintenance spare-parts** domains—not only retail. It bridges the gap between textbook market-basket examples and VacuTech’s workshop baskets.

**[7] Didriksen, S. K., Sigsgaard, K. W., Mortensen, N. H., & Jespersen, C. B. (2026).** *Assigning spare parts management decision-making strategies: A holistic portfolio classification methodology.* Applied Sciences, 16(4), 1961.  
[DOI](https://doi.org/10.3390/app16041961) · [Open access](https://www.mdpi.com/2076-3417/16/4/1961)

Recent spare-parts research emphasises **portfolio classification** and concentrated demand among a subset of SKUs (related to ABC/Pareto thinking). VacuTech’s Pareto chart (~21 parts ≈ 80% of PM add-on demand) implements the **80/20 inventory principle** in parallel with Apriori: rules suggest *what to bundle*; Pareto suggests *what to stock first*. Together they answer the planner’s two decisions without a black-box forecast.

### 3.4 Limitations

- Apriori finds **frequent** co-occurrence, not causation; rules must be validated with engineering knowledge.
- Support/lift thresholds are **set by reasoning**, not automated search—appropriate for transparency, not for maximising rule count.
- Pareto is **descriptive** on historical demand; it does not model lead times or costs.

---

## 4. W2 — Repair-duration prediction (Decision Tree regression)

### 4.1 Pain point

At **intake**, the service planner must give a credible repair window. The model must use only **leakage-safe** features (no QA or post-repair fields) and remain **explainable** to front-desk staff.

### 4.2 Method and implementation

| Element | Implementation |
|---------|----------------|
| Target | `repair_duration_days` |
| Features | Numeric: `pump_age_years`, `technician_experience_years`, `parts_cost_eur`; categorical (one-hot): `pump_model`, `complexity_class`, `failure_type`, `parts_from_hq_flag`, `region` |
| Algorithm | `DecisionTreeRegressor` |
| Hyperparameters | `max_depth=6`, `min_samples_leaf=20`, `random_state=7` |
| Split | 80/20 `train_test_split`, `random_state=7` |
| Metrics | R², MAE, RMSE on held-out test set |
| Code | `run_w2()`; `W2_Repair_Duration.ipynb` |

### 4.3 Scientific justification

**[8] Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984).** *Classification and regression trees.* Chapman & Hall.  
[Taylor & Francis](https://www.taylorfrancis.com/books/mono/10.1201/9781315139470/classification-regression-trees-leo-breiman-jerome-friedman-olshen-charles-stone)

The CART monograph defines **binary recursive partitioning** for both classification and regression, with pruning and honest estimation. scikit-learn’s `DecisionTreeRegressor` implements this paradigm. VacuTech’s `max_depth=6` and `min_samples_leaf=20` are **complexity controls** in the spirit of CART: limit tree depth and ensure each leaf aggregates enough cases to reduce variance on ~1,400 training rows.

**[9] Rudin, C. (2019).** *Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead.* Nature Machine Intelligence, 1, 206–215.  
[arXiv:1811.10154](https://arxiv.org/abs/1811.10154) · [DOI](https://doi.org/10.1038/s42256-019-0048-x)

Rudin argues that for **high-stakes** decisions (healthcare, justice, and by extension **customer-facing service promises**), organisations should prefer **inherently interpretable** models over post-hoc explanations of opaque models. Repair-duration estimates affect customer trust; a shallow tree whose splits can be stated in plain language aligns with this principle. This justifies W2’s choice of a single tree over, e.g., a neural network with SHAP plots.

**[10] Jang, J., Nana, D., Hochschild, J., & de Lorenzo, J. V. H. (2021).** *Predicting breakdown risk based on historical maintenance data for Air Force ground vehicles.* arXiv:2112.13922.  
[arXiv](https://arxiv.org/abs/2112.13922)

Jang et al. model **maintenance outcomes** from historical vehicle repair records (logistic regression, random forest, gradient boosting). The domain—**operational maintenance logs**—is analogous to VacuTech’s `repairs.csv`. The paper supports feasibility of supervised learning on such data; VacuTech opts for a **more interpretable** tree instead of their best-performing logistic model, trading a small accuracy gain for explainability (consistent with [9]).

**[11] Ding, Y., Gao, A., Ryden, T., Mitra, K., Kalmanje, S., Golany, Y., Carbin, M., & Hoffmann, H. (2022).** *Acela: Predictable datacenter-level maintenance job scheduling.* arXiv:2212.05155.  
[arXiv](https://arxiv.org/abs/2212.05155) · [PDF](https://arxiv.org/pdf/2212.05155)

Acela predicts **maintenance job duration** and stresses that **prediction error has asymmetric operational cost** (under-estimating duration is worse than over-estimating). VacuTech evaluates W2 with **MAE and RMSE** and recommends publishing ETAs as **ranges** in the handbook—consistent with treating duration as an operational KPI where error matters, even though VacuTech uses a standard regression tree rather than quantile regression.

### 4.4 Limitations

- A single shallow tree is **not** guaranteed to beat ensembles (random forest, gradient boosting) on R².
- Residual spread at intake reflects **unobserved heterogeneity** (workshop conditions, parts delays).
- No explicit **uncertainty quantification** (prediction intervals) in the current pipeline.

---

## 5. W3 — QA-failure risk (Decision Tree classification)

### 5.1 Pain point

Before QA sign-off, operations wants a **binary flag** for jobs that merit extra inspection—without a complex probability UI. The target `qa_failed_flag` is **imbalanced** (~15% failures).

### 5.2 Method and implementation

| Element | Implementation |
|---------|----------------|
| Target | `qa_failed_flag` (binary) |
| Features | Numeric: `pump_age_years`, `technician_experience_years`, `parts_cost_eur`, `repair_duration_days`; categorical: `pump_model`, `complexity_class`, `failure_type`, `parts_from_hq_flag` |
| Algorithm | `DecisionTreeClassifier` |
| Hyperparameters | `max_depth=6`, `min_samples_leaf=20`, `random_state=7` |
| Operating point | `threshold = 0.30` on `predict_proba` |
| Split | 80/20 stratified on target |
| Metrics | Confusion matrix, recall, precision, accuracy |
| Code | `run_w3()`; `W3_QA_Failure_Risk.ipynb` |

> **Note:** Including `repair_duration_days` scores jobs **at end of repair, before QA** (see handbook §8). For intake-only triage, that feature should be omitted—a scope limitation to state in the presentation.

### 5.3 Scientific justification

**[8] Breiman et al. (1984)** — see W2.  
Classification trees handle **binary outcomes** with the same interpretable split structure. Using identical depth and leaf constraints as W2 keeps the three work packages **methodologically comparable** for teaching and audit.

**[9] Rudin (2019)** — see W2.  
QA triage can trigger rework, cost, and customer impact. A flag that supervisors cannot interrogate is weak governance; tree splits on complexity, technician experience, and parts sourcing mirror **explicit operational hypotheses** testable in discussion with domain experts.

**[12] Zhang, Y., Gao, Z., Sun, J., & Liu, L. (2023).** *Machine-learning algorithms for process condition data-based inclusion prediction in continuous-casting process: A case study.* Sensors, 23(15), 6719.  
[DOI](https://doi.org/10.3390/s23156719)

Zhang et al. study **defect / inclusion prediction** in manufacturing with **imbalanced** process data, comparing several classifiers and stressing that **accuracy alone is misleading** when defects are rare. VacuTech reports **recall and precision** for the failure class at a fixed threshold—aligned with quality-control practice for rare events rather than optimising accuracy only.

**[13] Sonawani, S., & Mukhopadhyay, D. (2013).** *A decision tree approach to classify web services using quality parameters.* arXiv:1311.6240.  
[arXiv](https://arxiv.org/abs/1311.6240)

Sonawani and Mukhopadhyay use **decision trees to rank and classify entities by quality dimensions**, explicitly noting trees are **easy to interpret** and do not require long training. The application domain differs (web services), but the logic matches W3: multiple **quality-related attributes** → transparent classification for selection/triage.

### 5.4 Limitations

- Fixed **threshold 0.30** is a governance choice, not learned from cost matrices; recall/precision can be shifted by operations.
- Shallow trees **under-capture** rare failure patterns compared to boosted models or resampling (SMOTE, etc.).
- End-of-repair features limit transfer to **intake-time** QA risk scoring unless the feature set is reduced.

---

## 6. Synthesis

| Pain point | Method | Key academic anchors | Operational takeaway |
|------------|--------|----------------------|----------------------|
| W1 — PM add-on stocking | Apriori + Pareto | [3], [4], [6], [7] | Bundle rules from lift-ranked associations; stock Pareto-head SKUs regionally |
| W2 — Repair ETA at intake | Shallow CART regression | [8], [9], [10], [11] | Publish duration as a **range**; use importances for routing, not as causal proof |
| W3 — Pre-QA triage | Shallow CART + threshold 0.30 | [8], [9], [12], [13] | Binary flag for senior review; monitor recall/precision weekly |

**Shared design principle ([9]):** Prefer **interpretable** models when stakeholders must act on outputs (stocking, customer promise, QA gate)—consistent with VacuTech’s one-algorithm-per-W architecture.

---

## 7. References

1. Shearer, C. (2000). The CRISP-DM model: The new blueprint for data mining. *Journal of Data Warehousing*, 5(4), 13–22. https://www.taylorfrancis.com/chapters/mono/10.1201/b12040-8/process-model-data-mining%E2%80%94crisp-dm-daniel-putler-robert-krider

2. CRISP-DM Consortium. (2000). *CRISP-DM 1.0: Step-by-step data mining guide.* https://www.kde.cs.uni-kassel.de/wp-content/uploads/lehre/ws2015-16/kdd/files/CRISPWP-0800.pdf

3. Agrawal, R., & Srikant, R. (1994). Fast algorithms for mining association rules in large databases. In *Proceedings of VLDB '94* (pp. 487–499). https://snap.stanford.edu/class/cs224w-readings/Agrawal94AssosiationRule.pdf

4. Brin, S., Motwani, R., Ullman, J. D., & Tsur, S. (1997). Dynamic itemset counting and implication rules for market basket data. In *Proceedings of ACM SIGMOD '97* (pp. 255–276). https://dl.acm.org/doi/10.1145/253260.253325

5. Mündler, N. (2019). Association rule mining and itemset-correlation based variants. *arXiv:1907.09535*. https://arxiv.org/abs/1907.09535

6. Wang, J., Pan, X., Wang, L., & Wei, W. (2018). Method of spare parts prediction models evaluation based on grey comprehensive correlation degree and association rules mining: A case study in aviation. *Mathematical Problems in Engineering*, 2018, 2643405. https://doi.org/10.1155/2018/2643405

7. Didriksen, S. K., Sigsgaard, K. W., Mortensen, N. H., & Jespersen, C. B. (2026). Assigning spare parts management decision-making strategies: A holistic portfolio classification methodology. *Applied Sciences*, 16(4), 1961. https://doi.org/10.3390/app16041961

8. Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984). *Classification and regression trees*. Chapman & Hall. https://www.taylorfrancis.com/books/mono/10.1201/9781315139470/classification-regression-trees-leo-breiman-jerome-friedman-olshen-charles-stone

9. Rudin, C. (2019). Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. *Nature Machine Intelligence*, 1, 206–215. https://arxiv.org/abs/1811.10154 · https://doi.org/10.1038/s42256-019-0048-x

10. Jang, J., Nana, D., Hochschild, J., & de Lorenzo, J. V. H. (2021). Predicting breakdown risk based on historical maintenance data for Air Force ground vehicles. *arXiv:2112.13922*. https://arxiv.org/abs/2112.13922

11. Ding, Y., Gao, A., Ryden, T., Mitra, K., Kalmanje, S., Golany, Y., Carbin, M., & Hoffmann, H. (2022). Acela: Predictable datacenter-level maintenance job scheduling. *arXiv:2212.05155*. https://arxiv.org/abs/2212.05155

12. Zhang, Y., Gao, Z., Sun, J., & Liu, L. (2023). Machine-learning algorithms for process condition data-based inclusion prediction in continuous-casting process: A case study. *Sensors*, 23(15), 6719. https://doi.org/10.3390/s23156719

13. Sonawani, S., & Mukhopadhyay, D. (2013). A decision tree approach to classify web services using quality parameters. *arXiv:1311.6240*. https://arxiv.org/abs/1311.6240

14. Ngai, E. W. T., Xiu, L., & Chau, D. C. K. (2009). Application of data mining techniques in customer relationship management: A literature review and classification. *Expert Systems with Applications*, 36(2), 2592–2602. https://doi.org/10.1016/j.eswa.2008.02.021

---

*Document version: aligned with `bi_pipeline.py` hyperparameters as of project delivery. For business interpretation of results, see [`PROJECT_HANDBOOK.md`](PROJECT_HANDBOOK.md).*
