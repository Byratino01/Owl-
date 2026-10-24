# Owl asset inventory

Source artifacts originally provided in ChatGPT; **not included in this source-code bundle** because of GitHub large-file limits:

| Artifact | Purpose | Approximate size |
|---|---|---:|
| `Meshy_AI_Cyber_Owl_Sentinel_1024013233_generate.glb` | Raw Cyber Owl source | 53 MiB |
| `Meshy_AI_Cyber_Owl_Sentinel_1024014215_texture.glb` | PBR Cyber Owl source used by workflow | 121 MiB |
| `Meshy_AI_Aureon_Skywatcher_1024013516_generate.glb` | Raw White & Gold owl source | 64 MiB |
| `Meshy_AI_Aureon_Skywatcher_1024014120_texture.glb` | PBR White & Gold owl | 140 MiB |

The two Cyber Owl GLBs are two pipeline stages of one owl. The Aureon GLBs are two stages of a second owl. Retain saved source copies independent of GitHub.

## Published-assets policy

The repository is public by request. Workflow source is safe to publish. Uploading GLBs to a GitHub Release will make them publicly downloadable. Verify that you own the necessary rights to distribute assets, and do not place credentials in the repository or public logs.

## Experimental test plan

1. Retrieve the `cyber-owl-textured.glb` release asset.
2. Import with Blender Python on standard GitHub Actions Linux CPU runner.
3. Add separate emerald emissive geometry without changing source meshes.
4. Export BLEND and GLB; inspect dimensions, triangle counts and material preservation.
5. View resulting GLB from multiple angles. Determine whether physical strips are actually between feather plates.
6. Refine placements rather than blindly increasing geometry, and test under-feather shading.
7. Consider paid GPU rendering **only after** first CPU test and cost review.

**Known limitations:** Original owl is a single dense mesh (~2.33 million triangles); the prototype light paths are approximate and may float above the armor. Rigging and articulated animations are out of scope for this quick test.
