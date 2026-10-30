# Figure 6 FLAMES genome-alignment configuration

The exact executed configuration is
`upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json`.
Its SHA-256 is
`18dcabed08851f25a2bf7fdf361eaa1ea238afe32e506491d3582fe92d64b2a2`.
The file matches the pinned LongBench source, retained execution copy, and
producing RAD/Flexiplex manifests. All three effective logged configurations
were checked against it.

The configuration enables genome alignment and disables demultiplexing and
downstream quantification stages. It uses seed 2023, 32 threads and annotated
splice junctions. The separate native demultiplexing commands remain in the
Figure 6 guide.

`upstream/FLAMES_4b6058f58c5b19365919990b3f2c1053f2035b01/` preserves the corresponding FLAMES 2.0.1
pipeline, alignment implementation, configuration loader, package defaults
and GPL license. The default JSON is retained as context; the explicitly
supplied `flames_genome_map.json` determines this run. Original runners,
configuration-bearing logs, BAM headers and execution manifests are under
`execution/`. The gene/transcript JSONs are related workflow records, not the
genotype-alignment configuration.

The upstream authors retain their copyrights. FLAMES's original GPL license is
included. No license was supplied by the pinned LongBench repository, and no
new license is assigned here. Original source locations and hashes are listed
in `../../../pinned_flames_configs/origins.json`.
