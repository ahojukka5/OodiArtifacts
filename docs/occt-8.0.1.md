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
