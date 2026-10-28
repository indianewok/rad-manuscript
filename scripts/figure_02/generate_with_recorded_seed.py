#!/usr/bin/env python3
"""Run a pinned ScTagger quality generator with the recorded quality-tape seed.

The original generator hashes the model's location into the quality-tape seed.
This adapter supplies the recorded integer directly so model files can be moved.
Every other seed call, including each read's barcode-quality draws, is unchanged.
Arguments after -- are passed to the original generator; supply --model there.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'source_data/figure_02/quality_generation_contract.json'
GENERATOR_HASHES = {
    'nanopore2018': {'3efcd5b677bc65b3eebcfb9ed48432829b3c3a5cbb2521807e24f85cd57c834d'},
    'nanopore2023': {'3efcd5b677bc65b3eebcfb9ed48432829b3c3a5cbb2521807e24f85cd57c834d',
                     'aef619a3f417c4aa4c2c9ac3bfd161916a7e85efa23720ae74a8b630a9026e49'},
}
MODEL_HASHES = {
    'nanopore2018': '6f60b7db6691bdf5955da54f621776bd7584d6c21b30f7290dff82d7037a0a85',
    'nanopore2023': '75182dbd45424f811b5ad5f95b1606900a8900b5565075001011433c03478f90',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recorded_seed_function(original, effective_seed, run_seed):
    """Override only the quality-tape call, preserving all per-read RNG calls."""
    def stable_seed(text, seed, purpose):
        if purpose == 'quality-tape':
            if seed != run_seed:
                raise ValueError('Generator seed differs from the selected recorded run')
            return effective_seed
        return original(text, seed, purpose)
    return stable_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', required=True, type=Path,
                        help='Original generator file with a verified SHA-256')
    parser.add_argument('--condition', required=True,
                        choices=['nanopore2018_S', 'nanopore2018_L', 'nanopore2023_L'])
    parser.add_argument('generator_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    forwarded = args.generator_args
    if forwarded[:1] == ['--']:
        forwarded = forwarded[1:]
    if '--model' not in forwarded and not any(x.startswith('--model=') for x in forwarded):
        parser.error('Supply the model file explicitly after -- with --model')
    model_name = args.condition.rsplit('_', 1)[0]
    generator_sha = sha(args.generator)
    if generator_sha not in GENERATOR_HASHES[model_name]:
        raise ValueError('Original generator SHA-256 does not match a pinned source')
    contract = json.loads(CONTRACT.read_text())
    run_seed = contract['seeds'][args.condition]
    effective_seed = contract['effective_quality_tape_seeds'][args.condition]
    if '--seed' not in forwarded and not any(x.startswith('--seed=') for x in forwarded):
        forwarded += ['--seed', str(run_seed)]

    spec = importlib.util.spec_from_file_location('recorded_seed_generator', args.generator)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    parsed = module.build_parser().parse_args(forwarded)
    if parsed.seed != run_seed:
        raise ValueError('--seed must match the recorded seed for the selected condition')
    if sha(parsed.model) != MODEL_HASHES[model_name]:
        raise ValueError('Model SHA-256 differs from the selected quality model')
    module.stable_seed = recorded_seed_function(module.stable_seed, effective_seed, run_seed)
    original_argv = sys.argv
    try:
        sys.argv = [str(args.generator)] + forwarded
        status = module.main()
    finally:
        sys.argv = original_argv
    if status not in (0, None):
        return status
    receipt = dict(condition=args.condition, generator_sha256=generator_sha,
                   model_sha256=MODEL_HASHES[model_name], run_seed=run_seed,
                   effective_quality_tape_seed=effective_seed,
                   seed_override_scope='quality-tape only; every per-read seed uses the original function',
                   adapter_sha256=sha(__file__))
    (parsed.output_dir / 'recorded_seed_adapter.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
