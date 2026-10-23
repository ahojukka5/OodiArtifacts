# Native compatibility matrix, 2026-10-23

This matrix qualifies the unreleased Monge and Delone 0.1.0 candidates.
No package release tag is created. Binary releases are immutable.

Source candidates:

- Monge `68b588b50112c2a316e4d3db10e988dd86fa25a1`, PR #560;
- Delone/DelonePortable `c65fe65a42501622960ad0e5d15658fb46299195`,
  PR #1047;
- build tooling `b8a8bca` and its pinned `native/Project.toml`.

The [machine-readable index](native-matrix-20261023.json) records every new
archive checksum, artifact tree, source revision, platform and Julia ABI.
Each release additionally attaches the full dependency, compiler and library
linkage provenance. The Linux Netgen runtime remains the existing release
`NGSolveNetgen-22b6752d`, tree
`22b6752d1a2d14a9e02e48ea3abfbf3d901ac79b`, archive SHA-256
`b35522e610fb8c10f201dbdcc87c0be3e1036892e7779f7de0cb9cc76dd3406a`.
Its content was not changed. macOS uses one newly built Netgen runtime for
all four Julia minors.

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
| macOS aarch64 | 1.10.11 | Monge | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.10.11 | Delone | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.11.9 | Monge | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.11.9 | Delone | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.12.6 | Monge | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.12.6 | Delone | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.13.1 | Monge | PASS | PASS | PASS | pending |
| macOS aarch64 | 1.13.1 | Delone | PASS | PASS | PASS | pending |
| Linux x86_64 glibc (QEMU) | 1.10.12 | Monge | PASS | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.10.12 | Delone | PASS | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.11.9 | Monge | pending | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.11.9 | Delone | pending | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.12.7 | Monge | pending | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.12.7 | Delone | pending | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.13.2 | Monge | pending | pending | pending | pending |
| Linux x86_64 glibc (QEMU) | 1.13.2 | Delone | pending | pending | pending | pending |

Pending means unverified; it is not a pass. Full suites run through
`Pkg.test` from the exact clean source checkouts because Monge's gallery
checks repository history. They use the same fresh depots and published
native binaries as the URL installation test. No native build or binary
path override is introduced for those suites. Complete-suite outcomes are
independent of the geometry and meshing smoke results.

## Older Julia and later platforms

Julia 1.9.4 cannot resolve the selected Episteme 0.1 dependency: its UUIDs
and Dates compatibility requires Julia 1.10. The pinned CxxWrap 0.17.5
build stack also requires 1.10. CxxWrap 0.17.3 and libcxxwrap 0.14.4 can
resolve on 1.9, but do not remove the Episteme dependency floor. No Julia
1.9 native binary is claimed. DelonePortable independently passed its full
562-test suite on macOS aarch64 Julia 1.9.4.

The source compatibility floor for Monge and Delone is now 1.10. The lowest
fully verified versions will be stated after complete-suite qualification.
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

Manual compatibility workflows remain in Monge #558 and Delone #1045.
They dispatch against the published-binary source candidate and separate
resolution, loading, native execution and full-suite outcomes. No automatic
compatibility triggers, package version bumps or release tags are added.
