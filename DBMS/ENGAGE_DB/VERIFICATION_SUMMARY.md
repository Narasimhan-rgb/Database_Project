# ENGAGE DB — pre-upload verification summary

**Inspection date:** 03 Nov 2026. **GitHub status:** NOT UPLOADED.

## Checks actually performed in this preparation environment
- [x] Original ZIP opened and core Flask, PostgreSQL, Oracle, SQL and seed files inspected.
- [x] Removed `.env`, `.venv`, Python caches and unreproducible dependencies from the upload-ready copy.
- [x] Compiled the distributed Python sources without syntax errors (`python -m compileall`).
- [x] Ran five automated static repository checks successfully.
- [x] Counted 272 Oracle INSERT statements across 15 tables (237 in 12 core tables).
- [x] Verified README embeds two **actual team-provided screenshots** using relative image paths.
- [x] Rendered the DOCX technical report to PDF; verified the report pages visually.
- [x] Generated and visually inspected all 8 slides.
- [x] Rendered the one-page Word submission sheet.

## Not yet verified (must be done on local Windows/PostgreSQL/Oracle installation)
- [ ] Fresh setup and actual database connection.
- [ ] Five end-to-end UI actions, each paired with database verification screenshot.
- [ ] SQL execution and foreign-key/duplicate error handling on a test schema.
- [ ] Oracle mirror after explicit sync; matching row counts confirmed with SQL*Plus.
- [ ] 12 target screenshots plus cited screenshots of comparable existing systems.
- [ ] Final 3–5 minute video visibly featuring all three members.
- [ ] Three-member actual work/credit confirmation.
- [ ] Working GitHub and YouTube URLs pasted into submission Word and README.

The static checks do NOT certify production security or end-to-end functional correctness. The package must not be presented as fully tested until actual test records have been added.
