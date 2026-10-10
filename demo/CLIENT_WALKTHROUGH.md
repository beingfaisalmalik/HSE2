# HSE Enterprise Suite — Client Walkthrough

**Northstar Petrochemicals · Fictional industrial demonstration**

**73 module areas · 14 domains · 8 journeys · 49 steps · 90-minute full session**

> This is a demonstration of the existing application, not an operational safety procedure, clinical recommendation, certified engineering calculation or regulatory compliance certificate.

## Presenter preparation

1. Start the isolated demo using the [setup guide](../README.md). Never use a production database.
2. Sign in as `hse.presenter` at `/hse/demo`. Confirm **73 / 73** samples and no readiness issues. Initial explorer count: **160** primary/reference records; evidence/HR/child rows are additional.
3. Open `/hse/portal` as `hse.contractor` in a separate private browser. Do not switch accounts in a shared authenticated tab.
4. Enable **Presenter notes**. Keep the executive dashboard and selected report previews open in extra tabs. Warm assets before the client joins.
5. Download the current database’s walkthrough and coverage CSV from the hub. Those downloads contain the correct live links for that database.
6. Decide whether to run mutating exercises. Rebuild an isolated database between pristine sessions; a module upgrade preserves presentation edits.

**Portable references:** This document uses stable Odoo external IDs, not database-specific numeric links. In the hub, open the named journey step or find the corresponding module sample. An operator can resolve an ID with `env.ref("hse_demo_data.<id>")` in Odoo shell.

## Opening talk track

“Northstar operates a cracker unit, a polymer unit and a central warehouse. Maintenance, operating teams, contractors and HSE share the same safety picture. We will follow evidence from the worksite through authorization, investigation, corrective action and assurance. Every screen we open is the real Odoo application; every person, measurement and cost is fictional.”

**Client outcomes to emphasize:** connected evidence; accountable ownership; visible exceptions; controlled work; workforce participation; auditable reporting; measurable improvement.

## Choose the session length

| Session | Suggested focus |
|---|---|
| 15 minutes | 2 min introduction; 3 min dashboard; 5 min incident highlights; 3 min contractor portal; 2 min reports |
| 45 minutes | 3 min introduction; 4 min dashboard; 8 min incident; 8 min control of work; 8 min process safety; 6 min workforce; 5 min reports; 3 min Q&A |
| 90 minutes | 5 min introduction/dashboard; all eight journeys below (80 min); 5 min Q&A |

## Navigation and presentation controls

- **Start the guided demo** expands the first journey. Open records in new tabs so the hub remains your agenda.
- **Presenter notes** exposes a talk track and expected evidence for each step.
- **Mark demonstrated** and **Reset checklist** affect only this browser session, not business records.
- **Module explorer** searches names/descriptions and filters by domain. **Open register** shows native navigation; **Sample record** opens the featured record.
- **Report library** renders actual report data. Use browser **Print → Save as PDF** if the server PDF engine is absent.
- The hub’s print button expands all journey notes for printing, then restores the screen.

## The eight connected journeys

### 01. From incident to lasting learning — 12 minutes

**Audience:** HSE manager  
**Outcome:** Show how the organization learns from an event rather than simply closing a report.

One interruption-related injury. One connected evidence trail. A verified path to prevention.

#### 1. Report and classify the injury

Begin with the coupling injury reported 24 days before installation. Show the affected location, employee injury and OSHA-recordable flag.

**Show / expected evidence:** The injury sub-record, days away, four event milestones, and linked investigation are populated.

**Stable sample:** `hse_demo_data.dd_inc_lti1`

#### 2. Follow the investigation evidence

Open the analysis tabs. Follow all five why questions, six fishbone branches, the chronological timeline and four bow-tie barriers.

**Show / expected evidence:** Two effective, one degraded and one failed barrier explain a 50% bow-tie health baseline.

**Stable sample:** `hse_demo_data.dd_inv_lti1`

#### 3. Address the human and organizational factors

Show the handover, supervision and procedure-design factors. Explain that the analysis is not a judgment of individual blame.

**Show / expected evidence:** Four contributing factor flags and a human-factors corrective plan are present.

**Stable sample:** `hse_demo_data.dd_hfacs`

#### 4. Give the corrective action an owner

Show the overdue restart-checklist action, its owner and links back to the incident and investigation. Explain implementation versus independent effectiveness verification.

**Show / expected evidence:** Priority, target date, progress, and investigation/incident links are populated. Do not verify it without evidence.

**Stable sample:** `hse_demo_data.dd_capa_1`

#### 5. Put the control into the procedure

Inspect the published line-opening procedure and its four steps. Point out authorization and isolation hold points.

**Show / expected evidence:** The procedure is published and critical hold points are identified; it is also visible in the workforce portal.

**Stable sample:** `hse_demo_data.dd_sop_014`

#### 6. Close the learning loop

Finish with the culture baseline and roadmap. Link reporting confidence and shift-handover quality to the operational lesson.

**Show / expected evidence:** The assessment has populated maturity dimensions, strengths, vulnerabilities and roadmap actions.

**Stable sample:** `hse_demo_data.dd_culture`

### 02. Authorize work, not uncontrolled risk — 12 minutes

**Audience:** Operations / permit authority  
**Outcome:** Demonstrate real workflow checks using the native forms, not simulated buttons.

Follow a vessel inspection from its JSA and readiness gates to isolation, entry and handover.

#### 1. Review the task hazards

Show four hazards spanning critical, high, medium and low initial risk. Compare initial and residual scores and explain the linked controls.

**Show / expected evidence:** Four hazard lines and reusable controls are present; the executive risk matrix has non-zero drill-down counts.

**Stable sample:** `hse_demo_data.dd_jsa_1`

#### 2. Check the preparation gates

Click Authorize Ready while the final safety walkthrough is unchecked. The application must block it. Complete the remaining task and gate only as a demo exercise.

**Show / expected evidence:** A UserError blocks authorization until all four readiness gates are checked. The initial package is 75% ready.

**Stable sample:** `hse_demo_data.dd_prep`

#### 3. Prove positive isolation

Inspect the inlet blind and auxiliary breaker, lockbox and witnessed zero-energy evidence. Try de-isolation with the three clearance checks still unset.

**Show / expected evidence:** De-isolation is blocked until tools, guards and personnel-clear checks are all confirmed. Keep the plan isolated during this tour.

**Stable sample:** `hse_demo_data.dd_loto_cse`

#### 4. Challenge the SIMOPS conflict

The approved hot-work permit overlaps vessel entry in Unit-100. Click Start Work before assigning coordinator sign-off; explain the conflict warning.

**Show / expected evidence:** The high-risk concurrent-operation conflict prevents work starting without coordinator authorization.

**Stable sample:** `hse_demo_data.dd_ptw_hot`

#### 5. Account for every entrant

Show two entrant records, one still inside, the linked master permit and isolation scheme, and three safe gas readings. Try Close Entry before logging the entrant out.

**Show / expected evidence:** Closure is blocked while one entrant is inside. Log exit through the native entrant action before closing, if demonstrating completion.

**Stable sample:** `hse_demo_data.dd_cse`

#### 6. Hand over the operating picture

Inspect the shift event, abnormal compressor temperature round, standing alarm and incoming operator. Explain outgoing and incoming handover signatures.

**Show / expected evidence:** Events, rounds, alarms and standing orders are populated. The incoming relieving operator is identified.

**Stable sample:** `hse_demo_data.dd_oplog_1`

#### 7. Inspect specialized work authorization

Review the 48-tonne load, rigging allowance and chart capacity. Use the module explorer for the excavation and radiography certificates.

**Show / expected evidence:** The lift is classified critical at 82.5% utilization. Excavation and NDT samples each link to their own master permit.

**Stable sample:** `hse_demo_data.dd_lift`

### 03. Engineer safer change — 12 minutes

**Audience:** Process safety / engineering  
**Outcome:** Show a connected process-safety argument with explicit assumptions and accountable actions.

Trace a transmitter change through HAZOP, LOPA, safety functions and pre-startup evidence.

#### 1. Identify the process deviation

Open the T-201 node and high-level deviation. Explain causes, unmitigated versus residual risk, existing safeguards and the engineering recommendation.

**Show / expected evidence:** The study has a node, a deviation and a recommendation linked to both a MOC and central CAPA.

**Stable sample:** `hse_demo_data.dd_hazop`

#### 2. Assess the independent protection layers

Follow the linked HAZOP deviation and the credited alarm-response layer. Show initiating-event frequency, mitigated frequency and allocated SIL.

**Show / expected evidence:** Values are calculated from editable assumptions. This is an illustrative assessment, not certified engineering advice.

**Stable sample:** `hse_demo_data.dd_lopa`

#### 3. Inspect the safety instrumented function

Compare required versus calculated SIL, sensor and final-element architectures and the proof-test interval. Open the recorded proof-test demand.

**Show / expected evidence:** PFD, RRF and SIL status are computed; the demand records a successful 1.4-second response.

**Stable sample:** `hse_demo_data.dd_sif`

#### 4. Review assurance and barrier status

Show functionality, reliability and survivability standards and the passing assurance test. Contrast this with the separate inhibited barrier.

**Show / expected evidence:** The emergency shutdown element has test evidence; the barrier register includes an explicitly bypassed defense.

**Stable sample:** `hse_demo_data.dd_sece_esd`

#### 5. Govern the technical change

Review the justification, three discipline reviews and the linked engineering action. Explain the temporary-change sample and its reversion plan separately.

**Show / expected evidence:** The permanent MOC is in technical review, and the commissioned temporary sample has a future expiry and complete PSSR evidence.

**Stable sample:** `hse_demo_data.dd_moc_1`

#### 6. Inspect startup readiness

Show the nine-item PSSR exercise with eight verified items and one open night-shift training item. Mark it verified only for demonstration and watch the computed completion flag.

**Show / expected evidence:** PSSR completion changes from false to true when every line is verified. The current commissioning action is NOT an enforced PSSR gate; do not claim otherwise.

**Stable sample:** `hse_demo_data.dd_moc_pssr`

#### 7. Return to leading and lagging indicators

Show real exposure-hour inputs and API RP 754 rates, then open the classified release event and barrier register from the module explorer.

**Show / expected evidence:** Dashboard TRIR is sourced from the seeded exposure record rather than an unexplained hard-coded headline.

**Stable sample:** `hse_demo_data.dd_pse_2026`

### 04. Contain, recover and report — 9 minutes

**Audience:** Environmental specialist  
**Outcome:** Show operational evidence behind environmental performance and reporting.

Connect chemical information, a contained release, monitoring exceptions and environmental accounting.

#### 1. Know the substance

Open the illustrative SDS, GHS indicators and review date. Follow the location inventory and inspect acid/base compatibility separately.

**Show / expected evidence:** SDS records and chemical inventory are connected. Text is explicitly illustrative, not an official supplier SDS.

**Stable sample:** `hse_demo_data.dd_sds_benzene`

#### 2. Trace containment and recovery

Show the 25 L seal release, 24 L recovered, containment and remediation narrative.

**Show / expected evidence:** Recovery efficiency computes to 96%; the sample is remediated and remains within secondary containment.

**Stable sample:** `hse_demo_data.dd_spill`

#### 3. Investigate the monitoring exception

Compare this sample with the normal sample in the same register. Highlight pH and oil-and-grease exceptions.

**Show / expected evidence:** A compliant and a non-compliant sample are seeded; violation parameters are computed from the configured model rules.

**Stable sample:** `hse_demo_data.dd_water_exceedance`

#### 4. Manage waste evidence and deadlines

Review four drums, quantity, accumulation date, transporter and disposal facility. Explain shipment and final destruction evidence.

**Show / expected evidence:** The storage example has 12 days remaining at installation. All agency identifiers are clearly fictional.

**Stable sample:** `hse_demo_data.dd_waste`

#### 5. Detect a fugitive leak

Open the component reading and compare screening concentration with background and the leak threshold.

**Show / expected evidence:** A 1,245 ppm net reading exceeds the 500 ppm demo threshold. A second component provides a compliant comparison.

**Stable sample:** `hse_demo_data.dd_ldar_leak`

#### 6. Connect operations to ESG accounting

Inspect scopes 1–3, electricity and renewable inputs, water recycling and waste diversion. Use the air-emissions register to show a flagged flare event.

**Show / expected evidence:** Totals and intensities are calculated from synthetic activity inputs. Factors and limits require site-specific validation.

**Stable sample:** `hse_demo_data.dd_esg`

### 05. A qualified workforce, inside and out — 8 minutes

**Audience:** Workforce / contractor coordinator  
**Outcome:** Demonstrate participation as well as oversight, using two genuinely separate accounts.

Review contractor qualification, certifications and training gaps, then switch to frontline self-service.

#### 1. Qualify the contractor company

Show insurance, safety qualification, worker inductions and the populated monthly performance log.

**Show / expected evidence:** Two fictional contractor profiles exist; the selected company has active and expired inductions.

**Stable sample:** `hse_demo_data.dd_contract_alpha`

#### 2. Identify expired site access

Contrast the expired worker induction with Alex Morgan’s active sample. Explain that access-gate hardware integration is not included.

**Show / expected evidence:** The worker is explicitly expired. This register does not itself integrate with physical access control.

**Stable sample:** `hse_demo_data.dd_induction_expired`

#### 3. Prioritize certification renewal

Compare expired, expiring and valid personnel certificates. Use the equipment register to show the same range for plant assets.

**Show / expected evidence:** The demo includes renewal exceptions rather than only green examples; certificate statuses are visible.

**Stable sample:** `hse_demo_data.dd_pcert_sara`

#### 4. Turn competency gaps into a plan

Review five rows: compliant, expired, missing and two expiring. Explain the role requirements and native Evaluate Matrix action, which replaces matrix rows.

**Show / expected evidence:** The initial matrix has two missing/expired gaps. Re-evaluation is a real mutation; use a fresh database or duplicate for a repeatable tour.

**Stable sample:** `hse_demo_data.dd_tm_2026`

#### 5. Brief the team and record attendance

Show the toolbox topic, attendance, duration and minutes. Print the meeting record from the report library.

**Show / expected evidence:** Two meetings exist with real attendance figures and populated minutes.

**Stable sample:** `hse_demo_data.dd_meet_1`

#### 6. See a contractor-owned submission

Open /hse/portal in a private browser window and sign in as hse.contractor. Review My Submissions, send a new observation, then refresh the backend.

**Show / expected evidence:** The portal account owns one observation and one near miss. New observations persist in Odoo and become visible to the HSE team.

**Stable sample:** `hse_demo_data.dd_portal_observation`

### 06. Healthy people, a resilient site — 10 minutes

**Audience:** Occupational health / emergency lead  
**Outcome:** Connect prevention, worker health surveillance and response readiness without presenting demo data as clinical advice.

Move from exposure monitoring and preventive care to emergency preparedness and accountability.

#### 1. Define a similar exposure group

Show the maintenance tasks, workforce estimate and associated samples. Compare acceptable and overexposure results.

**Show / expected evidence:** Two benzene samples are attached to the same SEG and use explicit illustrative exposure-limit inputs.

**Stable sample:** `hse_demo_data.dd_seg`

#### 2. Follow the exposure exception

Show the 8-hour sample, calculated TWA, exceedance flags and engineering-control notes.

**Show / expected evidence:** The 1.5 ppm sample exceeds the 1.0 ppm demo PEL. No automatic clinical or regulatory decision should be inferred.

**Stable sample:** `hse_demo_data.dd_ih_overexposure`

#### 3. Review synthetic health surveillance

Show an elevated biomonitoring example. Open audiometry, respirator and radiation-dosimetry samples through the module explorer.

**Show / expected evidence:** Biomonitoring, baseline/annual hearing records, respirator renewal and TLD monitoring are all populated with fictional results.

**Stable sample:** `hse_demo_data.dd_biological`

#### 4. Design out manual-handling risk

Review the high-risk REBA score and workstation measures. Connect the proposal to the mechanical drum-handling improvement.

**Show / expected evidence:** Risk is computed from the supplied assessment; the remedial measure is a mechanical handling intervention.

**Stable sample:** `hse_demo_data.dd_ergonomics`

#### 5. Inspect the training-only response plan

Show the command hierarchy, internal callout list and primary/alternate muster stations. Inspect the three-member response roster.

**Show / expected evidence:** All emergency contacts are explicitly fictional and no external dispatch service is connected.

**Stable sample:** `hse_demo_data.dd_emergency_plan`

#### 6. Account for every person in the drill

Review response times, 120 personnel on site and 119 mustered, followed by the roster-reconciliation action.

**Show / expected evidence:** The computed unaccounted-personnel count is one. A centrally owned follow-up action exists.

**Stable sample:** `hse_demo_data.dd_emergency_drill`

### 07. Make compliance evidence visible — 10 minutes

**Audience:** Compliance / audit manager  
**Outcome:** Demonstrate a usable assurance trail and exportable client evidence.

Trace requirements, audit findings, asset certificates and corrective evidence without claiming automatic compliance.

#### 1. Start with the legal register

Review obligations, responsible specialists, clause references and the compliance audit. Explain that applicability requires legal review.

**Show / expected evidence:** The PSM, ISO 45001 and environmental permit examples include populated obligations.

**Stable sample:** `hse_demo_data.dd_reg_osha_psm`

#### 2. Show the overdue obligation

Review the due date, recurrence, assigned specialist and submission evidence fields; compare the upcoming legal-register update.

**Show / expected evidence:** The initial statutory task is overdue and the second task is upcoming. No submission is sent to an authority.

**Stable sample:** `hse_demo_data.dd_ctask_1`

#### 3. Inspect an evidence-based audit

Open three checklist lines and show their results, findings and severity. Use the report library for the audit report.

**Show / expected evidence:** The audit is in fieldwork and includes conforming and nonconforming evidence samples.

**Stable sample:** `hse_demo_data.dd_audit_iso`

#### 4. Review statutory asset certification

Inspect the pressure-vessel certificate, then compare relief-valve, crane and hazardous-area examples.

**Show / expected evidence:** The register contains expired, expiring and valid examples with asset and location links.

**Stable sample:** `hse_demo_data.dd_cert_pv`

#### 5. Contain nonconforming material

Show missing gasket traceability, quarantine tag and staging area. Explain disposition review and authorization.

**Show / expected evidence:** The quarantined sample actually has is_quarantined set and a populated containment action.

**Stable sample:** `hse_demo_data.dd_ncr_1`

#### 6. Connect policy to workforce acknowledgment

Review approved policy content and three acknowledgment records; explain that demo signature tokens are not legal digital signatures.

**Show / expected evidence:** Approved policies and published procedures appear in the authenticated portal.

**Stable sample:** `hse_demo_data.dd_pol_001`

### 08. Reliability with measurable return — 7 minutes

**Audience:** Maintenance / plant leadership  
**Outcome:** End the demo with a business-value story supported by actual linked records.

Follow a recurring compressor failure to elimination strategy, financial impact and reusable knowledge.

#### 1. Record the equipment failure

Review the K-301 bearing failure, mode, mechanism, detection method and shutdown impact.

**Show / expected evidence:** Failure reporting is linked to the correct compressor and Unit-100 location.

**Stable sample:** `hse_demo_data.dd_fail_k301`

#### 2. Eliminate the bad actor

Show the repeated trips, underlying thermal issue and elimination strategy. Explain long-term tracking rather than a one-off repair.

**Show / expected evidence:** The defect record identifies 24 failures in the previous 12 months and an execution-stage strategy.

**Stable sample:** `hse_demo_data.dd_defect_k301`

#### 3. Quantify the operational loss

Show eight hours of downtime and the production, repair and contractor cost breakdown.

**Show / expected evidence:** The calculated illustrative total loss is 86,500. It is not an accounting posting.

**Stable sample:** `hse_demo_data.dd_financial_loss`

#### 4. Compare proactive improvement value

Contrast the loss with the warehouse improvement, avoided costs and reduced risk estimate.

**Show / expected evidence:** The benefit record is linked to the mechanical handling initiative and totals 24,500 in illustrative benefit.

**Stable sample:** `hse_demo_data.dd_financial_benefit`

#### 5. Share the lesson across the business

Finish with the compressor lesson and reusable solution. Return to the executive dashboard to recap work, risk, learning and assurance.

**Show / expected evidence:** Two populated knowledge records are available, and every module in the explorer links to its native action and a sample.

**Stable sample:** `hse_demo_data.dd_sol_1`

## Live exercise boundaries and reset notes

| Exercise | Actual behavior | Presenter caution |
|---|---|---|
| Preparation readiness | 75% example is blocked until all four gates are ready | Checking the final gate and authorizing changes the sample |
| LOTO de-isolation | Requires zero-energy evidence and tools/guards/personnel clearance | These are software checks, not proof of actual physical isolation |
| Concurrent work | High-risk overlapping permits require coordinator authorization before start | Approval/start changes the real permit; do not imply physical enforcement |
| Confined-space closure | Cannot close while an entrant remains inside | Log the entrant out only in the fictional exercise |
| PSSR | Eight of nine items are verified; all nine make completion true | Commissioning does **not** enforce this flag as a gate |
| Critical lift | The sample is critical at 82.5% utilization; >95% approval is rejected | Native checks are not certified lifting calculations |
| Training matrix | Original five rows illustrate compliant/expired/gap cases | Reevaluation replaces lines and may generate new actions; reset to repeat the original story |
| CAPA verification | Implementation and effectiveness verification are different stages | Do not mark an action verified without synthetic evidence in the exercise |

## Reporting beyond the ten featured previews

The library links to the following live record-based reports:

- **Permit to work** — sample `hse_demo_data.dd_ptw_cse`; action `hse_reports.action_report_hse_permit`.
- **LOTO isolation plan** — sample `hse_demo_data.dd_loto_cse`; action `hse_reports.action_report_hse_loto`.
- **HAZOP study** — sample `hse_demo_data.dd_hazop`; action `hse_reports.action_report_hse_hazop`.
- **Management system audit** — sample `hse_demo_data.dd_audit_iso`; action `hse_reports.action_report_hse_audit`.
- **Compliance register** — sample `hse_demo_data.dd_obl_psm_e`; action `hse_reports.action_report_hse_compliance_register`.
- **Competency gap matrix** — sample `hse_demo_data.dd_tm_2026`; action `hse_reports.action_report_hse_competency_matrix`.
- **Equipment certification** — sample `hse_demo_data.dd_cert_pv`; action `hse_reports.action_report_hse_equipment_cert`.
- **OSHA 300 sample log** — sample `hse_demo_data.dd_inc_lti1`; action `hse_reports.action_report_hse_osha300_log`.
- **Monthly HSE performance** — sample `base.main_company`; action `hse_reports.action_report_monthly_hse_kpi`.
- **Safety meeting & toolbox talk** — sample `hse_demo_data.dd_meet_1`; action `hse_meeting.action_hse_meeting_report`.

The suite also has legacy incident, investigation, observation, RA/JSA, corrective/preventive and policy/procedure reports. All 22 record-based report definitions were rendered as HTML in the regression suite.

**Six parameterized summaries:** RA/JSA, observations, incident reports, investigations, legacy CAPA and meetings. Open the native summary action, choose dates (and meeting departments) and use **Print Report**. The first five filter **record creation timestamps**, so a same-day range on the installation date includes the seeded records. The meeting summary filters **meeting timestamps**; use the last 30 days and the Operations department for the seeded meeting story. End dates include the whole local calendar day.

Native server PDF requires wkhtmltopdf. The verification checks covered HTML and Chromium/browser printing, **not** native PDF or container execution — confirm both on the presenting machine using the [first-run checklist](LOCAL.md#first-run-checklist). Spreadsheet-report placeholders are not presented as completed XLSX exports; coverage CSV and native Odoo exports are separate capabilities.

## Full coverage checklist

Business sample areas are listed below. Input-only report wizards are intentionally not seeded as business records. Reference and child evidence are linked from the native forms.

### Safety & learning — 8 areas

| Area | What to show | Stable sample |
|---|---|---|
| Incident Management (OSHA) | Classify injuries, quantify impacts, and connect investigation and corrective actions. | `hse_demo_data.dd_inc_lti1` |
| Incident Investigations (RCA) | Follow five whys, a six-branch fishbone, the event timeline, and bow-tie barrier evidence. | `hse_demo_data.dd_inv_lti1` |
| Safety Observations | Capture frontline hazards, immediate containment, photographs, and follow-up. | `hse_demo_data.dd_obs_1` |
| Behavior-Based Safety (BBS) | Compare safe and at-risk behaviors and record immediate coaching feedback. | `hse_demo_data.dd_bbs_1` |
| Human Factors / TapRooT RCA | Move beyond blame to organizational, supervisory, and human-factors causes. | `hse_demo_data.dd_hfacs` |
| Stop Work Authority (SWA) | Recognize intervention, resolve unsafe conditions, and record safe resumption. | `hse_demo_data.dd_swa_1` |
| IOGP Life-Saving Rules | Communicate nine critical safety rules to employees and contractors. | `hse.lsr_energy_isolation` |
| Safety Culture (Bradley Curve) | Translate survey dimensions into a maturity baseline and improvement roadmap. | `hse_demo_data.dd_culture` |

### Process safety — 9 areas

| Area | What to show | Stable sample |
|---|---|---|
| Process Hazard Analysis / HAZOP | Explore a process node, deviations, safeguards, and engineering recommendations. | `hse_demo_data.dd_hazop` |
| Layers of Protection Analysis (LOPA) | Calculate scenario frequency and protection-layer credit from explicit assumptions. | `hse_demo_data.dd_lopa` |
| Safety Instrumented Functions (SIF/SIL) | Compare calculated PFD and SIL with the safety-function design target. | `hse_demo_data.dd_sif` |
| SIF Demands & Trips Log | Review proof-test and real-demand response evidence. | `hse_demo_data.dd_sif_demand` |
| Consequence & Dispersion (QRA) | Illustrate sensitivity to release and weather assumptions; not validated QRA. | `hse_demo_data.dd_dispersion` |
| Safety Critical Elements (SECE) | Track safety-critical equipment performance standards and assurance tests. | `hse_demo_data.dd_sece_esd` |
| Process Safety Events (API RP 754) | Classify a synthetic loss-of-containment event and its barrier findings. | `hse_demo_data.dd_pse_event` |
| API RP 754 Metrics & PSEE Rates | Connect exposure hours, event rates, and leading process-safety indicators. | `hse_demo_data.dd_pse_2026` |
| Safety Barrier Integrity Register | Distinguish effective, degraded, bypassed, and failed defenses. | `hse_demo_data.dd_barrier_inhibit` |

### Control of work — 10 areas

| Area | What to show | Stable sample |
|---|---|---|
| Permit to Work (PTW) | Inspect work scope, gas tests, sign-offs, and concurrent-operation conflicts. | `hse_demo_data.dd_ptw_hot` |
| Confined Space Entry Certificates | Follow entrants, isolation checks, and continuous gas readings. | `hse_demo_data.dd_cse` |
| SIMOPS Spatial Collision Radar | See overlapping activity exclusion zones in a fictional plant grid. | `hse_demo_data.dd_radar_hot` |
| SIMOPS Activity Rules Matrix | Compare prohibited, restricted, and compatible activity combinations. | `hse_demo_data.dd_simops_rule` |
| Lock & Tag Out Plans (LOTO) | Inspect lock points, zero-energy evidence, and three de-isolation clearances. | `hse_demo_data.dd_loto_k301` |
| Bypass Management (Inhibits) | Review criticality, compensating measures, authorization, and reinstatement. | `hse_demo_data.dd_byp_sis` |
| Preparation Activities (TBT) | Demonstrate a work package with three of four readiness gates complete. | `hse_demo_data.dd_prep` |
| Critical Lift & Rigging | Calculate load utilization and review lift-plan controls. | `hse_demo_data.dd_lift` |
| Excavation & Trenching | Inspect utility clearance, soil classification, and trench protection. | `hse_demo_data.dd_excavation` |
| Industrial Radiography (NDT) | Review source controls, exclusion boundaries, and radiation protection. | `hse_demo_data.dd_radiography` |

### Environment & ESG — 6 areas

| Area | What to show | Stable sample |
|---|---|---|
| ESG Carbon Accounting & Balance | Inspect scopes 1–3, intensity metrics, water circularity, and waste diversion. | `hse_demo_data.dd_esg` |
| Air Emissions & GHG Protocol | Compare routine combustion and a flagged flare-monitoring event. | `hse_demo_data.dd_air_boiler` |
| Wastewater & Outfall Monitoring | Contrast an acceptable sample with pH and oil-and-grease exceedance. | `hse_demo_data.dd_water_exceedance` |
| Hazardous Waste Manifests (RCRA) | Follow waste storage deadlines and cradle-to-grave shipping evidence. | `hse_demo_data.dd_waste` |
| Spill & Release Remediation | Review containment, recovery efficiency, and remediation progress. | `hse_demo_data.dd_spill` |
| LDAR Fugitive Components (EPA 21) | Trace component monitoring, leak thresholds, and repair clocks. | `hse_demo_data.dd_ldar_leak` |

### Occupational health — 7 areas

| Area | What to show | Stable sample |
|---|---|---|
| Exposure Monitoring & Air Sampling | Compare exposure results against illustrative limits and required controls. | `hse_demo_data.dd_ih_overexposure` |
| Similar Exposure Groups (SEGs) | Group similar tasks and workers for exposure monitoring. | `hse_demo_data.dd_seg` |
| Biological Monitoring (BEI) | Inspect synthetic biomonitoring results and occupational-health follow-up. | `hse_demo_data.dd_biological` |
| Radiation Dosimetry (TLD) | Review badge monitoring and cumulative-dose indicators. | `hse_demo_data.dd_radiation` |
| Audiometry & Hearing Conservation | Compare a baseline and annual audiogram with a threshold-shift example. | `hse_demo_data.dd_audiometry` |
| Respirator Fit Testing | Inspect fit-test evidence, medical clearance, and renewal dates. | `hse_demo_data/dd_respirator` |
| Ergonomics (REBA/NIOSH) | Translate manual-handling risk into workstation redesign. | `hse_demo_data.dd_ergonomics` |

### Contractor safety — 2 areas

| Area | What to show | Stable sample |
|---|---|---|
| Contractor Profiles & Prequalification | Review prequalification, insurance, worker inductions, and monthly KPIs. | `hse_demo_data.dd_contract_alpha` |
| Worker Site Inductions & Badges | Contrast active and expired fictional gate passes. | `hse_demo_data.dd_induction_expired` |

### Chemical safety — 2 areas

| Area | What to show | Stable sample |
|---|---|---|
| Safety Data Sheets (SDS) | Browse illustrative GHS information, review dates, and location inventory links. | `hse_demo_data.dd_sds_benzene` |
| Chemical Compatibility Matrix | Demonstrate acid/base segregation and incompatible storage rules. | `hse_demo_data.dd_compatibility` |

### Emergency response — 3 areas

| Area | What to show | Stable sample |
|---|---|---|
| Emergency Response Plans (ERP) | Inspect a training-only response plan, callout hierarchy, and muster points. | `hse_demo_data.dd_emergency_plan` |
| Simulation Drills & Headcount | Review evacuation performance and one unaccounted fictional badge. | `hse_demo_data.dd_emergency_drill` |
| Emergency Response Team (ERT) | Explore incident-command, fire, and rescue responsibilities. | `hse_demo_data.dd_ert_elena` |

### Risk & locations — 3 areas

| Area | What to show | Stable sample |
|---|---|---|
| Risk Assessments & JSA | Review task hazards, controls, and initial versus residual risk. | `hse_demo_data.dd_jsa_1` |
| Risk Matrix | Inspect the configured 5×5 severity/likelihood matrix and all 25 cells. | `hse.matrix_standard_5x5` |
| Location Safety Profiles | Navigate the plant hierarchy, chemical inventory, and live work counters. | `hse_demo_data.dd_plant` |

### Operations & compliance — 6 areas

| Area | What to show | Stable sample |
|---|---|---|
| Operator's Log (Shift Handover) | Review shift events, an abnormal round, standing alarms, and dual handover. | `hse_demo_data.dd_oplog_1` |
| Operating Procedures (SOP) | Inspect a published procedure with four steps and critical hold points. | `hse_demo_data.dd_sop_014` |
| Operating Policy | Review approved policy content and workforce acknowledgments. | `hse_demo_data.dd_pol_001` |
| Regulatory Compliance Standards | Connect obligations, audit evidence, and statutory filing tasks. | `hse_demo_data.dd_reg_osha_psm` |
| Statutory Compliance Calendar & Tasks | Prioritize overdue and upcoming obligations and submission evidence. | `hse_demo_data.dd_ctask_1` |
| Management System Audits | Inspect checklist findings, severity, and remediation tracking. | `hse_demo_data.dd_audit_iso` |

### Reliability & improvement — 7 areas

| Area | What to show | Stable sample |
|---|---|---|
| Management of Change (MOC) | Compare technical review, incomplete PSSR, and a commissioned change sample. | `hse_demo_data.dd_moc_pssr` |
| Non-Conformance Management (NCR) | Inspect quarantined material, traceability requirements, and disposition. | `hse_demo_data.dd_ncr_1` |
| Defect Elimination | Review a recurring compressor bad actor and elimination strategy. | `hse_demo_data.dd_defect_k301` |
| Failure Reporting (FRACAS) | Trace failure mode, mechanism, and operational impact. | `hse_demo_data.dd_fail_k301` |
| Solutions & Lessons Learned | Share transferable reliability and safety lessons across facilities. | `hse_demo_data.dd_sol_1` |
| Benefits & Losses | Compare downtime and repair losses with avoided-cost estimates. | `hse_demo_data.dd_financial_loss` |
| Continuous Improvements (CI) | Follow a warehouse handling improvement from idea to approved business case. | `hse_demo_data.dd_impr_drums` |

### Workforce assurance — 4 areas

| Area | What to show | Stable sample |
|---|---|---|
| Competency Management | Inspect role standards, assessed proficiency, and validity requirements. | `hse_demo_data.dd_comp_agt` |
| Personnel Certification Tracking | Contrast expired, expiring, and valid workforce certificates. | `hse_demo_data.dd_pcert_sara` |
| Equipment Certifications | Review pressure-vessel, relief-valve, crane, and hazardous-area certificates. | `hse_demo_data.dd_cert_pv` |
| Training Matrix & Competency Gaps | Inspect missing, expired, expiring, and compliant training rows. | `hse_demo_data.dd_tm_2026` |

### Actions & meetings — 2 areas

| Area | What to show | Stable sample |
|---|---|---|
| All Actions (CAPA Engine) | Follow ownership, priority, due dates, evidence, and effectiveness verification. | `hse_demo_data.dd_capa_1` |
| Safety meetings & toolbox talks | Review attendance, minutes, and the connection to operational safety briefings. | `hse_demo_data.dd_meet_1` |

### Reference configuration — 4 areas

| Area | What to show | Stable sample |
|---|---|---|
| Hazard Settings | Configure hazard categories used in frontline assessment. | `hse_demo_data.dd_hazard_chemical` |
| Hazard Controls | Maintain the reusable library of isolation, monitoring, and exclusion controls. | `hse_demo_data.dd_control_gas` |
| Severity Levels | Inspect the reference classification used in risk assessment. | `hse_demo_data.dd_severity_major` |
| Incident Categories | Maintain the incident taxonomy for consistent reporting. | `hse_demo_data.dd_inc_category` |

## Client Q&A — accurate answers

**Is this a real application or a mock-up?** The hub resolves actual Odoo records/actions. Counts, risk indicators, exceptions and reports come from the database. Synthetic data is used deliberately.

**Does PSSR block commissioning?** Not in the current native implementation. Completion is computed; an enforcing commissioning gate would be additional work.

**Does contractor expiry control a physical gate?** No physical access-control integration is configured. The demo shows induction status and portal participation, not door enforcement.

**Is the spatial radar live positioning?** No. It compares synthetic coordinates within the same modeled location. Site mapping, real sensors and adjacent-zone hazard rules need separate engineering and integration.

**Are calculations and regulatory outputs certified?** No. Exposure limits, SDS text, GHG factors, consequence formulas, risk thresholds and monetary assumptions are illustrative and must be validated by qualified specialists.

**Can anyone read employee health data?** The contractor cannot access the presenter hub/downloads. Existing internal HSE access is broad; production medical privacy, company separation and segregation of duties need explicit review and hardening.

**Is every corrective action automatically one synchronized record?** The suite includes a central CAPA engine and legacy form-level corrective/preventive models. Both have populated examples. Do not claim automatic synchronization or deduplication between those record families.

**Can we send agency notices, email or SMS?** No real external delivery is configured, and cron is disabled in the supplied isolated runtime. Do not connect this fictional database to production endpoints.

**Will an update reset everything?** No. Stable `noupdate` sample IDs and the one-time enrichment marker preserve edits. Use the documented isolated-volume reset for pristine, fresh-dated data.

**Can this be deployed directly to production?** This kit is for client demonstration. Production needs lifecycle/version planning, security/privacy review, site-specific configuration, professional validation, integrations, operating procedures, backups and acceptance testing.

## Close the demonstration

“We have followed one connected safety picture: the worksite reports evidence, operations authorizes controlled work, engineering manages change, specialists investigate exceptions and leadership reviews assurance. The next step is to agree your priority workflows, approval authorities, data/privacy boundaries and required integrations.”

Capture: industry/site scope; priority journeys; real role/approval matrix; medical/privacy requirements; engineering and regulatory validation owners; integrations; migration and production-version plan. Avoid promises of certification or integrations not shown.

For setup and reset instructions, return to the [repository README](../README.md). For executed checks and unverified items, see [verification notes](VERIFICATION.md).
