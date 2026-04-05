# Data Cleanup Audit

Generated: 2026-04-05

## Red Marks Status

- VS Code diagnostics check reports no code errors.
- Explorer red indicators are likely source-control decorations because this repo currently has many changed files.

## Keep (Do Not Delete)

High-risk runtime or training assets that are actively referenced.

- data/monica_memory.db
- data/monica_conversations.db
- data/users.json
- data/.security/
- data/training/
- data/training/voice_training/recordings/MJP/
- data/training/voice_training/recordings/MJP/manifest.json
- data/Monica_Knowledge_Base/
- data/monica_knowledge/

## Keep or Backup Before Changes

Referenced and important, but recoverable with rebuild/re-download.

- data/models/
- data/model_checkpoints/
- data/kenlm/
- data/knowledge_index/
- data/maxone_drive_index/
- data/monica_education/
- data/monica_sciences/
- data/monica_legal/

## Likely Cache/Artifact (Archive Candidate)

Low-risk cache outputs that can usually be regenerated.

- data/research_cache/
- data/search_cache/
- data/tile_cache/
- data/creative_cache/
- data/creative_output/
- data/memory/ (only if not used by your current runtime profile)
- data/file_purpose_cache.json

## Duplicate/Parallel Trees (Needs Consolidation)

These create drift risk because equivalent content exists in two roots.

- data/users.json and monica_ai/data/users.json
- data/maxone_drive_index/ and monica_ai/data/maxone_drive_index/
- data/monica_legal/ and monica_ai/data/monica_legal/
- data/monica_sciences/ and monica_ai/data/monica_sciences/

Recommendation:
1. Choose one canonical root (prefer data/).
2. Point all loaders to canonical paths.
3. Archive duplicate tree under monica_ai/data/_archive_YYYYMMDD/.

## Suggested Safe Cleanup Flow

1. Create archive staging folder: data/_archive_YYYYMMDD/
2. Move only low-risk cache/artifact items there first.
3. Run smoke test (startup, wake phrase, TTS, STT).
4. If all good for 7 days, permanently delete archived cache.
5. Consolidate duplicate trees only after path verification.

## PowerShell (Non-Destructive) Example

```powershell
$stamp = Get-Date -Format yyyyMMdd
$archive = "data/_archive_$stamp"
New-Item -ItemType Directory -Path $archive -Force | Out-Null

$toArchive = @(
  "data/research_cache",
  "data/search_cache",
  "data/tile_cache",
  "data/creative_cache",
  "data/creative_output",
  "data/file_purpose_cache.json"
)

foreach ($p in $toArchive) {
  if (Test-Path $p) {
    Move-Item -Path $p -Destination $archive -Force
  }
}
```

## Notes

- Avoid deleting training recordings or DB files directly.
- Archive first, validate behavior, then prune.
- If desired, this can be automated with a verified script that checks references before moving files.
