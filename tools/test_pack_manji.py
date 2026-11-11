#!/usr/bin/env python3
"""tools/pack_manji.py の回帰テスト（標準ライブラリのみ）。

実行:  python3 -m unittest discover -s tools -p "test_*.py"
      または tools/ から python3 -m unittest test_pack_manji -v

狙い: ①のスキーマ探索バグ（リポジトリのルートから実行すると
スキーマ検査が黙って省略され、不正な台本が exit 0 で通った）の再発を防ぐ。
そのため「不正な台本は必ずエラーになる」ことを、検査の入口（check()）
と CLI（--check）の両方から確かめる。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pack_manji  # noqa: E402


def files_from_folder(folder):
    return pack_manji.read_folder(folder)


def minimal_chapter(**over):
    doc = {
        "manji": "1.0",
        "title": "テスト",
        "cast": {"太郎": {"color": "#ffffff", "pos": "left"}},
        "settings": {},
        "events": [{"type": "say", "who": "太郎", "text": "こんにちは", "wait": 0}],
    }
    doc.update(over)
    return doc


def write_archive(folder, chapters, manifest=None):
    """chapters: {相対パス: dict}、manifest: dict または None（自動生成させる）"""
    os.makedirs(folder, exist_ok=True)
    for rel, doc in chapters.items():
        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
    if manifest is not None:
        with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False)


def run_check(files):
    rep = pack_manji.Report()
    man = pack_manji.check(files, rep)
    return man, rep


class TestSchemaValidationRuns(unittest.TestCase):
    """①の回帰: どのカレントフォルダからでもスキーマ検査が走ること。"""

    def test_invalid_script_fails(self):
        # 未知の項目 + wait 上限超え。修正前はスキーマ検査が省略され exit 0 で通った。
        bad = minimal_chapter(unknownTop=True)
        bad["events"] = [{"type": "say", "who": "太郎", "text": "x", "wait": 9999999}]
        with tempfile.TemporaryDirectory() as d:
            write_archive(d, {"chapters/01.manji": bad},
                          {"manji_archive": "1.0", "title": "t",
                           "chapters": [{"file": "chapters/01.manji", "title": "t"}]})
            _, rep = run_check(files_from_folder(d))
        self.assertTrue(rep.errors, "不正な台本がエラーにならなかった（スキーマ検査が省略されていないか）")

    def test_invalid_script_fails_from_tmp_cwd(self):
        bad = minimal_chapter(unknownTop=True)
        with tempfile.TemporaryDirectory() as d:
            write_archive(d, {"chapters/01.manji": bad},
                          {"manji_archive": "1.0", "title": "t",
                           "chapters": [{"file": "chapters/01.manji", "title": "t"}]})
            # カレントフォルダを /tmp に移して CLI で検査（①の再現条件）
            r = subprocess.run(
                [sys.executable, os.path.join(HERE, "pack_manji.py"), d,
                 "-o", os.path.join(d, "out.manjiz")],
                cwd="/tmp", capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, "不正な台本が exit 0 になった: " + r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(d, "out.manjiz")))

    def test_valid_archive_passes(self):
        # 同梱サンプルが今も通ること（正常系のガード）
        for name in ("samples/builtin/botchan.manjiz", "samples/builtin/hoichi.manjiz"):
            r = subprocess.run(
                [sys.executable, os.path.join(HERE, "pack_manji.py"),
                 "--check", os.path.join(ROOT, name)],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{name} が通らなくなった: {r.stdout}{r.stderr}")

    def test_load_schema_finds_docs_from_any_cwd(self):
        cwd = os.getcwd()
        try:
            os.chdir("/tmp")
            self.assertIsNotNone(pack_manji.load_schema("manji.schema.json"))
            self.assertIsNotNone(pack_manji.load_schema("manifest.schema.json"))
        finally:
            os.chdir(cwd)


class TestCrossChecks(unittest.TestCase):
    """スキーマでは拾えない pack 側の相互チェック。"""

    def _archive(self, chapters, manifest):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        write_archive(tmp.name, chapters, manifest)
        return files_from_folder(tmp.name)

    def _manifest(self, chapter_file="chapters/01.manji"):
        return {"manji_archive": "1.0", "title": "t",
                "chapters": [{"file": chapter_file, "title": "t"}]}

    def test_who_not_in_cast_is_error(self):
        doc = minimal_chapter()
        doc["events"] = [{"type": "say", "who": "花子", "text": "x", "wait": 0}]
        _, rep = run_check(self._archive({"chapters/01.manji": doc}, self._manifest()))
        self.assertTrue(any("花子" in e for e in rep.errors))

    def test_missing_chapter_file_is_error(self):
        _, rep = run_check(self._archive({}, self._manifest()))
        self.assertTrue(rep.errors)

    def test_malformed_json_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "chapters"))
            with open(os.path.join(d, "chapters/01.manji"), "w", encoding="utf-8") as f:
                f.write("{壊れた json")
            write_archive(d, {}, self._manifest())
            _, rep = run_check(files_from_folder(d))
        self.assertTrue(rep.errors)

    def test_missing_asset_reference_is_error(self):
        doc = minimal_chapter()
        doc["events"] = [{"type": "say", "who": "太郎", "text": "x", "wait": 0,
                          "se": "asset:ない音"}]
        man = self._manifest()
        man["assets"] = {"se": {}}
        _, rep = run_check(self._archive({"chapters/01.manji": doc}, man))
        self.assertTrue(any("ない音" in e for e in rep.errors))

    def test_unlisted_manji_is_warning_not_error(self):
        doc = minimal_chapter()
        files = self._archive({"chapters/01.manji": doc, "chapters/02.manji": doc},
                              self._manifest())
        _, rep = run_check(files)
        self.assertFalse(rep.errors)
        self.assertTrue(any("02.manji" in w for w in rep.warns))

    def test_missing_manifest_autogenerates_with_warning(self):
        doc = minimal_chapter()
        with tempfile.TemporaryDirectory() as d:
            write_archive(d, {"chapters/01.manji": doc}, None)
            man, rep = run_check(files_from_folder(d))
        self.assertFalse(rep.errors)
        self.assertIsNotNone(man)
        self.assertTrue(any("自動生成" in w for w in rep.warns))

    def test_pack_then_check_roundtrip(self):
        doc = minimal_chapter()
        with tempfile.TemporaryDirectory() as d:
            write_archive(d, {"chapters/01.manji": doc}, self._manifest())
            out = os.path.join(d, "out.manjiz")
            r = subprocess.run(
                [sys.executable, os.path.join(HERE, "pack_manji.py"), d, "-o", out],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(zipfile.is_zipfile(out))
            r = subprocess.run(
                [sys.executable, os.path.join(HERE, "pack_manji.py"), "--check", out],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
