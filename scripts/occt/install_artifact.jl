# Only Julia standard libraries; launch with one genuinely empty depot.
using Pkg
using Pkg.Artifacts
using Base.BinaryPlatforms
using Downloads
using SHA
using TOML

manifest, work, depot = abspath.(ARGS)
@assert DEPOT_PATH == [depot] "exactly one isolated depot is required"
@assert get(ENV, "JULIA_PKG_SERVER", "unset") == "" "use the pinned public URLs"
@assert get(ENV, "JULIA_PKG_IGNORE_HASHES", "false") == "false"
@assert !isfile(joinpath(depot, "artifacts", "Overrides.toml"))
key = "occt_8_0_1"
platform = HostPlatform()
meta = artifact_meta(key, manifest; platform)
@assert meta !== nothing "no OCCT release for this host"
@assert !haskey(meta, "julia_version")
@assert length(meta["download"]) == 1
hash = Base.SHA1(meta["git-tree-sha1"])
@assert !artifact_exists(hash) "artifact must not be cached before this test"

# Independent download is evidence for the archive identity, not the Pkg install.
archive = Downloads.download(meta["download"][1]["url"], joinpath(work, "OCCT.tar.gz"))
archive_sha = bytes2hex(open(sha256, archive))
@assert archive_sha == meta["download"][1]["sha256"]
provenance = Downloads.download(replace(meta["download"][1]["url"],
    "OCCT.tar.gz" => "OCCT.provenance.json"), joinpath(work, "OCCT.provenance.json"))

# The correct tree is still absent. A bad checksum cannot be masked by a cache hit.
bad = deepcopy(meta)
bad["download"][1]["sha256"] = repeat("0", 64)
bad["download"][1]["url"] = "file://" * archive
bad_manifest = joinpath(work, "bad-checksum.toml")
open(bad_manifest, "w") do io
    TOML.print(io, Dict(key => [bad]))
end
checksum_error = try
    println("NEGATIVE TEST: expected rejection of deliberately false archive SHA-256")
    ensure_artifact_installed(key, bad_manifest; platform, verbose=true)
    nothing
catch err
    sprint(showerror, err)
end
@assert checksum_error !== nothing
println("EXPECTED CHECKSUM REJECTION: ", checksum_error)
@assert occursin("Verification failed", checksum_error) && occursin("hash", lowercase(checksum_error))
@assert !artifact_exists(hash) "checksum rejection must not install an artifact"

unsupported = Platform("x86_64", "linux"; libc="musl")
@assert artifact_meta(key, manifest; platform=unsupported) === nothing
platform_error = try
    ensure_artifact_installed(key, manifest; platform=unsupported)
    nothing
catch err
    sprint(showerror, err)
end
@assert platform_error !== nothing && occursin("Cannot locate artifact", platform_error)

# This call independently downloads, validates and unpacks the public release.
prefix = ensure_artifact_installed(key, manifest; platform, verbose=true)
@assert realpath(prefix) == realpath(artifact_path(hash; honor_overrides=false))
@assert realpath(prefix) == realpath(joinpath(depot, "artifacts", string(hash)))
@assert verify_artifact(hash; honor_overrides=false)
@assert bytes2hex(Pkg.GitTools.tree_hash(prefix)) == string(hash)
@assert !isfile(joinpath(depot, "artifacts", "Overrides.toml"))
result = Dict(
    "julia_version" => string(VERSION), "platform" => triplet(platform),
    "artifact_key" => key, "artifact_prefix" => realpath(prefix),
    "artifact_tree" => string(hash), "archive_sha256" => archive_sha,
    "archive_url" => meta["download"][1]["url"], "depot_path" => DEPOT_PATH,
    "pkg_install" => "PASS", "pkg_verify_artifact" => "PASS",
    "checksum_negative" => "PASS", "checksum_negative_error" => checksum_error,
    "unsupported_platform_negative" => "PASS", "unsupported_platform_error" => platform_error,
    "override_used" => false, "pkg_server" => get(ENV, "JULIA_PKG_SERVER", "unset"),
)
open(joinpath(work, "pkg-result.toml"), "w") do io
    TOML.print(io, result)
end
println("PKG ARTIFACT PASS Julia ", VERSION, " ", triplet(platform), " prefix=", prefix)
