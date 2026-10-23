# SN-ONT RAD 4acbe00 full matrix rebuild

This artifact rebuilds the RAD `all` MEX from every record serialized by RAD commit
`4acbe004ba11b150d6832395452632f367a6e6c1`, including records tagged `-CT`. The frozen shared LongBench
GENCODE-v44 read-to-gene table and the archived exact `(cell barcode, gene, UMI)` collapse
implementation were reused. The canonical matrix was rebuilt from scratch; it was not made by
adding the quick-audit delta to the prior matrix.

New total UMIs: **22,875,174**  
Previous total UMIs: **21,013,660**  
Net change: **+1,861,514**

## Important `-CT` caveat

RAD labels concatenate/chimeric-derived segments with `-CT`. The frozen shared gene table assigns
the original unsplit physical read to one gene, so a deconcatenated segment inherits that parent
gene in this matrix. These records are retained intentionally for parity with the existing
Flexiplex matrix, which retained its default deconcatenated/multi-target rows.

The existing DEG tables and figures in the reviewer package were not regenerated during this
matrix-only promotion and are stale with respect to the replacement RAD input.
