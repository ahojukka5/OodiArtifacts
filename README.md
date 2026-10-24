# OodiArtifacts

**OodiArtifacts** is the public GitHub Release host for native binary artifacts
used by the [Oodi scientific computing ecosystem](https://github.com/ahojukka5/Oodi.jl).
It provides versioned, content-addressed downloads while some native dependencies
are not distributed through JuliaBinaryWrappers / Yggdrasil. It is **not** a Julia
package, a Julia registry, or a substitute for Julia's package manager.

**Canonical repository:** https://github.com/ahojukka5/OodiArtifacts

The repository was renamed from `ahojukka5/oodi-artifacts` in October 2026.
Use the new name for links and future `Artifacts.toml` updates. Consumers with
older URLs should update them as part of a reviewed, clean-install-qualified
source change; renaming the host does not justify republishing or changing
existing artifact contents.

## How it fits into Julia packaging

| Component | Responsibility |
| --- | --- |
| [OodiRegistry](https://github.com/ahojukka5/OodiRegistry) | Registers Julia package names, UUIDs, versions, dependencies and source trees |
| **OodiArtifacts** | Hosts the native tarballs and their build/provenance records in immutable GitHub Releases |
| [Monge.jl](https://github.com/ahojukka5/Monge.jl) and [Delone.jl](https://github.com/ahojukka5/Delone.jl) | Select the matching native binaries through their `Artifacts.toml` declarations |
| Julia Pkg / Artifacts | Downloads the selected asset and checks the archive SHA-256 and extracted artifact Git tree |

The public artifact downloads do **not** make private Julia package source
repositories public. The OodiRegistry currently registers Episteme; Monge,
Delone and DelonePortable have separate source/registration work in progress.
Publishing a binary release here does not register a Julia package in
OodiRegistry or Julia General.

## Published binary matrix

**Snapshot: 2026-10-23.** GitHub Releases contain the following Julia
**1.10, 1.11, 1.12 and 1.13** CxxWrap binaries for the two currently
qualified target platform families. Every table cell links to the exact
published release. The hexadecimal suffix is derived from the Julia artifact
content tree; it is **not** a semantic package version.

| Artifact | Platform | Julia 1.10 | Julia 1.11 | Julia 1.12 | Julia 1.13 |
| --- | --- | --- | --- | --- | --- |
| `libopencascade_cxxwrap` | Linux x86_64 (glibc) | [`2de1d4e9`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-2de1d4e9) | [`40362230`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-40362230) | [`8b685931`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-8b685931) | [`969c64a1`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-969c64a1) |
| `libopencascade_cxxwrap` | macOS aarch64 | [`767cd6ee`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-767cd6ee) | [`b2a338c1`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-b2a338c1) | [`52eda298`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-52eda298) | [`c44d084b`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-c44d084b) |
| `libnetgen_cxxwrap` | Linux x86_64 (glibc) | [`5fd776a6`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-5fd776a6) | [`063c21fd`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-063c21fd) | [`e665a174`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-e665a174) | [`8b265184`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-8b265184) |
| `libnetgen_cxxwrap` | macOS aarch64 | [`0a71b26c`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-0a71b26c) | [`c9be8c9b`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-c9be8c9b) | [`c6d99568`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-c6d99568) | [`a983e9b1`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-a983e9b1) |

The underlying Netgen runtime is independent of the Julia minor version
and is distributed once per platform:

| Artifact | Platform | Release |
| --- | --- | --- |
| `NGSolveNetgen` (`libngcore`, `libnglib`) | Linux x86_64 (glibc) | [`NGSolveNetgen-22b6752d`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/NGSolveNetgen-22b6752d) (retained existing build) |
| `NGSolveNetgen` (`libngcore`, `libnglib`) | macOS aarch64 | [`NGSolveNetgen-bfef5545`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/NGSolveNetgen-bfef5545) (published 2026-10-23) |

The separate OCCT 8.0.1 native runtime is available once per platform:

| Artifact | Platform | Release |
| --- | --- | --- |
| `OCCT` 8.0.1 (48 native toolkits, headers, CMake metadata and resources) | Linux x86_64, EL8/glibc qualified | [`OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24) |
| `OCCT` 8.0.1 (48 native toolkits, headers, CMake metadata and resources) | macOS aarch64, minimum target 11.0 | [`OCCT-8.0.1-macos-aarch64-04d2d2f805e3`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/OCCT-8.0.1-macos-aarch64-04d2d2f805e3) |

The [release and qualification records](docs/occt-8.0.1.md)
include both hashes and public-download verification. This runtime has no
Julia ABI selector and does not upgrade the existing 7.9.3 consumers.

Browse [all releases](https://github.com/ahojukka5/OodiArtifacts/releases)
for the tarball and any accompanying `*.provenance.json` or older
`*.provenance.toml` record. The OpenCASCADE and Netgen wrapper sources are
maintained separately in
[OpenCascadeCxxWrap](https://github.com/ahojukka5/OpenCascadeCxxWrap) and
[NetgenCxxWrap_jll](https://github.com/ahojukka5/NetgenCxxWrap_jll).

Source integration is merged in
[Monge #564](https://github.com/ahojukka5/Monge.jl/pull/564) and proposed in
[Delone #1055](https://github.com/ahojukka5/Delone.jl/pull/1055).
The [integration qualification](docs/native-integration-20261024.md)
tests their exact source revisions from fresh depots, with separate
resolution, loading, geometry/meshing and complete-suite outcomes.
This qualification is in progress; publication alone does not qualify a
package release. The [original compatibility evidence](docs/native-matrix-20261023.md)
and [historical results](docs/native-matrix-20261023-results.json) retain
earlier successes and failures, including the unsuccessful Delone Linux
1.12 suite. Cancelled, timed-out and partial runs never count as successes.

Other architectures, including Linux aarch64 and macOS x86_64, are **not**
covered by this published matrix. Do not infer platform support from the
presence of a release for another architecture.

## Artifact selection and provenance

- Native wrapper archives are built for a **specific platform and Julia minor
  ABI**. Monge and Delone must declare the matching `julia_version` selector
  in `Artifacts.toml`; the Netgen runtime needs no Julia-version selector.
- Consumers pin an exact `git-tree-sha1` for extracted artifact content and
  `sha256` for the downloaded tarball. The hash of one is **not** the hash of
  the other. Do not choose an archive merely because its tag is the newest.
- New releases include a provenance sidecar with source revision, platform,
  Julia ABI (where applicable), dependency versions, toolchain and archive/tree
  identities. Some older releases have less extensive metadata; do not invent
  missing historical provenance.
- A release tag and its binary bytes are immutable. Rebuilds belong in
  **new** content-addressed releases if their contents differ. Preserve the
  historical releases for reproducible research.
- The normal user installation path downloads published archives without
  compiling C++ and without `artifacts/Overrides.toml`. Local developer
  overrides and experimental builds do not qualify a release.

The new compatibility wrappers use OpenCASCADE/OCCT 7.9.3,
CxxWrap 0.17.5 and libcxxwrap 0.14.12. Linux binaries were built against
an EL8-compatible glibc baseline. Release-specific linkage and checksum
details are authoritative in each release's provenance record, rather than
in an unversioned README.

### Historical builds

Older tags such as
[`libopencascade_cxxwrap-707416b9`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-707416b9),
[`libopencascade_cxxwrap-fe916c69`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-fe916c69),
[`libnetgen_cxxwrap-d2a7f166`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-d2a7f166) and
[`libnetgen_cxxwrap-5f0f5daa`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libnetgen_cxxwrap-5f0f5daa)
remain available for consumers that deliberately pin their exact artifact
hashes. They are **not** a substitute for selecting the Julia-minor-qualified
matrix above. The even earlier
[`libopencascade_cxxwrap-19b04788`](https://github.com/ahojukka5/OodiArtifacts/releases/tag/libopencascade_cxxwrap-19b04788)
is retained for provenance, not recommended as the current Monge binding.

## Julia artifact consumption

The root [`Artifacts.toml`](Artifacts.toml) selects the existing native OCCT
8.0.1 releases through the `occt_8_0_1` key on Apple Silicon and Linux
x86_64/glibc. It has no Julia minor-version selector. The bounded
[clean-depot test harness and Yggdrasil handoff](docs/occt-8.0.1-yggdrasil.md)
separate actual Pkg installation, native load/geometry/relocation checks and
any independent BinaryBuilder source builds. This declaration does not
create an OCCT_jll package or upgrade Monge/Delone dependencies.

## Building and publishing

The native **OCCT 8.0.1** runtime has a separate
[manual Linux build/qualify/publish workflow](.github/workflows/publish-occt-8-linux.yml).
Its [pinned recipe and qualification contract](docs/occt-8.0.1.md) also
cover the paired Apple Silicon build. These archives contain OCCT itself,
have no Julia ABI selector, and do not change existing 7.9.3 consumers.

The checked-in
[`publish-opencascade-cxxwrap.yml`](.github/workflows/publish-opencascade-cxxwrap.yml)
is an **existing manual** (`workflow_dispatch`) publisher for a single
Linux x86_64 OpenCascade wrapper build. It uses the GitHub-hosted
`ubuntu-latest` runner and explicit pinned wrapper/Monge revisions. It
does **not** generate or qualify the entire cross-version matrix, and should
not be dispatched without reviewing its pins and the intended ABI.

For the Julia-versioned OpenCascade and Netgen **wrappers**, the
[source-pinned native build tools](scripts/build_native.jl),
[Julia dependency specification](native/Project.toml) and
[dated compatibility report](docs/native-matrix-20261023.md)
describe the separately qualified binary matrix. These recipes are
distinct from the OCCT 8.0.1 runtime build described above.
This repository documents and distributes binaries; it does not
automatically release Monge or Delone package versions.

No native artifact publication is triggered by an ordinary push or PR.
The lightweight [CI workflow](.github/workflows/ci.yml) validates workflow
policy; it does not publish binaries. Native publication and package release
qualification are separate operations.

## Licensing

The repository's [MIT license](LICENSE) applies to repository-owned source,
scripts and documentation. It **does not relicense** the native release
assets. OpenCascadeCxxWrap and NetgenCxxWrap wrapper code is MIT, while
linked OpenCASCADE and Netgen components retain their respective LGPL terms
and exceptions. Consult the per-release source and license provenance
before redistributing an archive.
