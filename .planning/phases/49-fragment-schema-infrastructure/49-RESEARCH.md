# Phase 49: Fragment Schema and Infrastructure - Research

**Researched:** 2026-02-19
**Domain:** SQLite schema extension, Pydantic v2 models, DatabaseManager pattern, Click CLI
**Confidence:** HIGH — all decisions verified against existing source code; no new dependencies

---

## Summary

Phase 49 is a pure infrastructure phase. It creates the storage foundation that every subsequent v5.0 phase depends on, but contains zero extraction logic, zero search logic, and zero agent integration. The deliverables are: schema v7 tables in a separate database file, Pydantic models for SSC records, DatabaseManager query methods, and a minimal `lucy fragment info` CLI command.

The key constraint driving all design decisions: the SSC database must live in a separate `lucy-ng-fragments.db` file, not in the existing `lucy-ng-derep.db`. This is a locked decision (see Prior Decisions in the phase context). The separate-file architecture means Phase 49 adds zero schema changes to the existing main database, and existing `lucy dereplicate c13` and `lucy predict c13` operations are completely unaffected.

Everything in this phase follows established patterns in the codebase. The schema v7 migration follows the existing `migrate_v5_to_v6()` pattern exactly. The Pydantic models follow `HOSEStatsRecord` and `BondPairStatsRecord` in `database/models.py`. The DatabaseManager methods follow `insert_hose_stats_batch()` and `get_hose_stats()`. The CLI command group follows `detect.py` and `database.py`. No new research into patterns is required — just apply existing patterns to new tables.

**Primary recommendation:** Build schema v7 in a dedicated `FragmentDatabaseManager` class in a new `lucy_ng/fragments/` module, with its own schema constants file. Do NOT modify the existing `database/schema.py` or `database/manager.py` — the fragment database is architecturally separate and should be reflected in code organization.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FRAG-01 | Fragment database schema v7 with `ssc` and `ssc_bitset` tables in separate `lucy-ng-fragments.db` | Schema DDL from ARCHITECTURE.md; separate-file architecture confirmed as locked decision; `schema_meta` table with `bin_size` record is the standard pattern from existing schema.py |
</phase_requirements>

---

## Standard Stack

### Core (No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `sqlite3` | stdlib | Database creation and schema execution | Already used throughout `database/manager.py` |
| Pydantic v2 | 2.12.5 | `SSCRecord`, `SSCMatch` model definitions | Project-wide model standard; all existing models use it |
| Click | 8.1.8 | `lucy fragment info` command group | All CLI commands use Click; fragment CLI follows same pattern |
| `pathlib.Path` | stdlib | Database file path handling | All existing CLI and DB code uses `Path` |

**Installation:** No new packages required. Zero `pip install` operations for this phase.

---

## Architecture Patterns

### Recommended Project Structure

```
src/lucy_ng/
├── fragments/               # NEW — entire new module
│   ├── __init__.py          # exports SSCRecord, SSCMatch, FragmentDatabaseManager
│   ├── models.py            # SSCRecord, SSCMatch Pydantic models
│   ├── schema.py            # CREATE_SSC_TABLE, CREATE_SSC_BITSET_TABLE, FRAGMENT_SCHEMA_VERSION
│   └── db.py                # FragmentDatabaseManager class
├── cli/
│   ├── fragment.py          # NEW — lucy fragment info command group
│   └── main.py              # MODIFIED — register fragment command group
└── database/                # UNCHANGED — no modifications to existing files
    ├── schema.py
    └── manager.py
```

**Critical decision: new `fragments/` module, not modification of existing `database/` module.** The fragment database has a separate lifecycle (separate file, separate schema version, separate manager class). Keeping it separate avoids coupling the fragment schema to the compound schema and prevents accidental breakage of existing dereplication/prediction code.

### Pattern 1: Schema Module (follows `database/schema.py`)

**What:** Constants for CREATE TABLE statements and migration functions.
**When to use:** Any new SQLite table in the project.
**Example from existing code (`database/schema.py` lines 124-136):**

```python
# Source: src/lucy_ng/database/schema.py

FRAGMENT_SCHEMA_VERSION = 7

CREATE_SSC_TABLE = """
CREATE TABLE IF NOT EXISTS ssc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smiles TEXT NOT NULL,
    atom_count INTEGER NOT NULL,
    shift_list TEXT NOT NULL,    -- JSON array: "[45.1, 130.2]"
    avg_shift REAL NOT NULL,
    min_shift REAL NOT NULL,
    max_shift REAL NOT NULL,
    UNIQUE(smiles)               -- global dedup: one SSC per unique substructure
)
"""

CREATE_SSC_BITSET_TABLE = """
CREATE TABLE IF NOT EXISTS ssc_bitset (
    ssc_id INTEGER PRIMARY KEY,
    bitset BLOB NOT NULL,        -- 32 bytes = 256 bits, 2 ppm bins
    FOREIGN KEY (ssc_id) REFERENCES ssc(id) ON DELETE CASCADE
)
"""

CREATE_SSC_ATOM_COUNT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ssc_atom_count ON ssc(atom_count)
"""

CREATE_SCHEMA_META_TABLE = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

FRAGMENT_SCHEMA_STATEMENTS = [
    CREATE_SCHEMA_META_TABLE,
    CREATE_SSC_TABLE,
    CREATE_SSC_BITSET_TABLE,
    CREATE_SSC_ATOM_COUNT_INDEX,
]
```

**Why `UNIQUE(smiles)` on the `ssc` table:** SSC extraction (Phase 50) must deduplicate by SMILES globally. The UNIQUE constraint at the database level enforces this and enables `INSERT OR IGNORE` for efficient insertion without per-record Python checks.

**Why `ssc_bitset` is a separate table:** The bitset BLOB (32 bytes) is only needed during fingerprint pre-screening (Phase 51). Keeping it separate avoids inflating the `ssc` table rows when querying only SMILES/shifts. Following the architectural recommendation from `ARCHITECTURE.md`.

**Why `bin_size` in `schema_meta`:** The fingerprint bin size (2 ppm) is baked into every stored bitset. Recording it in `schema_meta` prevents silent mismatch if the bin size is ever changed. Phase 49 writes `('bin_size', '2.0')` to `schema_meta` at database creation time, before any SSCs are stored.

### Pattern 2: DatabaseManager Class (follows `database/manager.py`)

**What:** Context manager class encapsulating SQLite connection and query methods.
**When to use:** Any module that needs to read/write a SQLite database.
**Example from existing code (`database/manager.py` lines 22-68):**

```python
# Source: src/lucy_ng/database/manager.py

class FragmentDatabaseManager:
    """Manager for the fragment (SSC) database.

    Separate from DatabaseManager to maintain independence from
    the main compound/HOSE database.

    Usage:
        with FragmentDatabaseManager("lucy-ng-fragments.db") as db:
            db.create_tables()
            db.insert_ssc_batch(records)
            count = db.get_ssc_count()
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> FragmentDatabaseManager:
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def create_tables(self) -> None:
        """Create fragment tables if they don't exist. Idempotent."""
        conn = self._connect()
        cursor = conn.cursor()
        for statement in FRAGMENT_SCHEMA_STATEMENTS:
            cursor.execute(statement)
        # Record schema version and bin_size
        cursor.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", str(FRAGMENT_SCHEMA_VERSION)),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO schema_meta (key, value) VALUES (?, ?)",
            ("bin_size", "2.0"),
        )
        conn.commit()
```

### Pattern 3: Pydantic Models (follows `database/models.py`)

**What:** Pydantic v2 `BaseModel` subclasses for each database entity.
**When to use:** All structured data in lucy-ng.
**Example from existing code (`database/models.py` lines 110-157):**

```python
# Source: src/lucy_ng/fragments/models.py (NEW)

import json
from pydantic import BaseModel, Field, field_validator


class SSCRecord(BaseModel):
    """A substructure-subspectrum correlation record.

    Stored in the `ssc` table of lucy-ng-fragments.db.
    One record per unique substructure (deduplicated by SMILES).
    """
    id: int | None = None
    smiles: str                      # Substructure SMILES (R = open site)
    atom_count: int                  # Heavy atom count including open-site R groups
    shift_list: list[float]          # Subspectrum 13C shifts
    avg_shift: float                 # Mean of shift_list
    min_shift: float                 # Min of shift_list
    max_shift: float                 # Max of shift_list
    bitset: bytes | None = None      # 32-byte fingerprint (loaded on demand only)

    @field_validator("shift_list", mode="before")
    @classmethod
    def parse_shift_list(cls, v: object) -> list[float]:
        """Parse JSON string from database if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v  # type: ignore[return-value]

    def shift_list_as_json(self) -> str:
        """Serialize shift_list for database storage."""
        return json.dumps(self.shift_list)


class SSCMatch(BaseModel):
    """Result of a fragment search — an SSC that matched the experimental spectrum.

    Produced by FragmentSearcher (Phase 51). Defined here so that
    Phases 51 and 52 can depend on this model independently of Phase 50 data.
    """
    ssc_id: int
    smiles: str
    atom_count: int
    avg_deviation: float             # AVGDEV from fine matching
    matched_shifts: list[float]      # Query shifts that were matched
    fragment_shifts: list[float]     # SSC subspectrum shifts
    rank: int = 0                    # 1-based rank (1 = best)
```

**Design notes:**
- `SSCRecord.bitset` is `None` by default and only populated when Phase 51 loads bitsets for screening. This avoids shipping 32-byte blobs in every query that doesn't need them.
- `SSCMatch` is defined in Phase 49 even though it is first _used_ in Phase 51. This is because Phases 51 and 52 can run in parallel (both depend only on `SSCMatch`, not on extraction data). The model is the dependency, not the data.
- `shift_list` uses a `field_validator` that accepts either a JSON string (from DB) or a Python list (from code). This is the same pattern as existing Pydantic models that bridge SQLite storage to Python types.

### Pattern 4: CLI Command Group (follows `cli/detect.py` and `cli/database.py`)

**What:** Click command group with subcommands, registered in `cli/main.py`.
**When to use:** Any new `lucy <verb>` top-level command.

```python
# Source: src/lucy_ng/cli/fragment.py (NEW)

import click
from pathlib import Path
from lucy_ng.fragments.db import FragmentDatabaseManager

DEFAULT_FRAGMENTS_DB = Path("data/reference/lucy-ng-fragments.db")

@click.group()
def fragment() -> None:
    """Fragment library management and search."""

@fragment.command("info")
@click.argument("db_path", type=click.Path(path_type=Path), default=DEFAULT_FRAGMENTS_DB)
def info(db_path: Path) -> None:
    """Show fragment database statistics.

    Example:
        lucy fragment info data/reference/lucy-ng-fragments.db
    """
    with FragmentDatabaseManager(db_path) as db:
        version = db.get_schema_version()
        count = db.get_ssc_count()
        bin_size = db.get_bin_size()
        click.echo(f"Database: {db_path}")
        click.echo(f"  Schema version: {version}")
        click.echo(f"  SSC count: {count:,}")
        click.echo(f"  Bin size: {bin_size} ppm")
        click.echo(f"  File size: {db_path.stat().st_size / 1e6:.1f} MB")
```

Registration in `cli/main.py`:
```python
from lucy_ng.cli.fragment import fragment
# ...
cli.add_command(fragment)
```

### Anti-Patterns to Avoid

- **Adding SSC tables to `database/schema.py`:** The fragment database is a separate file. Modifying `database/schema.py` would conflate two independent schemas and mislead future developers about what lives where.
- **Putting `SSCRecord`/`SSCMatch` in `database/models.py`:** Same reason — fragment models belong in `fragments/models.py` to preserve module independence.
- **Incrementing `SCHEMA_VERSION` in `database/schema.py` to 7:** The existing `SCHEMA_VERSION = 6` in `database/schema.py` describes `lucy-ng-derep.db`. The fragment database has its own version number in `fragments/schema.py`. These are independent.
- **Making `FragmentDatabaseManager` inherit from or delegate to `DatabaseManager`:** They manage different files and have no shared state. Inheritance would create fragile coupling.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization of `shift_list` | Custom serializer | `json.dumps`/`json.loads` + Pydantic `field_validator` | Existing pattern in project; stdlib, no deps |
| SQLite connection management | Custom connection pool | `sqlite3.connect` with `check_same_thread=False`, context manager `__enter__`/`__exit__` | Exactly what `DatabaseManager` already does |
| Row access by column name | Numeric indexing | `conn.row_factory = sqlite3.Row` | Standard project pattern; avoids index fragility on schema changes |
| Database file discovery | Hardcoded paths | `DEFAULT_FRAGMENTS_DB = Path("data/reference/lucy-ng-fragments.db")` with CLI override | Same pattern as `DEFAULT_DB_PATH` in `cli/database.py` |

---

## Common Pitfalls

### Pitfall 1: Writing `bin_size` to `schema_meta` as `INSERT OR REPLACE`

**What goes wrong:** Using `INSERT OR REPLACE` for `bin_size` at table creation means if `create_tables()` is called on an existing populated database, it overwrites the stored `bin_size` with the current default. The database may already contain SSCs built with a different bin size.

**How to avoid:** Use `INSERT OR IGNORE` for `bin_size` in `create_tables()`. Only Phase 50 (extraction) should set/confirm `bin_size` before starting extraction. Phase 49 writes the default (2.0) only if no value exists yet.

**Warning signs:** `bin_size` changes in `schema_meta` between runs without any extraction having occurred.

### Pitfall 2: `SSCMatch` model omitted from Phase 49 because it is "not needed yet"

**What goes wrong:** Phases 51 and 52 can run in parallel, both depending on `SSCMatch`. If `SSCMatch` is deferred to Phase 51, Phase 52 is blocked until Phase 51 ships. The whole point of Phase 49 defining models is to unblock parallel work.

**How to avoid:** Define both `SSCRecord` and `SSCMatch` in Phase 49. `SSCMatch` has no database dependency — it is a pure Python model for search results. Defining it now costs zero effort and unblocks Phase 52 parallelism.

**Warning signs:** Phase 52 plan lists "depends on Phase 51" — this is wrong if `SSCMatch` was defined in Phase 49.

### Pitfall 3: `lucy fragment info` opens main compound database instead of fragments database

**What goes wrong:** The CLI argument may default to the wrong path if copy-pasted from `database info` command code. `database info` uses `db_path` argument that defaults to nothing (requires argument). If `fragment info` accidentally opens `lucy-ng-derep.db`, it will either fail (no `ssc` table) or return wrong statistics silently.

**How to avoid:** Set the default argument to `DEFAULT_FRAGMENTS_DB` path (not the derep DB path). Add a version check in `info` output: display `schema_version` from `schema_meta`. If `schema_version` is 6 (the derep DB version), emit a warning.

**Warning signs:** `lucy fragment info` reports "Schema version: 6" — wrong DB opened.

### Pitfall 4: `UNIQUE(smiles)` constraint causes silent insertion failures in Phase 50

**What goes wrong:** Phase 49 defines `UNIQUE(smiles)` on the `ssc` table for deduplication. Phase 50's SSC extraction must use `INSERT OR IGNORE` (or `INSERT OR REPLACE` to update avg_deviation). If Phase 50 uses plain `INSERT`, duplicate SMILES raise `sqlite3.IntegrityError` and crash the extraction pipeline.

**How to avoid:** The `insert_ssc_batch()` DatabaseManager method defined in Phase 49 must use `INSERT OR IGNORE` semantics. Document this explicitly in the method docstring. Phase 50 will call this method, inheriting the correct behavior.

**Warning signs:** Extraction crashes with `UNIQUE constraint failed: ssc.smiles` after the first compound is processed (re-extractions would produce duplicates).

### Pitfall 5: `DatabaseManager.insert_ssc_batch()` returns row count inconsistently with `INSERT OR IGNORE`

**What goes wrong:** `INSERT OR IGNORE` silently skips duplicate rows. If the returned count includes both inserted and skipped rows (based on input list length), the caller's progress tracking will show false completion.

**How to avoid:** Use `cursor.rowcount` after each INSERT to count only actually-inserted rows. Track skipped count separately. Return a tuple `(inserted, skipped)` rather than a simple `int`.

---

## Code Examples

Verified patterns from existing source:

### Schema Version Read (from `database/manager.py` lines 94-112)

```python
# Source: src/lucy_ng/database/manager.py

def get_schema_version(self) -> int | None:
    cursor = self._connect().cursor()
    try:
        cursor.execute("SELECT value FROM schema_meta WHERE key = ?", ("schema_version",))
        row = cursor.fetchone()
        if row:
            return int(row["value"])
    except sqlite3.OperationalError:
        pass
    return None
```

Apply this same pattern verbatim in `FragmentDatabaseManager.get_schema_version()`.

### Batch Insert Pattern (from `database/manager.py` lines 434-504)

```python
# Source: src/lucy_ng/database/manager.py (insert_hose_stats_batch)

def insert_ssc_batch(
    self,
    records: list[SSCRecord],
    batch_size: int = 10000,
) -> tuple[int, int]:
    """Batch insert SSC records. Returns (inserted, skipped)."""
    conn = self._connect()
    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    for i, record in enumerate(records):
        cursor.execute(
            """
            INSERT OR IGNORE INTO ssc
                (smiles, atom_count, shift_list, avg_shift, min_shift, max_shift)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.smiles,
                record.atom_count,
                record.shift_list_as_json(),
                record.avg_shift,
                record.min_shift,
                record.max_shift,
            ),
        )
        if cursor.rowcount > 0:
            inserted += 1
            # Insert bitset if present
            if record.bitset is not None:
                ssc_id = cursor.lastrowid
                cursor.execute(
                    "INSERT OR IGNORE INTO ssc_bitset (ssc_id, bitset) VALUES (?, ?)",
                    (ssc_id, record.bitset),
                )
        else:
            skipped += 1

        if (i + 1) % batch_size == 0:
            conn.commit()

    conn.commit()
    return (inserted, skipped)
```

### Iterator for Bitset Screening (used by Phase 51)

```python
# Source: pattern from manager.py iter_compounds_with_shifts

def iter_ssc_bitsets(
    self, batch_size: int = 100_000
) -> Iterator[tuple[int, bytes]]:
    """Iterate over all (ssc_id, bitset) pairs for pre-screening.

    Memory-efficient: yields in batches. Phase 51 uses this for
    Boolean AND pre-screening during fragment search.

    Yields:
        (ssc_id, bitset_bytes) tuples
    """
    conn = self._connect()
    cursor = conn.cursor()
    cursor.execute("SELECT ssc_id, bitset FROM ssc_bitset ORDER BY ssc_id")

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            yield (row["ssc_id"], bytes(row["bitset"]))

def get_ssc_by_id(self, ssc_ids: list[int]) -> list[SSCRecord]:
    """Fetch SSC records by IDs for fine matching.

    Used by Phase 51 after pre-screening identifies candidate ssc_ids.
    """
    if not ssc_ids:
        return []
    conn = self._connect()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(ssc_ids))
    cursor.execute(
        f"SELECT id, smiles, atom_count, shift_list, avg_shift, min_shift, max_shift "
        f"FROM ssc WHERE id IN ({placeholders})",
        ssc_ids,
    )
    return [
        SSCRecord(
            id=row["id"],
            smiles=row["smiles"],
            atom_count=row["atom_count"],
            shift_list=row["shift_list"],   # field_validator parses JSON string
            avg_shift=row["avg_shift"],
            min_shift=row["min_shift"],
            max_shift=row["max_shift"],
        )
        for row in cursor.fetchall()
    ]
```

---

## Success Criteria Mapping

All 5 success criteria from the phase definition are addressable with the patterns above:

| Criterion | Implementation |
|-----------|----------------|
| 1. `lucy-ng-fragments.db` with schema v7 + `bin_size` | `FragmentDatabaseManager.create_tables()` writes both tables + inserts `schema_version=7` and `bin_size=2.0` to `schema_meta` |
| 2. `lucy fragment info` reports schema version, SSC count, path | `cli/fragment.py info` command calls `get_schema_version()`, `get_ssc_count()`, displays `db_path` |
| 3. Existing commands unaffected | No changes to `database/schema.py`, `database/manager.py`, or any existing module |
| 4. `SSCRecord` and `SSCMatch` instantiable and serializable to JSON | Pydantic v2 `BaseModel` subclasses; `.model_dump()` and `.model_dump_json()` work out-of-the-box |
| 5. DatabaseManager methods callable without error | `insert_ssc_batch`, `get_ssc_count`, `iter_ssc_bitsets`, `get_ssc_by_id` — all implemented as described above; unit tests verify each |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Schema changes added to existing `database/schema.py` (v3→v4→v5→v6) | New fragment schema in separate `fragments/schema.py` | Phase 49 (new) | Keeps existing 2.8 GB DB unchanged; enables separate file distribution |
| Single `DatabaseManager` for all tables | Separate `FragmentDatabaseManager` for SSC data | Phase 49 (new) | Independent lifecycle, independent file, no coupling risk |

---

## Open Questions

1. **Default path for `lucy-ng-fragments.db`**
   - What we know: The main DB defaults to `data/reference/lucy-ng-derep.db` (relative to CWD).
   - What's unclear: Should fragment DB default to `data/reference/lucy-ng-fragments.db` (same directory) or a separate location?
   - Recommendation: Default to `data/reference/lucy-ng-fragments.db` — same convention, same directory, easy to keep together. Users who put the compound DB in a non-default location would specify `--fragments-db` explicitly.

2. **`lucy fragment info` with no DB file yet**
   - What we know: `DatabaseManager` creates the file if it doesn't exist (this is the SQLite behavior).
   - What's unclear: Should `lucy fragment info` create an empty fragments DB if the file doesn't exist, or error out?
   - Recommendation: Error out with a helpful message. Unlike `database info` (which can be used to check any DB), `fragment info` is reporting on a specific pre-built asset. Creating an empty file silently would mask "database not downloaded" errors.

---

## Sources

### Primary (HIGH confidence)

- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/database/schema.py` — schema version pattern, migration chain, `SCHEMA_STATEMENTS` list, CREATE TABLE conventions
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/database/manager.py` — `DatabaseManager` class, context manager, `row_factory`, `insert_hose_stats_batch`, `iter_compounds_with_shifts`, `get_schema_version`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/database/models.py` — `HOSEStatsRecord`, `BondPairStatsRecord` as model patterns for `SSCRecord`/`SSCMatch`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/cli/fragment.py` (does not exist yet) — pattern from `cli/detect.py` and `cli/database.py`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/cli/main.py` — command group registration pattern
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/research/ARCHITECTURE.md` — `ssc` and `ssc_bitset` table DDL, `FragmentDatabaseManager` method signatures, separate-file decision
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/research/STACK.md` — fingerprint encoding (256-bit, 32 bytes, 2 ppm bins), no new dependencies confirmed
- `.planning/milestones/v5.0-ROADMAP.md` — success criteria, requirement FRAG-01

### Secondary (MEDIUM confidence)

- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/research/PITFALLS.md` — Pitfall 6 (separate file decision), `INSERT OR IGNORE` for dedup, `bin_size` in `schema_meta`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/background/sherlock-analysis.md` — 256-bit fingerprint design rationale, 2 ppm bin confirmed from Sherlock paper

---

## Metadata

**Confidence breakdown:**
- Schema DDL: HIGH — DDL taken directly from ARCHITECTURE.md which was researched against Sherlock thesis and RDKit docs
- DatabaseManager methods: HIGH — method signatures and patterns taken verbatim from existing `manager.py`
- Pydantic models: HIGH — pattern from existing `models.py`; `field_validator` for JSON parsing is standard Pydantic v2
- CLI command: HIGH — identical pattern to `cli/database.py info` command

**Research date:** 2026-02-19
**Valid until:** 2026-04-01 (stable stack, no rapidly changing dependencies)
