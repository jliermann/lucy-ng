# Phase 10: NMRXiv Dataset Fetching - Context

## User Vision

Download all spectra related to an NMRXiv compound into a local folder. The compound can be identified by DOI or NMRXiv identifier (e.g., P7).

## Research Findings

### NMRXiv Data Model

NMRXiv organizes data hierarchically:
- **Project** (P-prefixed, e.g., P7) - equivalent to a publication, receives DOI when published
- **Sample/Study** (S-prefixed) - groups NMR experiments of one sample (1H, 13C, HSQC, HMBC, etc.)
- **Dataset** (D-prefixed) - individual NMR measurement (e.g., a Bruker folder)
- **Spectra** - the actual files within a dataset

### API Endpoints Discovered

From analyzing nmrxiv.org routes:

1. **Metadata retrieval:**
   - `/api/v1/{id}` - Get individual record by ID (project, study, dataset)
   - `/api/v1/list/{model}` - List items of a given model type

2. **Download routes:**
   - `{username}/download/{project}/{key?}` - Download project data
   - `{username}/download/{project}/{study}/{filename}` - Download individual files
   - `{code}/studies/{study}/file/{filename}` - Study file retrieval

3. **BioSchemas:**
   - `/api/v1/schemas/bioschemas/{id}` - Structured metadata

### File Formats

NMRXiv accepts and stores:
- Bruker folders (primary format for raw data)
- JCAMP-DX
- JEOL
- NMReData
- nmrium files

Public projects are downloadable by anyone without authentication.

## What's Essential

1. **Fetch by identifier** - Accept DOI (e.g., `10.57992/NMRXIV.P10.S69`) or direct ID (e.g., `P10`)
2. **Download all spectra** - Get all datasets/studies for the compound into one folder
3. **Preserve Bruker structure** - Keep the original folder structure so lucy-ng readers work
4. **CLI command** - `lucy fetch nmrxiv <identifier> --output <dir>`
5. **MCP tool** - `fetch_nmrxiv_dataset` for agent integration

## What's Out of Scope

- Searching NMRXiv by compound name/formula (separate feature)
- Uploading to NMRXiv
- Authentication/private project access
- Format conversion during download

## DOI Format

NMRXiv DOIs follow the pattern: `10.57992/NMRXIV.P{project}.S{study}`

Example: `10.57992/NMRXIV.P10.S69`
- Registrant: `10.57992`
- Project: `P10`
- Study: `S69`

DOIs can be parsed directly to extract project and study IDs - no need to resolve via doi.org.

## Technical Approach

1. Parse DOI to extract project ID and optional study ID
2. Call API to get project/study metadata
3. Download files for specified study (or all studies with `--all`)
4. Organize into output directory with readable structure

---
*Created: 2026-01-12*
