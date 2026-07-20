---
title: "Assignment 4: Exploring Climate Policy with MIMOSA"
course: "Systems Thinking, Scenarios and Indicators for Sustainable Development (GEO4-2331)"
academic_year: "[20XX-20XX]"
status: "First discussion draft"
version: "0.1"
---

# Assignment 4: Exploring Climate Policy with MIMOSA

## A quantitative research project using an Integrated Assessment Model

> **Draft status**
>
> This is a first discussion draft. Dates, presentation length, word limits, grading weights, topic availability, model settings, and technical instructions still need to be confirmed. Text in square brackets is an instructor placeholder.

## 1. Introduction

Climate change is a complex systems problem. Emissions, technological change, economic development, climate impacts, adaptation, international cooperation, inequality, and ethical choices interact across regions and over long periods. Integrated Assessment Models (IAMs) provide simplified quantitative representations of some of these interactions. They are used to explore scenarios, compare policy strategies, estimate climate damages and mitigation costs, and investigate the consequences of alternative assumptions.

In this assignment, your group will work directly with **MIMOSA**, an open-source regional cost-benefit IAM developed at Utrecht University. The course version of MIMOSA represents 26 world regions and connects socioeconomic development, CO2 emissions, mitigation, temperature change, sea-level rise, sectoral climate impacts, adaptation, economic development, and welfare. It also includes alternative approaches to effort sharing, inequality, emissions trading, and international financial transfers.

MIMOSA does not predict what will happen. Nor does an optimized model result identify an objectively correct policy. Every result is conditional on the model structure, input data, parameter values, objective, and ethical assumptions. Your task is therefore not simply to run the model. You will use it as a scientific experiment: formulate a focused question, design transparent scenario comparisons, interpret causal mechanisms, test uncertainty, and critically assess what the model includes and excludes.

The assignment integrates the four central themes of the course:

1. systems thinking and complex social-environmental systems;
2. agency and decision-making;
3. scenario development and analysis;
4. indicators and quantitative evaluation of sustainable development.

The final results will be communicated in a scientific paper and an oral presentation.

## 2. Assignment goals

After completing this assignment, you will be able to:

- explain the main causal structure, feedbacks, assumptions, and limitations of a cost-benefit IAM;
- distinguish between simulation, optimization, scenario analysis, sensitivity analysis, and robustness analysis;
- formulate a focused and feasible quantitative research question that can be investigated with MIMOSA;
- design and execute a transparent set of model experiments;
- interpret global, regional, sectoral, physical, economic, and welfare outcomes;
- assess how scientific uncertainty and normative assumptions affect model results;
- evaluate what an "optimal" model outcome means and what it does not mean;
- identify important processes, values, groups, or impacts that are omitted or simplified;
- generate usable knowledge for climate and sustainable-development decision-making;
- communicate quantitative research in oral, written, and reproducible forms.

## 3. Organization and expected workload

The assignment is completed in self-organized groups of **four or five students** over approximately five weeks. Scheduled tutorials take place twice per week. Attendance at the tutorials is mandatory [confirm]. Substantial group work outside the tutorials is also expected.

Groups are encouraged to include students with different disciplinary backgrounds. Programming experience is not required for the core assignment. You will receive a prepared Jupyter or Google Colab environment with model-running, data-processing, and plotting functions. The principal assessed skills are research design, quantitative reasoning, systems interpretation, and critical evaluation - not Python syntax.

### Provisional timetable

| Moment | Activity or deliverable |
|---|---|
| Week 1, tutorial 1 | Assignment introduction and guided MIMOSA exercise |
| Week 1, tutorial 2 | Form groups, explore topics, and reproduce reference scenarios |
| End of week 1 | Submit group composition and provisional topic choice |
| Week 2, tutorial 1 | Research questions, literature, and system diagram workshop |
| Week 2, tutorial 2 | Scenario design and pilot runs |
| End of week 2 | Submit research proposal and experiment plan |
| Week 3 | Conduct experiments; advisor feedback on proposal and pilot results |
| Week 4 | Sensitivity, robustness, regional comparison, and critical analysis |
| Week 5, tutorial 1 | Results clinic and reproducibility check |
| Week 5, tutorial 2 | Presentation practice and peer feedback |
| Final course week | Oral presentations |
| [Date and time] | Submit paper and reproducibility package |

## 4. Assessment and deliverables

The provisional assessment follows the structure of the previous research assignment:

1. **Oral presentation: 25%** of the assignment grade.
2. **Scientific paper and reproducibility package: 75%** of the assignment grade.
3. The assignment contributes **[30%]** to the overall course grade.

The research proposal is a compulsory formative deliverable. It is not graded separately [confirm], but groups must receive approval for a feasible experiment plan before continuing.

### Final deliverables

Each group submits:

1. a scientific paper of no more than **[3,500-4,000] words**;
2. presentation slides;
3. the completed course notebook or analysis notebook;
4. a folder containing the model output and parameter files used in the paper;
5. a short `README` explaining how the reported results can be reproduced;
6. a group contribution statement.

Word counts exclude the abstract, figures, tables, references, appendices, and contribution statement.

## 5. Working with MIMOSA

Use the companion [student technical guide](technical_guides/Running_MIMOSA_for_Assignment_4.md) for the course environment, verified ACCREU scenario templates, output handling, validation checks, and troubleshooting.

### 5.1 What MIMOSA does

The course version of MIMOSA connects:

- SSP population, GDP, and baseline CO2 emissions;
- regional mitigation and aggregate mitigation costs;
- technological learning in mitigation costs;
- cumulative CO2 emissions and global mean temperature;
- sea-level rise;
- regional climate impacts on labour productivity, riverine flooding, sea-level rise, and heat- and cold-related mortality;
- sectoral adaptation expenditure, effectiveness, avoided damages, and residual damages;
- capital, GDP, consumption, and welfare;
- alternative welfare formulations, discounting, and inequality aversion;
- effort-sharing regimes, emissions trading, and financial transfers.

### 5.2 Simulation and optimization

MIMOSA can be used in two different modes.

| | Simulation | Optimization |
|---|---|---|
| Policy choices | Supplied by the user | Chosen by the model |
| Model equations | Evaluated | Evaluated |
| Objective and policy constraints | Not automatically enforced | Used by the optimizer |
| Main purpose | Explore a prescribed scenario or stress-test a policy | Find the best pathway according to a specified objective |

In simulation mode, you may prescribe mitigation and, depending on the selected model structure, adaptation expenditure. In optimization mode, MIMOSA can choose these pathways to maximize discounted welfare or minimize costs, possibly subject to a carbon budget, temperature ceiling, or effort-sharing rule.

An optimized pathway is not synonymous with a recommendation. You must always identify:

- what the model optimized;
- which outcomes were included in the objective;
- which constraints were imposed;
- whose welfare was represented and how it was aggregated;
- which impacts and decision-making barriers were omitted.

### 5.3 Required reference experiments

All groups begin with a guided common exercise. Unless an alternative is approved, your analysis must include the following reference cases:

1. **No-policy reference:** no additional mitigation and no additional adaptation.
2. **Reference CBA:** MIMOSA jointly chooses mitigation and adaptation under the course default assumptions.
3. **Topic-specific counterfactuals:** at least three carefully selected alternatives that isolate the mechanism in your research question.
4. **Sensitivity or uncertainty cases:** vary at least two uncertain or normative assumptions over defensible ranges.
5. **Robustness test:** evaluate at least one policy under assumptions different from those under which it was designed.

Your group should not run every possible parameter combination. A small, well-justified experiment is scientifically stronger than a large collection of unexplained model runs.

### 5.4 Minimum analytical requirements

Every project must:

- compare at least one physical outcome, one economic outcome, and one welfare or distributional outcome;
- examine results over time rather than only in one endpoint year;
- compare global results with at least three contrasting regions;
- distinguish direct sectoral impacts, adaptation costs, avoided damages, and residual damages where applicable;
- explain at least one result using the causal structure of the model;
- investigate at least one unexpected or counterintuitive result;
- report model settings and units clearly;
- perform basic validity checks, such as checking scenario ordering, totals, bounds, and relevant accounting identities;
- discuss uncertainty, limitations, and omitted mechanisms.

## 6. Topic choices

Choose one of the following topics. You may propose a different topic, but it must be approved by the teaching team before the research proposal deadline. Topic availability may be limited to ensure a reasonable distribution of groups and supervision capacity.

### Topic A: Mitigation, adaptation, or both?

**Central problem:** Mitigation limits future climate change, whereas adaptation reduces some consequences of the climate change that occurs. These strategies can be substitutes, complements, or both.

Possible research questions include:

- How does the optimal balance between mitigation and adaptation change with climate sensitivity or damage uncertainty?
- Does decision order matter when mitigation is chosen before adaptation rather than jointly?
- Which regions and impact sectors rely most strongly on adaptation?
- What happens when adaptation is less effective than decision-makers expected?
- Does access to effective adaptation reduce optimal mitigation, and is that outcome equitable?

Suggested experiments include:

- no mitigation and no adaptation;
- mitigation only;
- adaptation only;
- jointly optimized mitigation and adaptation;
- mitigation followed by adaptation;
- planned versus realized adaptation effectiveness.

Important limitations to consider include the stylized adaptation-effectiveness curves, the absence of an explicit adaptation-capital stock, and the treatment of institutional or financial barriers.

### Topic B: Agriculture beyond GDP

**Central problem:** Agriculture may represent a small share of global GDP, but agricultural losses can have large consequences for food prices, nutrition, livelihoods, and welfare, particularly in poorer regions.

This topic uses a prepared experimental agriculture module. Groups compare alternative ways of translating the same climate-related agricultural shock into societal consequences.

Possible representations include:

1. a direct agricultural GDP loss;
2. a stylized food-price and consumption effect;
3. a food-security or subsistence indicator;
4. a nonlinear welfare penalty when food consumption approaches a minimum level.

Possible research questions include:

- How does the representation of agricultural damages affect optimal mitigation?
- When does an apparently small GDP loss produce a large welfare loss?
- How do agricultural impacts differ between high-income and low-income regions?
- How strongly do assumptions about adaptation, trade, or food-demand elasticities affect conclusions?
- Does conventional regional welfare weighting adequately capture food insecurity?

The module is intentionally stylized. It does not reproduce a crop model, food-system model, or computable general equilibrium model. You must distinguish agricultural production, agricultural value added, food prices, food consumption, and food security. You must also assess possible double-counting with other damage estimates.

### Topic C: Biodiversity and ecosystems in a cost-benefit IAM

**Central problem:** Biodiversity and ecosystem change are central sustainability concerns, but their values cannot be reduced unambiguously to market GDP.

This topic uses a prepared experimental biodiversity module. The common physical layer describes a climate-related biodiversity or ecosystem-condition indicator. Groups then compare different ways of using that indicator in decision-making.

Possible representations include:

1. **indicator only:** biodiversity is reported but does not enter the objective;
2. **ecosystem-service damage:** ecosystem degradation affects production or consumption;
3. **non-use welfare value:** people derive welfare from the continued existence of biodiversity;
4. **natural-capital stock:** degradation affects future productive capacity or resilience;
5. **ecological guardrail:** policy is optimized subject to a minimum biodiversity condition.

Possible research questions include:

- How does adding climate-related biodiversity loss change optimal mitigation?
- Is monetization or an ecological guardrail more influential, transparent, or defensible?
- How do irreversibility, recovery rates, or ecological thresholds affect policy timing?
- What is the effect of scaling biodiversity value with regional income?
- Which values of nature remain absent from all model representations?

The module represents only the climate-related component of biodiversity pressure. It does not comprehensively represent land-use change, exploitation, pollution, invasive species, ecological interactions, or culturally specific values of nature. Avoid presenting the model output as a projection of total future biodiversity.

### Topic D: The value of climate-related mortality

**Central problem:** Climate change affects heat- and cold-related mortality. Including mortality in a cost-benefit calculation requires choices about how changes in mortality risk are valued.

Possible valuation approaches include:

1. physical mortality reported separately and excluded from the monetary objective;
2. one equal global value of a statistical life (VSL);
3. a VSL scaled with regional GDP per capita;
4. an advanced value-of-a-life-year (VOLY) approach, if age-specific mortality and years of life lost are available.

Possible research questions include:

- How does mortality monetization affect optimal mitigation and adaptation?
- How do equal and income-scaled VSL assumptions redistribute the represented benefits of climate policy?
- What do avoided cold-related deaths imply for the timing or regional distribution of policy benefits?
- Is excluding mortality from the objective more neutral than monetizing it?
- How would a focus on deaths, years of life lost, or non-monetary health indicators change the interpretation?

Always report physical mortality alongside monetary values. A VSL represents willingness to pay for small changes in mortality risk; it is not the price of an identifiable person's life. A VOLY analysis is only defensible when changes in years of life lost can be estimated. Do not infer this from total deaths alone.

### Topic E: Is there a robust optimal climate policy?

**Central problem:** The policy pathway that MIMOSA calls optimal depends on uncertain scientific parameters and contested economic and ethical assumptions.

Possible research questions include:

- Which assumptions have the largest effect on the optimal temperature or emissions pathway?
- Is there a policy that performs acceptably across multiple plausible futures?
- How do discounting, climate sensitivity, damage uncertainty, technological learning, and adaptation effectiveness interact?
- Does the optimal result change when inequality aversion or the welfare objective changes?
- How do limits on rapid mitigation or negative emissions affect the result?

This topic must go beyond changing one parameter at a time. Develop a structured uncertainty design, identify interactions, and distinguish:

- parametric uncertainty;
- scenario uncertainty;
- structural model uncertainty;
- normative uncertainty.

The final result should include a robustness comparison rather than only a collection of optimal pathways.

### Topic F: Effort sharing, inequality, and climate finance

**Central problem:** A globally cost-effective allocation of mitigation need not be fair. Alternative principles distribute emission allowances, mitigation costs, damages, and financial transfers differently.

MIMOSA includes several stylized effort-sharing approaches, including equal mitigation costs, equal total costs, per-capita convergence, ability to pay, and equal cumulative per-capita emissions.

Possible research questions include:

- How do alternative fairness principles redistribute mitigation obligations and costs?
- Where does mitigation physically occur, and to which region is it attributed after emissions trading?
- How large are the implied international financial flows?
- Do equal relative costs imply equal welfare consequences?
- How do mitigation obligations compare with regional damages and adaptation needs?
- Does historical responsibility lead to politically or economically feasible allocations in the model?

Unless otherwise approved, compare effort-sharing regimes under a common carbon budget. Clearly distinguish:

- physical emission reductions;
- attributed reductions and allowances;
- domestic mitigation costs;
- attributed mitigation costs and trading payments;
- climate damages;
- adaptation expenditure;
- consumption and welfare effects.

Effort-sharing rules in MIMOSA are stylized normative allocations, not predictions of international negotiations. Some combinations of rules and constraints can be infeasible; use the course-provided configurations.

## 7. Optional advanced model extension

Groups with relevant programming experience may propose an advanced model extension. This is optional and is not required for the highest grade. Programming complexity by itself does not earn additional marks; the scientific justification, verification, interpretation, and transparency of the extension are assessed.

Possible extensions include:

- completing a prepared agriculture or biodiversity equation;
- adding a non-monetary impact indicator;
- adding a simple regional vulnerability factor;
- comparing reversible and irreversible impact dynamics;
- adding an alternative valuation or guardrail;
- adding a carefully bounded new impact sector.

The teaching team will provide the model plumbing where possible, including file structure, imports, variable declarations, configuration entries, aggregation, units, and test cells. Students should normally edit only clearly marked equations and parameter tables.

The instructor-facing [extension scaffolding guide](technical_guides/Scaffolding_MIMOSA_Extensions_for_Assignment_4.md) gives proposed architectures and templates for agriculture, biodiversity, and mortality valuation.

Extensions that modify core economic equations, introduce circular feedbacks, replace the optimization objective, or require major new datasets need explicit approval.

## 8. Research process

### Step 1: Form a group and explore MIMOSA

Complete the guided notebook and ensure that every group member can:

- run a no-policy simulation;
- run or load a reference optimization;
- locate the parameter settings;
- distinguish global and regional variables;
- use the dashboard or supplied plotting functions;
- explain the difference between simulation and optimization;
- save a result with its associated parameter file.

Submit your group composition and provisional topic choice by **[date]**.

### Step 2: Review the literature and define the problem

Conduct a focused review of approximately **8-12 relevant scientific sources**. At least some sources should concern the substantive impact or policy issue, and at least some should concern its representation in IAMs, economic evaluation, or scenario analysis.

Use the following table to organize the review:

| Reference | System or impact studied | Model or method | Main variables | Key assumptions | Main findings | Limitation or gap relevant to our study |
|---|---|---|---|---|---|---|
| | | | | | | |

Your literature review should help you identify a genuine modelling or decision problem. The fact that MIMOSA can vary a parameter is not by itself a research gap.

### Step 3: Develop a system diagram

Develop a causal-loop diagram, stock-flow diagram, or other conceptual system map showing:

- important drivers and outcomes;
- feedbacks, delays, and accumulations;
- regional or distributional differences;
- policy choices;
- uncertain and normative assumptions;
- processes inside MIMOSA;
- relevant processes outside MIMOSA.

Use different visual styles or boundaries to distinguish variables represented endogenously, exogenous inputs, and omitted mechanisms. Keep the diagram as simple as possible, but not simpler than your research question permits.

### Step 4: Formulate the research question and expectations

A suitable research question is:

- focused and feasible within five weeks;
- comparative, relational, or explanatory;
- answerable using clearly defined model experiments;
- connected to a scientific or policy debate;
- explicit about the outcome, intervention or assumption, and comparison.

Examples of useful forms are:

- How does **X** affect **Y**, through which mechanisms, and how does this differ across **Z**?
- Under which assumptions does strategy **A** outperform strategy **B**?
- How robust is policy **P** when assumption **U** differs from what decision-makers expected?
- How does representing impact **I** as **M1** rather than **M2** change the model's optimal policy and distributional outcomes?

State one main research question and, if helpful, two or three subquestions. Formulate expected outcomes or hypotheses and explain the mechanisms behind them.

### Step 5: Develop the analytical framework and scenario matrix

Translate the research question into a step-by-step experiment plan. Before running the full analysis, complete a scenario matrix:

| Scenario | Decision mode | Policy or model change | Assumptions held constant | Main comparison | Expected mechanism |
|---|---|---|---|---|---|
| Reference 1 | Simulation | No mitigation or adaptation | Course defaults | No-policy reference | High emissions and damages |
| Reference 2 | Optimization | Joint mitigation and adaptation | Course defaults | CBA reference | Model balances represented costs and benefits |
| [Scenario] | | | | | |

For every varied parameter, record:

- its meaning and unit;
- the reference value;
- the alternative values;
- the scientific or normative justification for the range;
- the outcomes expected to respond.

Pilot at least two scenarios before proposal submission. Confirm that the model runs and that the selected outputs can be interpreted.

### Step 6: Submit the research proposal

Submit a proposal of approximately **[1,500] words** by **[date and time]**. It must contain:

1. group members and provisional title;
2. selected topic and problem definition;
3. focused research question and optional subquestions or hypotheses;
4. concise literature synthesis and completed literature table;
5. system diagram;
6. analytical framework and scenario matrix;
7. selected global, regional, sectoral, economic, physical, and welfare indicators;
8. two pilot figures or tables demonstrating technical feasibility;
9. expected limitations and risks;
10. preliminary division of group responsibilities;
11. reference list.

The proposal word count excludes the literature table, figures, scenario matrix, and reference list.

The advisor will assess whether the question, model experiments, outputs, and workload form a coherent and feasible project. Major changes may be required before approval.

### Step 7: Conduct the research

Follow the approved experiment plan, but document any necessary changes. Maintain a run log containing:

- scenario name;
- date and group member;
- model version;
- parameter changes;
- optimization or simulation status;
- warnings or failed runs;
- output filename;
- notes on interpretation.

Do not silently discard failed or unexpected results. Determine whether they reflect a technical problem, an infeasible scenario, or meaningful model behaviour.

### Step 8: Conduct sensitivity and robustness analysis

A sensitivity analysis asks how outcomes change when assumptions change. A robustness analysis asks whether a policy chosen under one set of assumptions still performs acceptably under another.

At minimum:

- vary two important uncertain or normative assumptions;
- test at least one interaction or structural alternative;
- replay one policy under different realized assumptions;
- explain which conclusion is robust and which is assumption-dependent.

Avoid describing a result as robust merely because two nearby parameter values produce similar figures.

### Step 9: Interpret and critically evaluate

Your discussion should address four levels:

1. **Numerical:** What changed, by how much, when, and where?
2. **Causal:** Which model equations, feedbacks, delays, or constraints produced the result?
3. **Decision-related:** What does the result imply for the decision problem in your research question?
4. **Critical:** Which assumptions, omissions, values, and distributional choices limit the conclusion?

Clearly separate results produced by the model from your own interpretation and from claims supported by literature.

## 9. Scientific paper

The final paper has a maximum length of **[3,500-4,000] words** and follows this structure:

1. **Title and author names**
2. **Abstract** - maximum 200 words, stating the problem, methods, principal results, and meaning.
3. **Introduction**
   - scientific and societal problem;
   - relevant literature and gap;
   - aim and research question;
   - concise expectations or hypotheses;
   - system diagram.
4. **Methods**
   - relevant MIMOSA structure and version;
   - simulation and optimization design;
   - scenario matrix;
   - parameters and justification;
   - selected regions, sectors, variables, and indicators;
   - sensitivity and robustness method;
   - model extension, if applicable;
   - reproducibility and validity checks.
5. **Results**
   - reference scenarios;
   - topic-specific comparisons;
   - temporal, regional, and sectoral results;
   - sensitivity and robustness findings;
   - unexpected results;
   - clear figures and tables with units.
6. **Discussion**
   - answer to the research question;
   - explanation of causal mechanisms;
   - comparison with literature;
   - scientific and policy significance;
   - distributional and ethical interpretation;
   - uncertainty and limitations;
   - what MIMOSA cannot establish;
   - useful next research steps.
7. **Conclusion** - one concise paragraph.
8. **References**
9. **Contribution statement**
10. **Optional appendices** - scenario details, supplementary figures, equations, or extension documentation.

## 10. Oral presentation

Each group gives a presentation of **[8 minutes plus 4 minutes for questions]**. At least [three/all] group members must contribute actively. Because presentation time is limited, communicate one coherent argument rather than every model output.

The presentation should contain:

- title and names;
- the decision problem and why it matters;
- research question;
- simplified system diagram;
- experiment design;
- two or three principal findings;
- one sensitivity or robustness result;
- interpretation and limitation;
- one clear take-home message.

## 11. Reproducibility package

The teaching team should be able to connect every result in the paper to a documented model run. Submit:

```text
group_name/
|-- README.md
|-- analysis.ipynb
|-- output/
|   |-- scenario_name.csv
|   `-- scenario_name.csv.params.json
|-- figures/
|-- scenario_matrix.csv
`-- contribution_statement.md
```

The `README` must state:

- the model version and course environment;
- the order in which notebook sections should be run;
- which files reproduce each main figure and table;
- any precomputed runs supplied by the teaching team;
- any known warnings or deviations from the proposal.

Notebooks should run from top to bottom in the course environment. Remove unused exploratory cells or mark them clearly. Do not manually edit exported model results.

## 12. Collaboration, research integrity, and use of tools

All group members are responsible for understanding the main research question, methods, model assumptions, and conclusions. Divide work, but do not divide understanding.

The contribution statement should briefly describe each member's contributions to literature review, scenario design, modelling, analysis, writing, visualization, and presentation.

Follow the course and Utrecht University rules concerning citation, collaboration, plagiarism, and the use of generative AI or other computational tools. **[Insert course-specific AI policy.]** Any permitted use of AI should be documented as required by the course policy. Model outputs, citations, and scientific claims remain the responsibility of the students.

# Appendix A: Research proposal feedback form

| Criterion | Approved | Revision needed | Comments |
|---|:---:|:---:|---|
| The problem is scientifically and societally relevant. | | | |
| The research question is focused, comparative or relational, and feasible. | | | |
| The literature review identifies a meaningful debate or gap. | | | |
| The system diagram distinguishes endogenous, exogenous, and omitted processes. | | | |
| The analytical framework follows logically from the research question. | | | |
| The scenario matrix isolates the relevant mechanism. | | | |
| Parameter ranges are justified. | | | |
| Required data and model modules are available. | | | |
| Pilot runs demonstrate technical feasibility. | | | |
| Selected outputs cover physical, economic, regional, and welfare dimensions. | | | |
| The sensitivity and robustness plan is adequate. | | | |
| The scope is realistic for five weeks. | | | |

# Appendix B: Scientific paper assessment form

The paper and reproducibility package account for **75% of the assignment grade** [confirm].

| Criterion | Weight | Excellent performance demonstrates |
|---|---:|---|
| Problem framing and literature | 12% | A focused, relevant problem grounded in appropriate scientific literature; a clear gap and research question. |
| Systems understanding | 12% | Accurate causal reasoning; clear feedbacks, delays, boundaries, endogenous and exogenous variables, and omissions. |
| Research and scenario design | 14% | Comparisons isolate the research mechanism; settings and ranges are justified; simulation and optimization are used correctly. |
| Quantitative analysis | 16% | Correct, transparent analysis of temporal, regional, sectoral, economic, physical, and welfare outcomes; appropriate checks. |
| Sensitivity and robustness | 10% | Meaningful uncertainty choices, interactions or structural alternatives, and a genuine out-of-sample policy stress test. |
| Interpretation and critical evaluation | 18% | Results are causally explained, compared with literature, and critically assessed for normative assumptions, distribution, uncertainty, and omissions. |
| Reproducibility | 8% | Complete scenario records, parameter files, runnable analysis, traceable figures, and transparent documentation. |
| Structure, figures, and writing | 10% | Coherent scientific structure, readable language, informative figures, correct units, and careful referencing. |
| **Total** | **100%** | |

Critical errors in model interpretation, undocumented manipulation of results, non-reproducible analysis, or unsupported claims may substantially lower the grade regardless of presentation quality.

# Appendix C: Oral presentation assessment form

The oral presentation accounts for **25% of the assignment grade** [confirm].

| Criterion | Weight | Indicators |
|---|---:|---|
| Scientific content and argument | 45% | Clear problem, question, method, result, interpretation, and conclusion. |
| Selection and explanation of quantitative evidence | 20% | Figures are readable, correctly labelled, and directly support the argument. |
| Critical reflection | 15% | Important uncertainty, limitation, or normative assumption is explained. |
| Organization and visual design | 10% | Logical structure, legible slides, appropriate amount of text. |
| Delivery and questions | 10% | Clear, within time, shared participation, and informed responses. |
| **Total** | **100%** | |

# Appendix D: Minimum checklist before submission

## Research question and design

- [ ] The research question can be answered by the reported experiments.
- [ ] Every scenario has a clear purpose and comparison.
- [ ] The no-policy and reference CBA cases are included or an alternative is justified.
- [ ] Parameter values and units are documented.

## Results

- [ ] Global and regional results are both presented.
- [ ] Physical and monetary outcomes are not conflated.
- [ ] Adaptation costs, avoided damages, and residual damages are distinguished.
- [ ] Figures have titles, axes, units, legends, and readable labels.
- [ ] At least one unexpected result is investigated.

## Interpretation

- [ ] "Optimal" is defined in terms of the model objective and assumptions.
- [ ] Sensitivity is distinguished from robustness.
- [ ] Distributional consequences are considered.
- [ ] Important omitted mechanisms and values are identified.
- [ ] Conclusions do not extend beyond what the experiments support.

## Reproducibility

- [ ] Output files and parameter files use unique scenario names.
- [ ] Main figures can be traced to specific files or notebook cells.
- [ ] The notebook runs in the course environment.
- [ ] The README and contribution statement are included.

# Appendix E: Provisional starting literature and documentation

The final guide should link to a curated reading list for each topic. Provisional starting points include:

- van der Wijst, K.-I., Hof, A. F., and van Vuuren, D. P. (2021). On the optimality of 2 degrees C targets and a decomposition of uncertainty. *Nature Communications*, 12, 2575.
- van der Wijst, K.-I., Bosello, F., Dasgupta, S., et al. (2023). New damage curves and multimodel analysis suggest lower optimal temperature. *Nature Climate Change*, 13, 434-441.
- Moore, F. C., Baldos, U., Hertel, T., and Diaz, D. (2017). New science of climate change impacts on agriculture implies higher social cost of carbon. *Nature Communications*, 8, 1607.
- Hultgren, A., et al. (2025). Impacts of climate change on global agriculture accounting for adaptation. *Nature*.
- Carleton, T., et al. (2022). Valuing the global mortality consequences of climate change accounting for adaptation costs and benefits. *Quarterly Journal of Economics*, 137(4), 2037-2105.
- Brooks, W. R., and Newbold, S. C. (2014). An updated biodiversity nonuse value function for use in climate change integrated assessment models. *Ecological Economics*, 105, 342-349.
- IPBES (2022). *Methodological Assessment Report on the Diverse Values and Valuation of Nature*.
- **[Add the appropriate ACCREU sectoral-impact and adaptation references.]**
- MIMOSA model documentation: **[insert stable course link]**.
