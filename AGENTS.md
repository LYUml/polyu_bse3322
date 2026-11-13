# Workspace instructions

## Scope
This workspace is for the BSE3322 Topic B ceiling-jet CFD and smoke extraction assignment. Use `01_Assignment_Brief/Project_Topic_1B_Smoke_Extraction.pdf` as the assignment source and `08_Project_Notes/project-requirements.md` as a working checklist.

## Working rules
- Communicate with the user in Chinese by default; retain source terminology and units.
- Preserve original brief files. Record assumptions and unresolved requirements explicitly.
- Do not invent group number, experimental data, material properties, solver results, or regulatory compliance claims.
- Confirm group number before selecting the group-specific simulation matrix.
- Distinguish assignment requirements, literature evidence, assumptions, and simulated results.
- Check Fig. 1 visually before implementing geometry; extracted PDF text alone is insufficient for opening positions and burner details.
- Keep propane validation cases separate from propylene smoke-extraction design cases.
- Record solver/version, units, mesh, boundary conditions, fire inputs, run duration and analysis interval for each case.
- Keep large generated simulation outputs in `04_Results/`; commit inputs, scripts and selected reviewable results only.
- Do not install software, launch long simulation batches or push to GitHub unless requested or authorized in the ongoing task.
- Never claim a simulation or validation passed without inspecting its actual outputs.

## Git synchronization preference
- The user authorized committing and pushing this project after completed changes on 2026-11-13. After each meaningful completed change and appropriate checks, commit and push to origin; do not ask for permission again for routine synchronization.
- Preserve large local course slide decks excluded by .gitignore. Never claim excluded local files were uploaded.
- Do not force-push, rewrite shared history, or include credentials or generated simulation output.
