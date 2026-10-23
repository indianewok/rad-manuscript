# Parallel pre-maintenance benchmark design

This run is the controlled accelerated replacement for the original serial
private-partition launch.

- CPU stratum: AMD EPYC 7543, 64 physical cores, one hardware thread per core.
- Every 64-thread tool/replicate pair has an exclusive node.
- After the priority change, each replicate's full tool chain is pinned to one
  node (replicate 1: r08; replicate 2: r09; replicate 3: r10), preserving the
  staged compressed input and controlling the within-replicate CPU host.
- Detection and demultiplexing use the same exact tool commands and acceptance
  schema, but the schedule now completes all whitelist-detection triplicates
  before beginning the remaining demultiplexing phases.
- The three tools and three replicates run concurrently because their raw,
  local-work, lock, and provenance paths are disjoint.
- Each compressed FASTQ is copied to node-local scratch before timing. Copy
  metrics are retained separately and excluded from tool CPU/RSS/wall time.
- Two 16-thread full blocks were started non-exclusively under the separate
  32-CPU general-account allowance so that condition could begin immediately.
  The redundant lab-account 16-thread blocks were cancelled after about two
  minutes of staging/prewarm so that the requested 64-core detection
  triplicates could start immediately; accepted checkpoints survive in the
  two general-account blocks and the separate shared-node arm.
- The lab association has a hard 208-CPU aggregate cap. Three canonical
  64-thread jobs run concurrently; the remaining 16 CPUs host the supplemental
  shared-node arm. This cap, rather than idle node count, limits concurrency.

At 18:28 EDT, the 64-thread jobs were reprioritized again to finish all three
SN-ONT whitelist-detection triplicates before any remaining demultiplexing:

`RAD scan -> Flexiplex scan -> BLAZE scan -> RAD demux -> Flexiplex demux -> BLAZE demux`.

The three post-fix RAD scans were accepted first; their allocations were then
cancelled at the phase boundary, leaving only unaccepted partial demux attempts.
The additive detection-only runner was syntax- and synthetic-tested for every
tool and writes `DETECTION_DONE`, never a demultiplexing acceptance marker.
Flexiplex detection jobs 9332863--9332865 are followed by BLAZE detection jobs
9332866--9332868. The remaining demultiplexing waves are jobs 9332870--9332879.

Historical SN-ONT RAD timings from before the seeding fix are explicitly
excluded from forecasting and from the controlled comparator.

Milestone collectors are interposed after all scans (job 9332869), after the
RAD/Flexiplex demultiplexing comparator (job 9332876), and after BLAZE
demultiplexing (job 9332880). Each writes the partial four-CSV result set before
the next compute-heavy wave is released.
- The input remains gzip-compressed. RAD therefore retains its native
  scan-time pigz behavior requested by the user.

This run must not be pooled with the supplemental non-exclusive SMT profile at
`three_tool_phase_benchmark_20260902_shared_a02`.
