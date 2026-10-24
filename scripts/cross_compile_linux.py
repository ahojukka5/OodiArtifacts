#!/usr/bin/env python3
"""Compile Linux wrapper objects with host Clang, then link in the EL8 container.

The Julia build script must first configure with NATIVE_CONFIGURE_ONLY=1.
The sysroot is exported from that same EL8 container, including /usr/include.
Run build_native.jl with NATIVE_INSTALL_ONLY=1 afterwards to verify linkage
and record the actual compilation compiler and sysroot identity.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shlex
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("build", type=Path)
parser.add_argument("--matrix", type=Path, required=True)
parser.add_argument("--workspace", type=Path, required=True)
parser.add_argument("--sysroot", type=Path, required=True)
parser.add_argument("--container", required=True)
parser.add_argument("--compiler", default="/usr/bin/clang++")
parser.add_argument("--gcc-version", default="12")
parser.add_argument("--jobs", type=int, default=2)
args = parser.parse_args()
build = args.build.resolve() / "build"
matrix, workspace, sysroot = (p.resolve() for p in (args.matrix, args.workspace, args.sysroot))


def host_path(token):
    return token.replace("/workspace/", str(workspace) + "/").replace("/matrix/", str(matrix) + "/")


prefix = [
    args.compiler, "--target=x86_64-linux-gnu", f"--sysroot={sysroot}",
    "-nostdinc++", "-isystem", str(sysroot / "usr/include/c++" / args.gcc_version),
    "-isystem", str(sysroot / "usr/include/c++" / args.gcc_version / "x86_64-redhat-linux"),
    "-isystem", str(sysroot / "usr/include/c++" / args.gcc_version / "backward"),
]
commands = json.loads((build / "compile_commands.json").read_text())


def compile_object(entry):
    tokens = shlex.split(entry["command"])
    command = prefix + [host_path(token) for token in tokens[1:]]
    output = command[command.index("-o") + 1]
    (build / output).parent.mkdir(parents=True, exist_ok=True)
    log = build / (Path(output).name + ".cross.log")
    with log.open("w") as stream:
        subprocess.run(command, cwd=build, stdout=stream, stderr=subprocess.STDOUT, check=True)
    print("compiled", Path(entry["file"]).name, flush=True)


with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    list(pool.map(compile_object, commands))
links = list((build / "CMakeFiles").glob("*.dir/link.txt"))
if len(links) != 1:
    raise SystemExit(f"expected one wrapper link command, found {links}")
linux_build = "/matrix/" + build.relative_to(matrix).as_posix()
subprocess.run([
    "docker", "exec", "-w", linux_build, args.container,
    "sh", links[0].relative_to(build).as_posix(),
], check=True)
print("linked", linux_build, flush=True)
