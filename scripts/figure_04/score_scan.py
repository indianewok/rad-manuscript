#!/usr/bin/env python3
"""Validate and score one completed RAD 4acbe00, error-0.3 barcode scan.

Only the current native whitelist is scored. TP/FP/FN mean membership in the
specified reference; a barcode outside that reference is not proof of an empty
or false biological cell. No sequencing reads or comparison runs are processed.
"""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

RAD_COMMIT = '4acbe004ba11b150d6832395452632f367a6e6c1'
from build_rad import verify_build


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def input_digests(path):
    """Read input bytes once, computing both stored-data identities."""
    sha256, md5 = hashlib.sha256(), hashlib.md5()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''):
            sha256.update(block)
            md5.update(block)
    return dict(sha256=sha256.hexdigest(), md5=md5.hexdigest())


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def load_record(path):
    record = read_json(path)
    required = ['dataset_id', 'input_sha256', 'input_bytes', 'input_records',
                'adapter_seq', 'barcode_length', 'left_margin', 'right_margin',
                'catalogue_sha256', 'reference_path', 'reference_sha256']
    require(all(key in record for key in required), 'Dataset record is missing required fields')
    require(record['dataset_id'] and isinstance(record['dataset_id'], str), 'Invalid dataset_id')
    require(record.get('chemistry') in [None, '10x_3v2', '10x_3v3'] or record.get('scan_mode') == 'single',
            'Nonstandard chemistry requires an explicitly verified scan_mode profile')
    require(record.get('scan_mode', 'single') == 'single',
            'This runner supports single-barcode scans only; supply a verified separate profile for split/masked capture')
    require(record.get('adapter_mode', 'alignment') == 'alignment',
            'Masked-capture adapters are not supported by this pinned single-barcode profile')
    require(re.fullmatch('[ACGTN]+', record['adapter_seq']) is not None, 'Invalid adapter sequence')
    require(record['barcode_length'] == 16, 'This reference scorer requires 16-base barcodes')
    require(all(isinstance(record[key], int) for key in ['left_margin', 'right_margin']), 'Margins must be integers')
    if 'reference_barcode_sha256' in record:
        require(re.fullmatch('[0-9a-f]{64}', record['reference_barcode_sha256']) is not None,
                'Invalid canonical reference barcode SHA256')
    if 'input_format' in record:
        require(record['input_format'] in ['fastq', 'fastq.gz'], 'Unsupported recorded input format')
    for key in ['catalogue_sha256', 'reference_sha256']:
        require(re.fullmatch('[0-9a-f]{64}', record[key]) is not None, 'Missing SHA256: '+key)
    for key, length in [('input_sha256', 64), ('input_md5', 32)]:
        value = record.get(key)
        require(value is None or isinstance(value, str) and re.fullmatch('[0-9a-f]{'+str(length)+'}', value),
                'Invalid dataset digest: '+key)
    for key in ['input_bytes', 'input_records']:
        value = record[key]
        require(value is None or type(value) is int and value > 0, 'Invalid positive dataset count: '+key)
    if any(record[key] is None for key in ['input_sha256', 'input_bytes', 'input_records']):
        require(bool(record.get('input_source')) and bool(record.get('input_selection_contract')),
                'Unknown input identities require exact input_source and input_selection_contract')
    return record


def file_stat(path):
    info = Path(path).stat()
    return dict(size=info.st_size, mtime_ns=info.st_mtime_ns, inode=info.st_ino, device=info.st_dev)


def validate_input_receipt(receipt, record, input_path):
    require(receipt.get('status') == 'passed', 'Input validation receipt has not passed')
    require(Path(receipt['output']).resolve() == Path(input_path).resolve(), 'Receipt is for a different input path')
    require(isinstance(receipt['bytes'], int) and receipt['bytes'] > 0, 'Invalid verified input size')
    require(re.fullmatch('[0-9a-f]{64}', receipt['sha256']) is not None, 'Invalid verified input SHA256')
    for field, expected in [('bytes', record['input_bytes']), ('sha256', record['input_sha256']),
                            ('md5', record.get('input_md5'))]:
        require(expected is None or receipt.get(field) == expected, 'Input '+field+' differs from the dataset pin')


def parse_command(command, record, expected_rad_sha256):
    require(len(command) > 2 and command[1] == 'scan-wl', 'Native command must be RAD scan-wl')
    require(sha(command[0]) == expected_rad_sha256, 'Native executable differs from pinned RAD 4acbe00')
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    for flag in ['input', 'output-prefix', 'adapter_seq', 'whitelist']:
        parser.add_argument('--'+flag, required=True)
    parser.add_argument('--barcode-length', type=int, required=True)
    parser.add_argument('--max-error', type=float, required=True)
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--chunk-size', type=int, required=True)
    parser.add_argument('--left-margin', type=int, default=0)
    parser.add_argument('--right-margin', type=int, default=0)
    parser.add_argument('--max-reads', type=int, default=0)
    parsed = parser.parse_args(command[2:])
    require(parsed.adapter_seq == record['adapter_seq'] and parsed.barcode_length == 16,
            'Native adapter or barcode length differs from the dataset profile')
    require(parsed.left_margin == record['left_margin'] and parsed.right_margin == record['right_margin'],
            'Native margins differ from the dataset profile')
    require(parsed.max_error == 0.3 and parsed.max_reads <= 0 and parsed.threads > 0 and parsed.chunk_size == 10000,
            'Require error0.3, full input, positive threads and chunk10000')
    require(sha(parsed.whitelist) == record['catalogue_sha256'], 'Native catalogue differs from the dataset pin')
    return parsed


def read_barcodes(path, allow_empty=False):
    content = Path(path).read_bytes()
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)
    lines = content.decode('ascii').splitlines()
    require((bool(lines) or allow_empty) and all(re.fullmatch('[ACGT]{16}', line) for line in lines),
            'Expected exactly one 16-base A/C/G/T barcode per line: '+str(path))
    require(len(lines) == len(set(lines)), 'Duplicate barcodes: '+str(path))
    return set(lines)


def reference_identity(path, record):
    """Require the matched barcode set, allowing equivalent gzip formatting."""
    reference = read_barcodes(path)
    file_sha256 = sha(path)
    barcode_sha256 = hashlib.sha256(('\n'.join(sorted(reference))+'\n').encode()).hexdigest()
    exact = file_sha256 == record['reference_sha256']
    require(exact or barcode_sha256 == record.get('reference_barcode_sha256'),
            'Reference differs from the exact-file and canonical-barcode pins')
    return reference, dict(file_sha256=file_sha256, barcode_sha256=barcode_sha256,
                           matched_by='file_sha256' if exact else 'canonical_barcode_sha256')


def reconcile_records(summary, stderr, record, input_path):
    processed = int(summary['reads_processed'])
    skips = re.findall(r"^Warning: skipping zero-length sequence record '([^']+)' in (.+)$", stderr, re.M)
    require(all(path == input_path for _, path in skips), 'Empty-record warning names a different input')
    suppressed = 'additional zero-length sequence warnings' in stderr
    expected = record['input_records']
    if suppressed:
        require(expected is not None and len(skips) == 10 and expected-processed >= 11,
                'Suppressed empty-record warnings require a known total record count')
        empty = expected-processed
        basis = 'Known input records minus native nonempty sequences; first10 empty IDs logged, subsequent warnings suppressed'
    else:
        empty = len(skips)
        require(expected is None or processed+empty == expected,
                'Native sequences plus skipped empty records do not match the input record count')
        basis = 'Native nonempty sequences plus every logged empty record'
    return dict(input_records=processed+empty, processed_nonempty_sequences=processed,
                skipped_empty_records=empty, logged_empty_read_ids=[name for name, _ in skips],
                input_record_count_basis=basis if expected is None or suppressed else 'Pinned input count reconciled with native nonempty sequences and empty-record warnings')


def score(record_path, run_dir, output_dir, input_receipt_path=None, native_receipt_path=None):
    record = load_record(record_path)
    run_dir, output_dir = Path(run_dir).resolve(), Path(output_dir).resolve()
    require(not output_dir.exists(), 'Scoring output must be a new directory')
    command_path = run_dir/'command.json'
    command = read_json(command_path)
    native_path = Path(native_receipt_path) if native_receipt_path else run_dir/'native_success.json'
    native = read_json(native_path)
    build_receipt = run_dir/'rad_build_receipt.json'
    require(native.get('rad_build_receipt_sha256') == sha(build_receipt), 'Source build receipt changed')
    build = verify_build(command[0], native['rad_source_path'], build_receipt, native['rad_sha256'])
    parsed = parse_command(command, record, build['rad_sha256'])
    receipt_path = Path(input_receipt_path) if input_receipt_path else run_dir/'input_receipt.json'
    input_receipt = read_json(receipt_path)
    validate_input_receipt(input_receipt, record, parsed.input)
    require(native.get('status') == 'passed' and native.get('input_stat_unchanged') is True,
            'Require a successful native receipt with unchanged input identity')
    require(native.get('native_exit_code', native.get('exit_code')) == 0, 'Native exit receipt is not zero')
    require(native.get('command_sha256') == sha(command_path),
            'Native receipt does not bind the exact command; first create a verified reuse receipt')
    require(native.get('input_receipt_sha256') == sha(receipt_path),
            'Native receipt does not bind the verified input receipt; first create a verified reuse receipt')
    require(native.get('rad_commit') == RAD_COMMIT and native.get('rad_sha256') == build['rad_sha256'],
            'Native receipt does not identify the pinned RAD build')
    time_text = (run_dir/'time.txt').read_text()
    require(re.findall(r'^\s*Exit status:\s*(\d+)\s*$', time_text, re.M) == ['0'], 'GNU time did not record native exit0')
    prefix = Path(parsed.output_prefix)
    require(prefix.parent.resolve() == run_dir, 'Native output prefix is outside the supplied run directory')
    summary_path = Path(str(prefix)+'_scan_wl.log')
    summary = dict(line.split('=', 1) for line in summary_path.read_text().splitlines() if '=' in line)
    require(summary.get('input') == parsed.input and summary.get('selection') == 'high_specificity',
            'Native summary must identify this full input and the default high-specificity selection')
    output_hashes = native.get('output_sha256', {})
    for evidence_path in [run_dir/'time.txt', run_dir/'stderr.log', summary_path, Path(str(prefix)+'.txt')]:
        require(output_hashes.get(evidence_path.name) == sha(evidence_path),
                'Native receipt does not bind this output: '+evidence_path.name)
    counts = reconcile_records(summary, (run_dir/'stderr.log').read_text(), record, parsed.input)
    whitelist_path = Path(str(prefix)+'.txt')
    calls = read_barcodes(whitelist_path, allow_empty=True)
    require(len(calls) == int(summary['selected_barcodes']), 'Native selected count does not match its whitelist')
    reference_path = Path(record['reference_path']).expanduser().resolve()
    reference, reference_proof = reference_identity(reference_path, record)
    tp, fp, fn = len(calls & reference), len(calls-reference), len(reference-calls)
    metrics = dict(dataset_id=record['dataset_id'], rad_commit=RAD_COMMIT, max_error=0.3,
                   **counts, detected_barcodes=len(calls), reference_barcodes=len(reference),
                   TP=tp, FP=fp, FN=fn, precision=tp/len(calls) if calls else 0.0, recall=tp/len(reference),
                   F1=2*tp/(len(calls)+len(reference)))
    # Per-barcode labels are also available in a readable table for plotting.
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir/'metrics.csv').open('x', newline='') as handle:
        simple = {key:value for key,value in metrics.items() if not isinstance(value, list)}
        writer = csv.DictWriter(handle, fieldnames=list(simple)); writer.writeheader(); writer.writerow(simple)
    with (output_dir/'barcode_membership.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['barcode', 'detected', 'in_reference'])
        writer.writeheader()
        writer.writerows(dict(barcode=barcode, detected=int(barcode in calls), in_reference=int(barcode in reference))
                         for barcode in sorted(calls | reference))
    evidence = [Path(record_path), command_path, receipt_path, native_path, build_receipt, run_dir/'time.txt',
                run_dir/'stderr.log', summary_path, whitelist_path, reference_path]
    write_json(output_dir/'metrics.json', dict(status='passed', metrics=metrics, native_summary=summary,
        reference_identity=reference_proof,
        selected_barcode_sha256=hashlib.sha256(('\n'.join(sorted(calls))+('\n' if calls else '')).encode()).hexdigest(),
        input_identity={key:input_receipt[key] for key in ['bytes', 'sha256', 'md5'] if key in input_receipt},
        command=command, threads=parsed.threads, rad_sha256=build['rad_sha256'],rad_source_commit=RAD_COMMIT,
        catalogue_sha256=record['catalogue_sha256'], scorer_sha256=sha(__file__),
        evidence=[dict(path=str(path), sha256=sha(path)) for path in evidence],
        interpretation='TP/FP/FN are reference-list agreement, not independently certified biological cell identities',
        completed_utc=datetime.now(timezone.utc).isoformat()))
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-record', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--input-receipt', type=Path, help='For a verified existing native run')
    parser.add_argument('--native-receipt', type=Path, help='For a verified existing native run')
    args = parser.parse_args()
    print(json.dumps(score(args.dataset_record, args.run_dir, args.output_dir,
                           args.input_receipt, args.native_receipt), indent=2))


if __name__ == '__main__':
    main()
