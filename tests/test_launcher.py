import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mc_launcher.core import Minecraft, offline_uuid
from mc_launcher.packs import import_modrinth_pack


class LauncherCoreTests(unittest.TestCase):
    def test_offline_uuid_uses_java_offline_player_name(self):
        # Known algorithm: MD5 UTF-8("OfflinePlayer:<name>") with UUID v3 bits.
        self.assertEqual(offline_uuid("Notch"), "b50ad385-829d-3141-a216-7e7d7539ba7f")

    def test_argument_expansion_and_rules(self):
        args = [{"rules": [{"action": "allow"}], "value": ["-Dname=${auth_player_name}", "literal"]},
                {"rules": [{"action": "disallow"}], "value": "excluded"}]
        self.assertEqual(Minecraft._expand_args(args, {"auth_player_name": "Alex"}), ["-Dname=Alex", "literal"])

    def test_import_modrinth_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "pack.mrpack"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("modrinth.index.json", json.dumps({"formatVersion": 1, "name": "Pack", "files": []}))
                zf.writestr("overrides/config/example.txt", "hello")
            instance = import_modrinth_pack(archive, root, "Test Pack")
            self.assertEqual((instance / "config/example.txt").read_text(), "hello")

    def test_import_rejects_zip_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "unsafe.mrpack"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("modrinth.index.json", json.dumps({"formatVersion": 1, "files": []}))
                zf.writestr("overrides/../../outside.txt", "unsafe")
            with self.assertRaises(ValueError):
                import_modrinth_pack(archive, root, "Unsafe")


if __name__ == "__main__":
    unittest.main()
