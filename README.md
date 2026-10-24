# Owl — Cloud Blender Lab

Public source code for a **small, non-destructive 3D lighting experiment** on Cyber Owl Sentinel, a model generated with Meshy AI.

## What it does

- Imports an existing, textured GLB and preserves its original geometry and PBR materials.
- Adds separate emerald-green geometry for provisional eye rings, chest accents, and wing light paths.
- Exports an editable `.blend`, a portable `.glb`, and a machine-readable inspection report.
- Uses **GitHub Actions CPU** by default; it does **not** rent a GPU or run on a schedule.

**This is a positioning prototype, not finished recessed under-feather lighting.** Strip placement must be visually reviewed and corrected. Animation of emission is retained in BLEND only; GLB emission is static.

## One-time model upload

The original textured GLB is ~121 MiB, exceeding GitHub's 100 MB normal Git-file limit. Never try to commit it as ordinary Git content. The workflow reads a GitHub **Release asset** named `cyber-owl-textured.glb` from a release with tag `owl-input-01`.

1. In this repository, go to **Releases → Draft a new release**.
2. Set tag `owl-input-01` and attach a **copy** of the textured source file, renamed `cyber-owl-textured.glb`.
3. Publish the release.
4. Go to **Actions → Cyber Owl Blender CPU Experiment → Run workflow**.
5. Check run logs and download artifact `cyber-owl-blender-cpu-v1` from the run.

**PUBLIC REPOSITORY WARNING:** Every release asset is publicly accessible. Upload only assets you are comfortable distributing. If the original model is intended to stay private, use a private storage bucket with credentials instead; the supplied release workflow would need adapting.

## Cost boundaries

Workflow is manually dispatched only (`workflow_dispatch`), with a 35-minute timeout. Default GitHub-hosted CPU runner. No GPU instance or paid rendering service is provisioned. Usage beyond your GitHub Actions allowances may be charged by GitHub; check billing settings.

## Directory map

- `enhance_owl.py` — Blender Python edit.
- `.github/workflows/blender-owl.yml` — GitHub Actions workflow.
- `ASSETS.md` — asset inventory, provenance, limits and follow-up test plan.

Do not change other repositories. Keep originals separately; all edits happen in fresh workflow directories.
