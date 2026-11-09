# 開発メモ — 仕様を変えるときのチェックリスト

漫字の「正しさ」は複数の場所に分かれて置かれている。1箇所だけ直すと必ずズレるので、仕様（`.manji` で書けること）を変えたら、このリストの該当欄を全部確認すること。

## 正しさの所在

| 場所 | 役割 |
|---|---|
| `docs/manji.schema.json` / `manifest.schema.json` | **厳密な形式の定義**（正）。台本が満たすべき形はここで決まる |
| `index.html` の `MANJI_RULES` | プレーヤー内蔵バリデーターの規則。スキーマと揃えるのが原則だが、**意図的に寛容**な部分がある（旧名の読み替え、数値文字列の受理、範囲外の丸め）。寛容さはバグではないので、スキーマに合わせて締めないこと |
| `index.html` のエンジン本体（`Manji.run`） | 再生の実装。書けることと実際に描けることはここで一致させる |
| `tools/pack_manji.py` | スキーマ駆動の検査＋独自の相互チェック（`who` が cast にいるか、`asset:` 参照が manifest にあるか）。項目の追加だけなら通常は変更不要。**相互チェックのルールが変わるときだけ**直す |
| `docs/MANJI_AI_GUIDE.md` / `docs/README_ja.md` | 人と AI が読む仕様書。実装と違うことが書いてあると、そのまま間違った台本が量産される |

## 共通（仕様を変えたら必ず）

- [ ] `docs/manji.schema.json`（アーカイブ関係なら `manifest.schema.json` も）
- [ ] `index.html` の `MANJI_RULES`（types / fx / SE / SLOTS の該当箇所）
- [ ] `index.html` のエンジン実装
- [ ] `docs/MANJI_AI_GUIDE.md` の対応する表
- [ ] `docs/README_ja.md` の対応する章
- [ ] 検証コマンド（末尾）をローカルで全部通す
- [ ] `manji_kit.zip` の差し替え要否を確認（末尾「キット」）

## 種類別

### fx（画面演出）を足す・変える

- [ ] エンジン：描画処理。残る演出なら `CH_DEF` / `FX_CH` / `makeTo` にチャンネル登録（時刻から純粋に計算できる形を守る。シークで破綻しないこと）
- [ ] `MANJI_RULES.fx` に、その fx で使える項目だけを登録（範囲・既定の考え方も揃える）
- [ ] スキーマ：`fx` イベントの項目定義
- [ ] ガイド7章の fx 表と README 6章に使い方を追加。「残る演出は戻し方まで」書く
- [ ] `samples/demo.manji` に見本を1つ入れる（演出デモは全演出の見本であること）

### イベント type / 項目を足す・変える

- [ ] エンジン：`normalize` の読み替えと描画、`byType` の振り分け
- [ ] `MANJI_RULES.types` に項目・必須（`_req`）・範囲を登録
- [ ] スキーマ：該当 type の `allOf` 定義（`additionalProperties: false` のため、登録漏れは即エラーになる）
- [ ] ガイド5章（type 一覧・項目詳細）と README 4章
- [ ] 旧名・別名を許すなら、ガイドには正名だけを書き、別名はバリデーター側だけに置く

### 効果音（se キー）を足す

- [ ] エンジン：`playSound` に合成処理（または `SE_MUSIC` に ManjiMusic の打楽器／楽器で定義）
- [ ] `MANJI_RULES.SE` の配列
- [ ] スキーマ：se の enum（**type ごとに複数箇所ある**ので全箇所検索して直す）
- [ ] ガイド5.3 の効果音キー一覧と README 7章の表

### BGM（preset）を足す

- [ ] `index.html` の音楽ブロック（`/*@@MUSIC_BEGIN@@*/`〜`/*@@MUSIC_END@@*/`）の `def({...})` で曲を定義。旧名を付けるなら `ALIAS` にも
- [ ] ガイド7.1 と README 6章の BGM 表（曲名・使いどころ・**1ループ秒数**。秒数は `ManjiMusic.list()` の値と合わせる）
- [ ] バリデーターとスキーマは preset 名を列挙していない（曲名は音楽ブロックが正）ので変更不要。ただし `bgmPresets` 自作形式を変える場合は別

### settings / cast の項目を足す・変える

- [ ] エンジン：`run` の初期値と、`toCfg` の受け渡しリスト（`settings` から cfg へコピーする項目名の一覧）に登録
- [ ] プレーヤー検証側の settings ルール（`index.html` の `validate` 内 `SR`。cast は `CR`）
- [ ] スキーマ：`settings` / `cast` の定義
- [ ] ガイド4章（settings）と3章（cast）、README 3章

### 内蔵サンプルを足す・差し替える

- [ ] 元ファイルを `samples/builtin/`（単独作は `samples/`）に置く
- [ ] `samples/builtin/catalog.json` のメタ（title / size / events など）を実ファイルに合わせる
- [ ] `index.html` の `builtinData` に埋め込む（`data` はファイル内容の base64、メタは **catalog と完全一致**させる）
- [ ] `.manjiz` の差し替えなら pack 検査も（検証コマンドに含まれる）

### プレーヤー UI / 本体だけを変える（仕様変更なし）

- [ ] バージョンを上げる：`index.html` の `Manji.version` と、エンジン冒頭コメントの版表記（2箇所を揃える）
- [ ] キットの player 差し替え（下記）。これを忘れると CI（validate）が落ちる

## キット（manji_kit.zip）

- キット内のファイルは、リポジトリ側に対応物があるものは**すべてバイト単位で一致**が必須（CI で検査される）。`index.html` を変えたら player を、ドキュメントや `tools/`、`samples/` を変えたら対応するキット側コピーも差し替える
  - 対応表：`player.html`＝`index.html`、`README_ja.md`／`MANJI_AI_GUIDE.md`／`*.schema.json`＝`docs/` 配下、それ以外は同名パス
- キットにだけあるファイル（生成スクリプト `tools/gen_*.py`、サンプルのソース一式 `samples/*_src/`）はリポジトリ側に無いので CI の対象外。消したり移したりするときはキット側の扱いも決める

## 検証コマンド（push 前に全部通す）

CI（`.github/workflows/validate.yml`）と同じ内容：

```sh
pip install jsonschema
for f in samples/builtin/*.manjiz samples/manji_sample_archive.manjiz; do
  python3 tools/pack_manji.py --check "$f"
done
for f in samples/builtin/*.manji samples/*.manji; do
  python3 -m jsonschema -i "$f" docs/manji.schema.json
done
# catalog と埋め込みメタの一致、バージョン表記2箇所の一致、キット内ファイルの一致は validate.yml の後半3ステップを参照
```
