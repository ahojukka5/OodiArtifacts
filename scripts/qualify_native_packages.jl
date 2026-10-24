using Pkg, TOML, Libdl
using Pkg.Artifacts
using Base.BinaryPlatforms
pkg, source, work, stage = ARGS
@assert Sys.isapple() && Sys.ARCH === :aarch64
@assert all(!isfile(joinpath(d, "artifacts", "Overrides.toml")) for d in DEPOT_PATH)
@assert !any(haskey(ENV,k) for k in ("DELONE_NETGEN_ROOT", "DELONE_NETGEN_CXXWRAP", "MONGE_TEST_ARTIFACTS_DIRECTORY"))
project = TOML.parsefile(joinpath(source,"Project.toml"))
@assert project["version"] == "0.1.0"
if stage == "resolve"
    Pkg.Registry.add("General")
    Pkg.Registry.add(Pkg.RegistrySpec(url="https://github.com/ahojukka5/OodiRegistry.git"))
    Pkg.activate(joinpath(work,"env"))
    if pkg == "Delone"
        Pkg.develop([Pkg.PackageSpec(path=joinpath(source,"portable")), Pkg.PackageSpec(path=source)])
    else
        Pkg.develop(path=source)
    end
    Pkg.add([
        Pkg.PackageSpec(name="CxxWrap",version=v"0.17.5"),
        Pkg.PackageSpec(name="OCCT_jll",version=v"7.9.3+0"),
        Pkg.PackageSpec(name="libcxxwrap_julia_jll",version=v"0.14.12+0")])
    if pkg == "Delone"
        Pkg.add("Zlib_jll")
        if VERSION < v"1.11"
            pin=TOML.parsefile(joinpath(source,"test","Project.toml"))["sources"]["GmshIO"]
            Pkg.add(Pkg.PackageSpec(url=pin["url"],rev=pin["rev"]))
        end
    end
    Pkg.instantiate()
    Pkg.status(; mode=Pkg.PKGMODE_MANIFEST)
elseif stage == "load"
    pkg == "Monge" ? (@eval using Monge) : (@eval using Delone; Delone.load_netgen!())
elseif stage == "native"
    if pkg == "Monge"
        @eval using Monge
        @assert Monge.Geometry.volume(Monge.Modeling.box(1,2,3)) ≈ 6
    else
        @eval using Delone
        Delone.load_netgen!()
        N=Delone.NetgenLive
        mesh=N.generate_mesh(N.geometry2d(N.Circle(0.,0.,1.,"disk","circle"));maxh=0.4)
        @assert Delone.Netgen.GetNSE(mesh)>0
        mesh3=N.generate_mesh(N.load_step(joinpath(source,"test/fixtures/box_100mm.step"));maxh=40.)
        @assert Delone.Netgen.GetNE(mesh3)>0
        @assert all(isfinite,N.points(mesh3))
    end
    loaded=filter(p->occursin(r"lib(opencascade_cxxwrap|netgen_cxxwrap|nglib|ngcore)",p),Libdl.dllist())
    @assert length(loaded)>=(pkg=="Monge" ? 1 : 3)
    for library in loaded
        @assert startswith(realpath(library),realpath(joinpath(DEPOT_PATH[1],"artifacts")))
        parts=splitpath(realpath(library)); at=findlast(==("artifacts"),parts)
        @assert at!==nothing
        @assert verify_artifact(Base.SHA1(parts[at+1]);honor_overrides=false)
    end
    deps=Dict{String,Any}()
    for (_,dep) in Pkg.dependencies()
        if dep.name in ("CxxWrap","OCCT_jll","libcxxwrap_julia_jll","Episteme",pkg)
            deps[dep.name]=Dict("version"=>string(dep.version),"source"=>something(dep.source,""),"tree"=>string(dep.tree_hash))
        end
    end
    open(joinpath(work,"native-result.toml"),"w") do io
        TOML.print(io,Dict("package"=>pkg,"version"=>string(VERSION),"source"=>source,
          "libraries"=>loaded,"dependencies"=>deps,"status"=>"PASS","platform"=>triplet(HostPlatform())))
    end
elseif stage == "full"
    Pkg.test(pkg)
else
    error("unknown stage")
end
println("STAGE PASS ",stage," ",pkg," ",VERSION)
