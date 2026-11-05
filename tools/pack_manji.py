#!/usr/bin/env python3
"""漫字アーカイブ（.manjiz）を作る・検査するツール。

使い方:
  python3 pack_manji.py <フォルダ> [-o 出力.manjiz]   フォルダを検査して .manjiz に固める
  python3 pack_manji.py --check <ファイル.manjiz|.zip>   既存のアーカイブを検査する

フォルダの中身:
  manifest.json            （無ければ .manji を名前順に並べて自動生成）
  chapters/*.manji         章ファイル（cast を省くと manifest の cast を引き継ぐ）
  assets/*.m4a|mp3|wav     任意の音声。manifest.json の assets.bgm / assets.se に ID を登録
終了コード: 0=OK（警告のみ含む） 1=エラーあり
"""
import json, os, re, sys, zipfile, io, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIO_OK = (".m4a", ".mp3", ".aac", ".wav", ".caf")
AUDIO_ALL = AUDIO_OK + (".ogg",)

def load_schema(name):
    for d in (ROOT, HERE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    return None

def validator(name):
    try:
        import jsonschema
    except ImportError:
        return None
    s = load_schema(name)
    return jsonschema.Draft7Validator(s) if s else None

def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

class Report:
    def __init__(self): self.errors, self.warns = [], []
    def err(self, m): self.errors.append(m)
    def warn(self, m): self.warns.append(m)

def schema_errors(v, doc):
    if not v: return []
    out = []
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in e.absolute_path) or "(最上位)"
        out.append(f"{path}: {e.message[:160]}")
    return out

def check(files, rep):
    """files: {相対パス: bytes}。manifest を返す（自動生成した場合も）。"""
    vm, vc = validator("manifest.schema.json"), validator("manji.schema.json")
    if vm is None or vc is None:
        rep.warn("jsonschema が無いかスキーマが見つからないため、スキーマ検査を省略しました（pip install jsonschema）")
    names = [n for n in files if not re.search(r"(^|/)(__MACOSX/|\._|\.DS_Store$)", n)]
    if "manifest.json" in files:
        try:
            man = json.loads(files["manifest.json"].decode("utf-8-sig"))
        except Exception as e:
            rep.err(f"manifest.json が JSON として読めません: {e}"); return None
        for m in schema_errors(vm, man): rep.err("manifest.json " + m)
    else:
        chs = sorted([n for n in names if n.lower().endswith(".manji")], key=natural_key)
        if not chs: rep.err("manifest.json も .manji ファイルもありません"); return None
        man = {"manji_archive": "1.0", "title": "", "chapters": []}
        for n in chs:
            try: t = json.loads(files[n].decode("utf-8-sig")).get("title", "")
            except Exception: t = ""
            man["chapters"].append({"file": n, "title": t or os.path.splitext(os.path.basename(n))[0]})
        man["title"] = man["chapters"][0]["title"]
        rep.warn("manifest.json が無いので、.manji を名前順に並べて自動生成しました")
    cast = man.get("cast") or {}
    assets = man.get("assets") or {}
    for kind in ("bgm", "se"):
        for aid, path in (assets.get(kind) or {}).items():
            if path not in files: rep.err(f"assets.{kind}.{aid}: ファイル「{path}」がありません")
            elif path.lower().endswith(".ogg"): rep.warn(f"assets.{kind}.{aid}: ogg は iPhone Safari で再生できません。m4a/mp3 を推奨")
            elif not path.lower().endswith(AUDIO_OK): rep.warn(f"assets.{kind}.{aid}: 対応外の拡張子かもしれません: {path}")
    used_assets = set()
    for i, ch in enumerate(man.get("chapters") or []):
        f = ch.get("file") if isinstance(ch, dict) else ch
        tag = f"第{i+1}章({f})"
        if f not in files: rep.err(f"{tag}: ファイルがありません"); continue
        try: doc = json.loads(files[f].decode("utf-8-sig"))
        except Exception as e: rep.err(f"{tag}: JSON として読めません: {e}"); continue
        for m in schema_errors(vc, doc): rep.err(f"{tag} " + m)
        merged = dict(cast); merged.update(doc.get("cast") or {})
        for j, e in enumerate(doc.get("events") or []):
            if not isinstance(e, dict): continue
            if e.get("who") is not None and e["who"] not in merged:
                rep.err(f"{tag} イベント#{j+1}: who「{e['who']}」が cast（章と manifest のどちらにも）にいません")
            se = e.get("se")
            if isinstance(se, str) and se.startswith("asset:"):
                used_assets.add(("se", se[6:]))
                if se[6:] not in (assets.get("se") or {}): rep.err(f"{tag} イベント#{j+1}: {se} が manifest の assets.se にありません")
            if e.get("type") == "fx" and e.get("fx") == "bgm" and str(e.get("preset", "")).startswith("asset:"):
                aid = e["preset"][6:]; used_assets.add(("bgm", aid))
                if aid not in (assets.get("bgm") or {}): rep.err(f"{tag} イベント#{j+1}: {e['preset']} が manifest の assets.bgm にありません")
    for kind in ("bgm", "se"):
        for aid in (assets.get(kind) or {}):
            if (kind, aid) not in used_assets: rep.warn(f"assets.{kind}.{aid} はどの章でも使われていません")
    listed = {c.get("file") for c in man.get("chapters") or [] if isinstance(c, dict)}
    for n in names:
        if n.lower().endswith(".manji") and n not in listed: rep.warn(f"{n} は manifest.json の chapters に入っていません（再生されません）")
    return man

def read_folder(folder):
    files = {}
    for root, _, fs in os.walk(folder):
        for f in fs:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            if re.search(r"(^|/)(\.DS_Store|\._)", rel): continue
            files[rel] = open(full, "rb").read()
    return files

def pack(files, man, out):
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("manifest.json"), json.dumps(man, ensure_ascii=False, indent=1).encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        for n in sorted(files, key=natural_key):
            if n == "manifest.json": continue
            comp = zipfile.ZIP_STORED if n.lower().endswith(AUDIO_ALL) else zipfile.ZIP_DEFLATED
            zi = zipfile.ZipInfo(n); zi.compress_type = comp
            z.writestr(zi, files[n], compress_type=comp, compresslevel=9 if comp == zipfile.ZIP_DEFLATED else None)

def main():
    ap = argparse.ArgumentParser(description="漫字アーカイブ(.manjiz)の作成・検査")
    ap.add_argument("src"); ap.add_argument("-o", "--out"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(); rep = Report()
    if a.check or os.path.isfile(a.src):
        with zipfile.ZipFile(a.src) as z:
            names = z.namelist()
            mf = sorted([n for n in names if n.endswith("manifest.json")], key=len)
            base = mf[0][:-len("manifest.json")] if mf else ""
            files = {n[len(base):]: z.read(n) for n in names if n.startswith(base) and not n.endswith("/")}
        man = check(files, rep); out = None
    else:
        files = read_folder(a.src); man = check(files, rep)
        out = a.out or (os.path.basename(os.path.normpath(a.src)) + ".manjiz")
        if man is not None and not rep.errors: pack(files, man, out)
    for w in rep.warns: print("注意:", w)
    for e in rep.errors: print("エラー:", e)
    raw = sum(len(b) for b in files.values())
    if out and not rep.errors:
        print(f"OK: {out}  章 {len(man['chapters'])}  元の合計 {raw:,} バイト → {os.path.getsize(out):,} バイト")
    elif not rep.errors:
        print(f"OK: 章 {len(man['chapters'])}  展開後の合計 {raw:,} バイト")
    sys.exit(1 if rep.errors else 0)

if __name__ == "__main__":
    main()
