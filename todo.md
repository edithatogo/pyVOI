# `voiage` Task List

This document lists the actionable tasks for `voiage` development. Agents should pick tasks from the "To Do" list.

## To Do

*   [x] Bind the Spack Polars runtime source to its exact verified sdist URL.
    *   Added regression coverage for the `_32` filename suffix after a native
        source build exposed Spack's ambiguous derived PyPI URL.
    *   Restored ignored solver evidence, verifying historical logs byte-for-byte
        against the original Git revision and the URL log against its manifest.

*   [~] Complete the authorized remaining backlog through
    `conductor/tracks/remaining_backlog_delivery_20260831/` (#1053): dependency
    delivery and Codecov controls (#656), measured opt-in testing (#1028), HPC
    recipes (#1025), remaining issue evidence, protected PR merges and verified
    cleanup. Keep unsatisfied human and external outcomes open.
    *   [~] Repair and validate the September Actions dependency update (#1092),
        preserving MSRV qualification and the historical R evidence boundary.
    *   [x] Add the stable Rust, Pydantic 2.13.4 and JSON Schema 4.26.0 provider layer for EasyBuild 2024a; native module qualification remains pending.
    *   [x] Add the Polars 1.42.1 provider layers for EasyBuild 2023a and 2024a with distinct dated-nightly Rust compilers; native module qualification remains pending.
    *   [x] Reconcile the EasyBuild 2024a root dependency with the provider's
        lowercase `polars` module name; native full-graph qualification remains
        pending.
    *   [x] Integrate the Arrow and PyArrow 25.0.1 EasyBuild 2024a provider overlay into the parent provider contract; native module qualification remains pending.
    *   [x] Add checksum-bound xarray 2024.11.0 and scikit-learn 1.7.2 provider recipes for both EasyBuild generations; native module qualification remains pending.
    *   [x] Add the checksum-bound Arrow and PyArrow 25.0.1 provider layer for EasyBuild 2023a; native module qualification remains pending.
    *   [x] Reconcile both EasyBuild root graphs with all provider overlays and
        retain generation-bound robot receipts; native builds and installed
        module qualification remain pending.
    *   [x] Add a guarded sequential native EasyBuild driver and fail-closed
        terminal receipt contract; actual 2023a and 2024a builds remain pending.
    *   [x] Enforce the NLTK 3.10.3 manuscript-tool security floor and retain a
        bounded disposition for the unpatched model-persistence advisory.
    *   [x] Refresh the cross-venue evidence contract after the final EasyBuild
        root-graph PR merge, binding PR #1087's exact tree-equal merge and
        terminal checks while retaining native, upstream, and venue gates (#614).
    *   [x] Repair the bounded Ruff 0.16 dependency-preview findings without
        promoting the preview dependency or widening Python support.

*   [~] Deliver the hardened v2.2.0 release through
    `conductor/tracks/v2_2_release_and_venue_submissions_20260830/` (#1037).
    *   [x] Synchronize package, binding, manuscript, and unposted candidate
        metadata; retain published citation metadata and validate locally.
    *   [x] Complete protected PR checks and exact-tree squash merge (#1038).
    *   [x] Complete signed tagging of the final checked source (#1046).
    *   [x] Complete private draft review, hash-bound publication, and
        public-artifact verification.
    *   [x] Replay the historical VOP calculation with the public v2.2.0 wheel
        through a hash-bound handoff between separate supported environments;
        retain the historical human-use record without adding an attestation.
    *   [x] Complete current venue-packet and manuscript repairs, verify the
        installed replay against public wheel bytes, retain the exact CSV,
        and review hosted PDF/HTML artifacts (PR #1051 merged as `0330fa55`;
        13 post-merge workflows passed and Julia Registry Sync was skipped).
    *   [ ] Proceed pyOpenSci first, then the eligible JOSS partner route and
        rOpenSci. Personal declarations are confirmed and previous requests
        withdrawn; survey completion and human-written submission text remain
        pending. Journal submission now precedes deferred arXiv action.
        *   [x] Refresh the local, unposted rOpenSci packet and bind the current
            R distribution inputs to the successful three-platform hosted
            matrix and full unsuppressed manual check without claiming zero NOTEs.

## Historical backlog and retained gate snapshots

The records below preserve task descriptions, checkboxes and status at their
source revisions; they are not the current executable queue. The 21 migrated
tracks are reconciled by the completed hardening programme's
[migration manifest](conductor/archive/pre_submission_comprehensive_hardening_20260829/migration-manifest.md).
Current execution belongs to the two active tracks above. Historical external and
scientific gates retain their evidence requirements; migration and release
publication do not automatically satisfy them.

*   [x] Complete the canonical pre-submission comprehensive-hardening programme
    in `conductor/archive/pre_submission_comprehensive_hardening_20260829/`
    (#1033): refresh venue and ecosystem requirements, run the whole-product
    feature/dependency/API/ABI gap analysis, profile and optimize tests and
    CI/CD, repair accepted findings, harden standalone R and polyglot packages,
    and complete exact-head assurance before any external submission.
    *   [x] Consolidate 21 prior active tracks and complete the dated
        requirements, feature, integration, data, dependency, API/ABI,
        structure, CI timing, and Scalene baseline.
    *   [x] Freeze dispositions and architecture, then repair core API/ABI,
        capability claims, dataset fixtures, interchange profiles, worked
        examples, and the four-domain executable workflow corpus.
    *   [x] Complete standalone R and Julia package hardening, dependency and
        measured CI/test optimization, venue/manuscript alignment, and final
        local plus exact-head hosted assurance.
    *   [x] Archive the completed programme after tree-equal merges, full local
        validation, exact-head hosted checks, and zero unresolved review threads.

*   [x] Prepare and validate an unposted pyOpenSci submission packet against a
    pinned current template, with an evidence-backed release candidate and all
    human or external actions left explicit.

*   [x] Complete Quality Frontier evidence-based hardening with Metamorphic Testing (MT) and Deterministic Simulation Testing (DST) suites (#657).
*   [x] Configure automated Gitleaks secret scanning and expanded continuous Rust and Python fuzz testing.
*   [x] Add structured GitHub Issue Forms, issue routing config, and root pull request template.
*   [x] Author CRediT taxonomy author statement and AI contribution transparency ledger (#323).
*   [x] Complete Industry Decision Problem and Intervention contracts (#566).
*   [x] Package Customer Churn & Retention worked example and dataset pack snapshots (#574, #575).
*   [x] Add curated Domain Templates and Adapter Registry (#577).
*   [x] Implement Decision Cards, Decision Registry, and signed result bundles (#580).
*   [x] Add Enterprise Model, Lineage, Metric, and Experiment Adapters (#583).
*   [x] Implement Decision-Focused Model Value (#576) and Policy/Uplift VOI (#578).
*   [x] Surface Industry Decision Contract Binding Dispositions across Rust, Python, R, Julia, and Mojo (#579).
*   [x] Implement Local Decision Studio and Business Reporting (#581).
*   [x] Implement Decision Correctness and Industry-Scale Assurance Suite (#584).
*   [x] Release 2.1.0 with the stable core and experimental frontier boundary.
    *   [x] Correct the regressing post-2.0.1 manifest identity and synchronize
        Rust, Python, R, and Julia release metadata.
    *   [x] Bind exact-head hosted checks, signed tag, staged artifacts,
        reviewed digests, and publication receipts in order.
    *   [x] Reconcile the exact green conda-forge and Yggdrasil candidates
        after immutable release URLs and checksums exist. Their maintainer
        merges, generated registries, and indexing remain external gates.
    *   [x] Complete the repository-owned Yggdrasil maximum-platform-coverage
        contract: 15 included targets pass Buildkite and product-integrity
        validation, three exclusions are evidence-bound, and native macOS ABI
        and numerical smoke evidence is recorded. Yggdrasil PR #14292 merge,
        JLL generation, clean-depot JLL execution, Julia General registration,
        and indexing remain external gates.

For experimental frontier items, references to scientific review mean the
role-specific subagent review panel and separate orchestrating agent defined in
`conductor/archive/supported_frontier_method_completion_20260723/scientific-review-panel.md`.
The orchestrator freezes the candidate, gathers role-separated reports, preserves
dissent and synthesizes recommendations. The panel supplies structured
challenge evidence. The repository owner records the accountable scientific,
maintainer, and release decisions without claiming independent review;
destination registry and publication decisions remain separate external gates.

*   [x] Execute #318 Phase 5 orchestrated scientific review.
    *   [x] Umbrella #841 completed across sub-issues #842, #846, #847, #848, and #849.
    *   [x] Scientific remediation for estimation variance (#843), study design efficiency/COSS (#844), and CRRA stability (#845).
    *   [x] High-risk and remaining C17/C18 review waves with role-separated advisory panels (#846, #847).
    *   [x] Portable frontier contract packaging and installed parity verification (#848).
    *   [x] Findings synthesis and promotion-readiness recommendations (#849).
    *   Umbrella #841 governs the programme. Nested implementation issues are
        #842 (evidence contracts), #843–#845 (Wave A remediation), #846–#847
        (remaining review waves), #848 (installed/parity assurance), #849
        (synthesis/adjudication), and #850 (sampling-acquisition harms).
    *   SR1–SR10 govern candidate freeze, evidence schemas, the #619/#571/#595
        Wave A panel, stochastic sampling-harm scoping, high-risk and remaining-
        family waves, installed/parity review, remediation re-review,
        orchestrator synthesis and accountable decision receipts.
    *   Initial panel findings include COSS commissioning and selection-
        uncertainty semantics, estimation specification/runtime and nested-
        assurance gaps, vector covariance units/scalarization, CRRA near-log
        stability, VoC presentation provenance, portable/installed evidence,
        lifecycle synchronization and Boolean-only promotion evidence.
    *   Any unresolved Critical/High finding or scientific dissent keeps the
        affected family experimental. Do not infer scientific acceptance,
        parity, promotion, release, publication, registry acceptance or issue
        closure from repository delivery or hosted-green checks.
    *   [~] Materialize #850 sampling-acquisition-harm governance as v1.3.0
        Must C18/M32 in track `sampling_acquisition_harm_voi_20260802`.
        Automated primary-source/estimand review and Critical/High remediation
        are complete; #851 (unsupported capability and negative discovery) and
        #852 (source/estimand packet) are repository-owned slices. #853/H8
        candidate-bound independent reports and human confirmations remain
        pending. H8-A selects only the generic automatic-scalar or study-
        authorizing kernel as the review target for a proposed exclusion;
        parameterized constrained/vector research remains outside that scope.
        The exclusion itself is not yet reviewed. H8-B evidence-contract
        hardening and H8-C exact freeze are complete. H8-D-A/H8-E-A retain a
        five-role automated challenge panel and separate synthesis with one
        Critical, fifteen High and three Medium pending findings. The panel is
        non-human, estimator-assurance independence is disqualifying and
        source review remains blocked, so H8-D/H8-E are not satisfied. H8-D–H8-H
        continue to govern the exact #850 freeze, eligible independent panel,
        separate orchestrator synthesis, finding/dissent disposition, two
        distinct scientific and domain/ethics humans, a conditional chair,
        separate maintainer decision and fail-closed governance readback. No
        runtime or real-study authorization exists.
        Native child #864's bounded post-challenge repository preparation is
        complete through PR #865 exact head `973a79dc`, squash-merged as
        `03277fef` after 38 successful checks, three governed skips, one neutral
        result and zero failures, pending checks or unresolved threads. Its
        machine-enforced #571/#598 non-aliases, post-#863 administrative delta,
        nineteen pending findings and fail-closed source/reviewer intake cannot
        satisfy or bypass H8-D–H8-H.
        Native child #867's repository-owned preparation completed through PR
        #868 exact head `ee9da9ba`, squash-merged as `b60d6ee9` after 38
        successful checks, three governed skips, one neutral result and zero
        failures, pending checks or unresolved review threads. It records
        current automated observations for the six frozen sources and
        partitions all nineteen pending findings into repository re-review,
        source-review and candidate/human prerequisites. The historical packet
        remains immutable, no source bytes or authority are retained, and a
        replacement packet remains `not_ready_to_freeze`. Issue #867 and its
        Project item are Closed/Done/Resolved/Verified/Clean, but accountable
        external inputs must still satisfy their own gates.
        Native child #870 completed a deterministic human commissioning
        preflight and role-specific handoff. Its recommended reviewed-exclusion
        path, alternatives, source/finding bindings, eligibility/conflict
        screening, digest contracts and privacy safeguards remain preparation
        only: the candidate choice, source authority, eligible reviewers,
        replacement packet and H8-D through H8-H are still accountable gates.
        PR #871 exact head `305bdad5` completed 38 successful checks and four
        governed skips with zero failures, pending checks or unresolved review
        threads before squash merge `8c710245`; #870 and Project 28 read back
        Closed/Done/Resolved/Verified/Clean while retaining Human/Critical.
        Native child #873 now records owner-authored option 1: independently
        review the proposed generic-kernel exclusion while preserving narrower
        non-authorizing research. It and Project 28 read back
        Closed/Done/Resolved/Verified/Clean. The receipt advances only candidate
        selection and preserves the historical unset preflight. Native child
        #876 is Open/In Progress/Blocked/Human/Critical/Clean for independent
        source retrieval, rights/applicability review, eligible reviewer
        assignment and a replacement packet. All nineteen findings, H8-D
        through H8-H, runtime, study, release and publication remain pending.
        PR #877 exact head `8de3a40a` completed 38 successful checks and four
        governed skips or neutral outcomes with zero failures, pending checks
        or review threads before squash merge `b3138ae7`. This closes only
        H8-D-E repository delivery; #876 remains the next Human/Critical gate.
        Canonical VOP C18/M32 planning is synchronized by merged PR #71 at
        `e0ff1d2ce3361d52ee22bb01e105b92653ed606c`; this is planning evidence,
        not H8 approval or runtime authority.
        VOIAGE PR #855 merged the repository delivery as
        `62d22743b1547266bd554b215f957934bf577234` after its exact-head matrix;
        hosted assurance is satisfied without satisfying #853/H8 or runtime
        authority.
        VOIAGE PR #863 exact head `13456c7a` passed 38 checks with three
        governed skips, one neutral summary and zero unresolved threads before
        squash merge `0c3f4314`; this is automated preparation evidence only.

*   [x] Complete #318 repository-owned programme closeout stages G14 and G15.
    *   G5–G15 repository-owned evidence and governance reconciliation is
        complete in `g5-g13-evidence-map.json` and
        `repository-completion-receipt-20260802.md` at source revision
        `163825d8`; G8 remains engineering review rather than scientific
        approval.
    *   PR #836 exact head `8f1d70cb` passed all 42 terminal-allowed checks,
        had zero review threads, and merged as `163825d8`.
    *   Do not close #318 or open family-parent issues from this stage. Retain
        scientific/design/classification, #599 sparse-subgroup, #600
        continuous/fitted-estimator and risk-composition, #619 covariance
        scalarization, Rust/R/Julia parity, stable promotion and release gates.

*   [ ] Complete outcome-conditional sample-information value after
    experimental merge.
    *   GitHub issue #600; delivery subissues #790–#792; umbrella track
        `supported_frontier_method_completion_20260723`; phases F600-1–F600-4;
        canonical C18/M31; planned v1.3.0 Should.
    *   The repository-owned slice is exact finite Python: predictive and
        posterior outcome laws, `delta-EV_x`, `VSI_x`, EVSI, Equation 10's
        weighted population `sigma-VSI`, `rVSI_delta`, quantiles/tails,
        complete ties, strict schemas, API/CLI and result assurance.
    *   Preserve expectation-only tower identities. Keep `rVSI0` distinct from
        policy-switch/tie-set-change mass, and do not reproduce the paper's
        unweighted MATLAB/Table 3 standard-deviation calculation.
    *   Final independent re-review found no open Critical, High or Medium
        finding after probability normalization, exact-reference and inclusive-
        boundary remediation. PR #831 exact head `eb5a201d` completed all 42
        terminal-allowed checks with 38 successes, three governed skips and one
        neutral CodeQL aggregation. All five review threads were resolved
        before squash merge `ac1d31bf`. Delivery subissues #790, #791 and #792
        may close.
    *   Remaining gates include continuous-outcome and fitted-estimator
        validation, independent scientific review, risk-sensitive composition,
        Rust/R/Julia parity, stable promotion, release, parent #600 closure and
        umbrella #318 closure.

*   [ ] Complete static/dynamic heterogeneity value after experimental merge.
    *   GitHub issue #599; delivery subissues #786/#788/#789; umbrella track
        `supported_frontier_method_completion_20260723`; phases F599-1–F599-4;
        canonical C18/M30; planned v1.3.0 Should.
    *   The exact finite Python slice reports `C0`, `Cf`, `P0`, `Pf`, static and
        dynamic value, population-common and subgroup-policy EVPI, subgroup
        policies, complete ties, an optional separate EVSI extension and exact
        identities without replacing the stable heterogeneity helper.
    *   Fresh independent engineering review found and remediated a High
        model-bound result-assurance defect, then passed with no remaining
        Critical, High or Medium findings. PR #809 exact head `b0fc8db7`
        completed all 42 terminal-allowed checks with 38 successes, three
        governed skips and one neutral CodeQL aggregation; it had zero review
        threads before squash merge `1a37526a`. Delivery subissues #786, #788
        and #789 may close. Remaining gates are named subgroup scientific
        validity, selection-bias and sparse-subgroup validity review,
        Rust/R/Julia parity, stable promotion, release, parent #599 closure and
        umbrella #318 closure.

*   [ ] Complete signed/social information value after experimental merge.
    *   GitHub issue #598; native subissues #783–#785; umbrella track
        `supported_frontier_method_completion_20260723`; phases F598-1–F598-5;
        canonical C18/M29; planned v1.3.0 Should.
    *   The merged exact finite Python slice covers named agents and
        roles, signal topology, nonanticipative centralized/fixed/declared-
        response/verified-equilibrium catalogs, signed agent/role/social values,
        selective sharing, full transfer/cost ledgers, rights receipts and
        harm/avoidance/switch/winner-loser diagnostics without clipping.
    *   PR #808 exact head `4d121b29` completed all 42 terminal-allowed checks
        with 38 successes, three governed skips and one neutral CodeQL
        aggregation, including installed-wheel and full-suite assurance. All 10
        review threads were resolved before squash merge `d649c344`. Delivery
        subissues #783–#785 may close. Remaining gates are the named scientific
        panel, Rust/R/Julia parity, stable promotion, release, parent #598
        closure and umbrella #318 closure. Persuasion, mechanism design,
        rational inattention and general games remain adjacent.
*   [ ] Complete belief-state and intervention-aware sequential information
    value after experimental repository delivery.
    *   GitHub issue #597; delivery subissues #780--#782; umbrella track
        `supported_frontier_method_completion_20260723`; canonical C18/M28.
    *   The exact finite Python contract uses control-transition-observe-update
        chronology and matched closed-loop/no-information Bellman comparators.
        It reports gross/net, myopic/nonmyopic and conditional sensing value,
        complete ties, belief/policy trees, horizon value, regret, exact bounds,
        null-sensor and posterior-martingale assurance.
    *   Action-dependent learning and dual control are diagnostics; no unique
        additive dual-control value is claimed.
    *   PR #807 exact head `35cfe522` completed all 42 terminal-allowed checks
        with 38 successes, three governed skips and one neutral CodeQL
        aggregation. All three review threads were resolved before squash merge
        `39de9c6a`; delivery subissues #780–#782 may close. Remaining gates are
        the named scientific panel, Rust/R/Julia parity, stable promotion,
        release, parent #597 closure and umbrella #318 closure.

*   [ ] Complete event-localized information value after experimental delivery.
    *   GitHub issue #596; delivery subissues #777–#779; umbrella track
        `supported_frontier_method_completion_20260723`; canonical C18/M27.
    *   The exact finite Python contract evaluates declared event/complement
        revelation, symmetric imperfect binary-channel accuracy and the
        policy-relative EUI density with complete ties, signed centered
        diagnostics, integral assurance, modes, directions, API/CLI and plots.
    *   PR #804 exact head `e6835358` passed all 42 hosted checks with 38
        successes and four governed skips, including installed-wheel and 100%
        changed-branch assurance, before squash merge `e3a62eba`; governed
        closeout PR #805 exact head `d8f5e2e3` then passed all 37 checks and
        squash-merged as `74113b5a`. Delivery subissues #777–#779 are closed.
        Monetary BPI remains delegated to #595.
        Remaining gates are the named scientific panel, Rust/R/Julia parity,
        stable promotion, release, parent #596 closure and umbrella #318 closure.

*   [ ] Complete uncertainty-modelling value after experimental repository delivery.
    *   GitHub issue #594; native subissues #774–#776; Conductor track
        `uncertainty_modelling_value_20260801`; canonical C18/M26.
    *   The exact finite Python slice covers a declared point estimate,
        two-/multistage shared-history policies, EEV, recourse, wait-and-see,
        VSS/EVIU, EVPI, minimization/maximization and infeasible recourse.
    *   PR #798 exact head `aa5d9fd8` completed all 42 hosted checks with 38
        successes and four governed skips; every wheel contract, aggregate
        coverage, CodeQL and security assurance passed, and all four review
        threads were resolved before squash merge `c5adca8f`.
    *   Repository-delivery subissues #774–#776 may close. Remaining gates are
        independent scientific review, Rust/R/Julia parity, stable promotion,
        release, parent #594 closure and umbrella #318 closure. DVSS/VMS require
        separately approved reference contracts.

*   [ ] Complete implementation-information decomposition after experimental
    repository delivery.
    *   GitHub issue #593; delivery subissues #766--#768; umbrella track
        `supported_frontier_method_completion_20260723`; phases F593-1--F593-4;
        canonical C18/M25.
    *   The strict finite Python contract covers EVPIM, EVSIM, realizable EVPI,
        EVP, IA-EVSI, interaction, uptake changes, exact identities and CLI/API
        execution without an implementation-information independence assumption.
    *   Retain the legacy `value_of_implementation` multiplier as a distinct
        compatibility helper. Independent repository re-review passed at signed
        review-artifact commit `f945f87b`, with patch-equivalent rebased
        boundary `f52feb28`. PR #787 exact head `de31458b` passed all 42 hosted
        checks, including installed-wheel and 100% changed-branch assurance;
        both review threads were evidence-resolved before squash merge
        `20e0c606`. Remaining gates are named scientific review, Rust/R/Julia
        parity, stable promotion, release, parent #593 closure and umbrella
        #318 closure.

*   [ ] Complete forecast and signal information VOI after experimental delivery.
    *   GitHub issue #572; native subissues #759, #760 and #762; umbrella track
        `supported_frontier_method_completion_20260723`; phases F572-1--F572-3;
        canonical C18/M23.
    *   The exact finite Python contract separates timely-oracle value, signed
        deployed value, calibration loss, regret avoided and maximum price.
    *   PR #770 exact head `c110706c` passed all hosted checks and 100% changed
        coverage before squash merge `4657f94e`.
    *   Remaining gates are independent scientific review, continuous and
        multistage methods, Rust/R/Julia parity, stable promotion, release and
        parent closure.

*   [ ] Complete risk-sensitive and constrained VOI after experimental delivery.
    *   GitHub issue #570; native subissues #757, #758 and #761; umbrella track
        `supported_frontier_method_completion_20260723`; phases F570-1--F570-3;
        canonical C18/M22.
    *   The exact finite Python contract covers declared expected utility,
        lower-tail CVaR, minimax regret, deterministic/chance constraints,
        matched feasible policy sets, complete ties and fail-closed assurance.
    *   PR #769 exact head `f513416f` passed all hosted checks and 100% changed
        coverage before squash merge `c25f3234`.
    *   Remaining gates are scientific review, Rust/R/Julia parity, stable
        promotion, release and parent closure.

*   [ ] Execute the Rust-first polyglot VOIAGE completion programme without
    promoting issue or Project status into implementation evidence.
    *   Root Conductor track: `rust_polyglot_voi_completion_20260723`.
    *   GitHub programme: #313; native workstreams: #314--#323.
    *   Materialized workstream tracks cover method census, landscape review,
        stable Rust completion, Value of Perspective, supported frontier
        methods, ML/LLM/agent VOI, binding parity, datasets/examples,
        quality/release automation, and contribution transparency.
    *   Workstream Conductor tracks:
        `voi_method_census_contract_reconciliation_20260723`,
        `external_voi_library_feature_parity_20260723`,
        `stable_voi_rust_core_completion_20260723`,
        `value_of_perspective_completion_20260723`,
        `supported_frontier_method_completion_20260723`,
        `ml_llm_agent_voi_20260723`,
        `polyglot_abi_binding_parity_20260723`,
        `datasets_worked_examples_20260723`,
        `quality_release_automation_20260723`, and
        `research_contribution_ai_transparency_20260723`.
    *   Execute each workstream's `plan.md` in dependency order; retain
        scientific review, rights, hosted CI, merge, release, publication,
        registry and human confirmation as separate gates.

*   [ ] Complete Value of Flexibility after experimental repository delivery.
    *   GitHub issue #559; umbrella track
        `supported_frontier_method_completion_20260723`; phases F559-1--F559-4;
        draft PR #723.
    *   Python timing-scenario execution, schemas, an enumerable fixture, CLI,
        documentation and dynamic-real-options compatibility repair are present
        on the branch.
    *   Remaining gates: independent implementation review, hosted exact-head
        checks, merge, scientific review, transition-aware policy extension,
        polyglot execution, stable promotion, release and issue closure.

*   [ ] Complete deterministic sensitivity and scenario analysis after
    experimental repository delivery.
    *   GitHub issue #556; delivery subissues #724--#728; umbrella track
        `supported_frontier_method_completion_20260723`; phases F556-1--F556-5;
        draft PR #723.
    *   Python callback and normalized-record execution, exact installed-wheel
        validation, one-way/two-way/scenario fixtures, CLI, tornado plot and
        documentation are present on the branch.
    *   Remaining gates: independent implementation review, hosted exact-head
        checks, merge, scientific review, Rust/R/Julia execution, stable
        promotion, release and issue closure.

*   [ ] Complete Value of Distribution-Family Information after experimental
    repository delivery.
    *   GitHub issue #557; delivery subissues #731–#735; umbrella track
        `supported_frontier_method_completion_20260723`; phases F557-1--F557-5;
        PR #736.
    *   Planned contract: v1.2.0; MoSCoW: Must; canonical requirements M19/M17.
    *   Experimental Python execution, strict installed schema/CLI, exact
        fixture, complete ties, signed net VDI, provenance, estimator assurance,
        independent implementation review and complete changed coverage are
        present on the branch.
    *   Keep this discrete-index EVPPI presentation distinct from
        distributional-equity VOI, full structural EVPI, model-discrimination
        EVSI and goodness-of-fit/model selection.
    *   PR #736 and governed closeout #737 are merged; #731–#735 are Done.
    *   Remaining gates include scientific terminology/partition approval,
        real probability provenance, polyglot parity, stable promotion, release
        and parent issue closure.

*   [x] Implement the portable qualitative value-of-information workflow.
    *   GitHub issue #558; delivery subissues #738–#742; umbrella track
        `supported_frontier_method_completion_20260723`.
    *   Planned contract: v1.3.0; MoSCoW: Should; canonical requirement M20.
    *   PRs #743 and #744 provide strict assessment/result/audit/rendering
        schemas, worked dissent/incomplete/adversarial fixtures, deterministic
        ordinal prioritization, immutable history, redaction, accountable
        AI/human-review provenance, installed Python/CLI execution, accessible
        rendering and complete changed-branch assurance.
    *   Never infer cardinal weights, probabilities, utilities, currency or a
        numerical VOI estimate from ordinal judgements.
    *   Retain practitioner/scientific review, stable promotion, polyglot
        execution, release and parent closure as separate gates.

*   [x] Implement experimental finite additive MCDA information value.
    *   GitHub issue #560; native delivery subissues #746–#750; umbrella track
        `supported_frontier_method_completion_20260723`.
    *   Planned contract: v1.3.0; MoSCoW: Should; canonical requirement M21.
    *   Freeze raw criterion units/directions, ex-ante value functions and
        normalization anchors, normalized nonnegative weights, the correlated
        finite joint uncertainty law and criterion/preference/joint
        perfect-resolution actions.
    *   Return baseline/conditional rankings and choices, complete ties,
        gross/net value, interaction/no-double-counting, regret, rank
        acceptability and expected/statewise Pareto diagnostics with exact
        enumeration assurance.
    *   Exclude AHP elicitation, outranking/veto/non-compensatory rules,
        post-information renormalization and imperfect-sample EVSI from v1.
    *   PR #751 supplies the exact Python evaluator, installed API/CLI,
        accessible plots, independent implementation review and fixtures.
        Scientific review, hosted exact-head/wheel assurance, Rust/R/Julia
        parity, stable promotion, release and parent closure remain open.

*   [ ] Complete the dependent information-source portfolio delivery.
    *   GitHub issue #582; native subissues #763–#765; Conductor track
        `information_source_portfolio_voi_20260801`; PR #772.
    *   Planned contract: v1.3.0; MoSCoW: Should; canonical requirement C18/M24.
    *   Experimental exact Python execution covers joint-world dependence,
        ordered feasible source sequences, conditional marginals and exact
        decision-value Shapley allocation without additive double-counting.
    *   PR #772 exact head `f1d6f77d` passed all hosted checks and 100% changed
        coverage before squash merge `55771017`.
    *   Remaining gates are scientific review, Rust/R/Julia parity, stable
        promotion, release and parent closure.

*   [x] Implement estimation-focused variance-reduction VOI.
    *   [x] Use a scale-aware tolerance for the floating-point total-variance
        bound and retain the discovered large-magnitude counterexample.
    *   Conductor track: `estimation_focused_variance_voi_20260727`.
    *   Planned contract: v1.2.0; MoSCoW: Must; canonical requirements M14/M17.
    *   GitHub issue: #619, native sub-issue of #318 under programme #313.
    *   Define scalar/vector-target `EVPPI_var` and `EVSI_var`, component
        units, variance or covariance functional, conditioning and sampling
        models, versioned result contracts, analytical/enumerable references,
        convergence assurance, CLI/reporting surfaces, and explicit language
        dispositions.
    *   Keep these estimands separate from decision-focused EVPPI/EVSI,
        sensitivity indices and estimator uncertainty.
    *   Experimental scalar Rust/Python execution, contracts, assurance,
        CLI/report/plot surfaces and documentation passed PR #676's exact-head
        matrix: 65 terminal contexts, 60 successes, four governed skips, one
        neutral CodeQL aggregation, zero bad or pending, and two resolved
        review threads before squash merge `9495fc3f`. Canonical sync PR #64
        passed 16 terminal contexts and merged as `cedc6fbb` with zero review
        threads. Delivery subissues #671--#674 are closed. E17 scientific
        classification and vector scalarization review, stable promotion,
        release, parent #619 closure and umbrella #318 closure remain separate
        gates. PR #837 exact head
        `076a29075e839e3cad49d0487dff0c4e2639845f` delivered the independently
        reviewed prior-predictive weighting, input-bound replay provenance and
        scalar result-consistency remediation, passed 65 terminal checks (60
        successes, four governed skips and one neutral conclusion) with zero
        review threads, and squash-merged as
        `366186b358abd775bea5fd2440d7e0ececb3ebaa`; the umbrella is resynchronized.

*   [x] Implement governed study-design efficiency and experiment portfolios.
    *   Conductor track: `study_design_efficiency_20260727`.
    *   Planned contract: v1.2.0; MoSCoW: Must; canonical requirements M15/M17.
    *   GitHub issue: #571, native sub-issue of #318 under programme #313.
    *   Implementation sub-issues: #680 (runtime), #681 (portfolio and user
        surfaces), and #682 (bindings, governance and assurance).
    *   PR #679 final exact head `ce5d7127` completed 65 terminal conclusions
        (60 successes, four governed skips and one neutral conclusion), with no
        pending or failed checks. Both review threads were resolved before
        squash merge `5d059a80`. Delivery subissues #680–#682 are closed.
    *   Add COSS over signed ENBS with evaluated design records, feasible
        range/set, deterministic optimum/tie/boundary behavior, uncertainty
        around the optimum and plotting inputs.
    *   Add EVSI/EVPI with common-unit/scaling checks, zero-EVPI behavior and a
        strict distinction from `total_voi / total_cost`.
    *   Reconcile existing plotting and legacy clinical-optimizer helpers
        before any maturity promotion.
    *   The exact portfolio slice covers additive signed ENBS, empty selection,
        capacities, dependencies, exclusions and guardrails; it requires
        declared metric, interference, sequential-monitoring, multiplicity,
        delayed-effect, duration/cost, stopping-rule and policy-change fields
        and returns gross/net EVSI and ENBS. Each model needs a provenance
        assurance of no effect or prior COSS incorporation; incremental costs
        must be provenance-declared as disjoint from COSS research cost, and
        tolerance ties use a fixed global maximum. Domain-specific adjustment
        estimators and platform adapters remain follow-on scope.
    *   Scientific review, Rust/R/Julia parity, stable promotion, release,
        parent #571 closure and umbrella #318 closure remain open.
*   [x] Implement expected-utility information pricing and VoC presentation.
    *   Conductor track: `risk_adjusted_information_pricing_20260731`.
    *   Planned contract: v1.2.0; MoSCoW: Must; canonical requirements M16/M17.
    *   GitHub issue #595 with native delivery subissues #694–#697 under #318.
    *   Repository implementation now provides EUI, CEI, BPI, SPI and anchored
        PPI with declared utility, wealth/reference, information/cost location,
        scope, root diagnostics, comparability and deterministic provenance.
    *   VoC delegates to the same expected-utility/clairvoyant-policy result;
        only verified positive-affine utility exposes the monetary EVPI alias.
    *   Rust and Python are executable; R and Julia are explicitly unsupported;
        Mojo remains an external boundary. PR #712 final exact head `1048c4bc`
        completed 65 terminal conclusions (60 successes, four governed skips
        and one neutral conclusion), with no pending or failed checks. Both
        review threads were resolved before squash merge `b8395abf`.
        Delivery subissues #694–#697 are closed.
    *   Scientific review, Rust/R/Julia parity, stable promotion, release,
        parent #595 closure and umbrella #318 closure remain open; VoC remains
        a presentation/delegating alias rather than a duplicate numerical
        method.

*   [ ] Complete standardized dataset ingestion through one format-neutral
    conductor input contract and optional source-format providers.
    *   Conductor track: `standardized-dataset-ingestion_20260723`.
    *   GitHub parent issue: #325.
    *   Native implementation sub-issues: #326--#333.
    *   Follow-on ecosystem and adoption sub-issues: #467--#468.
    *   Project: VOP–VOIAGE Conductor Roadmap #28.
    *   Preserve Arrow/Parquet interchange, xarray compute-facing structures,
        existing direct Python/CSV APIs, explicit VOI semantic bindings, and
        strict separation between core contracts and optional Croissant or
        Frictionless parsers.
    *   Keep source selection explicit and provider-owned: it may choose a
        declared source pair but must never become implicit projection or row
        filtering.
    *   Current merged increments establish the baseline contract, preparation
        boundary, optional CSV profiles, and provenance propagation. The
        unchecked acceptance criteria in the Conductor track remain active;
        issues #325--#333 and #467--#468 must not be closed or archived yet.
    *   The deterministic fixture-manifest validator now pins both checked-in
        source corpora; semantic and parser-differential conformance remains
        active under Phase 5.
    *   The current repository-owned endpoint is strict-local and offline-first.
        Controlled live interoperability is follow-on track
        `controlled_live_dataset_interoperability_20260801` / issue #752,
        pending approved rights-cleared source packets. General remote transport
        is follow-on track `remote_dataset_ingestion_security_20260801` / issue
        #753, pending an approved security policy and threat model.
    *   Canonical cross-format preparation now asserts identical NumPy and
        xarray compute-facing views without introducing a second runtime path.
    *   The canonical decision matrix now also exercises deterministic strict
        local Frictionless JSON Table, Parquet, and Arrow IPC file resources
        against direct preparation, EVPI, schema, and receipt identities;
        upstream-parser differential and live-source conformance remain active.
    *   CLI validation now has a credential-redaction regression contract for
        rejected descriptor resource URIs.
    *   Metadata-only CLI inspection now reports descriptor-declared tables,
        fields, keys, and known unsupported-feature diagnostics without opening
        resources or adding source-selection controls.
    *   ML and engineering reference descriptors now have executable CLI
        validation and inspection walkthroughs alongside the direct business
        DataFrame example.
    *   The reference-case matrix now records the fixture-specific EVPI/CEAF
        applicability boundary and proves CEAF plus normalized net-benefit
        parity only for the paired engineering cost/outcome inputs; it does not
        claim EVSI, EVPPI, ENBS, or perspective-split coverage.
    *   A separate explicit long net-benefit fixture now proves Croissant,
        Frictionless, and direct Arrow normalization parity; it does not claim
        that arbitrary long records have inferred decision semantics.
    *   DataFrame-interchange consumer tests now cover non-contiguous pandas
        slices, typed zero-row tables, and no-column producers without widening
        the supported producer contract.
    *   The README now links the conservative Croissant/Frictionless ingestion
        surface to its profile matrix, offline policy, and cross-domain examples.
    *   Verified offline-cache entries now reject symlinks and hard links so a
        cache object cannot be redirected or mutated through another path.
    *   The local benchmark matrix records bounded Croissant CSV and
        Frictionless CSV/JSON/Parquet/Arrow parse-to-Arrow, normalization,
        calculation, input-size, and memory evidence without treating elapsed
        time as a portable threshold or claiming remote/upstream performance.

## Completed public documentation

*   [x] Reconcile the public README and GitHub repository profile with the
    released v1.0 architecture, bindings, quality evidence, registries, paper
    status, and remaining external boundaries.

## Historical release and registry records

The current venue route is pyOpenSci first, then eligible JOSS partner review,
as recorded in the active task above; earlier route decisions below are historical.

*   [x] Complete repository-owned research-software registry and archival
    readiness after the
    immutable v1.0 release exists.
    *   Conductor track: `research_software_registry_readiness_20260721`.
    *   GitHub parent issue: #296, with Software Heritage, RRID, and JOSS
        deliverables in #297--#299.
    *   The arXiv-first manuscript lane is native subissue #312 under #299;
        PR #311 contains the final repository-owned review changes.
    *   Direct JOSS review is selected; native subissue #471 records
        demonstrated research use plus attributable human community
        engagement, external use, or collaborative input. Demonstrated use is
        a pre-review gate; engagement is a detailed-review criterion, strong
        positive pre-review signal, and author-selected prerequisite.
    *   PR #480 established the multi-role JOSS review loop, plain-language
        revision, explicit 1,600 ±2% article contract, SourceRight/AuthenText
        assurance, claim-to-interface reconciliation, and reproducibility
        evidence. PR #521 reconciled the current research-use criteria.
        Round nine now distinguishes generating from simulated results,
        tightens study-model interpretation, and passes locally at 1,583 words
        with 18/18 citation occurrences reconciled. Its hosted Open Journals
        PDF and six-page visual review passed for PR #522; the retained
        decision-maker wording passed its release-bound rebuild and six-page
        visual review in PR #529.
        The signed v2.0.0 GitHub, PyPI, TestPyPI, crates.io, provenance, SBOM,
        clean-install, and Software Heritage evidence is complete.
        The conda-forge recipe now requests the full supported Python 3.12+
        compiled matrix and tests the installed Rust core and a known EVPI
        result. Conda-forge's current Python 3.12 and 3.13 variants pass on
        Linux, macOS, and Windows; review and merge remain external.
        Author-confirmed AI attestation, final human source verification,
        and the external engagement record remain open. The release-bound PDF
        has passed its hosted build and six-page visual review. Conda-forge PR
        #34308 is under external review.
        Julia publication is tracked in #555. The Rust C ABI BinaryBuilder
        recipe is submitted in Yggdrasil PR #14292; JLL acceptance must precede
        the `bindings/julia` Registrator trigger and General merge.
        SciCrunch registration was submitted on 27 July 2026 after the portal
        found no similar resource and the account holder confirmed accuracy and
        terms. Curator review, RRID assignment, and resolver indexing remain
        external.
    *   The authenticated arXiv account was rechecked on 26 July 2026:
        submission `7861466` is absent from the active-submission table.
        Replacement `7870358` is an incomplete start-stage draft expiring
        9 August 2026 and is not completed submission evidence. Resolve that
        author and external gate before the arXiv-first JOSS submission step.
    *   Repository preparation is archived as complete. Identifiers,
        submission, review, acceptance, and indexing remain evidence-gated
        external states tracked by their open GitHub issues and handoff packet.

*   [x] Mature and harden the v1.0 release through the selected Rust-kernel
    takeover, legacy Python-kernel retirement, thin binding consolidation,
    Astro-only documentation, release-quality gates, registry verification,
    and signed final publication.
    *   Archived Conductor track: `mature-hardened-v1-release-programme_20260719`.
    *   Machine-readable baseline: `conductor/v1-programme-baseline.json`.
    *   Phases 1--6 are checkpointed: the stable contracts, production Rust
        workspace, PyO3/Maturin bridge, stable numerical kernels, and duplicate
        Python-kernel retirement are complete.
    *   Phases 7--10 now retain only Rust, Python, R and Julia repository
        surfaces, classify Mojo as an upstream boundary, make Astro the sole
        documentation source, and enforce signed solo-maintainer governance,
        coverage, mutation, sanitizer, Miri, continuous fuzzing, benchmark,
        dependency, SBOM and reproducibility gates.
    *   Signed public release: `v1.0.0`.
    *   Remaining registry review and indexing work is tracked by
        `research_software_registry_readiness_20260721`.
    *   Remaining work is the fail-closed Astro build, both merges, final v1
        version/evidence candidate, registry submissions and verification,
        signed publication, and explicit closeout of external indexing gates.

## Done

*   [x] Reconcile post-merge release/venue evidence and the historical backlog
    under R13f (PR #1052; `a6d748cc`). Full local tox passed all 15 environments
    with 4,601 tests passed and 95.11 percent coverage. At that checkpoint,
    declarations and contact-capacity eligibility remained R14 gates; hosted
    checks and merge of the reconciliation PR were separate from local completion.
    *   [x] Reconcile current venue projections with the verified withdrawal of
        requests #271 and #272 and defer arXiv until journal submission, without
        changing the unposted packet state or external human-action gates.

*   [x] Complete and archive the pyOpenSci-first/JOSS-fast-track repository-
    readiness track.
    *   PR #1029 merged with an exact reviewed-head tree match, 38 successful
        checks, four governed skips, and 13 successful post-merge main
        workflows.
    *   The archived schema-1.0 evidence ledger validates as a canonical
        UUID-keyed hash chain.
    *   Issue #471 remains open for factual non-author adoption evidence; no
        pyOpenSci inquiry or review and no JOSS referral, submission, editorial,
        publication, DOI, or badge action has been performed.

*   [x] Consolidate the distinct configuration and metamodel coverage retained
    from stale PRs #892, #925, #929, #940, #942, #954, #980, and #981 into one
    current-main implementation and preserve additive API behavior.

*   [x] Expose Rust-authoritative signed ENBS through the additive v1 C ABI and
    retained Julia binding without claiming JLL or General-registry delivery.

*   [x] Reconcile every Conductor track with GitHub issues, native subissues,
    Project 28, and evidenced completed-track pull requests.
    *   Archived Conductor track:
        `conductor/archive/conductor-github-cross-reference-reconciliation_20260724/`.
    *   GitHub issue #462 is closed, remains a native subissue of #322, and is
        recorded as Done in Project 28.
    *   PRs #465 and #810 merged after hosted validation.
    *   Historical tracks without a provable PR retain an explicit
        `none_found` evidence state rather than a guessed association.

*   [x] Bound TestPyPI JSON-to-Simple API propagation lag.
    *   Retry the exact reviewed wheel download for the same bounded six
        attempts used by the TestPyPI JSON and installation gates.
    *   Preserve failure after the propagation window and all exact-hash,
        provenance, and black-box smoke requirements.

*   [x] Preserve strict TestPyPI attestation verification through its Integrity
    API.
    *   Retrieve each provenance object from TestPyPI and verify it against the
        corresponding exact reviewed distribution.
    *   Keep Integrity API, identity, digest, signature, certificate,
        GitHub-provenance, hash, and Python 3.12--3.14 smoke failures blocking.

*   [x] Prepare the signed `v2.0.1-rc.4` TestPyPI candidate contract.
    *   Added explicit Cargo/Julia SemVer, Python PEP 440, and R numeric
        development-version projections without claiming R, Julia, or
        crates.io prerelease publication.
    *   Bound release filenames, TestPyPI queries, attestations, and smoke
        installs to the normalized Python identity while preserving the
        canonical signed tag and mixed-language SBOM identity.
    *   Superseded the unpublished RC1 staging attempt with RC2 after teaching
        the composer to root dependency-only CycloneDX Python inventories.
    *   Superseded unpublished RC2 with RC3 after adding the deterministic
        UUIDv5 serial number required by GitHub's SBOM attestation action.
    *   Published RC3 to TestPyPI with exact reviewed bytes and attestations,
        then superseded its hosted direct-URL verifier limitation with RC4's
        strict TestPyPI Integrity API verification.

*   [x] Normalize and archive the historical Conductor registry.
    *   Archived track:
        `conductor/archive/conductor-registry-normalization_20260727/`.
    *   Reduced the authoritative full-validator baseline from 223 errors to
        zero errors and zero warnings.
    *   Preserved external and superseded follow-ups without representing them
        as completed outcomes.

*   [x] Harden the repository-owned JOSS submission package.
    *   Added current JOSS paper sections, field comparisons, design
        trade-offs, reproducible near-term-significance evidence, archive
        references, and transparent AI-use boundaries.
    *   Added a fail-closed validator and pinned Open Journals/Inara hosted PDF
        build.
    *   Added a strict 2026 article contract, YAML and affiliation validation,
        1,600 ±2% target, comprehensive claim ledger, queued SourceRight
        sidecars, selected Authentext checks, and review-only Textstat evidence.
    *   Audited Python, Rust, R, and Julia reviewer installation paths and
        retained v2 publication, community engagement, AI attestation, the
        permanent arXiv identifier, submission, review, and acceptance as
        explicit gates.

*   [x] Strengthen the arXiv worked example with uncertainty and sensitivity
    evidence.
    *   Added fixed-seed bootstrap intervals for the reported probabilistic
        analysis, a prespecified one-way study-value sensitivity analysis, and
        machine-readable primary and sensitivity results.
    *   Removed the obsolete noncanonical manuscript and retained
        `paper/main.tex` as the only top-level paper source.

*   [x] Audit the arXiv manuscript for overclaiming and promotional language.
    *   Removed novelty and distinctiveness claims, qualified intended
        applications, and described the current Rust/Python boundary narrowly.

*   [x] Add cross-referenced glossary and abbreviation end matter.
    *   Expanded every abbreviation at first use and added labelled glossary
        and abbreviation sections to the canonical manuscript.

*   [x] Number the arXiv manuscript references sequentially by first citation.
    *   Switched the canonical BibTeX style from alphabetical `plain` ordering
        to citation-order `unsrt` ordering and verified the rendered sequence.

*   [x] Refocus the arXiv review draft on substantive VOI problems and
    contributions.
    *   Centered the manuscript on parameter, structural, population,
        implementation, evidence-system, and timing uncertainty.
    *   Distinguished established estimands from the package's novel shared,
        maturity-labelled decision-problem architecture.

*   [x] Align the arXiv review draft title and affiliations with the author's
    established manuscript records.
    *   Simplified the title to `voiage: Value of Information Analysis`.
    *   Reconciled the author name and three current affiliations against the
        `foi-o` and `vop_poc_nz` manuscripts.

*   [x] Apply the hardened LaTeX/arXiv template to the voiage manuscript.
    *   Made `paper/main.tex` the canonical semantic manuscript source and
        removed the obsolete Quarto/JSS generation path and tracked PDFs.
    *   Added deterministic source packaging, TeX Live 2023/2025 compilation,
        LaTeX lint, PDF/font assurance, semantic HTML, and independently
        rebuilt cleaner/collector variants.
    *   Pinned SourceRight and Authentext while preserving authorship,
        category, license, endorsement, upload, and acceptance as human or
        external gates.

*   [x] Complete the repository-owned Domain Abstraction Excellence work.
    *   Conductor track: `abstraction-excellence_20260719`.
    *   Human approval remains governed separately from implementation status.

*   [x] Complete the repository-owned Assurance Frontier work.
    *   Conductor track: `assurance-frontier_20260720`.
    *   Merge, release, publication, and issue closure remain explicit maintainer gates; agent-panel opinions provide all repository review input.

*   [x] Complete the repository-owned Operational Assurance Excellence work.
    *   Conductor track: `operational-assurance-excellence_20260720`.
    *   Baseline approval, merge, release, publication, and issue closure remain
        explicit maintainer gates; agent-panel opinions provide all repository review input.

*   [x] Add the engineering-frontier harness for logging, environments, typing,
    profiling, and expensive CI evidence.
    *   Pydantic v2 logging, SCM versions, Pixi/uv parity, `ty` plus
        BasedPyright, Scalene, mutation/security/experimental lanes, and
        cross-platform UTF-8/LF integrity are now explicit contracts.

*   [x] Harden Arrow interchange and dependency-frontier observability.
    *   Added versioned Parquet/IPC golden files, schema fingerprints,
        deterministic LF-normalized manifests, PyArrow/Polars and process-boundary
        conformance, performance guards, weekly dependency audits, and a
        non-blocking Python 3.14t observation lane.

*   [x] Consolidate the Conda handoff onto one native Maturin/Rust recipe.
    *   The release workflow replaces the version and SHA-256 only after the
        immutable PyPI sdist exists; staged-recipes review remains external.

*   [x] Strengthen context and harness engineering for the solo-maintainer
    workflow while retaining pull-request traceability and automated review
    gates.
    *   Added explicit agent context loading order and repository map, expanded
        fail-closed governance checks, and documented that independent review
        approval is intentionally not required.

*   [x] Enable tag-derived Python package versioning with `setuptools-scm`.
    *   Release tags now build exact Python versions; development checkouts
        produce identifiable development versions, while binding manifests
        remain synchronized to the latest reachable release tag.

*   [x] Prevent duplicate release-attestation generation across the TestPyPI
    and PyPI upload steps so the tag-driven publication workflow completes.

*   [x] Prepare the synchronized `0.2.1` release metadata and verify the
    tag-driven PyPI publication path.
    *   Updated the canonical Python version and all binding manifests in
        lockstep; release tagging and publication remain a separate hosted
        action.

*   [x] Archive the dynamic real-options VOI track after implementing the
    staged runtime and CLI; retain longitudinal-data, parity, and mature
    approval as explicit external gates.

*   [x] Archive the perspective-uncertainty VOI track after completing the
    runtime/evidence slice; retain real-data attribution, parity, and mature
    approval as explicit external gates.

*   [x] Archive the distributional and implementation VOI evidence track
    after adding provenance-preserving open-data snapshots and passing the
    repository and hosted CI gates; retain non-Python parity and stable
    approval as external gates.

*   [x] Restore OpenSSF Scorecard publication after the shared scanning rollout.
    *   Isolated the custom blocking-alert gate in a dependent least-privilege
        job that does not violate Scorecard workflow restrictions.

*   [x] Remove the runtime-only `ValueArray` import from the basic VOI methods.
    *   Moved the annotation dependency behind `TYPE_CHECKING` and retained the
        existing public type contract without runtime import overhead.

*   [x] Archive completed Conductor track records and repair their regression
    test and documentation references.
    *   Moved all completed registered tracks from `conductor/tracks/` to
        `conductor/archive/`, updated the registry/index links, and verified
        the archived evidence and status tests.

*   [x] Remediate the current lockfile dependency advisories.
    *   Updated the Python lockfile through the patched Jupyter Server,
        JupyterLab, mistune, soupsieve, bleach, tornado, idna, urllib3, and
        pytest releases; upgraded Astro/Starlight within a compatible major
        line; pinned the transitive esbuild resolution to a patched release;
        and updated the Starlight configuration for the current APIs.
    *   Verified with `pnpm audit --prod`, Astro check/build, and the complete
        tox matrix including Python 3.12 through 3.14, minimum/maximum
        dependency environments, coverage, docs, type, contract, and harness
        gates.

*   [x] Set up maximal repository harness engineering and GitHub security and
    quality controls.
    *   Added the fail-closed workflow/governance harness and tox gate,
        immutable action pins, least-privilege permissions, CodeQL gate repair,
        dependency review, OpenSSF Scorecard, Zizmor auditing, Renovate, and
        release provenance attestation.
    *   Applied repository merge/signoff settings and the active
        `main-maximal-quality` GitHub ruleset requiring pull requests,
        signed commits, linear history, resolved review threads, and required
        CI, dependency-review, and CodeQL checks. The review count is zero for
        the repository's single-maintainer operating model.
    *   Kept organization-owned policy, environment approvals, and unavailable
        plan-dependent secret-scanning enhancements explicitly external.

*   [x] Remove tracked generated artifacts and reconcile roadmap status labels.
    *   Removed committed pytest temp output, coverage reports, macOS metadata,
        legacy egg-info generated artifacts, and R CMD check output from
        version control.
    *   Removed tracked backup snapshots and added ignore/test coverage for
        common editor backup suffixes.
    *   Removed root-level legacy test scratch files and test result logs so
        active verification remains anchored under `tests/`.
    *   Removed stale root completion/coverage report mirrors, obsolete
        local-path mutation/demo scripts, and generated result outputs.
    *   Removed generated nbconvert notebooks and normalized local file links
        to portable repository-relative paths.
    *   Removed stale Qoder, repository-map, and legacy roadmap mirror
        documents that duplicated canonical project status files and described
        outdated placeholder or v0.1-era state.
    *   Removed remaining root Qoder quest output and duplicate planning,
        branch-architecture, CLI-changelog, repository-structure, and outdated
        todo mirrors.
    *   Removed legacy root JAX audit/setup, coverage-analysis, benchmark,
        verification, review, and testing-approach scaffolding that was not
        wired into maintained package, docs, tox, or CI surfaces.
    *   Fixed the Taskipy profile command and profiling script so the entry
        point targets the tracked script and current public API.
    *   Removed root-level generated CLI sample CSVs and pointed the README
        and CLI example script at the maintained `examples/cli_samples/`
        fixtures.
    *   Added the XML parser used by the ecosystem integration module to the
        base runtime dependencies and made the CLI example fail fast on
        command failures.
    *   Rewrote the stale root product, technology stack, workflow, and product
        guideline mirrors so they match the current roadmap, AGENTS workflow,
        Sphinx/Starlight documentation boundary, and >90% coverage gate.
    *   Fixed Sphinx heading and nested-list formatting in HPC developer docs
        so the warning-as-error docs gate passes.
    *   Added repo-local ignore coverage for macOS, tooling-cache, coverage,
        and temporary-output paths so local verification does not pollute
        future cleanup passes.
    *   Updated the roadmap so completed Conductor/spec/ecosystem phases are
        marked as repository-complete while external registry and hardware
        evidence gates remain explicit.

*   [x] Add free-runner pre-silicon FPGA/ASIC evidence tracks.
    *   Added a deterministic fixed-point EVPI-style RTL kernel, CPU fixture,
        manifest generator, committed FPGA/ASIC probe manifests, and GitHub
        Actions smoke workflow.
    *   Updated the FPGA and ASIC Conductor tracks so free CI evidence is
        first-pass progress while physical board, Tiny Tapeout, SkyWater MPW,
        and fabricated-silicon runtime remain external follow-up gates.

*   [x] Clean up HPC and Conductor tracking records after Colab GPU/TPU evidence capture.
    *   Normalized the HPC roadmap, accelerator/distribution docs, ASIC feasibility notes, and completed spec-track metadata so they distinguish visibility/parity evidence from production speedup evidence.
    *   Added regression coverage for Colab evidence paths, hardware-scope wording, and Conductor status contradictions.

*   [x] Add a Colab accelerator validation notebook for the HPC workflow.
    *   Added a compact notebook that clones the repo in Colab, installs the
        package, probes JAX CPU/GPU/TPU device visibility, checks EVPI parity,
        writes an evidence packet, and confirms FPGA/ASIC remain explicit
        placeholder adapters.
    *   Captured and persisted successful Colab T4 GPU and v5e TPU evidence
        payloads under the HPC acceleration abstraction handoff.
    *   Updated the HPC docs and Conductor feasibility records to cite the
        GPU/TPU evidence while keeping production speedup, FPGA, and ASIC
        claims evidence-gated.

*   [x] Create the SOTA strategy orchestration and dependency matrix guide.
    *   Codified the dependency graph, shared gates, and parallel lanes for the strategy work, then linked the guide into the developer docs.

*   [x] Complete the SOTA packaging review readiness, HPC distribution and
    acceleration strategy, Rust-core ABI and migration strategy, and polyglot
    repo/docs architecture tracks.
    *   Closed the strategy-layer roadmap work for submission readiness, HPC
        distribution policy, Rust ABI policy, and docs/repo structure, and
        captured the current-state / future-state summary in the roadmap.

*   [x] Make the community engagement surface explicit with support, security, and contributor guidance.
    *   Added repository support, code of conduct, and security policy documents, plus a support-question issue template and community guide links in the main docs.
    *   Covered by Conductor track: `community-engagement-support_20260507`.

*   [x] Make versioning SOTA by centralizing the canonical release version, synchronizing binding manifests, and adding a validator gate.
    *   Recorded the canonical versioning policy in the developer and release docs, synchronized the binding manifests to the canonical repo version, and wired the validator into tox and CI.
    *   Covered by Conductor track: `unified-versioning-policy_20260507`.

*   [x] Create the Starlight documentation platform track and record the versioning/plugin baseline in the roadmap and conductor setup.
    *   Added a dedicated Starlight docs-platform track, documented the versioning and plugin baseline, and marked the migration boundary against the current Sphinx docs.

*   [x] Align the validation and threshold frontier maturity labels and their docs.
    *   Updated the runtime, schemas, fixtures, examples, user guide, and setup docs so both surfaces now consistently report fixture-backed status.

*   [x] Complete CLI integration and docs wiring for the model-validation and threshold VOI tracks.
    *   Added `calculate-validation` and `calculate-threshold`, updated the frontier and migration docs, and closed the corresponding track checkpoints after the runtime, CLI, and fixture-backed slices landed.

*   [x] Implement the model-validation VOI runtime and fixture-backed conformance slices.
    *   Added the model-validation runtime shape, deterministic fixture-backed expectations, and the shared contract scaffold; the CLI entrypoint and docs wiring are now included in the completed track.
*   [x] Implement the threshold, tipping-point, and robust VOI runtime and fixture-backed conformance slices.
    *   Added the threshold runtime shape, deterministic fixture-backed expectations, and the shared contract scaffold; the CLI entrypoint and docs wiring are now included in the completed track.
*   [x] Create the Rust EVSI stochastic-kernel follow-on track and keep the EVSI summary boundary explicit.
    *   The Rust core already owns the EVSI summary contract; the new track now exists to port the stochastic kernel underneath that contract, add fixture-backed parity tests, and document the approximation policy.

*   [x] Add the Rust-core handoff, parallelism, and accelerator guidance pages.
    *   Documented the Rust-core boundary, the Rayon/SIMD feasibility policy,
        and the GPU/TPU/custom-circuit feasibility limits in the developer
        guide, then linked the new pages from the main docs index and the Rust
        binding README.
*   [x] Archive the Rust-core performance and profiling track after the new
    guidance pages closed the remaining feasibility work.
    *   Moved the completed track into `conductor/archive/` and updated the
        registry so the active backlog reflects the remaining numerics work
        only.
*   [x] Archive the Rust-core numerics engine track at the current contract
    boundary.
    *   Marked the EVSI summary boundary explicit, moved the completed track
        into `conductor/archive/`, and updated the registry so the active
        backlog no longer shows the numerics engine as open.

*   [x] Add the Rust EVPPI summary contract and close the Rust profiling memory/throughput measurement checkpoint.
    *   Implemented a deterministic Rust EVPPI analysis envelope and finalized the memory/throughput profiling phase-2 checkpoint for the Rust core.

*   [x] Add the Rust EVSI summary contract and the Rust profiling memory/throughput artifact and CI gate slices.
    *   Implemented a deterministic Rust EVSI analysis envelope, added a machine-readable memory/throughput profiling artifact for the scalar baseline, and wired the Rust benchmark job into CI.

*   [x] Reconcile the Rust numerics and profiling track bookkeeping.
    *   Closed the benchmark CI checkpoint and narrowed the remaining Rust-core open work to EVPPI, EVSI/frontier-adjacent kernels, and the unfinished profiling measurements/guidance phases.

*   [x] Archive the completed Rust-core migration foundation, domain model, bindings/release, and SOTA VOI frontier tracks after their final review checkpoints cleared.
    *   Moved the finished track folders into `conductor/archive/` and updated the registry so the completed work no longer appears as active backlog.

*   [x] Advance the Rust-core migration with the domain-model handoff, deterministic summary methods, scalar CPU benchmark baseline, and preference heterogeneity surface.
    *   Tightened the Rust core boundary, added deterministic dominance/CEAF/heterogeneity contracts in `voiage-core`, documented the migration handoff, and wired the preference front-end into the public Python API.

*   [x] Start the Rust-core migration program with the core boundary, domain model, deterministic scalar methods, and profiling baseline.
    *   Locked in Rust as the authoritative execution core, implemented the core data/reporting envelopes, added deterministic EVPI and ENBS kernels, and seeded a scalar CPU benchmark baseline for the Rust crate.

*   [x] Create the Rust-core migration program tracks for foundation, domain model, numerics, profiling, and bindings/release.
    *   Moved the execution core toward Rust in a staged way while keeping the Python façade and thin bindings/adapters aligned to the same contract.
    *   Kept profiling scalar-first and made the migration plan explicit about core ownership versus binding ownership.

*   [x] Complete the remaining documentation and CLI integration track bookkeeping.
    *   Archived the docs-developer-experience and cli-integration-testing tracks after closing the remaining doc, notebook, link-check, benchmark, and CLI branch-coverage slices.

*   [x] Add the docs-developer-experience notebook scaffold for EVPI, EVPPI, EVSI, and the getting-started tutorial.
    *   Added runnable validation/tutorial notebooks under `examples/` and verified they execute with `nbconvert`.
*   [x] Create the advanced methods tutorial notebook.
    *   Added `examples/advanced_methods.ipynb` covering structural VOI, NMA VOI, adaptive trial VOI, portfolio VOI, sequential VOI, efficient EVSI, CEAF, and extended dominance.

*   [x] Add the CLI benchmark and regression scaffolding for the core VOI methods.
    *   Added a lightweight `tests/benchmarks/` benchmark suite, backend comparison coverage, and deterministic regression payloads under `tests/regression_data/`.
*   [x] Add the end-to-end workflow, DecisionAnalysis, and cross-domain integration tests.
    *   Added smoke coverage for the EVPI/EVPPI/EVSI-to-plot path, the main `DecisionAnalysis` methods, and healthcare/financial/environmental factory entrypoints.
*   [x] Finish the R package documentation/manual track for the PDF reference manual and narrative vignette.
    *   Kept the package help pages, vignette, and deterministic PDF manual aligned with the release and verification guidance, then archived the completed track.
*   [x] Create the polyglot tutorial surface track for notebooks, vignettes, and language-specific walkthroughs.
    *   Aligned the Python notebooks, the R vignette/manual, and the non-Python binding walkthrough READMEs around the same canonical VOI use cases, then added repo-level smoke checks for the binding tutorials.

*   [x] Add the core API extension-evolution contract and archive the completed numerics track.
    *   Defined the additive-extension, versioning, and deprecation rules in `specs/core-api/extension-evolution.md`, then moved the completed numerics track into the archive registry.

*   [x] Create the missing user-facing method and reference pages for the docs surface.
    *   Added the Astro methods, plotting, CLI, data-structures, and backends pages, then wired them into the main docs index.

*   [x] Archive the completed HEOR naming track and clean the Conductor registry of duplicate live entries.
    *   Moved the naming brainstorm track into the archive and removed the redundant live duplicates for the already-complete cross-language, Python cleanup, and ecosystem tracks.

*   [x] Create the method implementation guide for the stable core VOI surface.
    *   Added a contributor-facing guide for extending the stable EVPI, EVPPI, EVSI, ENBS, CEAF, dominance, and heterogeneity methods, with a signature template and implementation checklist.

*   [x] Create the developer onboarding architecture and contribution guides.
    *   Added the Astro architecture and contribution pages, and wired them into the developer-guide index.

*   [x] Complete the Phase 1 core API conformance-fixture scaffold with a deterministic input bundle and runner helpers.
    *   Added the normative input bundle, wired the fixture manifest to input/output pairs, and taught the validator to load fixture cases directly.

*   [x] Align the polyglot release documentation and Conductor bookkeeping with the actual registry automation.
    *   Clarified which release paths are automated in-repo and which still depend on external feedstocks or registry processes.

*   [x] Add Vale prose linting for Markdown and reStructuredText documentation.
    *   Added a repo-local Vale config and style set, hooked the CI prose job to the real docs paths, and documented the command in `CONTRIBUTING.md`.

*   [x] Add CHEERS-VOI reporting objects and contract examples for the experimental frontier methods.
    *   Added shared reporting payload helpers, attached them to Value of Perspective, distributional/equity VOI, and implementation-adjusted VOI, and mirrored the fields in the frontier contract examples and schemas.

*   [x] Add CHEERS-VOI reporting metadata, structured result fields, and reproducibility outputs for every frontier method family.
    *   Added reporting envelopes to the remaining frontier contracts so every frontier result payload now carries the shared CHEERS-VOI baseline.

*   [x] Close the remaining SOTA frontier automated review checkpoints.
    *   Marked the documentation/release, dynamic real-options, and adjacent frontier review checkpoints complete after the corresponding track work landed.

*   [x] Define the cross-language core API runner contract and smoke validator.
    *   Added the runner guide for Python, R, Julia, and future TypeScript, Go, and Rust bindings, plus a narrow smoke validator for the fixture catalog layout.

*   [x] Add deterministic fixtures and reviewable example payloads for dynamic real-options VOI.
    *   Added the dynamic real-options contract scaffold, fixtures, registry entry, and contract tests.

*   [x] Define causal-identification, transportability, and external-validity VOI contracts.
    *   Added the causal-transportability contract scaffold with schema and example payloads for source-to-target population shifts.

*   [x] Define data-quality, measurement-error, data-acquisition, privacy, and linkage VOI contracts.
    *   Added the data-quality contract scaffold with schema and example payloads for acquisition costs, privacy constraints, and linkage weights.

*   [x] Define computational VOI and model-refinement VOI contract scope.
    *   Added the computational contract scaffold with schema and example payloads for compute budgets, approximation error, and refinement value.

*   [x] Define expert-elicitation VOI and evidence-synthesis design VOI contract scope.
    *   Added the expert-synthesis contract scaffold with schema and example payloads for elicitation costs and synthesis penalties.

*   [x] Define the shared maturity labels, diagnostics, reporting metadata, and handoff path for the adjacent frontier families.
    *   Added the adjacent-frontier shared-maturity contract scaffold with maturity labels, fixture-backed criteria, next-step requirements, and CHEERS-VOI reporting conventions.

*   [x] Add deterministic fixtures and registry entries for the adjacent frontier families.
    *   Added deterministic normative fixtures and registry entries for the causal, data-quality, computational, and expert-synthesis adjacent frontier contracts.

*   [x] Add CHEERS-VOI reporting objects to Value of Heterogeneity.
    *   Added the same reporting payload helper to the base distributional surface so the reporting model extends naturally from Value of Heterogeneity into distributional/equity VOI.

*   [x] Extend the CHEERS-VOI reporting baseline to CEAF and dominance.
    *   Added shared reporting payloads to the frontier summary outputs that feed the main cost-effectiveness analysis workflow.

*   [x] Extend the CHEERS-VOI reporting baseline to core scalar CLI outputs.
    *   Added shared reporting payloads to EVPI, EVPPI, EVSI, and ENBS JSON/CSV result output so the main command surface has a consistent reporting envelope.

*   [x] Add deterministic screening-program fixtures for Value of Perspective.
    *   Added a normative fixture manifest plus input/output payloads that anchor the fixture-backed CLI contract for the screening-program comparison surface.

*   [x] Implement distributional/equity VOI and implementation-adjusted VOI as experimental frontier methods.
    *   Added `value_of_distributional_equity` and `value_of_implementation` with `DecisionAnalysis` wrappers, curated exports, and regression tests.
    *   Kept the results explicit about subgroup weights, implementation uptake, adherence, coverage, delay, uncertainty, and maturity metadata.
    *   Added versioned experimental contract folders with deterministic JSON schemas and example payloads for both frontier families.

*   [x] Define the ecosystem module incubation policy for `voiage`.
    *   Documented the `voiage` role alongside `lifecourse`, `innovate`, `mars`, and HEOML.
    *   Kept the ecosystem scope focused on health economics and outcomes research.
    *   Reserved the HEOML `voiage` extension boundary for VOI handoff and VOI result metadata.
    *   Defined optional adapter gates and compatibility-fixture expectations.
    *   Kept `mars` as a fixed-API optional metamodel backend.

*   [x] Define the `lifecourse` integration contract and compatibility fixture plan.
    *   Added the v1 artifact profile scaffold for consuming `lifecourse` PSA outputs.
    *   Aligned the profile with HEOML while preserving `voiage` VOI-specific schemas.
    *   Documented the optional adapter and dependency policy.
    *   Added a shared result-envelope schema overlay and illustrative fixture for EVPI, EVPPI, EVSI, and ENBS metadata.
    *   Documented portable interchange formats and excluded pickle from the shared contract.
    *   Seeded a deterministic local compatibility fixture with EVPI and EVPPI reference payloads.
*   [x] Add compatibility versioning and exchange-validation docs for the `lifecourse` integration contract.
    *   Recorded the supported `voiage`, `lifecourse`, and HEOML profile versions in the fixture manifest and illustrative result envelope.
    *   Added deterministic EVSI and ENBS expectation payloads to the normative `lifecourse` compatibility bundle.
    *   Documented the artifact-exchange validation order, optional adapter boundary, and fixture-check expectations in the integration docs.

*   [x] Add CLI `--verbose` debug logging that writes diagnostics to stderr without changing stdout output.
*   [x] Add example config generation for `voiage generate-config evsi > evsi_config.json`.
*   [x] Ensure all CLI `--help` output includes working examples.
*   [x] Add CLI end-to-end smoke tests covering the full command surface with `CliRunner`, including the experimental perspective command pair.

*   [x] Define polyglot tooling parity and observability plan.
    *   Documented the Python-first tooling stack, mapped the per-language CI/package gates, and captured the logging and versioning contract for the polyglot bindings.
    *   Added a developer guide page that records the tooling split, versioning contract, and logging policy.
*   [x] Implement dynamic-programming portfolio VOI optimization.
    *   Replaced the placeholder with memoized budget-constrained subset selection, optional dependency-group value discounting, and regression tests proving DP can outperform greedy selection.
*   [x] Implement Value of Heterogeneity.
    *   Added subgroup-specific decision value calculations, numeric subgroup binning, optimal subgroup identification, and subgroup plotting.
*   [x] Implement dominance analysis and plotting.
    *   Added strong dominance, extended dominance, frontier extraction, ICER helpers, and a cost-effectiveness plane plot.
*   [x] Implement Cost-Effectiveness Acceptability Frontier (CEAF).
    *   Added CEAF calculation, plotting, uncertainty bands, and package export coverage.
*   [x] Add efficient and moment-based EVSI methods plus an EVSI CLI command.
    *   Added `evsi(..., method="efficient")`, `evsi(..., method="moment_based")`, efficient metamodel selection, and `voiage calculate-evsi`.
*   [x] Default calibration VOI to the built-in modeler.
    *   Made `voi_calibration` usable without a custom modeler by defaulting to the existing built-in calibration modeler.
*   [x] Add a built-in observational VOI modeler.
    *   Added a default observational modeler for explicit net-benefit or cost/effect PSA samples with sample-size and bias-strength uncertainty adjustment.
*   [x] Replace the JAX two-loop EVSI placeholder.
    *   Implemented a JAX-assisted posterior update and resampling path and added a regression test proving the NumPy fallback is not used.
*   [x] Replace the sequential VOI step-level EVPI placeholder.
    *   Implemented the standard EVPI formula for explicit net-benefit samples and added regression tests for payoff extraction, monotonic learning behavior, and resolved-uncertainty cases.
*   [x] Enforce 90% branch-aware Python coverage.
    *   Enabled branch coverage in the active coverage configuration and added targeted tests across schema, backend, structural VOI, config, financial-risk, healthcare, memory-optimization, and network meta-analysis paths.
*   [x] Scaffold polyglot binding package CI and release publishing.
    *   Added TypeScript/npm, Go module, Rust/crates.io, Julia, .NET 11/NuGet, and R package validation paths.
*   [x] Add regression coverage for the TreeAge invalid XML fail-soft path and warning emission.
    *   Locked in the empty-dict fallback and `UserWarning` emission for malformed TreeAge XML imports.
*   [x] Add regression coverage for callable import resolution and schema round-trips.
    *   Covered `import_callable` builtin resolution and model round-trip serialization for `DecisionOption` and `TrialDesign`.
*   [x] Lock the backend and method module export contracts.
    *   Added regression coverage for the curated `__all__` surfaces in `voiage.backends` and `voiage.methods`.
*   [x] Expanded the core API contract validator test to cover the full versioned schema/example matrix.
    *   Added matrix coverage for all versioned core API schema/example pairs.
*   [x] Add regression coverage for EVPPI handling of raw dictionary parameter samples.
    *   Confirmed `evppi` accepts raw dict parameter samples in addition to `ParameterSet` inputs.
*   [x] Complete the Python cleanup phase for public imports, result payload shapes, and diagnostic behavior.
    *   Confirmed the curated export surface, stable reporting payloads, and explicit EVPPI compatibility warning path against the stable contract.
*   [x] Add deterministic provenance metadata validation for normative core API fixtures in the versioned manifest.
    *   Added provenance validation for normative manifest entries and hardened validator tests.
*   [x] Seed the normative and illustrative core API conformance fixtures for `ceac` under `specs/core-api/fixtures/v1/`.
    *   Added normative and illustrative CEAC payloads and registered them in the versioned manifest.
*   [x] Sync the core API v1 README indexes with the CEAC contract.
    *   Added the CEAC schema and example references to the versioned results and examples README indexes.
*   [x] Sync the core API v1 schema README index with the full contract matrix.
    *   Expanded the schema README from the entity-only list to the complete stable v1 entity and result contract matrix.
*   [x] Add a stable core API result schema and example for CEAC outputs.
    *   Added the CEAC result schema, versioned example payload, and validator coverage.
*   [x] Stabilize the curated package export surface for `voiage.core`, `voiage.methods`, and `voiage.plot`.
    *   Replaced placeholder subpackage entrypoints with explicit re-exports and added regression coverage to lock in the package-level import surface.
*   [x] Stabilize the top-level `voiage` package export surface.
    *   Added a root package facade that re-exports the primary submodules and locked it in with regression coverage.
*   [x] Seed the illustrative core API conformance fixture for `evsi` under `specs/core-api/fixtures/v1/illustrative/`.
    *   Added an EVSI illustrative example fixture and registered it in the versioned manifest.
*   [x] Seed the normative and illustrative core API conformance fixtures for `enbs` under `specs/core-api/fixtures/v1/`.
    *   Added ENBS normative and illustrative benchmark payloads and registered them in the versioned manifest.
*   [x] Seed the illustrative core API conformance fixture for `evppi` under `specs/core-api/fixtures/v1/illustrative/`.
    *   Added an EVPPI illustrative example fixture and registered it in the versioned manifest.
*   [x] Seed the first illustrative core API conformance fixture under `specs/core-api/fixtures/v1/illustrative/`.
    *   Added an EVPI illustrative example fixture and registered it in the versioned manifest.
*   [x] Seed the normative core API conformance fixture for `evsi` under `specs/core-api/fixtures/v1/normative/`.
*   [x] Seed the first normative core API conformance fixture under `specs/core-api/fixtures/v1/normative/`.
*   [x] Seed the normative core API conformance fixture for `evppi` under `specs/core-api/fixtures/v1/normative/`.
*   **[TEST]** Added validation coverage for the versioned core API fixture manifest scaffold.
    *   Added the initial `manifest.json` contract and regression tests for manifest versioning, artifact resolution, and missing-artifact failures.
*   **[SPEC]** Create the versioned fixture layout under `specs/core-api/fixtures/v1/`.
    *   Materialized the normative/illustrative fixture tree and README scaffold for the Phase 1 conformance-fixture track.
*   **[INFRA]** Raise enforced coverage to 90% with targeted regression tests for deterministic public modules.
    *   Added focused regression coverage for deterministic backend GPU helpers and advanced backend delegation paths.
*   **[TEST]** Add focused CLI regression coverage for NMA VOI validation and error branches.
    *   Locked in NMA CLI config-file handling, invalid JSON reporting, and unexpected-exception branches.
*   **[TEST]** Added deterministic regression coverage for plotting and ecosystem integration modules.
    *   Locked in plotting validation and optional-branch behavior together with ecosystem import/export edge cases.
*   **[TEST]** Added targeted regression coverage for deterministic runtime modules.
    *   Expanded backend, ecosystem-integration, health-economics, CLI, schema, exception, and fluent-API tests to lock in current behavior and raise measured suite coverage substantially.
*   **[TEST]** Added focused regression coverage for NICE HTA scoring and decision thresholds.
    *   Locked in NICE evaluation scoring for evidence quality, cost-effectiveness, budget impact, and the resulting approval/rejection decisions.
*   **[DOCS]** Create a validation notebook for EVPI and EVPPI.
    *   The notebook replicates the benchmark case documented in the Astro
        validation-evidence guide and covers EVPI, EVPPI, EVSI, and plotting checks.
*   **[DOCS]** Create the remaining compact validation notebooks for NMA and structural VOI.
    *   Added runnable `examples/nma_validation.ipynb` and `examples/structural_voi_validation.ipynb` slices that execute the published-style NMA and structural VOI surfaces.
*   **[INFRA]** Created `AGENTS.md` to establish a protocol for AI agents.
*   **[INFRA]** Created `CONTRIBUTING.md` with technical development guidelines.
*   **[DOCS]** Updated `roadmap.md` to reflect the current project status.
*   **[INFRA]** Set up a `tox` configuration for automated testing and linting.
*   **[INFRA]** Implemented a pre-commit hook configuration for quality assurance.
*   **[INFRA]** Stabilized the `tox` test environment by fixing pytest marker configuration, restoring missing runtime/test dependencies, and resolving compatibility failures across schema, GPU, memory, clinical-trial, and metamodel code paths.
*   **[API]** Refactored the core logic into a `DecisionAnalysis` class.
*   **[API]** Established the initial domain-agnostic data schemas in `voiage/schema.py`.
*   **[DATA]** Finalized the transition to domain-agnostic data structures.
    *   Replaced internal direct dependency on legacy data-structure wrappers with `voiage.schema`.
    *   Standardized `DecisionAnalysis` and method signatures around `ParameterSet` and `ValueArray`.
*   **[EVSI]** Completed the EVSI implementation.
    *   Restored the `two_loop` path, added regression-based EVSI, and hardened the associated tests.
*   **[PLOT]** Implemented the core plotting functions.
    *   Added `voiage.plot.ceac` and `voiage.plot.voi_curves` for EVPI/EVSI visualization.
*   **[PAPER]** Added a synthetic health decision worked example.
    *   Generated deterministic CEAC-style, EVPPI, and ENBS visual evidence
        from one coherent programme-adoption model for the arXiv manuscript.
*   **[NMA]** Began the Network Meta-Analysis VOI implementation.
    *   Added the `voiage/methods/network_nma.py` workflow and supporting schema/tests.
