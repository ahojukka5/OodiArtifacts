# oodi-artifacts

Privately-hosted Julia binary artifacts for early Oodi-ecosystem dependencies whose
binaries are not yet available from the public artifact CDN (JuliaBinaryWrappers /
Yggdrasil). Each artifact is attached as a release asset; the consuming package's
`Artifacts.toml` points its `[[download]]` at the asset URL.

## Hosted artifacts

The Julia 1.10–1.13 matrix and immutable archive identities are listed in
[the compatibility report](docs/native-matrix-20261023.md). It separates
installation, loading, native execution and complete-suite results.

Earlier retained artifact records include:

- **libopencascade_cxxwrap — Linux x86_64/glibc**
  - release: `libopencascade_cxxwrap-707416b9`
  - Julia artifact tree: `707416b9331d65576938b0ef9cd93301079e8491`
  - rebuilt on EL8 so the wrapper remains compatible with the intended glibc baseline;
- **libopencascade_cxxwrap — macOS aarch64**
  - release: `libopencascade_cxxwrap-fe916c69`
  - Julia artifact tree: `fe916c696b41979301c71c01e398d3f6efb07466`;
- **libnetgen_cxxwrap**
  - historical release: `libnetgen_cxxwrap-d2a7f166`;
  - older retained releases include `cf0507bc`, `890f20b2`, and `654a8ffa` for historical consumer revisions;
- **NGSolveNetgen**
  - retained release: `NGSolveNetgen-22b6752d`.

The old `libopencascade_cxxwrap-19b04788` release is retained as historical
provenance only. It is not the current Monge wrapper and must not be presented as
the installation target.

Release assets are immutable inputs to consuming `Artifacts.toml` files. A consumer
should pin the exact artifact tree and download checksum it has qualified rather than
infer compatibility from the newest release name alone.

## Publishing OpenCascadeCxxWrap

`.github/workflows/publish-opencascade-cxxwrap.yml` owns the current temporary
**Linux x86_64/glibc OpenCascade wrapper** publication path until the wrapper moves to
Yggdrasil. Other artifacts listed above are hosted here but are not currently rebuilt
by this workflow.

The workflow pins both the wrapper source revision and the Monge revision used for
qualification.

The workflow is **manual only** (`workflow_dispatch`). A native OpenCASCADE
build occupies a self-hosted runner for a long time and republishes an
immutable, rarely-regenerated binary, so dispatch it when the pinned wrapper
revision actually changes -- not on every edit to the workflow file.

It builds the Linux x86_64/glibc artifact once and proves the strict raw
`GeomFill_Gordon` fixture together with the public `gordon_surface` rectangle
fixture. The deterministic archive, provenance record, and build log are
uploaded as workflow artifacts.

Reproducibility is not re-checked by a second native build in the same run. The
immutable-tag rule below catches a rerun whose bytes differ from an already-published
tag; first-publication reproducibility therefore rests on the pinned source/toolchain
inputs plus the qualification evidence recorded by the workflow.

The qualification publishes a release named from the Julia artifact tree hash.
Existing tags are immutable by policy: a rerun succeeds only when both the archive
bytes and provenance are identical. Every release records the wrapper source commit,
qualification commit, platform, archive SHA-256, and extracted Julia artifact tree
hash.

Monge's `Artifacts.toml` should be updated only after that release succeeds and
the published asset can be installed from a clean depot.

## License

The files in this repository are MIT. The release assets are not: each
binary keeps the license of the wrapper or library it was built from, and
of OpenCASCADE or Netgen when those are linked in. See [LICENSE](LICENSE).

## Local Julia compatibility matrix

The native matrix uses the existing immutable release-asset convention. The
build and package commands are local and do not add automatic CI jobs:

```sh
# Copy native/Project.toml into a separate environment for each Julia minor.
JULIA_PKG_PRECOMPILE_AUTO=0 julia --project="$BUILD_ENV" -e 'using Pkg; Pkg.instantiate()'
julia --project="$BUILD_ENV" scripts/build_native.jl \
  libopencascade_cxxwrap "$PINNED_WRAPPER_SOURCE" "$OUTPUT"
python3 scripts/package_native.py "$OUTPUT" --julia "$JULIA_EXECUTABLE"
```

`build_native.jl` checks clean, immutable native source revisions and passes
its running Julia executable to CMake. The build environment fixes OCCT
7.9.3, CxxWrap 0.17.5 and libcxxwrap 0.14.12. Netgen uses upstream commit
`a3e08f0ec196b442f7de3b9b717ab86c6993f1ab` and is built once per platform.
Wrappers record their Julia linkage, compiler, dependency artifact identities,
archive SHA-256 and artifact tree hash. Archives include wrapper licenses.

Linux builds use EL8 glibc headers and GCC 12 C++ headers and link tools.
GCC 8 filesystem headers are incompatible with the published Netgen runtime
and are not a supported build input. On this macOS host, the
installed Clang compiles `x86_64-linux-gnu` objects against exported EL8
headers, then the EL8 container links and inspects the shared libraries.
Select `/opt/rh/gcc-toolset-12/root/usr/bin/g++` with `NATIVE_TARGET_CXX`.
`scripts/cross_compile_linux.py` consumes CMake's compile commands. Configure
first with `NATIVE_CONFIGURE_ONLY=1`; after cross-compilation, run the build
script with `NATIVE_INSTALL_ONLY=1`, `NATIVE_COMPILATION_COMPILER`,
`NATIVE_COMPILE_METHOD` and `NATIVE_SYSROOT_IDENTITY` set to the actual
inputs. Native compilation on a Linux host remains supported.

For x86_64 Julia under the local QEMU runtime, set
`QEMU_RESERVED_VA=0x100000000000`; Julia 1.10 otherwise fails while relocating
its system image. Limit concurrent versions to the available container
memory and set `JULIA_NUM_PRECOMPILE_TASKS=1` for each version.

Package qualification must consume published archives from an empty depot,
with General and OodiRegistry, without artifact overrides or native source
builds. Resolve, load, native execution and complete tests are separate
results. Package release tags wait for review of those results.
