# Code follow ups

## Remove model pathname from ScTagger quality sampling seed

Status: deferred code change, recorded at the author's request on 22 October 2026. No generator change or data regeneration is authorized by this note.

Target: the maintained ScTagger synthetic-quality benchmark generator.

The historical generators calculate the background quality-tape seed with:

```python
stable_seed(str(args.model), args.seed, "quality-tape")
```

This makes the random draws depend on the model pathname. Moving an identical model file changes the background qualities, even when the selected base seed is unchanged.

Required change:

- Use the explicitly selected numeric seed for the background random-number generator. Do not include the model pathname in seed calculation.
- Record the actual generator seed, software versions, and model-content checksum in output provenance. Record file paths as metadata only.
- Verify that identical model contents at different paths produce identical quality strings with the same selected seed.
- Retain the paired quality draws across shifts and the existing read-specific determinism.

Apply the change to a maintained working copy. Preserve the archived executed scripts and existing generated inputs, results, and hashes. Any subsequent regeneration must be identified as a new analysis, with affected outputs checked before manuscript numbers are updated.

Evidence copies:

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_quality_generation/generate_truth_conditioned_qscores.py`, seed helper at lines 50–52 and tape seed at line 349.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/generate_truth_conditioned_qscores.py`, tape seed at line 379.

For the final ScTagger-L experiments, 20260731 was the selected base seed. The historical NumPy tape seed was derived from that value, the purpose label, and the model pathname.
