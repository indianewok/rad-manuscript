# LR-Split-seq FLAMES configurations

These copies preserve the authors' analysis configurations at
`ChangqingW/FLAMES_figures` commit `7d5c16cd4542986e27dbd04927f58d0de77a436a`,
and the actual component ED2 wrappers used for the RAD comparison.

| File | Settings |
|---|---|
| `upstream/ChangqingW_FLAMES_figures/files/config_splitseq.json` | Separate component catalogs; component ED1, buffer 1, flank ED3, terminal T8 |
| `upstream/ChangqingW_FLAMES_figures/files/config_splitseq_bc.json` | Short-read-derived complete barcode combinations; segment ED3, group ED6, flank ED10, terminal T8 |
| `executed/flexiplex_ed2_native/run_native_ed2.R` | Component ED2, buffer 1, flank ED3, terminal T8 |
| `executed/flexiplex_no_polyt_ed2_native/run_native_ed2.R` | Component ED2, buffer 1, flank ED3, poly-T omitted |

The complete upstream target is preserved in
`upstream/ChangqingW_FLAMES_figures/targets/LR-split-seq.R`. Its component
configuration call is at line 308; the complete-cell configuration call is at
line 491. Successful execution manifests accompany both ED2 wrappers.

The original files are unchanged. The upstream authors retain their copyrights;
no license was supplied by this pinned figure repository, and this archive
does not assign one. FLAMES engine licenses are preserved separately in
`../splitseq/licenses/`. Attribution, original URLs, hashes and source versions
are recorded in `../../../pinned_flames_configs/origins.json`.
