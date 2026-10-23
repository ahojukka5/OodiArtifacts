# Native OCCT 8.0.1

Issues [#25](https://github.com/ahojukka5/OodiArtifacts/issues/25) (Linux)
and [#24](https://github.com/ahojukka5/OodiArtifacts/issues/24) (Apple Silicon)
publish the native C++ runtime independently of the existing OCCT 7.9.3
Julia wrappers. There is no Julia version selector and no consumer upgrade.

## Shared source and toolkit contract

Both platforms use upstream `V8.0.1`, commit
`b8f597c677811d1f9f4d8a97f5ae2825c0353a42`. The script checks the exact
source archive SHA-256 before extracting it. No source patches are applied.
Yggdrasil PR #14115 was inspected as a reference: its musl, Windows,
FreeBSD and old cross-SDK fixes are not appropriate to these native builds.
Its 8.0.0p1 numeric-limit `noexcept` patches are not imported speculatively.

Shared C++17 toolkits cover FoundationClasses, ModelingData,
ModelingAlgorithms and DataExchange. Draw and Visualization modules are
disabled. XCAF requires TKService, TKV3d and TKVCAF transitively; these
remain present without OpenGL, X11, FreeType, GUI executables or optional
external integrations. This is a geometry and exchange runtime; optional
RapidJSON-dependent glTF functionality and font rendering are disabled.
Apple system frameworks required by TKService are allowed and audited.

The installation contains `lib/`, `include/opencascade/`,
`lib/cmake/opencascade/`, `share/opencascade/resources/`, and upstream
`LICENSE_LGPL_21.txt` and `OCCT_LGPL_EXCEPTION.txt`. Nonrelocatable upstream
shell environment helpers in `bin/` are omitted. Use the installed CMake
configuration and set `CSF_OCCTResourcePath` to the relocated resource tree.
Compiler file-prefix mapping replaces local paths in assertion messages with
`/usr/src/occt` and `/usr/src/occt-build`. Those build-only mapping flags are
removed from exported CMake metadata; consumers do not inherit build paths.
The native audit rejects embedded local build paths as well as bad linkage.

## Linux: deliberately dispatched hosted build

Merge the reviewed workflow PR into `master` with human approval before
dispatching. Run exactly the intended build:

```sh
gh workflow run publish-occt-8-linux.yml --repo ahojukka5/OodiArtifacts \
  --ref master -f publish=true
```

The workflow has only `workflow_dispatch`. It rejects refs other than
`master`, uses a fixed `ubuntu-24.04` runner, and compiles within a digest-pinned
AlmaLinux 8.10 x86_64 container, not on Ubuntu's compiler/sysroot.
The compiler is EL8 GCC 8 with the C++11 string ABI. Actual installed RPM
identities, compiler/linker/CMake versions, options and memory/parallelism
are recorded. Compilation uses at most four jobs and one per 2 GiB RAM.
Build and qualification have a 330 minute hosted-job limit. Logs are
uploaded on failure; an incomplete build is not a qualified binary.

The build job only has read access. A separate publication job receives
write access only after qualification and when `publish=true`. The default
`publish=false` retains candidates without creating a release. No secrets
are passed into the build container. Never run the Linux build under QEMU
on the Mac.

## Apple Silicon: local native build

Prerequisites are Apple Command Line Tools (full Xcode is not required),
Python 3, CMake, Ninja and Git. Run from the recipe checkout:

```sh
bash scripts/occt/build-macos.sh
```

Build output stays under `~/.cache/oodi/OodiArtifacts/occt-8.0.1/` by
default; `OCCT_WORK_DIR` selects a different external cache. The build
explicitly uses arm64, deployment target macOS 11.0, C++17 and at most six
compiler jobs. It never consumes the existing OCCT_jll or Homebrew OCCT.
Apple Clang, SDK, OS, CMake and linker identities are recorded in the
sidecar. Mach-O dependencies must be the packaged OCCT libraries or Apple
system libraries/frameworks; Homebrew runtime dependencies fail the audit.

The command builds, packages, then compiles/runs the relocated native
consumer before leaving candidates in `dist/`. After reviewing the result,
the authorized publication command is:

```sh
python3 scripts/occt/occt.py publish \
  "$HOME/.cache/oodi/OodiArtifacts/occt-8.0.1/dist"
```

Publication repeats qualification, creates an immutable public release,
downloads both assets without authentication and repeats checks and smoke
from a fresh prefix. A build or package failure does not authorize upload.

## Qualification and immutable release

`scripts/occt/occt.py` checks native architectures, every toolkit's dynamic
dependencies, ELF symbol version floors or Mach-O deployment targets,
loader-relative runtime paths and installed CMake metadata. Linux requires
GLIBC <= 2.28 and GLIBCXX <= 3.4.25 and records the exact observed maximum
GLIBC, GLIBCXX and CXXABI versions for all imported symbols. System C/C++
runtime dependencies are allowed; undeclared external libraries fail.

The archive is extracted under a new temporary prefix. A fresh CMake C++
consumer imports the installed targets, loads every toolkit, validates a
box, checks a Boolean cut's volume, meshes it, checks a STEP roundtrip's
volume and exports IGES/STL. No library-path override is used. Linux does
this inside EL8 before publication and again after public download.

Artifact tree hashes are independently computed with Python Git object
encoding and `git write-tree`, before and after extraction. Archive
SHA-256 is checked using hashlib and the native checksum utility. These
are Julia Artifacts-compatible Git trees; no Julia ABI is involved.

Only `OCCT.tar.gz` and `OCCT.provenance.json` become release assets, under
`OCCT-8.0.1-<platform>-<tree-prefix>`. The sidecar records the source,
toolchain, options, ABI, full toolkit linkage, qualification and both hashes.
Reusing an existing release requires identical archive and provenance
bytes. Publication never overwrites assets or tags. Public unauthenticated
downloads must match both original files and pass a fresh relocation smoke.
Delivery logs are separate from immutable pre-publication provenance.

## Local recipe validation

`python3 -m py_compile scripts/occt/occt.py` checks syntax;
`actionlint .github/workflows/publish-occt-8-linux.yml .github/workflows/ci.yml`
checks workflow syntax. On Apple Silicon, `build --configure-only` audits
the same source/options without attempting the Linux build. A local syntax
or configure check is not evidence of a completed Linux build.

## Published Apple Silicon artifact

Published on 2026-10-24 (Europe/Helsinki; 2026-10-23 21:04 UTC):
[OCCT-8.0.1-macos-aarch64-04d2d2f805e3](https://github.com/ahojukka5/OodiArtifacts/releases/tag/OCCT-8.0.1-macos-aarch64-04d2d2f805e3).
The assets are
[`OCCT.tar.gz`](https://github.com/ahojukka5/OodiArtifacts/releases/download/OCCT-8.0.1-macos-aarch64-04d2d2f805e3/OCCT.tar.gz)
and
[`OCCT.provenance.json`](https://github.com/ahojukka5/OodiArtifacts/releases/download/OCCT-8.0.1-macos-aarch64-04d2d2f805e3/OCCT.provenance.json).

| Identity | Value |
| --- | --- |
| Source commit | `b8f597c677811d1f9f4d8a97f5ae2825c0353a42` |
| Build recipe commit / release target | `2f8d6d67358bd7d9c9b02a7d9f3574831569a9f6` |
| Artifact `git-tree-sha1` | `04d2d2f805e3e6931e6f02670cc1309f180e5d55` |
| Archive SHA-256 | `17f2ddb18db38dc94c1e0cafcdee1567b8c837d405c4118265e0aaca666037c0` |
| Provenance sidecar SHA-256 | `bb1b3ff333f9c2bfd43d62f4cfba610dec4c2a609be1cb7290185dfa6a55cc62` |

The local build used macOS 27.0.1 (26A434), Apple Clang 21.0.0
(clang-2100.3.34.2), SDK 27.0, Command Line Tools
27.0.0.0.1788430756, CMake 4.4.2 and Ninja 1.13.2. Architecture is arm64;
deployment target and every Mach-O minimum OS are 11.0. The source is
unpatched. No Homebrew runtime dependency or local source/build path is
embedded in the packaged libraries or CMake metadata.

All 48 toolkits loaded. BREP box validation, Boolean cut volume 4500,
meshing, STEP export/import and volume preservation, and IGES/STL exports
passed from the relocated archive, including normal process shutdown.
These checks passed again after unauthenticated public download. Python's
Git object implementation, `git write-tree` and Julia 1.13.1
`Pkg.GitTools.tree_hash` agree on the artifact identity; hashlib and
`shasum -a 256` agree on the archive hash. The public archive was separately
downloaded and extracted for Julia's tree-hash check.

The qualification covers this geometry/exchange smoke on the recorded host.
macOS 11.0 is the audited deployment target; execution on a physical macOS
11 system was not tested. Optional rendering and RapidJSON/glTF functionality
remain disabled as described above. Existing 7.9.3 artifacts and downstream
consumer declarations are unchanged. The independent Linux qualification is
recorded below; Mac success alone does not qualify Linux.

## Published Linux artifact

The owner-approved manual
[workflow run 40025009407](https://github.com/ahojukka5/OodiArtifacts/actions/runs/40025009407)
succeeded, producing exactly one Linux release:
[OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24](https://github.com/ahojukka5/OodiArtifacts/releases/tag/OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24).
The assets are
[`OCCT.tar.gz`](https://github.com/ahojukka5/OodiArtifacts/releases/download/OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24/OCCT.tar.gz)
and
[`OCCT.provenance.json`](https://github.com/ahojukka5/OodiArtifacts/releases/download/OCCT-8.0.1-linux-x86_64-glibc-9ad71dc7bc24/OCCT.provenance.json),
published at 2026-10-23 21:44 UTC (2026-10-24 Europe/Helsinki).

| Identity | Value |
| --- | --- |
| Source commit | `b8f597c677811d1f9f4d8a97f5ae2825c0353a42` |
| Merged build recipe / release target | `d22a008e10826ed76bd32c0a10a76b9e30d9d9a8` |
| Artifact `git-tree-sha1` | `9ad71dc7bc24252016d89611722806a84a9c100b` |
| Archive SHA-256 | `27447b3eaa9c16e568651e479c02f466db7957a32c5c3e3122b302232af63762` |
| Provenance sidecar SHA-256 | `f1040c20eb08e86195e8fcba9bb03002f223d1387a6f89ee137abf7cb2d8eaf6` |

The GitHub-hosted `ubuntu-24.04` build job used the pinned AlmaLinux 8.10
container, GCC 8.5.0 (Red Hat 8.5.0-29), GNU ld 2.30, CMake 3.26.5,
Ninja 1.8.2 and four compiler jobs. The complete build job took 31 minutes
44 seconds, including setup, build, packaging, qualification and uploads.
No Linux compilation or QEMU was run on the Mac.

All 48 toolkit products match the Mac product set. The actual maximum
required dynamic symbol versions are **GLIBC 2.27**, **GLIBCXX 3.4.21** and
**CXXABI 1.3.9**. The C++ string ABI is `cxx11`; runtime paths are `$ORIGIN`.
This is an EL8/glibc 2.28 runtime qualification. An observed symbol floor
alone is not a claim that an older Linux distribution was tested.

The relocated installed-prefix native consumer passed in EL8 before
publication. After public download, it passed on the publication runner
and again in a fresh EL8 container, including loading every toolkit,
BREP validation, Boolean volume, meshing, STEP volume roundtrip, IGES/STL
exports and normal process exit. Build and public-delivery logs are
preserved as workflow artifacts. A separate unauthenticated download on
the Mac matched the GitHub asset digests, Python and `git write-tree`
artifact identities, and Julia 1.13.1 `Pkg.GitTools.tree_hash` after
extraction. Native Linux execution was performed in CI.
