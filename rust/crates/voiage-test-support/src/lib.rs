//! Shared fixture and test support for the voiage Rust workspace.

#![forbid(unsafe_code)]

use std::collections::HashSet;
use std::fmt;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::Deserialize;
use serde_json::Value;

mod compatibility_contract;

pub use compatibility_contract::{
    classify_compatibility_contracts, execute_deterministic_compatibility_contracts,
    execute_foundational_compatibility_contracts, CompatibilityClassification, CompatibilityMethod,
    ContractErrorMapping, ContractOutcome, ContractParityError, ContractParityReport,
};

const FIXTURE_ROOT: &str = "specs/core-api/fixtures/v1";
const COMPATIBILITY_MANIFEST: &str = "compatibility-manifest.json";

/// An error produced while locating or validating shared compatibility fixtures.
#[derive(Debug)]
pub enum FixtureError {
    /// A fixture file could not be read.
    Io(std::io::Error),
    /// A fixture file did not contain valid JSON or match its expected shape.
    Json(serde_json::Error),
    /// The compatibility catalog violated a required invariant.
    InvalidCatalog(String),
}

impl fmt::Display for FixtureError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(formatter, "fixture I/O error: {error}"),
            Self::Json(error) => write!(formatter, "fixture JSON error: {error}"),
            Self::InvalidCatalog(message) => {
                write!(formatter, "invalid fixture catalog: {message}")
            }
        }
    }
}

impl std::error::Error for FixtureError {}

impl From<std::io::Error> for FixtureError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for FixtureError {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

/// Provenance identifying how the canonical compatibility catalog was produced.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompatibilityProvenance {
    /// Language implementation that generated the expected results.
    pub reference_implementation: String,
    /// Execution mode used to generate the catalog.
    pub execution_mode: String,
    /// Stable identifier for the source catalog.
    pub catalog: String,
}

/// One compatibility case and its repository-relative artifacts.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompatibilityCase {
    /// Stable unique case identifier.
    pub case_id: String,
    /// Stable method exercised by this case.
    pub method: String,
    /// Normal, edge, or invalid classification.
    pub classification: String,
    /// Optional evidence category associated with the case.
    #[serde(default)]
    pub evidence: Option<String>,
    /// Path to the case input, relative to the v1 fixture root.
    pub input_artifact: PathBuf,
    /// Path to the expected outcome, relative to the v1 fixture root.
    pub expected_artifact: PathBuf,
}

/// Validated Phase 2 compatibility manifest.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompatibilityManifest {
    /// Compatibility contract version.
    pub version: String,
    /// Deterministic seed used by the reference fixture runner.
    pub seed: u64,
    /// Reference execution provenance.
    pub provenance: CompatibilityProvenance,
    /// Ordered compatibility cases.
    pub cases: Vec<CompatibilityCase>,
}

/// Fully loaded input and expected JSON values for one compatibility case.
#[derive(Clone, Debug, PartialEq)]
pub struct LoadedCompatibilityCase {
    /// Validated case metadata.
    pub case: CompatibilityCase,
    /// Parsed input artifact.
    pub input: Value,
    /// Parsed expected artifact.
    pub expected: Value,
}

/// Returns the repository's canonical v1 fixture directory.
#[must_use]
pub fn fixture_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .join(FIXTURE_ROOT)
}

/// Loads and validates the canonical Phase 2 compatibility manifest.
///
/// # Errors
///
/// Returns [`FixtureError`] when the manifest cannot be read, parsed, or
/// validated.
pub fn load_compatibility_manifest() -> Result<CompatibilityManifest, FixtureError> {
    let root = fixture_root();
    let bytes = fs::read(root.join(COMPATIBILITY_MANIFEST))?;
    let manifest: CompatibilityManifest = serde_json::from_slice(&bytes)?;
    validate_manifest(&manifest, &root)?;
    Ok(manifest)
}

/// Loads every compatibility case in manifest order.
///
/// # Errors
///
/// Returns [`FixtureError`] when the manifest or any referenced fixture cannot
/// be read, parsed, or validated.
pub fn load_compatibility_cases() -> Result<Vec<LoadedCompatibilityCase>, FixtureError> {
    let root = fixture_root();
    let manifest = load_compatibility_manifest()?;
    manifest
        .cases
        .into_iter()
        .map(|case| {
            let input = read_json(&root.join(&case.input_artifact))?;
            let expected = read_json(&root.join(&case.expected_artifact))?;
            Ok(LoadedCompatibilityCase {
                case,
                input,
                expected,
            })
        })
        .collect()
}

fn read_json(path: &Path) -> Result<Value, FixtureError> {
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}

fn validate_manifest(manifest: &CompatibilityManifest, root: &Path) -> Result<(), FixtureError> {
    require_nonempty("version", &manifest.version)?;
    require_nonempty(
        "provenance.reference_implementation",
        &manifest.provenance.reference_implementation,
    )?;
    require_nonempty(
        "provenance.execution_mode",
        &manifest.provenance.execution_mode,
    )?;
    require_nonempty("provenance.catalog", &manifest.provenance.catalog)?;
    if manifest.cases.is_empty() {
        return Err(FixtureError::InvalidCatalog(
            "cases must not be empty".into(),
        ));
    }

    let mut ids = HashSet::with_capacity(manifest.cases.len());
    for case in &manifest.cases {
        require_nonempty("case_id", &case.case_id)?;
        require_nonempty("method", &case.method)?;
        require_nonempty("classification", &case.classification)?;
        if !ids.insert(case.case_id.as_str()) {
            return Err(FixtureError::InvalidCatalog(format!(
                "duplicate case_id {:?}",
                case.case_id
            )));
        }
        validate_artifact_path(root, &case.input_artifact)?;
        validate_artifact_path(root, &case.expected_artifact)?;
    }
    Ok(())
}

fn require_nonempty(field: &str, value: &str) -> Result<(), FixtureError> {
    if value.trim().is_empty() {
        return Err(FixtureError::InvalidCatalog(format!(
            "{field} must not be empty"
        )));
    }
    Ok(())
}

fn validate_artifact_path(root: &Path, relative: &Path) -> Result<(), FixtureError> {
    if relative.as_os_str().is_empty()
        || relative.is_absolute()
        || relative
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(FixtureError::InvalidCatalog(format!(
            "artifact path must be a contained relative path: {}",
            relative.display()
        )));
    }
    let path = root.join(relative);
    if !path.is_file() {
        return Err(FixtureError::InvalidCatalog(format!(
            "artifact does not exist: {}",
            relative.display()
        )));
    }
    let canonical_root = root.canonicalize()?;
    let canonical_path = path.canonicalize()?;
    if !canonical_path.starts_with(&canonical_root) {
        return Err(FixtureError::InvalidCatalog(format!(
            "artifact resolves outside fixture root: {}",
            relative.display()
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_the_numerical_case_register_with_live_test_targets() {
        let register = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../../conductor/tracks/agent_safe_engineering_20260907/numerical-case-register.json");
        let bytes = fs::read(register).expect("numerical case register must be present");
        let value: Value =
            serde_json::from_slice(&bytes).expect("numerical case register must be valid JSON");
        assert_eq!(value["schema_version"], "1.0");
        let cases = value["independent_references"]
            .as_array()
            .expect("case list");
        assert!(!cases.is_empty());
        for case in cases {
            assert!(case["case_id"].as_str().is_some_and(|id| !id.is_empty()));
            assert!(case["implementation_test"]
                .as_str()
                .is_some_and(|test| test.contains("::")));
        }
    }

    #[test]
    fn locates_canonical_fixtures_from_the_crate_manifest_directory() {
        let root = fixture_root();
        assert!(root.ends_with(FIXTURE_ROOT));
        assert!(root.join(COMPATIBILITY_MANIFEST).is_file());
    }

    #[test]
    fn loads_the_phase_two_catalog_with_valid_identity_and_provenance() {
        let manifest = load_compatibility_manifest().expect("canonical manifest must load");
        assert_eq!(manifest.version, "v1");
        assert_eq!(manifest.seed, 101);
        assert_eq!(manifest.provenance.reference_implementation, "python");
        assert_eq!(manifest.provenance.execution_mode, "deterministic");
        assert_eq!(manifest.provenance.catalog, "v1-python-reference");
        assert_eq!(manifest.cases.len(), 25);

        let ids: HashSet<_> = manifest.cases.iter().map(|case| &case.case_id).collect();
        assert_eq!(ids.len(), manifest.cases.len());
        assert!(manifest
            .cases
            .iter()
            .all(|case| !case.case_id.trim().is_empty()));
    }

    #[test]
    fn loads_every_input_and_expected_artifact_in_manifest_order() {
        let cases = load_compatibility_cases().expect("canonical cases must load");
        assert_eq!(cases.len(), 25);
        assert_eq!(cases[0].case.case_id, "evpi-normal-001");
        assert_eq!(cases[0].input["net_benefit"][0][0], 10.0);
        assert_eq!(cases[0].expected["result"], 0.666_666_666_666_666_7);
    }

    #[test]
    fn rejects_duplicate_case_ids() {
        let root = fixture_root();
        let mut manifest = load_compatibility_manifest().expect("canonical manifest must load");
        let duplicate_id = manifest.cases[0].case_id.clone();
        manifest.cases[1].case_id = duplicate_id;
        let error = validate_manifest(&manifest, &root).expect_err("duplicate IDs must fail");
        assert!(error.to_string().contains("duplicate case_id"));
    }

    #[test]
    fn rejects_unknown_case_fields() {
        let bytes = fs::read(fixture_root().join(COMPATIBILITY_MANIFEST)).unwrap();
        let mut value: Value = serde_json::from_slice(&bytes).unwrap();
        value["cases"][0]["unexpected"] = Value::Bool(true);
        assert!(serde_json::from_value::<CompatibilityManifest>(value).is_err());
    }

    #[test]
    fn rejects_missing_provenance_and_escaping_artifact_paths() {
        let root = fixture_root();
        let mut manifest = load_compatibility_manifest().expect("canonical manifest must load");
        manifest.provenance.catalog.clear();
        assert!(validate_manifest(&manifest, &root)
            .expect_err("blank provenance must fail")
            .to_string()
            .contains("provenance.catalog"));

        manifest.provenance.catalog = "catalog".into();
        manifest.cases[0].input_artifact = PathBuf::from("../outside.json");
        assert!(validate_manifest(&manifest, &root)
            .expect_err("escaping paths must fail")
            .to_string()
            .contains("contained relative path"));
    }
}
