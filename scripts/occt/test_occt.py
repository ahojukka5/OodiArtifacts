"""Checks for artifact identity and archive handling before any publication."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

import occt


class ArtifactTests(unittest.TestCase):
    def test_git_identity_with_modes_links_sorting_and_empty_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'foo').mkdir()
            (root / 'foo/entry').write_bytes(b'contents\n')
            (root / 'foo.bar').write_bytes(b'neighbor\n')
            (root / 'executable').write_bytes(b'#!/bin/sh\n')
            (root / 'executable').chmod(0o755)
            (root / 'link').symlink_to('foo/entry')
            (root / 'empty/nested').mkdir(parents=True)
            self.assertEqual(occt.tree_hash(root), occt.git_tree_hash(root))
            before = occt.tree_hash(root)
            (root / 'executable').chmod(0o644)
            self.assertNotEqual(before, occt.tree_hash(root))

    def test_extract_rejects_traversal_and_external_symlinks(self):
        for name, link in [('../escape', None), ('link', '/etc/passwd'),
                           ('link', '../../escape')]:
            with self.subTest(name=name, link=link), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                archive = root / 'bad.tar.gz'
                with tarfile.open(archive, 'w:gz') as tar:
                    member = tarfile.TarInfo(name)
                    if link:
                        member.type = tarfile.SYMTYPE
                        member.linkname = link
                        tar.addfile(member)
                    else:
                        member.size = 1
                        tar.addfile(member, io.BytesIO(b'x'))
                with self.assertRaises(RuntimeError):
                    occt.extract(archive, root / 'extracted')

    def test_extract_preserves_shared_library_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            (source / 'libTK.so.8').write_bytes(b'library')
            (source / 'libTK.so').symlink_to('libTK.so.8')
            archive = root / 'good.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for path in source.iterdir():
                    tar.add(path, arcname=path.name)
            target = root / 'relocated'
            occt.extract(archive, target)
            self.assertEqual(occt.tree_hash(source), occt.tree_hash(target))
            self.assertEqual((target / 'libTK.so').read_bytes(), b'library')


if __name__ == '__main__':
    unittest.main()
