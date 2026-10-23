# OCCT 8.0.1: Julia artifact qualification and Yggdrasil handoff

This handoff addresses [OodiArtifacts #28](https://github.com/ahojukka5/OodiArtifacts/issues/28).
OodiArtifacts hosts existing native archives. Yggdrasil must independently
compile source with BinaryBuilder and qualify its selected targets. Installing
an archive through Julia Pkg does not create `OCCT_jll` or qualify Monge,
Delone, CxxWrap or Netgen against OCCT 8.

## Immutable inputs and reproduction

The [root Artifacts.toml](../Artifacts.toml) binds `occt_8_0_1` to exactly two
platforms: `aarch64`/`macos` and `x86_64`/`linux`/`glibc`. It deliberately has
no `julia_version` selector. The archive/tree identities are in the
[native release record](occt-8.0.1.md#published-apple-silicon-artifact), along
with the Linux record immediately below it. Published archives and tags
remain unchanged.

Source is upstream [V8.0.1](https://github.com/Open-Cascade-SAS/OCCT/releases/tag/V8.0.1),
commit `b8f597c677811d1f9f4d8a97f5ae2825c0353a42`.
The [commit tarball](https://codeload.github.com/Open-Cascade-SAS/OCCT/tar.gz/b8f597c677811d1f9f4d8a97f5ae2825c0353a42)
SHA-256 is `dba62b81078dd43cec23feba89432be301582341001edad1b93342ad8bda35ea`.
The [pinned qualification inputs](../scripts/occt/qualification-inputs.json)
include archive/tree hashes, provenance-sidecar checksums and all products.

Prerequisites are Python 3.11 or newer, CMake, Ninja, Git and a native C++17
compiler. On Apple Silicon, the tested Juliaup channels are `1.10`
(currently Julia 1.10.11 on this host) and `1.13.1`:

```sh
python3 scripts/occt/qualify_artifacts.py --julia julia --channel 1.10 \
  --work "$HOME/.cache/oodi/OodiArtifacts/occt-8.0.1-pkg/macos-julia-1.10"
python3 scripts/occt/qualify_artifacts.py --julia julia --channel 1.13.1 \
  --work "$HOME/.cache/oodi/OodiArtifacts/occt-8.0.1-pkg/macos-julia-1.13"
```

Each work directory must be new and empty. The harness creates one empty
Julia depot per case and sets `JULIA_DEPOT_PATH` to that depot alone,
`JULIA_LOAD_PATH=@stdlib`, `JULIA_PKG_SERVER=""`, and hash verification on.
There is no artifact override or reused binary cache. Julia's
`ensure_artifact_installed`, `artifact_meta`, `artifact_path` and
`verify_artifact` perform selection, public download, checksum validation,
unpacking and resolution. A separate Downloads/SHA check is recorded as
independent archive verification, not as the Pkg installation itself.

The negative cases use an unsupported Linux/musl selector and the real
archive with an intentionally false SHA-256 before the correct tree is
installed. The latter uses a local file URL only for the negative input;
the successful install downloads the canonical public release URL.
Failures must be platform selection/checksum failures, not network errors.

The existing [C++ consumer](../scripts/occt/smoke/main.cpp) is built with the
Pkg-selected prefix's installed CMake targets. It records the libraries
actually loaded, not only declared linker dependencies. All 48 must come
from that prefix. The harness then copies the installed tree, hides the
original Pkg prefix, and repeats configure/build/load/geometry tests from
the relocated copy. It restores the original directory even on failure.
`qualification.json`, `pkg-result.toml` and the console log retain results.
Bulk logs, test depots and generated binaries stay outside this repository.

Linux uses the existing [manual workflow](../.github/workflows/publish-occt-8-linux.yml),
with its read-only qualification mode, on a real `ubuntu-24.04` x86_64 runner:

```sh
gh workflow run publish-occt-8-linux.yml --repo ahojukka5/OodiArtifacts \
  --ref test/28-artifact-qualification -f publish=false -f qualify_artifacts=true
```

After merge, use `--ref master`. This mode has Julia 1.10.11/1.13.1 jobs,
downloads the existing archives, builds only the tiny C++ consumers, and
uploads logs/reports. It skips both OCCT source building and release
publication, including when `publish=true` was also supplied. The original
publisher still requires master and its explicit publish control. No new
workflow, secret, automatic trigger, artifact replacement or release tag
is introduced by this validation.

## Evidence and limits

The native build evidence is complete in [PR #26](https://github.com/ahojukka5/OodiArtifacts/pull/26),
[PR #27](https://github.com/ahojukka5/OodiArtifacts/pull/27) and
[Linux run 40025009407](https://github.com/ahojukka5/OodiArtifacts/actions/runs/40025009407).
New Pkg-installed-prefix results are independent of those native build
jobs. All four final cases passed from clean committed harness source
`0ea8ca83ffdb97ccf2024149f7978da54ea2fd7c`. The
[compact evidence record](occt-8.0.1-pkg-evidence.json) includes every
actual toolkit filename and its work-relative loaded prefix; raw reports
retain absolute paths. The native-source build and Pkg-consumer results
are separate evidence classes.

| Evidence | macOS aarch64 | Linux x86_64/glibc |
| --- | --- | --- |
| Existing native source build / native release qualification | PASS, original local Apple Clang evidence | PASS, original hosted EL8 evidence |
| New archive/provenance download and checksum / extracted tree | PASS on Julia 1.10.11 and 1.13.1 | PASS on Julia 1.10.11 and 1.13.1 |
| New actual Pkg artifact selection/install/verify in empty depots | PASS on Julia 1.10.11 and 1.13.1 | PASS on Julia 1.10.11 and 1.13.1 |
| Wrong checksum / unsupported platform rejection | PASS on both versions | PASS on both versions |
| Actual shared-library load paths | PASS, all 48 from selected prefix, both versions | PASS, all 48 from selected prefix, both versions |
| C++ geometry/exchange smoke from Pkg prefix and relocated copy | PASS, both versions, original prefix hidden for relocation | PASS, both versions, original prefix hidden for relocation |
| BinaryBuilder/Yggdrasil source build | NOT RUN | NOT RUN |

The [Linux qualification run 40040162123](https://github.com/ahojukka5/OodiArtifacts/actions/runs/40040162123)
succeeded, with both the source-build and publisher jobs skipped. Its
`occt-pkg-linux-julia-1.10.11` and `occt-pkg-linux-julia-1.13.1` workflow
artifacts contain the complete logs, Pkg results and load-path reports.
These new Pkg/C++ cases ran on **Ubuntu 24.04.5 LTS**; the separate original
native archive build/runtime qualification used EL8. The new Linux C++
consumer used GNU C++ 13.3.0. The local Mac cases
ran on macOS 27.0.1 and retain raw reports at
`~/.cache/oodi/OodiArtifacts/occt-8.0.1-pkg/macos-1.10-final/qualification.json`
and `macos-1.13-final/qualification.json`, with adjacent console logs.
No physical macOS 11 host or earlier Linux distribution was tested.

A BinaryBuilder source build was not reproduced on the Mac: Docker's daemon
is unavailable. The optional BinaryBuilder cross-build matrix is not part
of the bounded Linux Pkg-consumption job. Neither native nor Pkg success
is a BinaryBuilder PASS. No claim covers untested architectures, musl,
Windows, FreeBSD, macOS x86_64 or other Julia versions. macOS 11.0 is the
inspected deployment target; physical execution on macOS 11 was not tested.

Native toolchains and measured ABI requirements:

| Field | Linux native archive | Mac native archive |
| --- | --- | --- |
| Compiler | GCC 8.5.0 (Red Hat 8.5.0-29), C++17, cxx11 string ABI | Apple Clang 21.0.0 (clang-2100.3.34.2), C++17, libc++ |
| Build system | CMake 3.26.5, Ninja 1.8.2, GNU ld 2.30-128.el8_10 | CMake 4.4.2, Ninja 1.13.2, Apple ld 27037.1 |
| Sysroot / OS | Digest-pinned AlmaLinux 8.10, glibc 2.28 | SDK 27.0 / macOS 27.0.1 (26A434), arm64 |
| Actual imported symbol ceilings | GLIBC 2.27, GLIBCXX 3.4.21, CXXABI 1.3.9 | Not ELF; every Mach-O minimum OS is 11.0 |
| Qualified runtime | EL8/glibc 2.28; earlier distributions untested | macOS 27.0.1; 11.0 execution untested |
| External runtime dependencies | System C/C++/pthread/dl/m/rt libraries only | Packaged OCCT libraries plus Apple system libraries/frameworks |
| Relocation | `$ORIGIN` | `@rpath` IDs and `@loader_path` search path |

The native Linux image is
`almalinux:8.10@sha256:e6d31b01fca10ed4f914e84e1139c3a40d6acf3d8346224a32f3e5649b1a3f7d`.
Permanent native recipe snapshots are
[Linux d22a008](https://github.com/ahojukka5/OodiArtifacts/blob/d22a008e10826ed76bd32c0a10a76b9e30d9d9a8/scripts/occt/occt.py)
and
[Mac 2f8d6d6](https://github.com/ahojukka5/OodiArtifacts/blob/2f8d6d67358bd7d9c9b02a7d9f3574831569a9f6/scripts/occt/build-macos.sh).
Permanent Pkg qualification snapshots are
[the artifact declaration](https://github.com/ahojukka5/OodiArtifacts/blob/0ea8ca83ffdb97ccf2024149f7978da54ea2fd7c/Artifacts.toml)
and
[the harness](https://github.com/ahojukka5/OodiArtifacts/blob/0ea8ca83ffdb97ccf2024149f7978da54ea2fd7c/scripts/occt/qualify_artifacts.py).

The JSON sidecars contain every library's linkage and the complete Linux
RPM identities. Source paths in diagnostics are mapped to `/usr/src/occt`
and `/usr/src/occt-build`; private mapping flags are removed from exported
CMake metadata. No Homebrew runtime dependency is admitted.

## Native CMake contract and products

The canonical shared switches are `OPTIONS` in
[`scripts/occt/occt.py`](../scripts/occt/occt.py). In particular:

```text
CMAKE_BUILD_TYPE=Release  BUILD_LIBRARY_TYPE=Shared
BUILD_CPP_STANDARD=C++17  BUILD_SOVERSION_NUMBERS=3
BUILD_MODULE_FoundationClasses=ON  BUILD_MODULE_ModelingData=ON
BUILD_MODULE_ModelingAlgorithms=ON  BUILD_MODULE_DataExchange=ON
BUILD_MODULE_ApplicationFramework=OFF  BUILD_MODULE_Visualization=OFF
BUILD_MODULE_Draw=OFF  BUILD_USE_PCH=OFF  BUILD_USE_VCPKG=OFF
USE_TK=OFF  USE_XLIB=OFF  USE_OPENGL=OFF  USE_GLES2=OFF
USE_FREETYPE=OFF  USE_FREEIMAGE=OFF  USE_FFMPEG=OFF  USE_TBB=OFF
USE_RAPIDJSON=OFF  USE_DRACO=OFF  USE_EIGEN=OFF
INSTALL_DIR_LIB=lib  INSTALL_DIR_INCLUDE=include/opencascade
INSTALL_DIR_CMAKE=lib/cmake/opencascade
INSTALL_DIR_RESOURCE=share/opencascade/resources
```

The Unix install also contains `LICENSE_LGPL_21.txt` and
`OCCT_LGPL_EXCEPTION.txt`. Nonrelocatable upstream `bin/` environment helpers
are omitted. Set `CSF_OCCTResourcePath` to the relocated resource directory.
XCAF pulls in TKService/TKV3d/TKVCAF without enabling the full Visualization
module. The qualified workload is headless geometry/exchange; rendering,
fonts and RapidJSON/glTF functionality are disabled.

All 48 library basenames (prefix `lib`, native `.so`/`.dylib` suffix):

```text
TKBO TKBRep TKBin TKBinL TKBinTObj TKBinXCAF TKBool TKCAF TKCDF
TKDE TKDECascade TKDEIGES TKDEOBJ TKDEPLY TKDESTEP TKDESTL TKDEVRML
TKExpress TKFeat TKFillet TKG2d TKG3d TKGeomAlgo TKGeomBase TKHLR
TKHelix TKLCAF TKMath TKMesh TKOffset TKPrim TKRWMesh TKService
TKShHealing TKStd TKStdL TKTObj TKTopAlgo TKV3d TKVCAF TKXCAF
TKXMesh TKXSBase TKXml TKXmlL TKXmlTObj TKXmlXCAF TKernel
```

## Updating the pending Yggdrasil recipe

Reference inspected: [PR #14115](https://github.com/JuliaPackaging/Yggdrasil/pull/14115),
head `5f4b7b27c95eb2289572654031caf9bb00e59bc8`, including its
[`O/OCCT/build_tarballs.jl`](https://github.com/JuliaPackaging/Yggdrasil/blob/5f4b7b27c95eb2289572654031caf9bb00e59bc8/O/OCCT/build_tarballs.jl)
and eight bundled patch files. That recipe sets `version = v"8.0.0"`,
pins `V8_0_0_p1` commit `4f95ecaa3b690e34988d42e2ca7fe882e7a8bc7d`,
enables RapidJSON, declares 40 products and requests GCC 9.

1. Change `version` to `v"8.0.1"` and `GitSource` to the immutable 8.0.1
   commit above. An `ArchiveSource` alternative must use the exact commit
   tarball/checksum above. Keep BinaryBuilder's toolchain-file setting.
2. Review the headless contract rather than copying our binary URLs into
   `sources`. If retaining Yggdrasil's existing RapidJSON/glTF functionality,
   keep its RapidJSON build dependency and `TKDEGLTF` product and test them;
   our artifacts do not qualify glTF. Our 48-product set adds TKBinTObj,
   TKDE, TKDECascade, TKExpress, TKHelix, TKStd, TKStdL, TKTObj and TKXmlTObj
   compared with the reference's 40 products, and omits TKDEGLTF.
3. Preserve existing broader target support unless maintainer-reviewed
   changes deliberately narrow it. Our cxx11 Linux build does not qualify
   BinaryBuilder's cxx03 ABI variant or any other cross target.
4. Reassess each patch against true 8.0.1 and the chosen cross toolchain:

| Patch | Reference target | Native 8.0.1 evidence | BinaryBuilder action |
| --- | --- | --- | --- |
| `Standard_Integer.hxx.patch` / `Standard_Real.hxx.patch` | Unconditional numeric-limit `noexcept` changes | Both native builds pass without them | Check GCC 9 / cross libc++ behavior before retaining or removing |
| `OSD_MemInfo.cxx.patch` / `OSD_signal.cxx.patch` | musl | No musl build was run | Retest musl; do not remove based on glibc success |
| `Standard_StackTrace.cxx.patch` | musl and FreeBSD | Not needed for tested native glibc/macOS builds | Retest each affected cross target |
| `CMakeLists.txt.patch` | MinGW | Windows untested | Keep/revise only with MinGW build evidence |
| `Standard_CString.cxx.patch` / `STEPConstruct_AP203Context.cxx.patch` | FreeBSD | FreeBSD untested | Retest FreeBSD; do not extrapolate |

All eight patch files pass GNU patch 2.8 `--dry-run --batch -p1` on the
unmodified pinned 8.0.1 tree. That is applicability evidence, not compiler
or runtime qualification. Stock macOS BSD patch aborted on some malformed
creation-style headers; use GNU patch for this check. No source patch was
applied to the published native builds.

5. Revalidate the reference's separate **x86_64 macOS SDK workaround** with
   its actual BinaryBuilder SDK. A native arm64 SDK 27.0 build with minimum
   OS 11.0 says nothing about that old cross SDK or its 10.15 target.
6. Build representative `x86_64-linux-gnu-cxx11` and
   `aarch64-apple-darwin` candidates in a separate BinaryBuilder workspace,
   with no `--deploy` or registry/JLL publication. Record compiler/sysroot,
   dependency identities, produced products and audit output. Run compatible
   runtime consumers independently; a cross-compile alone is not runtime
   qualification. Then validate the remaining supported target/ABI matrix.
7. Preserve LGPL/exception notices, verify installed CMake/include/resource
   relocation, and run the independent C++ consumer. Treat any change to
   RapidJSON/rendering dependencies as a separate tested contract decision.

## Ready-to-copy discussion proposal (not posted)

> We have published and independently qualified native OCCT 8.0.1 reference
> archives for Linux x86_64/glibc and macOS arm64 from upstream commit
> `b8f597c677811d1f9f4d8a97f5ae2825c0353a42`. The reproducible native recipes,
> provenance, release hashes, product inventory and independent C++ geometry
> smoke are available in [OodiArtifacts](https://github.com/ahojukka5/OodiArtifacts/blob/master/docs/occt-8.0.1.md).
> Independent clean-depot Pkg.Artifacts installations passed on Julia
> 1.10.11 and 1.13.1 on both platforms, with actual 48-toolkit load paths
> and installed/relocated C++ geometry smoke. The detailed 8.0.1 handoff,
> evidence and copy-ready source-update checklist are in
> [OodiArtifacts PR #29](https://github.com/ahojukka5/OodiArtifacts/pull/29);
> [the manual Linux run](https://github.com/ahojukka5/OodiArtifacts/actions/runs/40040162123)
> contains full public test logs.
> The current Yggdrasil PR still pins 8.0.0p1. We suggest updating its source
> version/commit to 8.0.1, reviewing patches under the actual BinaryBuilder
> toolchains, and independently rebuilding its supported matrix. Our native
> builds require no source patches for these two tested native toolchains,
> but do not establish that cross-target patches are unnecessary. We also
> disabled RapidJSON/glTF, so they do not qualify the existing glTF product.
> Our prebuilt release archives are evidence/reference, not replacement
> source inputs for BinaryBuilder, and no JLL or downstream wrapper upgrade
> is implied.

No upstream comment or change has been made. Share this proposal only after
reviewing the final evidence table and the OodiArtifacts PR.
