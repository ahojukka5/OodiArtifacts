#!/usr/bin/env python3
"""Pinned native OCCT 8.0.1 build, relocation qualification and immutable delivery."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

COMMIT = 'b8f597c677811d1f9f4d8a97f5ae2825c0353a42'
SOURCE_SHA256 = 'dba62b81078dd43cec23feba89432be301582341001edad1b93342ad8bda35ea'
SOURCE_URL = 'https://codeload.github.com/Open-Cascade-SAS/OCCT/tar.gz/' + COMMIT
REPOSITORY = 'ahojukka5/OodiArtifacts'
CONTAINER = 'almalinux:8.10@sha256:e6d31b01fca10ed4f914e84e1139c3a40d6acf3d8346224a32f3e5649b1a3f7d'
SMOKE = Path(__file__).resolve().parent / 'smoke'
OPTIONS = {
    'CMAKE_BUILD_TYPE': 'Release', 'BUILD_LIBRARY_TYPE': 'Shared',
    'BUILD_CPP_STANDARD': 'C++17', 'BUILD_SOVERSION_NUMBERS': '3',
    'BUILD_USE_VCPKG': 'OFF', 'BUILD_USE_PCH': 'OFF',
    'BUILD_MODULE_FoundationClasses': 'ON', 'BUILD_MODULE_ModelingData': 'ON',
    'BUILD_MODULE_ModelingAlgorithms': 'ON', 'BUILD_MODULE_DataExchange': 'ON',
    'BUILD_MODULE_ApplicationFramework': 'OFF', 'BUILD_MODULE_Visualization': 'OFF',
    'BUILD_MODULE_Draw': 'OFF', 'BUILD_DOC_Overview': 'OFF', 'BUILD_DOC_RefMan': 'OFF',
    'USE_TK': 'OFF', 'USE_XLIB': 'OFF', 'USE_OPENGL': 'OFF', 'USE_GLES2': 'OFF',
    'USE_FREETYPE': 'OFF', 'USE_FREEIMAGE': 'OFF', 'USE_FFMPEG': 'OFF',
    'USE_TBB': 'OFF', 'USE_RAPIDJSON': 'OFF', 'USE_DRACO': 'OFF', 'USE_EIGEN': 'OFF',
    'INSTALL_DIR_LAYOUT': 'Unix', 'INSTALL_DIR_LIB': 'lib',
    'INSTALL_DIR_INCLUDE': 'include/opencascade', 'INSTALL_DIR_CMAKE': 'lib/cmake/opencascade',
    'INSTALL_DIR_RESOURCE': 'share/opencascade/resources',
    'CMAKE_INSTALL_RPATH_USE_LINK_PATH': 'OFF', 'CMAKE_BUILD_WITH_INSTALL_RPATH': 'ON',
}
REQUIRED = {'TKernel', 'TKMath', 'TKBRep', 'TKPrim', 'TKBO', 'TKBool', 'TKMesh',
            'TKDESTEP', 'TKDEIGES', 'TKDESTL', 'TKXCAF'}


def run(args, cwd=None):
    args = [str(a) for a in args]
    print('+ ' + ' '.join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def capture(args):
    return subprocess.check_output([str(a) for a in args], text=True,
                                   stderr=subprocess.STDOUT).strip()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tree_hash(root):
    """Git object encoding, independently cross-checked with git write-tree."""
    def obj(kind, data):
        return hashlib.sha1(kind + b' ' + str(len(data)).encode() + b'\0' + data).digest()
    entries = []
    for path in root.iterdir():
        name = os.fsencode(path.name)
        if path.is_symlink():
            mode, digest, key = b'120000', obj(b'blob', os.fsencode(os.readlink(path))), name
        elif path.is_dir():
            subtree = tree_hash(path)
            if subtree == '4b825dc642cb6eb9a060e54bf8d69288fbee4904':
                continue  # Git/Julia artifact trees omit empty directories.
            mode, digest, key = b'40000', bytes.fromhex(subtree), name + b'/'
        else:
            mode = b'100755' if path.stat().st_mode & 0o111 else b'100644'
            digest, key = obj(b'blob', path.read_bytes()), name
        entries.append((key, mode + b' ' + name + b'\0' + digest))
    return obj(b'tree', b''.join(data for _, data in sorted(entries))).hex()


def git_tree_hash(root):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / 'objects.git'
        run(['git', 'init', '--bare', repo])
        command = ['git', '--git-dir=' + str(repo), '--work-tree=' + str(root),
                   '-c', 'core.filemode=true', '-c', 'core.autocrlf=false']
        run(command + ['add', '--force', '--all', '--', '.'], cwd=root)
        return capture(command + ['write-tree'])


def extract(archive, target):
    target.mkdir(parents=True)
    with tarfile.open(archive) as stream:
        # Only our expected install/source trees; disallow traversal and escaping links.
        for member in stream.getmembers():
            dest = (target / member.name).resolve()
            if os.path.commonpath([str(target.resolve()), str(dest)]) != str(target.resolve()):
                raise RuntimeError('unsafe archive path: ' + member.name)
            if member.isdev() or member.isfifo() or member.islnk():
                raise RuntimeError('unsupported archive member: ' + member.name)
            if member.issym():
                link = (target / member.name).parent / member.linkname
                if os.path.commonpath([str(target.resolve()), str(link.resolve())]) != str(target.resolve()):
                    raise RuntimeError('unsafe archive symlink: ' + member.name)
        stream.extractall(target)


def target_platform():
    system, machine = platform.system(), platform.machine()
    if (system, machine) == ('Darwin', 'arm64'):
        return 'macos-aarch64'
    if (system, machine) == ('Linux', 'x86_64'):
        return 'linux-x86_64-glibc'
    raise RuntimeError('unsupported native builder: ' + system + '/' + machine)


def libraries(prefix):
    suffix = '*.dylib' if platform.system() == 'Darwin' else '*.so*'
    return sorted({p.resolve() for p in (prefix / 'lib').glob('libTK' + suffix)})


def audit(prefix):
    prefix = prefix.resolve()
    products = libraries(prefix)
    names = {p.name.split('.')[0][3:] for p in products}
    if not REQUIRED <= names:
        raise RuntimeError('missing toolkits: ' + str(REQUIRED - names))
    details = []
    glibc, glibcxx, cxxabi = set(), set(), set()
    for path in products:
        if any(marker in path.read_bytes() for marker in
               (b'/Users/', b'/home/runner/', b'/work/')):
            raise RuntimeError('local source/build path embedded in library: ' + str(path))
        item = {'file': str(path.relative_to(prefix)), 'format': capture(['file', path])}
        if platform.system() == 'Darwin':
            if capture(['lipo', '-archs', path]) != 'arm64':
                raise RuntimeError('non-arm64 library: ' + str(path))
            linked = capture(['otool', '-L', path])
            loads = capture(['otool', '-l', path])
            item.update(linkage=linked.replace(str(prefix), '${PREFIX}'), load_commands=loads.replace(str(prefix), '${PREFIX}'))
            for line in linked.splitlines()[1:]:
                dep = line.strip().split(' (')[0]
                if dep.startswith('@rpath/'):
                    if not (prefix / 'lib' / dep[7:]).exists():
                        raise RuntimeError('unresolved dependency: ' + dep)
                elif not dep.startswith(('/usr/lib/', '/System/Library/')):
                    raise RuntimeError('undeclared dependency: ' + dep)
            rpaths = re.findall(r'cmd LC_RPATH\s+cmdsize \d+\s+path (.*?) \(offset', loads)
            if rpaths != ['@loader_path']:
                raise RuntimeError('unexpected Mach-O rpaths: ' + str(rpaths))
            versions = re.findall(r'\bminos (\S+)', loads)
            legacy = re.findall(r'cmd LC_VERSION_MIN_MACOSX\s+cmdsize \d+\s+version (\S+)', loads)
            if versions + legacy != ['11.0']:
                raise RuntimeError('unexpected deployment target: ' + str(versions + legacy))
        else:
            header = capture(['readelf', '-h', path])
            if 'ELF64' not in header or 'Advanced Micro Devices X86-64' not in header:
                raise RuntimeError('wrong ELF architecture: ' + str(path))
            dynamic = capture(['readelf', '-d', path])
            symbols = capture(['readelf', '--dyn-syms', '--wide', path])
            versions = capture(['readelf', '--version-info', path])
            linked = capture(['ldd', path])
            item.update(dynamic=dynamic, linkage=linked.replace(str(prefix), '${PREFIX}'), version_info=versions)
            needed = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
            allowed = {'libstdc++.so.6', 'libgcc_s.so.1', 'libc.so.6', 'libm.so.6',
                       'libdl.so.2', 'libpthread.so.0', 'librt.so.1', 'ld-linux-x86-64.so.2'}
            for dep in needed:
                if dep not in allowed and not (dep.startswith('libTK') and (prefix / 'lib' / dep).exists()):
                    raise RuntimeError('undeclared ELF dependency: ' + dep)
            rpaths = re.findall(r'\((?:RUNPATH|RPATH)\).*?\[(.*?)\]', dynamic)
            if rpaths != ['$ORIGIN'] or 'not found' in linked:
                raise RuntimeError('broken ELF linkage: ' + dynamic + linked)
            undefined = '\n'.join(line for line in symbols.splitlines() if ' UND ' in line)
            glibc.update(re.findall(r'@GLIBC_([\d.]+)', undefined))
            glibcxx.update(re.findall(r'@GLIBCXX_([\d.]+)', undefined))
            cxxabi.update(re.findall(r'@CXXABI_([\d.]+)', undefined))
        details.append(item)
    for config in (prefix / 'lib/cmake').rglob('*.cmake'):
        if re.search(r'/(?:Users/|home/runner/|work/|__w/)', config.read_text()):
            raise RuntimeError('build path in CMake metadata: ' + str(config))
    def maximum(values):
        return max(values, key=lambda v: tuple(map(int, v.split('.')))) if values else None
    floor = {'GLIBC': maximum(glibc), 'GLIBCXX': maximum(glibcxx), 'CXXABI': maximum(cxxabi)}
    if floor['GLIBC'] and tuple(map(int, floor['GLIBC'].split('.'))) > (2, 28):
        raise RuntimeError('glibc baseline exceeds EL8: ' + str(floor))
    if floor['GLIBCXX'] and tuple(map(int, floor['GLIBCXX'].split('.'))) > (3, 4, 25):
        raise RuntimeError('libstdc++ baseline exceeds EL8 GCC8: ' + str(floor))
    return {'products': sorted(names), 'libraries': details, 'required_symbol_versions': floor}


def qualify(prefix, work):
    prefix = prefix.resolve()
    work = work.resolve()
    report = audit(prefix)
    work.mkdir(parents=True)
    command = ['cmake', '-S', SMOKE, '-B', work / 'build', '-G', 'Ninja',
               '-DCMAKE_BUILD_TYPE=Release', '-DOpenCASCADE_DIR=' + str(prefix / 'lib/cmake/opencascade')]
    if platform.system() == 'Darwin':
        command += ['-DCMAKE_OSX_ARCHITECTURES=arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0']
    run(command)
    run(['cmake', '--build', work / 'build', '--parallel', '2'])
    env = os.environ.copy()
    for key in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH', 'CASROOT'):
        env.pop(key, None)
    env['CSF_OCCTResourcePath'] = str(prefix / 'share/opencascade/resources')
    subprocess.run([str(work / 'build/occt_smoke')] + [str(p) for p in libraries(prefix)],
                   cwd=work, env=env, check=True)
    report['installed_prefix_smoke'] = 'PASS: toolkit loading, box, Boolean volume, mesh, STEP volume roundtrip, IGES/STL export'
    report['runtime'] = capture(['sw_vers']) if platform.system() == 'Darwin' else Path('/etc/os-release').read_text()
    report['relocated'] = True
    return report


def build(args):
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    system = target_platform()
    if system.startswith('linux'):
        if 'AlmaLinux' not in Path('/etc/os-release').read_text():
            raise RuntimeError('Linux build must run inside the pinned EL8 container')
        if capture(['getconf', 'GNU_LIBC_VERSION']) != 'glibc 2.28':
            raise RuntimeError('expected glibc 2.28 build environment')
    source_archive = work / 'source.tar.gz'
    if not source_archive.exists():
        urllib.request.urlretrieve(SOURCE_URL, source_archive)
    if sha256(source_archive) != SOURCE_SHA256:
        raise RuntimeError('source archive SHA256 mismatch')
    source = work / ('OCCT-' + COMMIT)
    with tempfile.TemporaryDirectory(dir=work) as tmp:
        unpack = Path(tmp) / 'unpack'
        extract(source_archive, unpack)
        if not source.exists():
            shutil.move(str(unpack / source.name), source)
        elif tree_hash(source) != tree_hash(unpack / source.name):
            raise RuntimeError('source directory differs from the pinned clean archive')
    prefix = work / 'install'
    options = dict(OPTIONS, CMAKE_INSTALL_PREFIX=str(prefix))
    mappings = ['-ffile-prefix-map=' + str(source) + '=/usr/src/occt',
                '-ffile-prefix-map=' + str(work / 'build') + '=/usr/src/occt-build']
    options.update(CMAKE_C_FLAGS=' '.join(mappings), CMAKE_CXX_FLAGS=' '.join(mappings))
    if system == 'macos-aarch64':
        options.update(CMAKE_OSX_ARCHITECTURES='arm64', CMAKE_OSX_DEPLOYMENT_TARGET='11.0',
                       INSTALL_NAME_DIR='@rpath', CMAKE_INSTALL_RPATH='@loader_path')
    else:
        options.update(CMAKE_INSTALL_RPATH='$ORIGIN')
        options['CMAKE_CXX_FLAGS'] += ' -D_GLIBCXX_USE_CXX11_ABI=1'
    run(['cmake', '-S', source, '-B', work / 'build', '-G', 'Ninja'] +
        ['-D' + k + '=' + v for k, v in sorted(options.items())])
    if args.configure_only:
        return
    # ~2 GiB per C++ compiler, at most four on hosted CI and six on the Mac.
    if platform.system() == 'Darwin':
        memory = int(capture(['sysctl', '-n', 'hw.memsize']))
        jobs = min(6, os.cpu_count() or 2, max(1, memory // (2 * 1024**3)))
    else:
        memory = int(re.search(r'MemTotal:\s+(\d+)', Path('/proc/meminfo').read_text())[1]) * 1024
        jobs = min(4, os.cpu_count() or 2, max(1, memory // (2 * 1024**3)))
    run(['cmake', '--build', work / 'build', '--parallel', str(jobs)])
    run(['cmake', '--install', work / 'build'])
    for notice in ('LICENSE_LGPL_21.txt', 'OCCT_LGPL_EXCEPTION.txt'):
        shutil.copy2(source / notice, prefix / notice)
    # OCCT's shell environment helpers bake in the install location. Consumers
    # use relocatable CMake metadata and CSF_OCCTResourcePath instead.
    shutil.rmtree(prefix / 'bin', ignore_errors=True)
    # These flags describe this compilation, not downstream consumers. OCCT
    # exports CMAKE_*_FLAGS into its config; remove only these private mappings.
    for config in (prefix / 'lib/cmake').rglob('*.cmake'):
        text = config.read_text()
        for flag in mappings:
            text = text.replace(flag, '')
        config.write_text(text)
    info = {
        'schema_version': 1, 'name': 'OCCT', 'version': '8.0.1', 'platform': system,
        'source': {'repository': 'https://github.com/Open-Cascade-SAS/OCCT', 'commit': COMMIT,
                   'archive_url': SOURCE_URL, 'archive_sha256': SOURCE_SHA256, 'patches': []},
        'build_options': {k: v.replace(str(source), '${SOURCE}').replace(str(work / 'build'), '${BUILD}')
                          for k, v in options.items() if k != 'CMAKE_INSTALL_PREFIX'},
        'toolchain': {'compiler': capture(['c++', '--version']), 'linker': capture(['ld', '-v']) if system == 'macos-aarch64' else capture(['ld', '--version']),
                      'cmake': capture(['cmake', '--version']), 'ninja': capture(['ninja', '--version']),
                      'cpu_parallelism': jobs, 'memory_bytes': memory},
        'abi': {'language': 'C++17', 'julia_version_selector': None, 'occt_soversion': '8.0.1',
                'cxxstring_abi': 'cxx11' if system.startswith('linux') else 'libc++'},
        'packaging': {'removed': ['bin/ (nonrelocatable OCCT environment helpers)',
                                  'private compiler path mappings from exported CMake flags']},
        'recipe_revision': os.environ.get('GITHUB_SHA') or capture(['git', 'rev-parse', 'HEAD']),
    }
    if system == 'macos-aarch64':
        info['toolchain'].update(os=capture(['sw_vers']), sdk=capture(['xcrun', '--show-sdk-version']),
                                 sdk_path=capture(['xcrun', '--show-sdk-path']), deployment_target='11.0', architecture='arm64')
        info['toolchain']['developer_directory'] = capture(['xcode-select', '-p'])
        info['toolchain']['command_line_tools'] = capture(['pkgutil', '--pkg-info=com.apple.pkg.CLTools_Executables'])
    else:
        info['toolchain'].update(sysroot='AlmaLinux 8.10 / glibc 2.28', container=CONTAINER,
                                 packages=capture(['rpm', '-qa', '--qf', '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n']))
    save(work / 'build.json', info)
    package(work)


def package(work):
    prefix = work / 'install'
    out = work / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / 'OCCT.tar.gz'
    digest = tree_hash(prefix)
    if git_tree_hash(prefix) != digest:
        raise RuntimeError('independent Git tree verification failed')
    def normalize(member):
        member.uid = member.gid = 0
        member.uname = member.gname = ''
        member.mtime = 0
        return member
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as tar:
            for path in sorted(prefix.iterdir()):
                tar.add(path, arcname=path.name, filter=normalize)
    info = json.loads((work / 'build.json').read_text())
    info.update(sha256=sha256(archive), **{'git-tree-sha1': digest})
    info['release_tag'] = 'OCCT-8.0.1-' + info['platform'] + '-' + digest[:12]
    info['release_url'] = 'https://github.com/' + REPOSITORY + '/releases/tag/' + info['release_tag']
    with tempfile.TemporaryDirectory(prefix='occt-relocated-') as tmp:
        target = Path(tmp) / 'prefix'
        extract(archive, target)
        if tree_hash(target) != digest or git_tree_hash(target) != digest:
            raise RuntimeError('unpacked archive tree mismatch')
        info['qualification'] = qualify(target, Path(tmp) / 'consumer')
    save(out / 'OCCT.provenance.json', info)
    # A second archive digest implementation verifies the recorded identity.
    digest_command = ['shasum', '-a', '256', archive] if platform.system() == 'Darwin' else ['sha256sum', archive]
    if capture(digest_command).split()[0] != info['sha256']:
        raise RuntimeError('independent archive SHA256 mismatch')
    print(json.dumps({k: info[k] for k in ('release_url', 'sha256', 'git-tree-sha1')}, indent=2))


def verify(directory):
    directory = Path(directory).resolve()
    info = json.loads((directory / 'OCCT.provenance.json').read_text())
    if (info['source']['commit'], info['version'], info['platform']) != (COMMIT, '8.0.1', target_platform()):
        raise RuntimeError('unexpected artifact source/version/platform')
    archive = directory / 'OCCT.tar.gz'
    if sha256(archive) != info['sha256']:
        raise RuntimeError('downloaded archive SHA256 mismatch')
    with tempfile.TemporaryDirectory(prefix='occt-delivery-') as tmp:
        prefix = Path(tmp) / 'prefix'
        extract(archive, prefix)
        if tree_hash(prefix) != info['git-tree-sha1'] or git_tree_hash(prefix) != info['git-tree-sha1']:
            raise RuntimeError('downloaded artifact tree mismatch')
        report = qualify(prefix, Path(tmp) / 'consumer')
    print('DELIVERY PASS ' + info['release_url'])
    return report


def publish(directory):
    directory = Path(directory).resolve()
    verify(directory)
    info = json.loads((directory / 'OCCT.provenance.json').read_text())
    tag = info['release_tag']
    assets = ['OCCT.tar.gz', 'OCCT.provenance.json']
    existing = subprocess.run(['gh', 'release', 'view', tag, '--repo', REPOSITORY], stdout=subprocess.DEVNULL)
    if existing.returncode:
        # gh refuses an existing tag; never use --clobber or modify a release.
        tags = json.loads(capture(['gh', 'api', 'repos/' + REPOSITORY + '/git/matching-refs/tags/' + tag]))
        if tags:
            raise RuntimeError('tag already exists without verified release identity')
        notes = directory / 'release-notes.md'
        notes.write_text('Native OCCT 8.0.1; ' + info['platform'] + '\n\nSource: `' + COMMIT +
                         '`\n\nArtifact tree: `' + info['git-tree-sha1'] + '`\n\nArchive SHA256: `' + info['sha256'] +
                         '`\n\nQualified relocated C++ consumer: box, Boolean volume, mesh, STEP roundtrip, IGES/STL; every toolkit loaded.\n'
                         '\nLGPL-2.1 with OCCT exception; notices included. Native C++ runtime; no Julia ABI selector.\n')
        run(['gh', 'release', 'create', tag, '--repo', REPOSITORY, '--target', info['recipe_revision'],
             '--title', tag, '--notes-file', notes, '--latest=false'] + [directory / a for a in assets])
    with tempfile.TemporaryDirectory(prefix='occt-public-download-') as tmp:
        fresh = Path(tmp)
        for name in assets:
            # Public unauthenticated download, separate from the gh upload path.
            url = 'https://github.com/' + REPOSITORY + '/releases/download/' + tag + '/' + name
            urllib.request.urlretrieve(url, fresh / name)
            if sha256(fresh / name) != sha256(directory / name):
                raise RuntimeError('public content/provenance differs from intended release: ' + name)
        report = verify(fresh)
        save(directory / 'public-delivery.json', {'release_url': info['release_url'], 'qualification': report,
                                                'sha256': info['sha256'], 'git-tree-sha1': info['git-tree-sha1']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    builder = sub.add_parser('build')
    builder.add_argument('--work', required=True)
    builder.add_argument('--configure-only', action='store_true')
    for name in ('verify', 'publish'):
        sub.add_parser(name).add_argument('directory')
    args = parser.parse_args()
    if args.command == 'build':
        build(args)
    elif args.command == 'verify':
        verify(args.directory)
    else:
        publish(args.directory)


if __name__ == '__main__':
    main()
