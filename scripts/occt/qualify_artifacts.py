#!/usr/bin/env python3
"""Qualify existing OCCT releases through real Pkg.Artifacts and native consumers."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import occt

REPO = Path(__file__).resolve().parents[2]
INPUTS = Path(__file__).with_name('qualification-inputs.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--julia', default='julia')
    parser.add_argument('--channel', help='Optional juliaup channel (local Mac only)')
    parser.add_argument('--work', required=True, help='New empty directory outside the checkout')
    args = parser.parse_args()
    work = Path(args.work).resolve()
    if work.is_relative_to(REPO):
        raise RuntimeError('test depots and output must stay outside the source checkout')
    if work.exists() and any(work.iterdir()):
        raise RuntimeError('each test requires a fresh empty work directory: ' + str(work))
    work.mkdir(parents=True, exist_ok=True)
    depot = work / 'depot'
    depot.mkdir()
    assert not any(depot.iterdir())
    env = os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(depot), JULIA_LOAD_PATH='@stdlib', JULIA_PKG_SERVER='',
               JULIA_PKG_IGNORE_HASHES='false', JULIA_PKG_PRECOMPILE_AUTO='0')
    # Neither the Julia install nor C++ subprocesses may consume loader overrides.
    for name in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH',
                 'JULIA_PROJECT', 'JULIA_ARTIFACT_OVERRIDE', 'CASROOT'):
        env.pop(name, None)
    command = [args.julia]
    if args.channel:
        command += ['+' + args.channel]
    command += ['--startup-file=no', '--history-file=no', str(REPO / 'scripts/occt/install_artifact.jl'),
                str(REPO / 'Artifacts.toml'), str(work), str(depot)]
    report = {'schema_version': 1, 'depot_initially_empty': True, 'status': 'RUNNING',
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'recipe_revision': occt.capture(['git', '-C', REPO, 'rev-parse', 'HEAD']),
              'source_worktree_dirty': bool(occt.capture(['git', '-C', REPO, 'status', '--porcelain'])),
              'binarybuilder_reproduction': 'NOT RUN (independent source-build qualification)',
              'native_build': 'EXISTING IMMUTABLE RELEASE; no OCCT rebuild'}
    try:
        print('+ ' + ' '.join(command), flush=True)
        subprocess.run(command, env=env, check=True, timeout=900)
        pkg = tomllib.loads((work / 'pkg-result.toml').read_text())
        facts = json.loads(INPUTS.read_text())
        expected = facts['platforms'][occt.target_platform()]
        assert pkg['artifact_tree'] == expected['tree']
        assert pkg['archive_url'] == expected['archive_url']
        assert pkg['archive_sha256'] == expected['archive_sha256']
        assert pkg['override_used'] is False
        assert pkg['depot_path'] == [str(depot)]
        assert occt.sha256(work / 'OCCT.tar.gz') == expected['archive_sha256']
        assert occt.sha256(work / 'OCCT.provenance.json') == expected['provenance_sha256']
        provenance = json.loads((work / 'OCCT.provenance.json').read_text())
        assert provenance['source']['commit'] == facts['source_commit'] == occt.COMMIT
        assert provenance['version'] == facts['version'] == '8.0.1'
        assert provenance['git-tree-sha1'] == expected['tree']
        assert provenance['sha256'] == expected['archive_sha256']
        assert provenance['qualification']['products'] == expected['products']
        prefix = Path(pkg['artifact_prefix']).resolve()
        assert prefix == (depot / 'artifacts' / expected['tree']).resolve()
        assert occt.tree_hash(prefix) == occt.git_tree_hash(prefix) == expected['tree']
        for path in ('lib', 'include/opencascade', 'lib/cmake/opencascade',
                     'share/opencascade/resources', 'LICENSE_LGPL_21.txt', 'OCCT_LGPL_EXCEPTION.txt'):
            assert (prefix / path).exists(), path
        report.update(pkg=pkg, platform=occt.target_platform(), source_commit=facts['source_commit'],
                      source_provenance_sha256=expected['provenance_sha256'],
                      tree=expected['tree'], archive_sha256=expected['archive_sha256'])
        installed = occt.qualify(prefix, work / 'installed-consumer', record_loads=True)
        assert installed['products'] == expected['products']
        installed['relocated'] = False  # This first test uses the actual Pkg-installed prefix.
        report['pkg_installed_native'] = installed
        relocated = work / 'relocated' / 'prefix'
        shutil.copytree(prefix, relocated, symlinks=True)
        assert occt.tree_hash(relocated) == occt.git_tree_hash(relocated) == expected['tree']
        parked = work / 'parked-original-artifact'
        prefix.rename(parked)
        try:
            report['relocated_native'] = occt.qualify(relocated, work / 'relocated-consumer', record_loads=True)
            report['original_pkg_prefix_hidden_during_relocation'] = True
        finally:
            parked.rename(prefix)
        assert not (depot / 'artifacts/Overrides.toml').exists()
        checksum_command = ['shasum', '-a', '256'] if sys.platform == 'darwin' else ['sha256sum']
        assert occt.capture(checksum_command + [str(work / 'OCCT.tar.gz')]).split()[0] == expected['archive_sha256']
        report['status'] = 'PASS'
        print('QUALIFICATION PASS ' + pkg['julia_version'] + ' ' + pkg['platform'], flush=True)
    except BaseException as error:
        report.update(status='FAIL', error=str(error))
        raise
    finally:
        report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        occt.save(work / 'qualification.json', report)


if __name__ == '__main__':
    main()
