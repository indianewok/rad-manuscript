**Supplementary Figure 1. RAD performance on a public 10X Visium HD murine brain dataset.**

Four replicate sections (PBC44593, PBC44760, PBC49262, PBC52788) at 16 µm bin resolution. Each bin is classified per sample as Both (valid in RAD and in Percula's `in_tissue` set), RAD only, Seurat only (Percula not RAD), or Neither. Panels B and E plot ncpm (count × 10⁶ / per-sample total) on a log10 y-axis labeled "Counts per 16 µm bin"; zero values are dropped. In B and E, the black crossbar marks the median and errorbars span the IQR (full bin set).

**(A)** Per-sample spatial maps of log1p(ncpm) for RAD-valid bins (Both + RAD only); shared plasma scale.

**(B)** Per-sample faceted violins of four groups: DP-Percula (Both bins, Percula counts), DP-RAD (Both bins, RAD counts), SP-RAD (RAD only, RAD counts), Neither (RAD counts). Quasirandom dots subsampled to 1,500 per (sample, group); counts at base are the total per (sample, group).

**(C)** Per-sample spatial maps of single-positive RAD bins (plasma) over all bins (grey); shared color scale. Title n = per-sample single-positive RAD count.

**(D)** Pairwise Pearson r of RAD log1p(ncpm) across the four samples, computed over Percula's `in_tissue` bin set.

**(E)** Pooled kernel-density violins of the same four groups as B across all four samples.
