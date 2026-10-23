#!/usr/bin/env python3
"""Link the completed extension from the original summary and seal artifacts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731')
summary=ARCHIVE/'SWEEP_SUMMARY.md'
manifest=ARCHIVE/'SUMMARY_ADDITIONS_SHA256SUMS.txt'
marker='## 2026-09-13: completed nanopore2023 extension'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert json.loads((ROOT/'provenance/combined_validation.json').read_text())['status']=='PASS'
    assert (ROOT/'blaze_replay/DONE').exists()
    backup=ROOT/'provenance/original_summary_before_extension'
    backup.mkdir(exist_ok=True)
    before=summary.read_text()
    if marker not in before:
        for p in [summary,manifest]:
            destination=backup/p.name
            assert not destination.exists()
            destination.write_bytes(p.read_bytes())
        expected=dict(line.split('  ',1)[::-1] for line in manifest.read_text().splitlines() if '  ' in line)
        assert expected['SWEEP_SUMMARY.md']==digest(summary)
        addition=f'''

{marker}

The separate **ScTagger-L nanopore2023 sweep** now covers all eleven quality
levels of the 2018 experiment. New negative shifts were selected by matching
the achieved full-dataset whole-read mean Q as closely as integer shifts
permit (maximum mismatch 0.373602 Q). The shifts are
-17,-16,-15,-14,-12,-11,-9,-7,-6,-5,-4; shifted bases use the same Q1..50 rule.

BLAZE's original counting and whitelist-selection code was replayed on the
full saved unadjusted extraction (4,993,805 reads). As requested, **only the
unadjusted BLAZE callset was used as a validation control**: its 5,015 entries
were reproduced byte for byte (5,000 TP,15 FP,0 FN). Shifted conditions then
ran, and RAD/Flexiplex callsets were reused for the identical sequences.

At 2023 mean whole-read Q22.1736, BLAZE has 4,965 TP,30 FP,35 FN,
F1=0.993497; at Q26.8075 it has 5,000 TP,20 FP,0 FN,F1=0.998004.
Unadjusted 2023 remains 5,000 TP,15 FP,0 FN,F1=0.998502.
These are whitelist metrics; no additional read-assignment replay was run.

- [Complete extension report]({ROOT}/README.md)
- [All 2023 tools and qualities]({ROOT}/results/all_tools_2023_sweep.tsv)
- [Paired 2018/2023 BLAZE results]({ROOT}/results/BLAZE_2018_vs2023.tsv)
- [BLAZE comparison figure]({ROOT}/results/BLAZE_model_comparison.png)
- [Paired 50K quality distributions]({ROOT}/quality/matched_distribution_grid.png)

The original 2018 metrics above remain unchanged. This extension does not
alter a Prism project. The prior version of this summary and its checksum
manifest are backed up under the extension's `provenance/` directory.
'''
        summary.write_text(before.rstrip()+addition+'\n')
        lines=manifest.read_text().splitlines()
        updated=[]
        for line in lines:
            if line.endswith('  SWEEP_SUMMARY.md'):
                line=digest(summary)+'  SWEEP_SUMMARY.md'
            updated.append(line)
        manifest.write_text('\n'.join(updated)+'\n')
    changes=[]
    for p in [summary,manifest]:
        changes.append(dict(path=str(p),before_sha256=digest(backup/p.name),after_sha256=digest(p)))
    (ROOT/'provenance/original_summary_update.json').write_text(json.dumps(changes,indent=2)+'\n')
    (ROOT/'COMPLETE').write_text(datetime.now(timezone.utc).isoformat()+'\n')
    all_files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=ROOT/'SHA256SUMS.txt')
    entries=[(p,digest(p)) for p in all_files]
    (ROOT/'SHA256SUMS.txt').write_text(''.join(h+'  '+str(p.relative_to(ROOT))+'\n' for p,h in entries))
    assert all(digest(p)==h for p,h in entries)
    print(json.dumps(dict(status='PASS',files_in_manifest=len(entries),summary_updated=str(summary)),indent=2))


if __name__=='__main__':main()
