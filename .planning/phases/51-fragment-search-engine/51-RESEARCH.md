# Phase 51: Fragment Search Engine - Research

**Researched:** 2026-02-19
**Domain:** Bitset pre-screening + fine spectral matching over the SSC fragment database
**Confidence:** HIGH — all infrastructure from Phases 49-50 is code-complete and examined; algorithm parameters sourced from Wenk thesis (PRIMARY)

---

## Summary

Phase 51 adds the `FragmentSearcher` class and the `lucy fragment search` CLI command to the already-built fragment library infrastructure. Phases 49-50 completed the storage layer: `FragmentDatabaseManager`, `SSCRecord`/`SSCMatch` models, `shifts_to_fingerprint`, the `SSCExtractor` pipeline, and `lucy fragment build`/`lucy fragment info`. Phase 51 is purely a read-path implementation — it queries the populated SSC table, screens bitsets, fine-matches, ranks, and emits JSON output for the agent.

The algorithm is a strict two-phase pipeline: (1) Boolean AND pre-screening using the 32-byte fingerprints already stored in `ssc_bitset`, and (2) greedy nearest-neighbour fine matching on the surviving candidate `SSCRecord`s loaded via the already-implemented `get_ssc_by_id`. All query plumbing (`iter_ssc_bitsets`, `get_ssc_by_id`) exists. What is missing is a `searcher.py` module that wires them together, plus the `lucy fragment search` CLI command.

The critical implementation detail that is NOT yet present in `shifts_to_fingerprint`: the ±1 bin tolerance expansion at query time. The stored SSC fingerprints have no expansion applied (correct — expansion happens only on the query side so that a stored fragment shift at 45.1 ppm matches a query shift at 44.9 ppm that straddles a 2 ppm boundary). This must be implemented as a separate `expand_query_fingerprint` helper in Phase 51.

**Primary recommendation:** Add `src/lucy_ng/fragments/searcher.py` with a `FragmentSearcher` class that does chunked bitset scan + fine matching, add `lucy fragment search` to `cli/fragment.py`, and export `FragmentSearcher` from `fragments/__init__.py`. No new dependencies; no schema changes.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SRCH-01 | 256-bit fingerprint generated per SSC (2 ppm bins, 0-510 ppm range) with tolerance expansion | Fingerprint storage done (Phase 50). Tolerance expansion is a QUERY-SIDE operation not yet in shifts_to_fingerprint — must be a separate `expand_query_fingerprint(fp, bins=1)` function in Phase 51. SSC fingerprints stored as 32-byte BLOBs in `ssc_bitset` via `iter_ssc_bitsets`. |
| SRCH-02 | Boolean AND pre-screening eliminates non-matching SSCs before fine matching | `iter_ssc_bitsets(batch_size=100_000)` already implemented in `FragmentDatabaseManager`. Phase 51 must implement the AND logic: `(query_fp_bytes & ssc_fp_bytes) == ssc_fp_bytes` byte-by-byte, collect passing `ssc_id`s. |
| SRCH-03 | Fine spectral matching filters by DEV (2 ppm), AVGDEV (1 ppm), multiplicity, and equivalence | `get_ssc_by_id(ssc_ids)` already implemented. Phase 51 must implement greedy nearest-neighbour matching: for each fragment shift find closest query shift, check per-pair DEV <= 2 ppm, check overall AVGDEV <= 1 ppm. Multiplicity check requires `SSCMatch` to include multiplicity data — but `SSCRecord.shift_list` is plain floats, no multiplicity. Research finding: multiplicity matching may be deferred or simplified (see Open Questions). |
| SRCH-04 | Fragment results ranked by heavy atom count (descending) then AVGDEV (ascending) | `SSCRecord.atom_count` is stored. `SSCMatch.avg_deviation` is computed during fine matching. Ranking is a `sort()` call on the result list after fine matching completes. |
| SRCH-05 | CLI `lucy fragment search --shifts "..." --format json` returns ranked fragments with matched signals | New command in `cli/fragment.py`. Must accept `--shifts` (comma-separated ppm), optional `--db` path, `--format json` (already the default pattern across lucy-ng CLI). JSON output must include `deff_commands` and `fexp_command` as exact LSD strings. |
| SRCH-06 | CLI `lucy fragment info` reports library statistics (SSC count, database size) | ALREADY IMPLEMENTED in `cli/fragment.py`. Reports schema version, SSC count, bin size, file size. No new code needed — this requirement is already satisfied. |
</phase_requirements>

---

## What Already Exists (Do Not Re-Implement)

| Component | Location | Status |
|-----------|----------|--------|
| `FragmentDatabaseManager` | `src/lucy_ng/fragments/db.py` | Complete — `iter_ssc_bitsets(batch_size)`, `get_ssc_by_id(ids)`, `get_ssc_count()`, `get_bin_size()` |
| `SSCRecord` model | `src/lucy_ng/fragments/models.py` | Complete — `id`, `smiles`, `atom_count`, `shift_list`, `avg_shift`, `min_shift`, `max_shift`, `bitset` |
| `SSCMatch` model | `src/lucy_ng/fragments/models.py` | Complete — `ssc_id`, `smiles`, `atom_count`, `avg_deviation`, `matched_shifts`, `fragment_shifts`, `rank` |
| `shifts_to_fingerprint` | `src/lucy_ng/fragments/fingerprint.py` | Complete — 256-bit, 2 ppm bins, 0-511 ppm range, no expansion (correct for storage side) |
| `SSCExtractor` pipeline | `src/lucy_ng/fragments/extractor.py` | Complete — BFS fragmentation, checkpoint/resume, `lucy fragment build` |
| `lucy fragment info` | `src/lucy_ng/cli/fragment.py` | Complete — satisfies SRCH-06 already |
| `lucy fragment build` | `src/lucy_ng/cli/fragment.py` | Complete — populates `ssc` + `ssc_bitset` tables |
| `fragment` CLI group registered | `src/lucy_ng/cli/main.py` | Complete — `fragment` group already in `cli.add_command(fragment)` |

**What is missing for Phase 51:**

1. `src/lucy_ng/fragments/searcher.py` — `FragmentSearcher` class
2. `lucy fragment search` command in `src/lucy_ng/cli/fragment.py`
3. `expand_query_fingerprint` helper (query-side ±1 bin expansion) in `fingerprint.py`
4. Export of `FragmentSearcher` from `src/lucy_ng/fragments/__init__.py`
5. Tests in `tests/test_fragment_searcher.py`

---

## Standard Stack

No new dependencies. All required tools are already installed.

| Library | Version | Purpose |
|---------|---------|---------|
| Python stdlib | 3.10+ | No new packages |
| RDKit | 2025.9.4 | NOT needed for search (search is shift-list based, not molecular) |
| NumPy | 2.2.1 | Byte-by-byte bitwise AND during pre-screening |
| SQLite | stdlib | `iter_ssc_bitsets` and `get_ssc_by_id` queries |
| Click | 8.1.8 | `lucy fragment search` CLI command |
| Pydantic v2 | 2.12.5 | `SSCMatch` output serialisation |

---

## Architecture Patterns

### Pattern 1: FragmentSearcher as Context Manager

Follow the `StatisticalDetector` / `DatabaseQueryService` pattern. `FragmentSearcher` wraps `FragmentDatabaseManager` and implements `__enter__`/`__exit__`.

```python
class FragmentSearcher:
    def __init__(self, db_path: str | Path) -> None:
        self._db = FragmentDatabaseManager(db_path)

    def __enter__(self) -> FragmentSearcher:
        self._db._connect()
        return self

    def __exit__(self, *args: object) -> None:
        self._db.close()

    def search(
        self,
        experimental_shifts: list[float],
        dev_threshold: float = 2.0,
        avgdev_threshold: float = 1.0,
        max_results: int = 20,
        min_atom_count: int = 3,
        verbose: bool = False,
    ) -> list[SSCMatch]: ...
```

### Pattern 2: Expand Query Fingerprint (±1 Bin)

Add `expand_query_fingerprint(fp: bytes, expand_bins: int = 1) -> bytes` to `fingerprint.py`. This is the query-side tolerance expansion. SSC fingerprints stored in the database are NOT expanded. Expanding the query ensures a fragment shift at 45.1 ppm (bin 22) matches a query shift at 44.9 ppm (bin 22) that nominally falls in bin 22 but is near the 44.0-46.0 boundary.

```python
def expand_query_fingerprint(fp: bytes, expand_bins: int = 1) -> bytes:
    """Expand query fingerprint by ±expand_bins to handle boundary effects.

    For each set bit in fp, also set the neighboring bits ±expand_bins.
    This is only applied to the QUERY fingerprint, not to stored SSC fingerprints.

    Args:
        fp: 32-byte query fingerprint from shifts_to_fingerprint.
        expand_bins: Number of neighboring bins to set (default 1).

    Returns:
        32-byte expanded fingerprint as bytes.
    """
    arr = np.frombuffer(fp, dtype=np.uint8).copy()
    # For each set bit, expand to neighbors
    bits = np.unpackbits(arr)  # 256 bits as 0/1 array
    expanded = bits.copy()
    for i in range(len(bits)):
        if bits[i]:
            for offset in range(-expand_bins, expand_bins + 1):
                j = i + offset
                if 0 <= j < 256:
                    expanded[j] = 1
    return np.packbits(expanded).tobytes()
```

### Pattern 3: Chunked Bitset Scan

Use `iter_ssc_bitsets(batch_size=100_000)` exactly as designed in Phase 49. Do NOT load all bitsets into RAM. This implements SRCH-02's "does not load full database into RAM at startup" requirement.

```python
def _prescreening_pass(
    self,
    query_fp_expanded: bytes,
    verbose: bool = False,
) -> list[int]:
    """Return ssc_ids that pass Boolean AND pre-screening."""
    candidate_ids: list[int] = []
    q = bytearray(query_fp_expanded)
    for ssc_id, ssc_fp in self._db.iter_ssc_bitsets():
        ssc_ba = bytearray(ssc_fp)
        # All bits of ssc_fp must be present in query_fp
        if all((q[i] & ssc_ba[i]) == ssc_ba[i] for i in range(32)):
            candidate_ids.append(ssc_id)
    if verbose:
        print(f"Pre-screen: {len(candidate_ids)} candidates passed", file=sys.stderr)
    return candidate_ids
```

**Performance note:** The `all((q[i] & ssc_ba[i]) == ssc_ba[i] for i in range(32))` loop can be vectorised with NumPy for large batches. The chunked scan means only 100K rows are in memory at once. For 24M SSCs this is ~240 batches, each requiring one `fetchmany` call. Expected scan time: measured empirically in Phase 51, but target is < 2 seconds for the full scan (SRCH success criterion).

**Alternative vectorised approach within each batch:**

```python
# Inside the batch loop, if rows is a list of (ssc_id, bytes) tuples:
batch_ids = [r[0] for r in rows]
batch_fps = np.array([np.frombuffer(r[1], dtype=np.uint8) for r in rows])  # (N, 32)
q_arr = np.frombuffer(query_fp_expanded, dtype=np.uint8)  # (32,)
# Boolean AND: all bits of each row must be in query
mask = np.all((batch_fps & q_arr) == batch_fps, axis=1)  # (N,) bool
passing = [batch_ids[i] for i in range(len(batch_ids)) if mask[i]]
```

This NumPy vectorised path is significantly faster and is preferred if the per-batch loop is too slow.

### Pattern 4: Greedy Fine Matching

For each `SSCRecord` from `get_ssc_by_id`, match every fragment shift to the nearest unmatched query shift. Check DEV <= 2.0 ppm per pair and AVGDEV <= 1.0 ppm overall.

```python
def _fine_match(
    self,
    record: SSCRecord,
    query_shifts: list[float],
    dev_threshold: float,
    avgdev_threshold: float,
) -> SSCMatch | None:
    """Return SSCMatch if fine matching passes, else None."""
    # Greedy nearest-neighbour: for each fragment shift, find closest query shift
    remaining_query = list(query_shifts)
    matched_query: list[float] = []
    matched_fragment: list[float] = []
    for frag_shift in sorted(record.shift_list):
        if not remaining_query:
            return None  # Not enough query signals to match all fragment shifts
        # Find closest query shift
        closest_idx = min(range(len(remaining_query)),
                         key=lambda i: abs(remaining_query[i] - frag_shift))
        dev = abs(remaining_query[closest_idx] - frag_shift)
        if dev > dev_threshold:
            return None  # Individual deviation too large
        matched_query.append(remaining_query.pop(closest_idx))
        matched_fragment.append(frag_shift)

    if not matched_fragment:
        return None
    avg_dev = sum(abs(mq - mf) for mq, mf in zip(matched_query, matched_fragment)) / len(matched_fragment)
    if avg_dev > avgdev_threshold:
        return None

    assert record.id is not None
    return SSCMatch(
        ssc_id=record.id,
        smiles=record.smiles,
        atom_count=record.atom_count,
        avg_deviation=avg_dev,
        matched_shifts=matched_query,
        fragment_shifts=matched_fragment,
    )
```

### Pattern 5: JSON Output Format

The `lucy fragment search --format json` output must include `deff_commands` and `fexp_command` as exact LSD strings (per success criterion 1). The DEFF/FEXP commands use fragment file paths that Phase 52 (LSD formatter) will eventually write. For Phase 51, include placeholder paths or omit the file-writing responsibility — see Open Questions.

Required JSON structure (from ARCHITECTURE.md):

```json
{
  "query_shifts": [18.08, 22.37, ...],
  "prescreening_count": 2341,
  "fine_match_count": 47,
  "result_count": 5,
  "fragments": [
    {
      "rank": 1,
      "smiles": "c1cc(CC(C)C(=O)O)ccc1CC(C)C",
      "atom_count": 13,
      "avg_deviation": 0.17,
      "matched_shifts": [18.08, ...],
      "fragment_shifts": [18.55, ...]
    }
  ],
  "deff_commands": ["DEFF F1 'fragment_1.lsd'"],
  "fexp_command": "FEXP 'F1'"
}
```

**Key design decision for Phase 51:** `deff_commands` and `fexp_command` are success criterion 1. The success criterion says "exact LSD strings." This implies Phase 51 must either: (a) write the fragment `.lsd` files and output their paths, or (b) output placeholder DEFF lines with SMILES as content. Option (b) defers the full SSTR/LINK formatter to Phase 52 (which the roadmap says "can run in parallel"). The cleanest split: Phase 51 outputs SMILES-based DEFF with a comment noting Phase 52 writes the actual files. Confirm this with success criterion wording.

The success criterion says "returns ranked fragments with `deff_commands` and `fexp_command` fields as exact LSD strings." Since Phase 52 handles the DEFF file writing, Phase 51 likely needs to output the command strings with correct fragment identifiers even if the file content is deferred. Investigate whether LSD can accept SMILES directly in DEFF or requires a separate file.

### Anti-Patterns to Avoid

- **Loading all 24M bitsets at module import**: Anti-pattern 1 from ARCHITECTURE.md. `FragmentSearcher.__init__` MUST NOT trigger DB reads. Load happens inside `search()`.
- **In-memory deduplication of 24M SMILES**: `get_ssc_by_id` returns SSCRecord by ID — no deduplication needed post-screening since the SSC table already deduplicates by SMILES at insert time.
- **Running fine matching before pre-screening**: Pre-screening MUST run first. Fine matching on 24M records without pre-screening would take minutes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| 256-bit integer bitwise AND | Custom int128 or bitarray library | NumPy uint8 array, 32 bytes, vectorised AND |
| SSC database access | Direct SQL in searcher | `FragmentDatabaseManager.iter_ssc_bitsets()` and `get_ssc_by_id()` (already implemented) |
| Result serialisation | Manual dict construction | `SSCMatch.model_dump()` from Pydantic v2 (already in models) |
| CLI boilerplate | New click patterns | Follow existing `lucy detect hybridisation` / `lucy lsd rank` pattern exactly |

---

## Common Pitfalls

### Pitfall 1: Tolerance Expansion on Wrong Side

**What goes wrong:** Applying ±1 bin expansion to stored SSC fingerprints at extraction time (Phase 50 already built), then applying it again at query time. Double expansion means a 2 ppm bin becomes effectively a 6 ppm bin — too loose, too many false positives.

**Why it happens:** The Wenk thesis says "tolerance expansion" without being explicit that it is query-side only.

**How to avoid:** Stored SSC fingerprints in `ssc_bitset` have NO expansion (this is correct — Phase 50's `shifts_to_fingerprint` has no expansion). In Phase 51, expand ONLY the query fingerprint before the AND operation.

**Warning sign:** Self-search (searching a compound with its own shifts) returns 10,000+ candidates — a sign the query expansion is too aggressive.

### Pitfall 2: SRCH-03 Multiplicity Requirement vs. Available Data

**What goes wrong:** The requirement says "filters by DEV, AVGDEV, multiplicity, and equivalence." But `SSCRecord.shift_list` stores only `list[float]` — no multiplicity (CH, CH2, CH3, C) per shift. There is no multiplicity column in the `ssc` table schema.

**Why it happens:** Phase 49-50 stored shifts but not multiplicities. Multiplicity matching requires HSQC-derived information for experimental shifts AND per-atom H-count in the stored SSC fragments.

**How to avoid:** For Phase 51, implement DEV + AVGDEV filtering correctly. Multiplicity matching is a filter that can be added incrementally: if `experimental_multiplicities` is not provided to `search()`, skip multiplicity check silently. The success criteria only require `deff_commands` and `fexp_command` output, not strict multiplicity filtering. Log a note in RESEARCH.md that full multiplicity matching requires schema extension (add `H-count` per shift in `ssc` table) which is out of scope for Phase 51.

**Warning sign:** Phase 51 fails if it tries to enforce multiplicity from `shift_list` alone — there is no H-count data.

### Pitfall 3: DEV / AVGDEV Threshold Confusion

**What goes wrong:** FEATURES.md says DEV=2 ppm and AVGDEV=1 ppm. STACK.md says DEV=3 ppm and AVGDEV=2 ppm. These differ because the FEATURES.md values are from the Wenk thesis (Sherlock's defaults) while STACK.md values are looser (relaxed for initial use).

**Which to use:** Use FEATURES.md values (DEV=2 ppm, AVGDEV=1 ppm) as the defaults per SRCH-03. These match the success criterion. Make both configurable via CLI flags (`--dev-threshold` and `--avgdev-threshold`) so they can be tuned.

### Pitfall 4: SRCH-06 Already Done — Don't Modify lucy fragment info

**What goes wrong:** Treating SRCH-06 as incomplete and adding redundant fields to `lucy fragment info`.

**Confirmed status:** `lucy fragment info` already reports SSC count, database file size, bin size, and schema version. It works correctly. SRCH-06 is satisfied. Do NOT change `fragment info`.

### Pitfall 5: Performance — Bitset Scan Must Beat 2 Seconds

**What goes wrong:** Python byte-by-byte comparison of 24M × 32-byte rows is O(768M byte ops). This is slow in pure Python.

**How to avoid:** Use the NumPy vectorised batch approach (Pattern 3 above). Load each batch of 100K rows from `iter_ssc_bitsets`, convert to `np.ndarray` of shape `(100000, 32)`, use `np.all((batch & query) == batch, axis=1)` — this is SIMD-accelerated and processes 100K rows in a single NumPy call. Benchmark on the actual populated database before deciding whether to add further optimisations.

**Target:** < 2 seconds on M1 Mac for a 24M SSC database. If NumPy batching doesn't achieve this, escalate to `mmap`-based approach or consider writing the bitset scan in a single SQL query using `HEX(bitset)` tricks — but profile first.

### Pitfall 6: Phase 52 Dependency on DEFF File Writing

**What goes wrong:** The success criterion says `deff_commands` must be "exact LSD strings." If Phase 51 outputs `DEFF F1 'fragment_1.lsd'` but never writes `fragment_1.lsd`, the agent gets a valid-looking DEFF line that references a non-existent file.

**How to avoid:** One of two approaches:
- **Option A (clean separation):** Phase 51 writes the SSTR/LINK fragment `.lsd` files and includes full `deff_commands`. Phase 52 adds the `lucy fragment to-lsd` standalone command for testing the formatter independently. Both phases write the same SSTR/LINK logic.
- **Option B (deferred files):** Phase 51 outputs `deff_commands` with correct file paths but does not write the files. Documents that `lucy fragment search` must be followed by `lucy fragment to-lsd`. Phase 52 adds file writing.

Given "Phases 51 and 52 can run in parallel" in the prior decisions, **Option B is more consistent** with the parallelism intent. But it means the success criterion about "exact LSD strings" must be interpreted as "syntactically correct DEFF strings even if the referenced files are written by Phase 52."

**Resolution:** Clarify with the planner. For research purposes, Phase 51 should output DEFF strings with correct path templates and rely on Phase 52 for the file content.

---

## Code Examples

### Minimal FragmentSearcher Usage

```python
# Source: derived from existing FragmentDatabaseManager API (db.py lines 309-376)
from lucy_ng.fragments.searcher import FragmentSearcher

with FragmentSearcher("data/reference/lucy-ng-fragments.db") as searcher:
    matches = searcher.search(
        experimental_shifts=[18.08, 22.37, 30.14, 44.90, 45.03,
                              127.26, 129.38, 136.96, 140.84, 180.56],
        dev_threshold=2.0,
        avgdev_threshold=1.0,
        max_results=5,
        verbose=True,  # prints pre-screen count and fine-match count to stderr
    )
    for m in matches:
        print(f"Rank {m.rank}: {m.smiles}, atom_count={m.atom_count}, "
              f"avgdev={m.avg_deviation:.2f}")
```

### CLI Command Pattern

```python
# Follows existing lucy lsd rank pattern in cli/lsd.py
@fragment.command("search")
@click.option(
    "--shifts",
    required=True,
    type=str,
    help='Comma-separated 13C chemical shifts in ppm (e.g. "18.08,22.37,130.2")',
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default=DEFAULT_FRAGMENTS_DB,
    show_default=True,
    help="Path to fragment database",
)
@click.option(
    "--dev-threshold",
    default=2.0,
    type=float,
    show_default=True,
    help="Max per-signal deviation for fine matching (ppm)",
)
@click.option(
    "--avgdev-threshold",
    default=1.0,
    type=float,
    show_default=True,
    help="Max average deviation for fine matching (ppm)",
)
@click.option(
    "--top",
    "max_results",
    default=5,
    type=int,
    show_default=True,
    help="Maximum number of fragments to return",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show pre-screen and fine-match candidate counts",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="json",
    show_default=True,
    help="Output format",
)
def search(
    shifts: str,
    db_path: Path,
    dev_threshold: float,
    avgdev_threshold: float,
    max_results: int,
    verbose: bool,
    output_format: str,
) -> None:
    """Search fragment library for SSCs matching experimental 13C shifts.

    Returns ranked fragments with DEFF/FEXP LSD command strings.

    Example:

        lucy fragment search --shifts "18.08,22.37,130.2,140.8" --format json
    """
    shift_list = [float(s.strip()) for s in shifts.split(",")]
    with FragmentSearcher(db_path) as searcher:
        matches = searcher.search(
            experimental_shifts=shift_list,
            dev_threshold=dev_threshold,
            avgdev_threshold=avgdev_threshold,
            max_results=max_results,
            verbose=verbose,
        )
    # Format and output...
```

### Bitset AND Comparison

```python
# Source: derived from validate_self_search in extractor.py (lines 495-504)
# which already demonstrates the correct Boolean AND pattern
def _bitset_matches(query_fp: bytes, ssc_fp: bytes) -> bool:
    """Return True if all bits of ssc_fp are present in query_fp."""
    return all(
        (query_fp[i] & ssc_fp[i]) == ssc_fp[i]
        for i in range(32)
    )

# Vectorised equivalent for batches (preferred for performance):
import numpy as np

def _batch_bitset_screen(
    query_fp: bytes,
    batch: list[tuple[int, bytes]],
) -> list[int]:
    """Return ssc_ids from batch that pass Boolean AND screening."""
    if not batch:
        return []
    q = np.frombuffer(query_fp, dtype=np.uint8)  # shape (32,)
    ids = [item[0] for item in batch]
    fps = np.array(
        [np.frombuffer(item[1], dtype=np.uint8) for item in batch]
    )  # shape (N, 32)
    mask = np.all((fps & q) == fps, axis=1)  # shape (N,)
    return [ids[i] for i in range(len(ids)) if mask[i]]
```

---

## Suggested Implementation Order

1. **Add `expand_query_fingerprint` to `fingerprint.py`** — small function, directly tested, blocks nothing else.
2. **Add `searcher.py` with `FragmentSearcher`** — two internal methods: `_prescreening_pass` (uses `iter_ssc_bitsets`) and `_fine_match` (uses `get_ssc_by_id`). Public `search()` method calls both.
3. **Add `search` command to `cli/fragment.py`** — thin wrapper over `FragmentSearcher.search()`, formats JSON output with `deff_commands`/`fexp_command` fields.
4. **Export `FragmentSearcher` from `fragments/__init__.py`** — update `__all__`.
5. **Write tests** — `tests/test_fragment_searcher.py` with in-memory database populated with known SSCs, verify pre-screening and fine-matching independently.

---

## State of the Art

| Old Approach | Current Approach (Phase 51) |
|--------------|----------------------------|
| Sherlock uses MongoDB + Java for bitset scan | lucy-ng uses SQLite BLOB + Python/NumPy — slower but acceptable for single-user CLI |
| Sherlock loads all bitsets into RAM | lucy-ng streams in batches of 100K — lower peak RAM |
| Sherlock fine-matches with multiplicity + equivalence | Phase 51 fine-matches with DEV + AVGDEV only; multiplicity deferred |
| Sherlock reports "< 2 seconds" for Java implementation | lucy-ng targets < 2 seconds via NumPy vectorisation |

---

## Open Questions

1. **Phase 51 vs. Phase 52 boundary for DEFF file writing**
   - What we know: Phase 52 is the "LSD Fragment Formatter" (SSTR/LINK file writing). Phase 51 success criterion says `deff_commands` must be "exact LSD strings."
   - What's unclear: Should Phase 51 write the `.lsd` fragment files, or only output the DEFF path strings with Phase 52 handling the content?
   - Recommendation: Phase 51 outputs DEFF command strings with path templates (e.g., `DEFF F1 'fragment_1.lsd'`) and documents that the file content is Phase 52's responsibility. The `fexp_command` is `FEXP 'F1'` (or `FEXP 'F1 OR F2'` for multiple fragments).

2. **Multiplicity matching (SRCH-03)**
   - What we know: `SSCRecord.shift_list` is `list[float]` — no H-count per shift. The `ssc` table has no multiplicity column.
   - What's unclear: Can Phase 51 satisfy "filters by multiplicity" without per-shift H-count data?
   - Recommendation: Implement DEV + AVGDEV filtering in Phase 51. Add a note that multiplicity matching requires a schema extension (new `ssc_multiplicities` table or `shift_list_with_mult` JSON field). Mark SRCH-03 multiplicity clause as "deferred pending schema extension."

3. **Performance target verification**
   - What we know: The success criterion is "< 2 seconds on M1 Mac." The actual SSC count in the database depends on whether Phase 50 has been run to completion.
   - What's unclear: If Phase 50 has only run on a sample, the actual search time won't be measurable until the full database is built.
   - Recommendation: Test with whatever data is available; document the SSC count during testing; note that sub-2-second performance is validated only on a full database.

---

## Sources

### Primary (HIGH confidence)

- `src/lucy_ng/fragments/db.py` — `iter_ssc_bitsets`, `get_ssc_by_id` API confirmed
- `src/lucy_ng/fragments/models.py` — `SSCRecord`, `SSCMatch` field definitions confirmed
- `src/lucy_ng/fragments/fingerprint.py` — `shifts_to_fingerprint` confirmed as storage-side only (no tolerance expansion)
- `src/lucy_ng/fragments/extractor.py` — `validate_self_search` lines 495-504 confirms Boolean AND pattern
- `src/lucy_ng/cli/fragment.py` — `info` and `build` commands exist; `search` is absent; `fragment` group registered in `main.py`
- `.planning/research/FEATURES.md` — DEV=2 ppm, AVGDEV=1 ppm thresholds (Wenk thesis §3.1.4.1.4), ranking by atom_count DESC then AVGDEV ASC
- `.planning/research/ARCHITECTURE.md` — `FragmentSearcher` design, JSON output schema, anti-patterns
- `.planning/research/PITFALLS.md` — Pitfall 7 (fine matching performance), tolerance expansion mechanics

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` — NumPy vectorised bitset screening pattern (Pattern 2, lines 167-177)
- `tests/test_fragment_db.py` and `tests/test_fingerprint.py` — test patterns to follow for Phase 51 tests
- Wenk thesis (via FEATURES.md and ARCHITECTURE.md) — confirms query-side tolerance expansion, two-phase search algorithm

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and tested in Phases 49-50
- Architecture: HIGH — `iter_ssc_bitsets` and `get_ssc_by_id` are exact interfaces needed; confirmed by source inspection
- Pitfalls: HIGH — tolerance expansion, DEV/AVGDEV threshold source, multiplicity gap, and Phase 51/52 boundary all identified from source code inspection
- Performance: MEDIUM — NumPy vectorisation approach is correct; actual speed depends on database population and hardware

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable codebase; only risk is Phase 50 database population status)
