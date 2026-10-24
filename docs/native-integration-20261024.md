# Native matrix integration qualification, 2026-10-24

This qualification tests the integrated consumers of the already published
Julia 1.10–1.13 native matrix for [issue #20](https://github.com/ahojukka5/OodiArtifacts/issues/20).
The [2026-10-23 report](native-matrix-20261023.md) remains historical evidence,
including its incomplete and failed Linux runs. The
[release index](native-matrix-20261023.json) remains authoritative for the
immutable native source, ABI, archive SHA-256 and artifact tree identities.

## Tested source

| Package | Exact revision | Integration status |
| --- | --- | --- |
| Monge 0.1.0 | `0d593d7df62ca302b73003a86bc488f5df8fb709` | Merged [PR #564](https://github.com/ahojukka5/Monge.jl/pull/564) |
| Delone / DelonePortable 0.1.0 | `631628e08f577f2c1b99830b3d55eff6bea831c8` | Qualified PR head; [#1055](https://github.com/ahojukka5/Delone.jl/pull/1055) subsequently rebase-merged, identical release tree |

The earlier Monge #560 and Delone #1047 candidates were superseded during
integration. Results are tied to the exact revisions above, not to moving
branch names or to the workflow-event revision. Delone's resulting master
commit `98b13fae8c8260015a24c949f3f1fb9636a0a7fd` has the same
root package tree as the tested PR head. Both packages were subsequently
tagged as 0.1.0 and registered in [OodiRegistry #6](https://github.com/ahojukka5/OodiRegistry/pull/6).
Those release operations are not part of the qualification runs.

## Method

Each package and Julia minor starts with an empty user depot and a separate
temporary environment. The only additional depot is that Julia executable's
packaged runtime depot. General and OodiRegistry provide dependencies;
CxxWrap 0.17.5, OCCT_jll 7.9.3+0 and libcxxwrap_julia_jll 0.14.12+0 are
selected explicitly. Delone's environment also enables its Zlib provider.
Julia 1.10 explicitly installs the existing GmshIO test-source pin
`b0901fc0a137b46f3d0f31ef5519e42834262398`, because Pkg 1.10 does not
interpret the test project's `[sources]` table.

Resolution, loading, native execution and `Pkg.test` run in separate Julia
processes. All use the same case's depot and environment, one Julia thread,
one precompile task and one OpenBLAS thread. Local source checkout
cleanliness is recorded before and after each case.
The package's default complete suite runs without domain or tier filters.
Monge's public suite reports one existing optional integration skip in its
`Broken` column; the actual counts remain in the recorded summaries.

Monge's native check constructs a box with volume 6. Delone generates a
circle mesh, imports the committed STEP box and generates a finite 3D mesh.
Actual loaded wrapper/Netgen libraries must come from that case's artifact
depot. The recorded trees are matched to the published release index and
the intended Julia minor. No C++ build, artifact override or binary-path
override participates in qualification.

Archive SHA-256 values come from the original publication records in the
release index. Integration runs record the selected installed content trees
and execution results separately from those archive checksum measurements.

Mac tests run locally on Apple Silicon, macOS 27.0.1. The
[exact executed Julia driver](../scripts/qualify_native_packages.jl) additionally
verifies each loaded artifact tree with `verify_artifact(...;
honor_overrides=false)`. Its SHA-256 is recorded in the results. Each stage
is invoked as:

```sh
julia +1.10.11 --startup-file=no --project="$case_dir/env" \
  scripts/qualify_native_packages.jl Monge "$source_checkout" "$case_dir" resolve
```

Use an empty `$case_dir/depot` followed by the selected Julia runtime depot
in `JULIA_DEPOT_PATH`, `JULIA_LOAD_PATH=@:@stdlib`, and
`JULIA_PKG_PRECOMPILE_AUTO=0`. Set `JULIA_NUM_THREADS`,
`JULIA_NUM_PRECOMPILE_TASKS` and `OPENBLAS_NUM_THREADS` to `1`, and unset
native provider/build overrides and `LD_LIBRARY_PATH` / `DYLD_LIBRARY_PATH`
loader overrides. Then run `load`, `native` and `full` in place
of `resolve`. Select each Julia executable explicitly; give every
package/minor combination a new case directory. Sources must be the exact
Git revisions above. Credentials for private package sources remain local.

Linux uses the already dispatched, existing manual compatibility workflows:

- [Monge run 40075611982](https://github.com/ahojukka5/Monge.jl/actions/runs/40075611982)
- [Delone run 40076654905](https://github.com/ahojukka5/Delone.jl/actions/runs/40076654905)

These runs were reused without duplicate dispatches, workflow edits or
runner changes. The actual checkout and Julia patch version are verified
from each completed job log. Delone's workflow event uses its default
branch revision while its source checkout is the candidate above; the two
identities are recorded separately.

## Results

All sixteen package/platform/minor cases passed resolution, loading,
native execution and the complete suite: eight local macOS cases and
eight Linux CI cases. The
[machine-readable results](native-integration-20261024-results.json) record
each stage, exact runtime and source revision, selected native trees,
complete-suite summaries, job links and completed-log SHA-256 values.
Completed log snapshots and Mac environments remain in the local
qualification cache rather than in this repository. Linux evidence is
retained in the linked completed job logs and their downloaded snapshots.

Both Linux Julia 1.11 first attempts stopped because their self-hosted
runners lost communication with GitHub: Monge during loading, Delone during
the full suite after its native stage passed. Their check-run annotations
are retained separately in the results. No package test failure is
inferred. Those interrupted attempts remain unqualified. Both independent
retries completed successfully and qualify the 1.11 cases below. Successful
original executions retain their original job/log identities when GitHub
copies them into a later run attempt.

| Platform | Package | Julia | Resolution | Loading | Native execution | Full suite |
| --- | --- | --- | --- | --- | --- | --- |
| Linux x86_64 glibc | Delone | 1.10.12 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Delone | 1.11.9 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Delone | 1.12.7 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Delone | 1.13.2 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Monge | 1.10.12 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Monge | 1.11.9 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Monge | 1.12.7 | PASS | PASS | PASS | PASS |
| Linux x86_64 glibc | Monge | 1.13.2 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Delone | 1.10.11 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Delone | 1.11.9 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Delone | 1.12.6 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Delone | 1.13.1 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Monge | 1.10.11 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Monge | 1.11.9 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Monge | 1.12.6 | PASS | PASS | PASS | PASS |
| macOS aarch64 | Monge | 1.13.1 | PASS | PASS | PASS | PASS |

## Compatibility limits

Julia 1.9 was investigated separately in the
[original report](native-matrix-20261023.md#older-julia-and-later-platforms): Episteme's
dependency floor and the selected CxxWrap build stack require Julia 1.10.
No Julia 1.9 native binary is claimed. That investigation is not a new
qualification of these integrated source revisions.

This work qualifies the OCCT 7.9.3 CxxWrap consumers and Netgen matrix.
The separate OCCT 8.0.1 native/Pkg qualification remains in its
[own record](occt-8.0.1-yggdrasil.md). Other architectures, macOS 11
execution, Julia package registration and package release tags are outside
this qualification. Existing releases retain their original bytes.
