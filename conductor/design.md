# VOIAGE design

```mermaid
flowchart LR
    Literature[Literature census] --> Registry[Canonical method registry]
    Libraries[External library census] --> Registry
    Registry --> Rust[Rust numerical authority]
    VOP[Shared VOP C01/C02] --> Perspective[Perspective contracts]
    Registry --> Perspective
    Rust --> ABI[Versioned C ABI]
    Perspective --> ABI
    ABI --> Python
    ABI --> R
    ABI --> Julia
    ABI --> Mojo
    Registry --> ML[ML, LLM, and agent VOI]
    ML --> ABI
    Data[Rights-cleared evidence] --> Conformance[Cross-language conformance]
    Python --> Conformance
    R --> Conformance
    Julia --> Conformance
    Mojo --> Conformance
    Conformance --> Releases[v1.1, v1.2, v1.3]
```

GitHub issue #313 is the public programme record. Native subissues #314--#323
map one-to-one to active Conductor child tracks. Local specifications,
versioned registries, fixtures, and evidence remain authoritative for technical
completion; Project 28 is the synchronized public projection.

```mermaid
flowchart TD
    subgraph Discovery["Recorded discovery channels"]
        CRAN[CRAN and R-universe]
        PyPI[PyPI]
        Rust[crates.io]
        Julia[Julia General]
        Mojo[Mojo channels]
        Git[GitHub and GitLab]
        Web[Web and commercial documentation]
        Papers[Guidelines and software literature]
        Adjacent[Bayesian design and active learning]
    end

    Discovery --> Candidates[Candidate records]
    Candidates --> Evidence{Authoritative evidence?}
    Evidence -- No --> Reject[Record search limitation or reject hit]
    Evidence -- Yes --> Features[Feature-level inventory]
    Features --> Classify{Classify capability}
    Classify --> Estimand[Estimand]
    Classify --> Estimator[Estimator]
    Classify --> Workflow[Workflow or application]
    Classify --> Visual[Visualization]
    Classify --> Related[Related analysis]
    Estimand --> Methods[Canonical method IDs]
    Estimator --> Methods
    Workflow --> Methods
    Visual --> Methods
    Related --> Methods
    Methods --> Disposition[VOIAGE parity disposition]
    Disposition --> Matrix[Generated public feature matrix]
    Matrix --> Tests[Schema, traceability and freshness tests]
```

```mermaid
stateDiagram-v2
    [*] --> planned
    planned --> native: VOIAGE-owned implementation and tests
    planned --> equivalent: independent equivalent evidence
    planned --> adapter: migration or interchange only
    planned --> excluded: reviewed scientific, legal or architectural reason
    planned --> not_reproducible: behavior cannot be independently pinned
    adapter --> native: numerical authority moves into VOIAGE
    not_reproducible --> planned: new public evidence appears
    excluded --> planned: reviewed rationale expires or changes
```

The source registry is authoritative. The Markdown matrix is deterministic
derived output. Refresh automation may update machine-readable registry
metadata, but feature interpretation, exclusions, scientific maturity, and
license decisions remain reviewed changes.

```mermaid
flowchart LR
    Problem["Canonical Decision Problem"] --> Alternatives["Alternatives"]
    Problem --> States["Uncertain states"]
    Problem --> Actions["Information actions"]
    Problem --> Utility["Utility or loss"]
    Problem --> Context["Perspective, population, horizon, units"]
    Problem --> Provenance["Data and model provenance"]
    Draws["Posterior or predictive draws"] --> Problem
    Problem --> Estimator["Registered estimand and estimator"]
    Estimator --> Assurance["MC error, convergence, RNG, budget, stopping"]
    Assurance --> Result["Versioned Arrow and JSON result"]
    Result --> Bindings["Rust, Python, R, Julia, Mojo"]
```

The Decision Problem is the portable semantic boundary. Inference systems may
produce draws, but stable VOI calculations do not require their runtimes. Each
result carries estimator assurance rather than presenting a point estimate
without its numerical uncertainty.

```mermaid
flowchart TD
    Registry["Canonical method and capability registries"] --> Code["Rust facade and ABI"]
    Registry --> Matrix["Feature and maturity matrices"]
    Registry --> Docs["Astro documentation"]
    Registry --> Packages["Binding capability manifests"]
    Code --> Check{"Claim conformance"}
    Matrix --> Check
    Docs --> Check
    Packages --> Check
    Check -- mismatch --> Fail["Fail release"]
    Check -- aligned --> Evidence["Fixture-linked release evidence"]
    Drift["Quarterly and pre-release drift proposals"] --> Review["Human scientific review"]
    Review --> Registry
```

Machine updates may propose dependency and landscape changes. They do not
approve a method, exclusion, maturity promotion, or architecture decision.

```mermaid
flowchart TD
    Advisory["GitHub dependency graph and Dependabot alerts"] --> Renovate["Renovate"]
    OSV["OSV vulnerability feed"] --> Renovate
    Registries["Python, Cargo, npm, Actions, submodules"] --> Renovate
    Renovate --> Dashboard["Dependency and security dashboard"]
    Renovate --> PR["Immutable update PR"]
    PR --> Stability["Release-age and artifact checks"]
    Stability --> Protected["Maximal-quality required checks"]
    Protected --> Review{"Maintainer decision required?"}
    Review -- "Security, major, numerical, lock or submodule" --> Human["Maintainer review"]
    Review -- "Eligible ordinary non-major" --> Auto["Protected automerge"]
    Human --> Merge["Merge"]
    Auto --> Merge
    Merge --> Posture["Live alert and security-posture reconciliation"]
    Posture --> Release{"Release gate"}
```

Deleting `dependabot.yml` disables duplicate Dependabot version updates, not
GitHub's advisory alerts. Dependabot security updates remain a temporary
fallback until the Renovate App demonstrates a dashboard and checked PR; only
then are they disabled to ensure one update owner without a coverage gap.

```mermaid
flowchart LR
    VOP[VOP canonical contract]
    Mirror[Digest-pinned VOIAGE mirror]
    Perspective[Perspective method API]
    Arrow[Arrow IPC and Parquet]
    Polars[Polars consumer]
    Fixtures[Golden fixtures and manifest]
    Harness[Repository and benchmark harness]
    CI[Python 3.12–3.14 CI and security gates]
    External[External maturity and publication gates]

    VOP --> Mirror
    Mirror --> Perspective
    Perspective --> Arrow
    Arrow --> Polars
    Arrow --> Fixtures
    Fixtures --> Harness
    Polars --> Harness
    Harness --> CI
    CI --> External
```

```mermaid
sequenceDiagram
    participant V as VOIAGE method
    participant F as Fingerprint
    participant W as Arrow writer
    participant X as Fresh-process consumer
    participant T as Hosted tests

    V->>F: Describe ordered logical fields
    F->>F: Hash canonical JSON
    V->>W: Add shared contract metadata
    W->>X: IPC or Parquet artifact
    X->>T: Values, types, metadata and fingerprint
    T-->>V: Pass or fail closed
```

## Specialized VOI v1.2.0–v1.3.0

```mermaid
flowchart LR
    Target["Scalar/vector target + component units"] --> Functional["Variance/covariance functional"]
    Conditioning["Prior + conditioning convention"] --> Estimation["EVPPI_var / EVSI_var"]
    Sampling["Sampling model + design"] --> Estimation
    Functional --> Estimation
    Estimation --> Assurance["Estimator uncertainty + diagnostics"]

    Designs["Evaluated feasible designs"] --> EVSI["Decision EVSI"]
    EVSI --> ENBS["Signed ENBS curve"]
    Costs["Study + opportunity costs"] --> ENBS
    ENBS --> COSS["Optimum + tie/boundary state + uncertainty"]
    COSS --> Plot["Accessible plotting inputs"]
    EVSI --> Ratio["EVSI / EVPI"]
    EVPI["Commensurate EVPI"] --> Ratio
    COSS --> Candidate["Governed portfolio candidate"]
    PortfolioSemantics["Metrics + heterogeneity + delay + interference + multiplicity + stopping"] --> AssuranceDeclaration["No-effect or already-in-COSS assurance + provenance"]
    AssuranceDeclaration --> Candidate
    DisjointCosts["Incremental costs excluded from COSS + provenance"] --> Candidate
    Candidate --> Portfolio["Exact signed-ENBS subset allocation"]
    PortfolioConstraints["Capacity + dependencies + exclusions + guardrails"] --> Portfolio
    Portfolio --> GlobalTieSet["Fixed global maximum + one tolerance tie set"]

    Payoffs["Payoffs + state/signal probabilities"] --> CurrentEU["Optimize current-policy EU"]
    Utility["Named utility + wealth/reference state"] --> CurrentEU
    Utility --> InformedEU["Optimize informed/clairvoyant-policy EU"]
    Payoffs --> InformedEU
    CurrentEU --> EUI["EUI on utility scale"]
    InformedEU --> EUI
    CurrentEU --> CEI["Inverse-utility CEI"]
    InformedEU --> CEI
    CurrentEU --> Roots["BPI/SPI indifference roots + diagnostics"]
    InformedEU --> Roots
    EUI --> PPI["Anchored probability price"]
    InformedEU --> VoC["VoC alias/presentation governed by #595"]
    Affine{"Positive-affine utility?"} -->|yes| Monetary["Verified EVPI/EVSI reduction"]
    Affine -->|no| DistinctScale["Keep utility and monetary scales distinct"]

    DSABaseline["DSA baseline + direction + units"] --> DSAAdapter{"Callback or normalized records"}
    DSAAdapter --> DSAEvaluator["Shared deterministic evaluator"]
    DSAEvaluator --> DSASurfaces["One-way / two-way / scenarios"]
    DSASurfaces --> DSASwitches["Observed ties + bracketing switch intervals"]
    DSASurfaces --> DSARanking["Deterministic ranges + ranking"]
    DSARanking --> DSATornado["Accessible tornado plot"]
    DSASwitches --> DSABoundary["Not PSA, EVPPI, global sensitivity or VoI"]

    ModelFamilies["Declared model-family index + P(M|D)"] --> FamilyValues["Within-family conditional expected values"]
    FamilyValues --> CurrentFamilyPolicy["Current mixture-optimal policy"]
    FamilyValues --> ResolvedFamilyPolicies["Family-resolved policies"]
    CurrentFamilyPolicy --> FamilyVDI["Gross and signed net VDI"]
    ResolvedFamilyPolicies --> FamilyVDI
    FamilyVDI --> FamilyBoundary["Discrete-index EVPPI; not full structural EVPI"]

    QualDecision["Decision + agent-panel opinions plus accountable maintainer decision"] --> QualAssessment["Versioned qualitative assessment"]
    QualGaps["Information questions + evidence gaps"] --> QualAssessment
    QualJudgements["Ordinal impact, feasibility, timeliness, equity/ethics, burden and confidence"] --> QualAssessment
    QualAssessment --> QualPriority["Deterministic priority classes + complete ties"]
    QualDissent["Dissent + conflict + missingness"] --> QualPriority
    QualAI["AI provenance + unverified state"] --> QualHuman{"Human verified?"}
    QualHuman -->|no| QualIncomplete["Incomplete/unverified"]
    QualHuman -->|yes| QualResult["Recommendation classes + rationale"]
    QualPriority --> QualResult
    QualResult --> QualAudit["Immutable audit history + accessible rendering"]
    QualAudit --> QualBoundary["Not numerical VOI, MCDA, Delphi or evidence grading"]

    MCDAInputs["Alternatives + criteria units/directions + fixed value anchors"] --> MCDAKernel["Shared additive-value kernel"]
    MCDAWeights["Normalized nonnegative preferences"] --> MCDAKernel
    MCDAJoint["Finite correlated outcome/preference states"] --> MCDACurrent["Baseline ranking + complete choice ties"]
    MCDAKernel --> MCDACurrent
    MCDAActions["Criterion/preference/joint perfect resolution"] --> MCDAConditional["Conditional scores + choices"]
    MCDAJoint --> MCDAConditional
    MCDAKernel --> MCDAConditional
    MCDACurrent --> MCDAVOI["Gross/net MCDA information value"]
    MCDAConditional --> MCDAVOI
    MCDAVOI --> MCDADiagnostics["Interaction, regret, rank acceptability + Pareto"]
    MCDADiagnostics --> MCDABoundary["Not AHP, outranking, veto, renormalized scoring or EVSI"]

    ForecastArtifact["Declared forecast artifact; no training"] --> SignalLaw["P(outcome) × P(signal | outcome)"]
    SignalLaw --> Posterior["Signal probability + calibrated posterior"]
    Reported["Reported outcome probabilities"] --> DeployedPolicy["Feasible deployed action"]
    Posterior --> OraclePolicy["Timely oracle action"]
    Posterior --> DeployedPolicy
    Timing["Horizon + freshness + latency + lead time"] --> Usable{"Available and fresh at decision?"}
    DeployedPolicy --> Usable
    Usable -->|yes| ForecastValue["Signed deployed value + regret avoided"]
    Usable -->|no| BaselinePolicy["Baseline action; operational value zero"]
    OraclePolicy --> CalibrationLoss["Oracle value − timely deployed value"]
    ForecastValue --> MaximumPrice["max(0, deployed value)"]
    Cost["Acquisition cost in objective units"] --> NetForecast["Signed net deployed value"]
    ForecastValue --> NetForecast
    CalibrationLoss --> ForecastDiagnostics["Calibration L1 + Brier + coverage"]
    ForecastDiagnostics --> ForecastBoundary["C18 / M23: accuracy is not value; experimental Python only"]

    RiskStates["Finite states + declared probabilities"] --> RiskCurrent["Current feasible policy problem"]
    RiskPolicies["Statewise policy objective or declared utility"] --> RiskCurrent
    RiskFunctional["Expected value/utility, lower-tail CVaR or minimax regret"] --> RiskCurrent
    RiskConstraints["Deterministic/chance operational constraints"] --> RiskCurrent
    RiskStates --> RiskInformed["Perfect-state contingent policy problem"]
    RiskPolicies --> RiskInformed
    RiskFunctional --> RiskInformed
    RiskConstraints --> RiskInformed
    RiskCurrent --> RiskVOI["Gross/net risk-sensitive constrained VOI"]
    RiskInformed --> RiskVOI
    RiskVOI --> RiskDiagnostics["Complete ties + switches + risk/constraint diagnostics"]
    RiskDiagnostics --> RiskShadow["Exact constraint-removal evidence, not local shadow prices"]
    RiskShadow --> RiskBoundary["Experimental C18/M22; no EVSI, continuous solver or parity claim"]

    SignedWorlds["Complete finite joint-world law"] --> SignedPolicies["Nonanticipative bounded policy catalogs"]
    SignedTopology["Agents, roles, topology + sharing designs"] --> SignedPolicies
    SignedPolicies --> SignedLedgers["Pre-transfer + transfer + cost + post-transfer ledgers"]
    SignedWelfare["Declared cardinal comparability + welfare aggregator"] --> SignedLedgers
    SignedLedgers --> SignedValues["Signed private, role + social values"]
    SignedRights["Rights + consent + purpose receipts"] --> SignedValues
    SignedValues --> SignedDiagnostics["Selective sharing + harm + avoidance + switches + winners/losers"]
    SignedDiagnostics --> SignedBlackwell{"Aligned centralized refinement?"}
    SignedBlackwell -->|yes| SignedCheck["Strict gross nonnegativity check"]
    SignedBlackwell -->|no| SignedReasons["Explicit inapplicability reasons"]
    SignedCheck --> SignedBoundary["Experimental C18/M29; no persuasion, mechanism or general-game solver"]
    SignedReasons --> SignedBoundary

    EventStates["Finite states + coordinates + declared event"] --> EventBaseline["Baseline-optimal reference policy"]
    EventBaseline --> EventDensity["C18/M27 policy-relative EUI density"]
    EventStates --> EventDensity
    EventStates --> EventChannel["Perfect event + imperfect symmetric binary channel"]
    EventDensity --> EventAssurance["Integral + modes + directions"]
    EventChannel --> EventAssurance
    EventAssurance --> EventBoundary["Experimental Python; monetary BPI remains #595"]

    SampleStates["Finite states + prior"] --> Predictive["Declared P(x | state) and predictive P(x)"]
    SampleValues["Action utility or loss + common unit"] --> BaselineSample["Baseline complete ties + declared reference action"]
    Predictive --> PosteriorSample["Posterior action values and complete ties by x"]
    BaselineSample --> PosteriorSample
    PosteriorSample --> ConditionalSample["delta-EV_x + VSI_x"]
    ConditionalSample --> SampleDistribution["Weighted outcome distribution"]
    SampleDistribution --> SampleSummary["EVSI + weighted population sigma-VSI + rVSI_delta + quantiles"]
    SampleSummary --> SampleAssurance["Expectation-only tower identities + Bayes/probability/result assurance"]
    SampleAssurance --> SampleBoundary["C18 / M31: exact finite experimental Python; not an EVSI interval or system-risk measure"]
```

```mermaid
flowchart LR
    C16Risk["C16 / v1.2 predecessors"] --> C18Risk["C18 / M22 planned v1.3.0"]
    C17MCDA["C17 / M21 sibling"] -. "separate v1.3 wave" .-> C18Risk
    C18Risk --> Parent570["#570"]
    Parent570 --> Contract757["#757 contract + fixtures"]
    Parent570 --> Runtime758["#758 evaluator + surfaces"]
    Parent570 --> Assurance761["#761 assurance + parity"]
    Contract757 --> Experimental570["Exact experimental Python evidence"]
    Runtime758 --> Experimental570
    Assurance761 --> Gate570{"Hosted + science + parity + promotion?"}
    Experimental570 --> Gate570
    Gate570 -->|"pending"| RemainExperimental570["Remain experimental"]
```

```mermaid
flowchart LR
    Scope850["#850 sampling-acquisition-harm scope"] --> Track["sampling_acquisition_harm_voi_20260802"]
    Subissues["#851–#853 and governed descendants including #867 and #870"] --> Track
    Track --> Contract["C18 / M32 planned v1.3.0 Must"]
    Action["Sampling action d + explicit no-sampling d0"] --> Joint["Design-indexed information, state and harm law"]
    Joint --> Ledger{"Separable, commensurate and mutually exclusive ledger?"}
    Ledger -->|"yes"| Scalar["Signed incremental value"]
    Ledger -->|"no"| NonScalar["Joint-welfare, constrained or vector result"]
    Scalar --> MathStatus["Feasible, infeasible or indeterminate"]
    NonScalar --> MathStatus
    Contract --> Action
    MathStatus --> ScopeChoice{"Narrow domain/jurisdiction candidate or reviewed exclusion?"}
    ScopeChoice -->|"generic or unavailable"| Unsupported["Fail-closed governed research scope; no runtime"]
    ScopeChoice -->|"narrow candidate"| Freeze850["Verify Git OIDs, canonical SHA-256 packet, tree bytes, sources, claims and findings"]
    Freeze850 --> Challenge850["Automated challenge and 19-finding register"]
    Challenge850 --> SourceRefresh850["#867 non-authorizing source refresh and readiness partition"]
    SourceRefresh850 --> Commission850["#870 fail-closed human commissioning preflight and handoff"]
    Commission850 --> Ready850{"Candidate context, independent sources and eligible humans ready?"}
    Ready850 -->|"no"| Unsupported
    Ready850 -->|"yes"| Panel850["Independent role subagents plus domain/ethics specialist"]
    Panel850 --> Orchestrator850["Non-deciding synthesis: findings, dissent, options, contingencies, rationale and recommendation"]
    Orchestrator850 --> Humans850{"Two distinct scientific and domain/ethics humans confirm?"}
    Humans850 -->|"dissent or dispute"| Chair850["Independent chair; remediate, refreeze and re-review"]
    Chair850 --> Freeze850
    Humans850 -->|"no, expired or conflicted"| Unsupported
    Humans850 -->|"yes"| Maintainer850{"Separate maintainer implementation decision?"}
    Maintainer850 -->|"retain or exclude"| Unsupported
    Maintainer850 -->|"authorize future work"| Future["Separate implementation track and assurance"]
    Unsupported --> External["No ethics, regulatory, promotion, release or closure claim"]
```

```mermaid
flowchart TD
    C16["Canonical C16 / v1.2.0"] --> Projection["Versioned public projection"]
    Projection --> Planner["Three-way conflict-safe planner"]
    Planner --> Issues["#313 > #318 > #571/#595/#619"]
    Planner --> Consumers["Other registered repositories"]
    Issues --> Project["Project 28"]
    Consumers --> Project
    Project --> Fields["MoSCoW + Contract Version + Track ID + Record ID + Sync State"]
    Planner --> Guard{"Conflict, private data, or missing credential?"}
    Guard -->|yes| Stop["Fail closed"]
    Guard -->|no and authorized| Managed["Update managed fields only"]
```

The archived Conductor registry documents historical implementation. GitHub
issues and the shared project provide the public ledger; local specifications,
fixtures, and CI evidence remain authoritative for technical completion.

```mermaid
flowchart LR
    Source["VOIAGE public source and docstrings"] --> Extract["Commit-pinned astro-polyglot extractors"]
    Griffe["Griffe Python analysis"] --> Extract
    Extract --> Guard{"Public members and safe paths?"}
    Guard -- No --> Fail["Fail closed"]
    Guard -- Yes --> MDX["Ignored generated MDX"]
    MDX --> Astro["Astro 7 and Starlight"]
    Astro --> Links["Link and content validation"]
    Astro --> LLMSTxt["Offline llms.txt output"]
    Links --> Build["Static production build"]
    LLMSTxt --> Build
    Build --> Pages["GitHub Pages artifact"]
```

The initial production extractor is Python because it has a deterministic,
CPU-only Griffe path in the repository docs environment. Rust, R, Julia, and
Mojo enter the same pipeline only after their native toolchains, public-symbol
filtering, generated-page contracts, and failure semantics have fixture-backed
evidence. The plugin is a source-pinned submodule until it has a reviewed
registry release; this prevents a local workspace link from being mistaken for
an independently installable package.

```mermaid
flowchart TD
    Cargo[Cargo workspace version] --> Maturin[Maturin dynamic metadata]
    Tag[Git release tag] --> Validate[Fail-closed tag validation]
    Cargo --> Validate
    Maturin --> Package[Dynamic package version]
    Validate --> Package
    Settings[Pydantic v2 LoggingSettings] --> Logs[Human or JSONL logs]
    Run[Run and command context] --> Logs
    Pixi[Pixi tasks] --> UV[uv lock and execution]
    UV --> Fast[Ruff + ty + BasedPyright + test matrix]
    Fast --> Build[Build, install and release gates]
    Scheduled[Scheduled/manual frontier] --> Scalene[Scalene artifact]
    Scheduled --> Mutation[Mutation evidence]
    Scheduled --> Experimental[Experimental/free-threaded probes]
```

Pixi delegates Python environment resolution to uv, so the repository retains
one dependency lock. Expensive evidence is scheduled or manually requested;
stable pull requests keep deterministic correctness, typing, security,
interchange, coverage, and package gates.

```mermaid
flowchart LR
    Concern --> Risk
    Evidence --> Decision
    Risk --> Decision
    Decision --> IssueLink
    IssueLink --> Project
    AnalysisSpec --> NumericalPolicy
    AnalysisSpec --> Kernel
    Kernel --> BackendCapabilities
    Kernel --> AnalysisResult
    RunContext --> AnalysisResult
    AnalysisResult --> Arrow
```

```mermaid
sequenceDiagram
    participant S as Analysis specification
    participant D as Capability dispatcher
    participant B as Backend
    participant K as Calculation kernel
    participant R as Result envelope
    S->>D: Requirements and numerical policy
    D->>B: Check explicit capabilities
    alt Unsupported
      D-->>S: Fail closed or disclosed fallback
    else Supported
      D->>K: Execute with backend and run context
      K->>R: Typed payload, diagnostics and provenance
      R-->>S: Versioned serializable result
    end
```
