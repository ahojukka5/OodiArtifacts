# Native compatibility matrix, 2026-10-23

This matrix qualifies the unreleased Monge and Delone 0.1.0 candidates.
No package release tag is created. Binary releases are immutable.

Source candidates and qualification revisions:

- Monge initial fresh-depot source `68b588b50112c2a316e4d3db10e988dd86fa25a1`, [PR #560](https://github.com/ahojukka5/Monge.jl/pull/560);
- Delone/DelonePortable runtime/artifacts
  `c65fe65a42501622960ad0e5d15658fb46299195`,
  [PR #1047](https://github.com/ahojukka5/Delone.jl/pull/1047);
- build tooling `b8a8bca` and its pinned `native/Project.toml`.

Delone's Julia 1.10 documentation test was backported at
`36442f5320ab6f37e7c1c0c7cc89b0a64b849481`; its full 1.10 suite was rerun,
and the affected test passed 415 checks on every macOS minor. Subsequent installation prose and test comments leave dependency and artifact
selection unchanged. Monge then removes redundant replay bookkeeping at
`aeaea2fb` and restores the original allocation bound; its independent scan
oracle passes all 22 checks on every macOS minor. Native smoke checks and all four macOS
full suites pass after that change; each suite has 11,791 passes and the
existing optional integration skip. Final Monge commit
`8b740524f60905343a36d86e1b3577b8260e6f74` changes only a documentation
cross-reference target inside a docstring; all executable source and artifact
selections match that full-suite qualification. Both manuals then build on
Julia 1.12.6 with doctests/export checks enabled and deployment disabled.

Delone's Linux 1.10 full run found a platform-dependent fixture reduction:
its curved shared-edge sample rounded onto the boundary rather than one ulp
past it. Test-only commit `223b934d` moves one coordinate node by one ulp;
it retains the exact overshoot assertion, independent graph oracle and all
projection tolerances. The revised 62-check case passes on all macOS minors
and Linux 1.10; restoring the earlier Newton trial produces ten failures,
confirming preserved regression coverage. Remaining Linux checks are running.
Linux 1.11 also passes the revised case. The first Linux 1.10 full run later
ended with SIGKILL: the VM kernel recorded memory exhaustion when an extra
fixture probe overlapped two full suites. That probe was cancelled; subsequent
qualification uses at most two workers. A second OOM interrupted the Linux 1.11 architecture subprocess; that run
also records an Aqua 180s shutdown timeout. A temporary 4 GiB swap file was
added to the existing 8 GiB local VM without restarting active tests.
Interrupted runs remain FAIL,
with both its fixture failure and resource interruption retained, until rerun.

The [structured results](native-matrix-20261023-results.json) retain separate
stage outcomes, log checksums and immutable snapshot identities. Bulk logs
and snapshots remain in the local qualification cache. The [machine-readable index](native-matrix-20261023.json) records every new
archive checksum, artifact tree, source revision, platform and Julia ABI.
Each release additionally attaches the full dependency, compiler and library
linkage provenance. The Linux Netgen runtime remains the existing release
`NGSolveNetgen-22b6752d`, tree
`22b6752d1a2d14a9e02e48ea3abfbf3d901ac79b`, archive SHA-256
`b35522e610fb8c10f201dbdcc87c0be3e1036892e7779f7de0cb9cc76dd3406a`.
Its content was not changed. Its embedded `netgen_version.hpp` records
`6.2.2606` and `ga3e08f0e`, matching the version/source prefix of the pinned
macOS build. The old release has no separate provenance attachment; its
archive/tree and embedded identity are retained rather than inventing missing
historical build metadata. macOS uses one newly built Netgen runtime for
all four Julia minors. Its provenance records the Julia build-driver version
and an augmented build-host triplet; `julia_abi = "none"` and the consuming
artifact declaration has no Julia selector.

## Installation results

These results use empty per-minor depots, General plus OodiRegistry, exact
GitHub source revisions, published artifact URLs, and no artifact overrides
or C++ source builds. CxxWrap, OCCT_jll and Zlib_jll are explicitly added to
the active environment for Delone's optional native-provider contract.
Monge geometry checks box volume 6. Delone generates a circle mesh and
imports the committed STEP box before producing a finite tetrahedral mesh.

Linux x86_64 tests run under local QEMU on this Apple Silicon machine, in
an AlmaLinux 8 container. They are not a native x86_64 hardware run. macOS
aarch64 tests run directly on the host. Patch versions differ because the
installed host and downloaded Linux runtimes were selected independently.

| Platform | Julia | Package | Resolution | Loading | Native execution | Full tests |
|---|---|---|---|---|---|---|
| macOS aarch64 | 1.10.11 | Monge | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.10.11 | Delone | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.11.9 | Monge | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.11.9 | Delone | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.12.6 | Monge | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.12.6 | Delone | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.13.1 | Monge | PASS | PASS | PASS | PASS |
| macOS aarch64 | 1.13.1 | Delone | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc (QEMU) | 1.10.12 | Monge | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.10.12 | Delone | PASS | PASS | PASS | FAIL |
| Linux x86_64 glibc (QEMU) | 1.11.9 | Monge | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.11.9 | Delone | PASS | PASS | PASS | FAIL |
| Linux x86_64 glibc (QEMU) | 1.12.7 | Monge | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.12.7 | Delone | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.13.2 | Monge | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.13.2 | Delone | PASS | PASS | PASS | pending |

Monge's complete macOS suites each passed 11,791 assertions, with one
existing skip for an optional legacy Netgen.jl monorepo integration. Delone's
macOS full suites passed 92,319 (1.10), 92,344 (1.11/1.12), and 92,343
(1.13) assertions. The 1.13 count precedes the test-only documentation
backport; the changed 415-check file was then rerun successfully.

Pending means unverified; it is not a pass. The local VM and agent server
restarted during initial Linux full-suite runs. Interrupted logs are retained;
resumed package suites are recorded separately and never counted as passes
without their completion marker. Full suites run through
`Pkg.test` from the exact clean source checkouts because Monge's
tracked-file and provenance checks require a Git checkout. They use the same fresh depots and published
native binaries as the URL installation test. No native build or binary
path override is introduced for those suites. Complete-suite outcomes are
independent of the geometry and meshing smoke results. Linux complete-suite
subprocesses use `--optimize=1 --pkgimages=no` under QEMU; newer Linux runs
also select `--cpu-target=generic` and retain Julia's bundled stdlib cache.
The initial 1.11 run reported conflicting optional StaticArrays constraints,
and 1.12 hit an internal Pkg constraint-graph assertion with package images
disabled. Resolution succeeded with the generic-CPU/bundled-cache settings.
No package compatibility bounds were narrowed to bypass those failures.
macOS uses the default optimization settings. The test entrypoints and selection are unchanged.

## Older Julia and later platforms

| Platform | Julia | Package | Resolution | Loading | Native execution | Full tests |
|---|---|---|---|---|---|---|
| macOS aarch64 | 1.9.4 | Monge | FAIL (dependency floor) | unrun | unbuilt | unrun |
| macOS aarch64 | 1.9.4 | Delone | FAIL (dependency floor) | unrun | unbuilt | unrun |
| macOS aarch64 | 1.9.4 | DelonePortable | PASS | PASS | not applicable | PASS (562) |

Julia 1.9.4 cannot resolve the selected Episteme 0.1 dependency: its UUIDs
and Dates compatibility requires Julia 1.10. The pinned CxxWrap 0.17.5
build stack also requires 1.10. CxxWrap 0.17.3 and libcxxwrap 0.14.4 can
resolve on 1.9, but do not remove the Episteme dependency floor. No Julia
1.9 native binary is claimed. DelonePortable independently passed its full
562-test suite on macOS aarch64 Julia 1.9.4.

The source compatibility floor for Monge and Delone is now 1.10. Both are
fully verified on macOS aarch64 Julia 1.10.11, their lowest verified patch.
Linux native execution has also passed on Julia 1.10.12.
Linux aarch64 and macOS x86_64 remain future extensions, without a support
claim or newly enabled platform declaration.

## Build and qualification notes

Sources are OpenCascadeCxxWrap
`fc988de3315b21cd900a86548989d2d31293619e`, NetgenCxxWrap
`301822bb5309af57ec7242e557a16ea1f12f610a`, and macOS Netgen
`a3e08f0ec196b442f7de3b9b717ab86c6993f1ab`. All new wrappers use OCCT
7.9.3, CxxWrap 0.17.5 and libcxxwrap 0.14.12. Every wrapper explicitly
selects the intended Julia executable and records matching minor-ABI
library linkage. Archive and extracted tree hashes are checked separately.

Linux builds use EL8 glibc headers with GCC 12 C++ headers/linker and host
Clang object compilation. GCC 8 filesystem headers produced a crash when
passing STEP filenames to the existing Netgen runtime; those candidates
were rejected and never published. CxxWrap's default ELF DEEPBIND flag
also separated fundamental type caches with Clang's weak symbols. Both
packages now request ordinary lazy/global binding, verified by native tests.
macOS machine-name parsing accepts the qualified Apple Silicon family,
including versioned `arm64-apple-darwin` identities.

Julia 1.10/1.11 source fixes preserve Monge's public Assembly path and avoid
redefining Delone's shared closure-bearing test fixture. Isolated Monge
tests now declare Base64 and Pkg. Delone's moved hierarchy fixture path was
corrected, and Aqua retains its persistent-task test with a finite 180s
shutdown allowance for Julia 1.11 cache emission. No tests are disabled.

Manual compatibility workflows remain in
[Monge #558](https://github.com/ahojukka5/Monge.jl/pull/558) and
[Delone #1045](https://github.com/ahojukka5/Delone.jl/pull/1045).
They dispatch against the published-binary source candidate and separate
resolution, loading, native execution and full-suite outcomes. No automatic
compatibility triggers, package version bumps or release tags are added.
