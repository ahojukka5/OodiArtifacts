#!/usr/bin/env python3
"""Package a staged native build, without publishing or replacing assets."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("build", type=Path)
parser.add_argument("--julia", required=True)
args = parser.parse_args()
root = args.build.resolve()
stage = root / "stage"
build = tomllib.loads((root / "build.toml").read_text())
name = build["artifact"]
tree = subprocess.check_output([
    args.julia, "--startup-file=no", "-e",
    "using Pkg; print(bytes2hex(Pkg.GitTools.tree_hash(ARGS[1])))", str(stage),
], text=True).strip()
dist = root / "dist"
dist.mkdir(exist_ok=True)
archive = dist / f"{name}.tar.gz"
if archive.exists():
    raise SystemExit(f"refusing to replace existing archive {archive}")
with archive.open("wb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as tar:
            for path in sorted(stage.rglob("*")):
                info = tar.gettarinfo(str(path), arcname=path.relative_to(stage).as_posix())
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ""
                if info.isfile():
                    with path.open("rb") as content:
                        tar.addfile(info, content)
                else:
                    tar.addfile(info)
digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
verified = subprocess.check_output([
    args.julia, "--startup-file=no", "-e",
    'using Tar; print(Tar.tree_hash(`gzip -dc $(ARGS[1])`))', str(archive),
], text=True).strip()
if verified != tree:
    raise SystemExit(f"archive tree mismatch: {verified} != {tree}")
tag = f"{name}-{tree[:8]}"
identity = dict(
    build, tree_hash=tree, archive=archive.name, archive_sha256=digest,
    release_tag=tag, julia_abi="none" if name == "NGSolveNetgen" else
    ".".join(build["julia_version"].split(".")[:2]),
    download_url=f"https://github.com/ahojukka5/OodiArtifacts/releases/download/{tag}/{archive.name}",
)
if (root / "linkage.txt").exists():
    identity["linkage"] = (root / "linkage.txt").read_text()
(dist / f"{name}.provenance.json").write_text(json.dumps(identity, indent=2) + "\n")
print(json.dumps(identity, indent=2))
