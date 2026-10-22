#!/usr/bin/env julia
# Run in the version-specific environment in native/Project.toml.
# Usage: build_native.jl KIND SOURCE OUTPUT [NETGEN_ROOT]
using OCCT_jll, Zlib_jll, Libdl, TOML
import libcxxwrap_julia_jll
using Base.BinaryPlatforms: HostPlatform, triplet

length(ARGS) in (3, 4) || error("expected KIND SOURCE OUTPUT [NETGEN_ROOT]")
kind, source, output = ARGS[1:3]
source, output = abspath(source), abspath(output)
expected = Dict(
    "libopencascade_cxxwrap" => "fc988de3315b21cd900a86548989d2d31293619e",
    "libnetgen_cxxwrap" => "301822bb5309af57ec7242e557a16ea1f12f610a",
    "NGSolveNetgen" => "a3e08f0ec196b442f7de3b9b717ab86c6993f1ab",
)
repositories = Dict(
    "libopencascade_cxxwrap" => "https://github.com/ahojukka5/OpenCascadeCxxWrap",
    "libnetgen_cxxwrap" => "https://github.com/ahojukka5/NetgenCxxWrap_jll",
    "NGSolveNetgen" => "https://github.com/NGSolve/netgen",
)
haskey(expected, kind) || error("unknown native artifact $kind")
revision = readchomp(`git -C $source rev-parse HEAD`)
revision == expected[kind] || error("unexpected source revision $revision")
isempty(readchomp(`git -C $source status --porcelain --untracked-files=no`)) ||
    error("source checkout has tracked changes")
build = joinpath(output, "build")
stage = joinpath(output, "stage")
mkpath(stage)
jobs = parse(Int, get(ENV, "NATIVE_BUILD_JOBS", "2"))
jobs > 0 || error("NATIVE_BUILD_JOBS must be positive")
julia = joinpath(Sys.BINDIR, Base.julia_exename())
jlcxx_prefix = libcxxwrap_julia_jll.artifact_dir
cxxwrap_project = TOML.parsefile(joinpath(dirname(dirname(Base.find_package("CxxWrap"))), "Project.toml"))
prefix = join([OCCT_jll.artifact_dir, Zlib_jll.artifact_dir, jlcxx_prefix], ';')
options = String[
    "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=$stage",
    "-DCMAKE_PREFIX_PATH=$prefix", "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF",
    "-DCMAKE_INSTALL_RPATH=" * (Sys.isapple() ? "@loader_path" : "\$ORIGIN"),
    "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
]
if Sys.isapple()
    push!(options, "-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0")
end
if kind == "NGSolveNetgen"
    hostbin = joinpath(output, "hostbin")
    mkpath(hostbin)
    run(`c++ -O2 -std=c++17 $(joinpath(source, "rules", "makerlsfile.cpp")) -o $(joinpath(hostbin, "makerls"))`)
    ENV["PATH"] = hostbin * (Sys.iswindows() ? ";" : ":") * ENV["PATH"]
    append!(options, [
        "-DUSE_SUPERBUILD=OFF", "-DUSE_NATIVE_ARCH=OFF", "-DUSE_GUI=OFF",
        "-DUSE_PYTHON=OFF", "-DUSE_MPI=OFF", "-DUSE_OCC=ON",
        "-DUSE_JPEG=OFF", "-DUSE_MPEG=OFF", "-DUSE_CGNS=OFF",
        "-DBUILD_STUB_FILES=OFF", "-DNETGEN_VERSION_GIT=v6.2.2606-0-ga3e08f0e",
        "-DNG_INSTALL_DIR_BIN=bin", "-DNG_INSTALL_DIR_LIB=lib",
        "-DNG_INSTALL_DIR_INCLUDE=include", "-DNG_INSTALL_DIR_CMAKE=lib/cmake/netgen",
        "-DNG_INSTALL_DIR_RES=share",
        "-DOpenCASCADE_DIR=$(joinpath(OCCT_jll.artifact_dir, "lib", "cmake", "opencascade"))",
        "-DZLIB_ROOT=$(Zlib_jll.artifact_dir)",
    ])
    cmake_source = source
else
    append!(options, [
        "-DJlCxx_DIR=$(joinpath(jlcxx_prefix, "lib", "cmake", "JlCxx"))",
        "-DJulia_EXECUTABLE=$julia",
    ])
    if kind == "libnetgen_cxxwrap"
        length(ARGS) == 4 || error("Netgen wrapper requires NETGEN_ROOT")
        push!(options, "-DNETGEN_ROOT=$(abspath(ARGS[4]))")
    end
    cmake_source = joinpath(source, "bundled")
end
@info "Native build" kind revision julia VERSION platform=triplet(HostPlatform()) output jobs
run(`cmake -S $cmake_source -B $build $options`)
run(`cmake --build $build --parallel $jobs`)
run(`cmake --install $build`)
if kind != "NGSolveNetgen"
    cache = read(joinpath(build, "CMakeCache.txt"), String)
    occursin(julia, cache) || error("CMake did not retain the explicit Julia executable")
    library = joinpath(stage, "lib", "$kind.$(Libdl.dlext)")
    isfile(library) || error("missing wrapper library")
    linkage = read(Sys.isapple() ? `otool -L $library` : `readelf -d $library`, String)
    occursin("libjulia", linkage) || error("wrapper does not declare libjulia linkage")
    abi_pattern = Regex("libjulia(?:\\.so)?\\.$(VERSION.major)\\.$(VERSION.minor)(?:\\.|\\s|\\])")
    occursin(abi_pattern, linkage) || error("wrong Julia ABI: $linkage")
    write(joinpath(output, "linkage.txt"), linkage)
end
licenses = joinpath(stage, "share", "licenses", kind)
mkpath(licenses)
license = isfile(joinpath(source, "LICENSE")) ? joinpath(source, "LICENSE") :
    joinpath(source, "bundled", "LICENSE")
cp(license, joinpath(licenses, "LICENSE"); force=true)
open(joinpath(output, "build.toml"), "w") do io
    TOML.print(io, Dict(
        "artifact" => kind, "source_commit" => revision,
        "source_repository" => repositories[kind],
        "julia_version" => string(VERSION), "julia_executable" => julia,
        "platform" => triplet(HostPlatform()),
        "cxxwrap_version" => cxxwrap_project["version"],
        "occt_version" => string(pkgversion(OCCT_jll)),
        "libcxxwrap_version" => string(pkgversion(libcxxwrap_julia_jll)),
        "occt_artifact" => basename(OCCT_jll.artifact_dir),
        "libcxxwrap_artifact" => basename(jlcxx_prefix),
        "cmake" => readchomp(`cmake --version`),
        "compiler" => readchomp(`c++ --version`),
        "build_options" => options,
        "qemu_reserved_va" => get(ENV, "QEMU_RESERVED_VA", ""),
    ))
end
