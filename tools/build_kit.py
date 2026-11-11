#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配布用キット manji_kit.zip をリポジトリから再構築する。

キットの正本はリポジトリ側のファイルである。このスクリプトが集めるのは:

- ルート直下ファイル（ROOT_FILES）: プレーヤー・使い方ページと docs/ の
  ドキュメント・スキーマを、キット側の名前に写して収める
- samples/ 配下の全ファイル: サンプル・同梱作品・台本ソース
  （samples/*_src/）をそのままのパスで収める
- tools/ の配布対象（TOOL_FILES）: pack ツールと台本生成スクリプト

使い方:
    python3 tools/build_kit.py            # manji_kit.zip を再構築する
    python3 tools/build_kit.py --check    # 再構築せず、現在の manji_kit.zip が
                                          # リポジトリから再現できるか検査する

再現性のため、zip のタイムスタンプは固定値にし、エントリ順も定義順に
そろえる。--check はエントリ名の並びと各ファイルの中身を比べる
（zip のバイト列そのものは圧縮実装の差で変わりうるので比べない）。
新しいルートファイルや tools をキットに入れたくなったら、
ROOT_FILES / TOOL_FILES に1行足すこと（samples/ 配下は自動で入る）。
"""
import argparse
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT_DIR = "manji_kit"
KIT_ZIP = os.path.join(ROOT, "manji_kit.zip")
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
STORED_SUFFIXES = (".manjiz", ".zip", ".mp3", ".m4a")

# (キット側の相対パス, リポジトリ側の相対パス)
ROOT_FILES = [
    ("player.html", "index.html"),
    ("guide.html", "guide.html"),
    ("MANJI_AI_GUIDE.md", "docs/MANJI_AI_GUIDE.md"),
    ("README_ja.md", "docs/README_ja.md"),
    ("manifest.schema.json", "docs/manifest.schema.json"),
    ("manji.schema.json", "docs/manji.schema.json"),
]
TOOL_FILES = [
    "tools/pack_manji.py",
    "tools/gen_manzai.py",
    "tools/gen_hoichi.py",
]


def collect():
    """キットに入るファイルを (キット側相対パス, 実ファイルのパス) の
    決定的な並びで返す。"""
    entries = []
    for kit_rel, repo_rel in ROOT_FILES:
        entries.append((kit_rel, os.path.join(ROOT, repo_rel)))
    samples_root = os.path.join(ROOT, "samples")
    sample_files = []
    for dirpath, dirnames, filenames in os.walk(samples_root):
        dirnames.sort()
        for name in sorted(filenames):
            if name == ".DS_Store" or name.startswith("._"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            sample_files.append((rel, full))
    entries.extend(sorted(sample_files))
    for rel in TOOL_FILES:
        entries.append((rel, os.path.join(ROOT, rel)))
    for kit_rel, full in entries:
        if not os.path.isfile(full):
            raise SystemExit(f"キットの材料がありません: {full}（キット側: {kit_rel}）")
    return entries


def plan():
    """zip の全エントリ（フォルダ, ファイルの別と材料パスつき）を返す。"""
    items = []
    seen_dirs = set()

    def add_dir(rel):
        if rel and rel not in seen_dirs:
            seen_dirs.add(rel)
            items.append((rel + "/", None))

    add_dir(KIT_DIR)
    for kit_rel, full in collect():
        parts = (KIT_DIR + "/" + kit_rel).split("/")[:-1]
        for i in range(2, len(parts) + 1):
            add_dir("/".join(parts[:i]))
        items.append((KIT_DIR + "/" + kit_rel, full))
    return items


def read_plan():
    """エントリ名の並びと、ファイルエントリの中身（bytes）を返す。"""
    names = []
    contents = {}
    for name, full in plan():
        names.append(name)
        if full is not None:
            with open(full, "rb") as fh:
                contents[name] = fh.read()
    return names, contents


def write_zip(out):
    names, contents = read_plan()
    with zipfile.ZipFile(out, "w") as z:
        for name in names:
            zi = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            zi.create_system = 3
            if name.endswith("/"):
                zi.compress_type = zipfile.ZIP_STORED
                zi.external_attr = (0o755 << 16) | 0x10
                z.writestr(zi, b"")
            else:
                stored = name.lower().endswith(STORED_SUFFIXES)
                zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                z.writestr(zi, contents[name],
                           compresslevel=None if stored else 9)
    return len(contents)


def check():
    if not os.path.isfile(KIT_ZIP):
        print("manji_kit.zip がありません")
        return 1
    names, contents = read_plan()
    with zipfile.ZipFile(KIT_ZIP) as z:
        actual_names = z.namelist()
        diffs = []
        if actual_names != names:
            only_zip = [n for n in actual_names if n not in names]
            only_repo = [n for n in names if n not in actual_names]
            if only_zip:
                diffs.append("キットにだけある: " + ", ".join(only_zip))
            if only_repo:
                diffs.append("リポジトリ側にだけある: " + ", ".join(only_repo))
            if not only_zip and not only_repo:
                diffs.append("エントリの並びが違います")
        for name, data in contents.items():
            try:
                if z.read(name) != data:
                    diffs.append(f"中身が違う: {name}")
            except KeyError:
                pass  # 名前の差分として報告済み
    if diffs:
        print("キットはリポジトリから再現できません:")
        for d in diffs:
            print(" -", d)
        return 1
    print(f"OK: manji_kit.zip はリポジトリから再現できます（ファイル {len(contents)} 件）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="配布用キット manji_kit.zip の再構築・検査")
    ap.add_argument("--check", action="store_true",
                    help="再構築せず、現在の manji_kit.zip が再現できるか検査する")
    ap.add_argument("-o", "--out", default=KIT_ZIP,
                    help="出力先（既定: リポジトリ直下の manji_kit.zip）")
    args = ap.parse_args()
    if args.check:
        return check()
    n = write_zip(args.out)
    print(f"{args.out} を再構築しました（ファイル {n} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
