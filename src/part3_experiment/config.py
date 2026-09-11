"""Constants for Part 3.

The single RNG seed literal in this repository lives here (ARCHITECTURE.md §7.5,
A-018). A second seed literal anywhere is a defect.
"""

from __future__ import annotations

from pathlib import Path

# --- Seed -------------------------------------------------------------------
# The ONLY seed literal in the repository. Every generator is constructed
# explicitly from it; independent streams are derived by spawning (§7.5, A-063).
RANDOM_SEED = 20260910

# --- Pre-registration provenance (§1.7) -------------------------------------
# The commit that contains ARCHITECTURE.md, assumptions.md and .gitignore and
# nothing else, made before the first commit touching src/. The report cites it.
PREREGISTRATION_COMMIT = "c6d72f834359fba8b8748a0d7251592a8cab80c5"
ARCHITECTURE_BLOB_SHA = "29b4f465421b18e8cd9dcbd2b7380e5962fd1305"

# --- Paths ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSUMPTIONS_PATH = PROJECT_ROOT / "assumptions.md"
ARCHITECTURE_PATH = PROJECT_ROOT / "ARCHITECTURE.md"
LOCKFILE_PATH = PROJECT_ROOT / "requirements.lock.txt"
PYTHON_VERSION_PATH = PROJECT_ROOT / ".python-version"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "run_manifest.json"

# --- Input ------------------------------------------------------------------
DATASET_SLUG = "mursideyarkin/mobile-games-ab-testing-cookie-cats"
RAW_CSV_NAME = "cookie_cats.csv"
RAW_CSV_PATH = RAW_DIR / RAW_CSV_NAME

# The assumptions.md entry whose recorded SHA-256 step 2 verifies against
# (§5.5, §7.7 step 2, A-064). The checksum is not duplicated here on purpose.
PROVENANCE_ENTRY_ID = "A-072"

# Documented size of the dataset. A mismatch is a finding, never an adjustment.
DOCUMENTED_ROW_COUNT = 90189

EXPECTED_COLUMNS = ("userid", "version", "sum_gamerounds", "retention_1", "retention_7")
EXPECTED_COLUMN_SET = frozenset(EXPECTED_COLUMNS)

# --- Interpreter (§7.5, A-026) ----------------------------------------------
REQUIRED_PYTHON_MINOR = (3, 12)
DIRECT_DEPENDENCIES = ("pandas", "numpy", "scipy", "statsmodels", "matplotlib")

# --- Arms (§1.6, A-036) -----------------------------------------------------
ARM_CONTROL = "gate_30"   # incumbent, confirmed from the dataset card (A-036)
ARM_VARIANT = "gate_40"   # the proposed move
ARMS = (ARM_CONTROL, ARM_VARIANT)
ARM_TOKENS = frozenset(ARMS)

# --- Token sets (§5.4) ------------------------------------------------------
# Comparison is on the trimmed value and is case-sensitive, except where a
# spelling is listed in both cases. The empty string stands for both an empty
# field and a whitespace-only field, since comparison happens after trimming.
TRUE_TOKENS = frozenset({"True", "1"})
FALSE_TOKENS = frozenset({"False", "0"})
MISSING_TOKENS = frozenset({"", "NA", "N/A", "NaN", "nan", "null", "NULL", "None"})

RETENTION_COLUMNS = ("retention_1", "retention_7")
PRIMARY_METRIC = "retention_7"     # §1.1, A-002
GUARDRAIL_METRIC = "retention_1"   # §1.2, A-003
ENGAGEMENT_COLUMN = "sum_gamerounds"
ID_COLUMN = "userid"
ARM_COLUMN = "version"

# --- Pre-registered statistical constants -----------------------------------
ALPHA = 0.05          # §1.3, A-004 — two-sided, all of it on the primary
MDE_PP = 1.00         # §1.4, A-005 — action threshold, absolute percentage points
POWER_TARGETS = (0.80, 0.95)   # §3

SRM_NULL_P = 0.5      # §2.1, A-008 — the 1:1 allocation the SRM test runs against
SRM_FAIL_P = 0.001    # §2.3, A-011

# Downgrade thresholds. Denominators are fixed by A-065: the first two are
# shares of raw input rows, the third is a share of each arm's assignment count.
UNASSIGNABLE_THRESHOLD = 0.001        # §2.2 — 0.1% of raw rows
CROSS_ARM_DUPLICATE_THRESHOLD = 0.001  # §5.2 — 0.1% of raw rows
PRIMARY_MISSING_THRESHOLD = 0.005      # §5.3 — 0.5% of EITHER arm

N_RESAMPLES = 10_000          # §4.2, A-017
BOOTSTRAP_CHUNK = 500         # replicates per draw batch; affects memory only
CI_LEVEL = 0.95
PERCENTILE_METHOD = "linear"  # A-071

WINSOR_PERCENTILE = 99.0      # §5.1, A-068 — pooled cap for the engagement summary

# --- Reporting precision (§4.1, A-031, A-069) -------------------------------
PP_DECIMALS = 2        # retention rates and effects, in percentage points
PVALUE_SIGFIGS = 3     # exact p-values, never "p < 0.05", never rounded to 0
FULL_PRECISION_FMT = "{:.12g}"   # deterministic `value` column format

# --- Figure determinism (§7.5, A-043) ---------------------------------------
FIG_BACKEND = "Agg"
FIG_DPI = 150
FIG_SIZE = (8.0, 5.0)
FIG_FONT_FAMILY = "sans-serif"
FIG_FONT_FALLBACK = ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"]
