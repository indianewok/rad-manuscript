#!/usr/bin/env python3
"""Exercise public FASTQ reordering and rejection using explicitly synthetic reads.

These tiny fixtures test code behavior, not biological data or public replication.
The selected identity and the successful output are independently fingerprinted
by the existing Figure 3 identity script.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def gz(path, payload):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as handle:
            handle.write(payload)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT/'validation/rage_public_reorder_fixtures.json')
    args = parser.parse_args()
    checks = []
    with tempfile.TemporaryDirectory(prefix='rage_order_fixture_') as folder:
        folder = Path(folder)
        records = [b'@fixture-A source=selected\nACGT\n+\nIIII\n',
                   b'@fixture-B source=selected\nGCA\n+fixture-B\nABC\n',
                   b'@fixture-C source=selected\nTTAACC\n+\n!#%&()\n']
        selected, identity, order = (folder/name for name in ('selected.fq.gz', 'identity.json', 'order.txt.gz'))
        gz(selected, b''.join(records))
        fingerprint = [sys.executable, str(ROOT/'scripts/revision/figure_3_fastq_identity.py')]
        subprocess.run(fingerprint + [str(selected), '--report', str(identity), '--ids-output', str(order)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        selected_identity = json.loads(identity.read_text())
        cases = [
            ('reversed_order', b''.join(reversed(records)), True, True),
            ('different_metadata', b''.join(reversed(records)).replace(b'source=selected', b'source=public').replace(b'+fixture-B', b'+'), True, False),
            ('duplicate_public_ID', records[0] + records[0] + records[2], False, None),
            ('missing_public_ID', records[0] + records[2], False, None),
            ('extra_public_ID', b''.join(records) + b'@fixture-extra\nA\n+\nI\n', False, None),
            ('changed_sequence', b''.join(reversed(records)).replace(b'ACGT', b'ACGA'), False, None),
            ('changed_quality', b''.join(reversed(records)).replace(b'IIII', b'IIHI'), False, None),
            ('malformed_record', b''.join(records).replace(b'!#%&()', b'!#%&'), False, None),
        ]
        for name, payload, should_pass, exact_match in cases:
            public, output, report = (folder/(name+suffix) for suffix in ('.public.fq.gz', '.ordered.fq.gz', '.json'))
            gz(public, payload)
            command = [sys.executable, str(ROOT/'scripts/figure_03/reorder_public_fastq.py'),
                       '--public', str(public), '--order', str(order), '--identity', str(identity),
                       '--output', str(output), '--report', str(report), '--scratch', str(folder),
                       '--sort-threads', '1', '--sort-memory', '1M', '--pigz-threads', '1',
                       '--min-temp-free-bytes', '0']
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            observed = json.loads(report.read_text())
            assert (result.returncode == 0) == should_pass, (name, result.stderr.decode())
            assert output.exists() == should_pass, name
            if should_pass:
                independent = folder/(name+'.identity.json')
                subprocess.run(fingerprint + [str(output), '--report', str(independent)],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                checked = json.loads(independent.read_text())
                for key in ('records', 'unique_original_ids', 'duplicate_original_ids', 'sequence_bases',
                            'canonical_record_sha256', 'sequence_quality_order_sha256', 'original_id_order_sha256'):
                    assert checked[key] == selected_identity[key], (name, key)
                assert observed['exact_decompressed_fastq_matches_selected'] == exact_match
                assert (checked['exact_decompressed_fastq_sha256'] == selected_identity['exact_decompressed_fastq_sha256']) == exact_match
            else:
                assert observed['status'] == 'failed'
                assert not list(folder.glob(output.name+'.partial.*'))
            checks.append(dict(case=name, status='passed', expected_acceptance=should_pass,
                               rejection_reason=observed.get('error')))
        for name, payload, should_pass in [
                ('verify_only_complete', b''.join(reversed(records)), True),
                ('verify_only_changed_quality', b''.join(reversed(records)).replace(b'IIII', b'IIHI'), False)]:
            public, report = folder/(name+'.public.fq.gz'), folder/(name+'.json')
            gz(public, payload)
            before_fastq_files = set(folder.glob('*.fq.gz'))
            result = subprocess.run([sys.executable, str(ROOT/'scripts/figure_03/reorder_public_fastq.py'),
                       '--public', str(public), '--order', str(order), '--identity', str(identity),
                       '--verify-only', '--report', str(report), '--scratch', str(folder),
                       '--sort-threads', '1', '--sort-memory', '1M', '--pigz-threads', '1',
                       '--min-temp-free-bytes', '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            observed = json.loads(report.read_text())
            assert (result.returncode == 0) == should_pass, (name, result.stderr.decode())
            assert set(folder.glob('*.fq.gz')) == before_fastq_files
            assert observed['mode'] == 'verify_only' and observed['output'] is None
            assert 'output_hashes' not in observed
            if should_pass:
                assert observed['full_ordered_stream_verified'] and not observed['full_fastq_written']
                assert observed['reconstructed_identity']['canonical_record_sha256'] == selected_identity['canonical_record_sha256']
            else:
                assert observed['status'] == 'failed'
            checks.append(dict(case=name, status='passed', expected_acceptance=should_pass,
                               full_fastq_written=False, rejection_reason=observed.get('error')))
        # The selected order is itself checked: duplicate IDs fail even when its
        # compressed hash is supplied, and an undeclared order edit fails the hash.
        duplicate_order = folder/'duplicate_order.gz'
        gz(duplicate_order, b'fixture-A\nfixture-A\nfixture-C\n')
        duplicate_identity = dict(selected_identity, input_ids_sha256=sha(duplicate_order))
        edited_identity = folder/'duplicate_identity.json'
        edited_identity.write_text(json.dumps(duplicate_identity))
        for name, identity_path in [('duplicate_order_ID', edited_identity), ('changed_order_hash', identity)]:
            report, output = folder/(name+'.json'), folder/(name+'.fq.gz')
            command = [sys.executable, str(ROOT/'scripts/figure_03/reorder_public_fastq.py'),
                       '--public', str(selected), '--order', str(duplicate_order), '--identity', str(identity_path),
                       '--output', str(output), '--report', str(report), '--scratch', str(folder),
                       '--sort-threads', '1', '--sort-memory', '1M', '--pigz-threads', '1',
                       '--min-temp-free-bytes', '0']
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            observed = json.loads(report.read_text())
            assert result.returncode != 0 and observed['status'] == 'failed' and not output.exists()
            checks.append(dict(case=name, status='passed', expected_acceptance=False, rejection_reason=observed['error']))
        # Force temporary runs and an external merge with a buffer much smaller
        # than the encoded stream. This exercises the production sort path.
        merge_records = [('00000000-0000-0000-0000-{:012d}'.format(i).encode('ascii'),
                          b'ACGT' * 100, b'I' * 400) for i in range(5000)]
        def fastq(record):
            rid, sequence, quality = record
            return b'@' + rid + b'\n' + sequence + b'\n+\n' + quality + b'\n'
        gz(selected, b''.join(fastq(record) for record in merge_records))
        subprocess.run(fingerprint + [str(selected), '--report', str(identity), '--ids-output', str(order)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        public, output, report = (folder/name for name in ('merge.public.fq.gz', 'merge.ordered.fq.gz', 'merge.json'))
        gz(public, b''.join(fastq(record) for record in reversed(merge_records)))
        subprocess.run([sys.executable, str(ROOT/'scripts/figure_03/reorder_public_fastq.py'),
                        '--public', str(public), '--order', str(order), '--identity', str(identity),
                        '--output', str(output), '--report', str(report), '--scratch', str(folder),
                        '--sort-threads', '1', '--sort-memory', '1M', '--pigz-threads', '1',
                        '--min-temp-free-bytes', '0'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        independent = folder/'merge.identity.json'
        subprocess.run(fingerprint + [str(output), '--report', str(independent)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert json.loads(independent.read_text())['canonical_record_sha256'] == json.loads(identity.read_text())['canonical_record_sha256']
        checks.append(dict(case='external_merge_5000_synthetic_reads', status='passed', expected_acceptance=True,
                           sort_buffer='1M', encoded_input_bytes_at_least=5000*800))
    receipt = dict(status='passed', scope='Explicitly synthetic code-behavior fixtures (three-read edge cases and 5000-read external merge); not biological evidence',
                   implementation='scripts/figure_03/reorder_public_fastq.py',
                   implementation_sha256=sha(ROOT/'scripts/figure_03/reorder_public_fastq.py'),
                   independent_identity_script_sha256=sha(ROOT/'scripts/revision/figure_3_fastq_identity.py'),
                   fixture_script_sha256=sha(Path(__file__)), checks=checks)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(receipt, indent=2)+'\n')
    print('{} reordering/rejection fixtures passed'.format(len(checks)))


if __name__ == '__main__':
    main()
