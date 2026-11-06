# 漫字（まんじ）エンジン v3 — 台本の書き方

自動で再生される「漫字」用のエンジンです。黒い舞台にセリフの吹き出しが現れ、下の窓に地の文が流れます。
v2 では、スーパーファミコン時代の画面演出（フェード、色演算、ラスター、ウィンドウ、Mode7風、多重スクロール、天候、チップチューンBGM など）を一通り使えるようにしました。

- エンジン本体：`manji.js`（プレーンな ES5、Canvas 2D、画像素材なし）
- 見本：`demo.html`（全演出のデモリール、約2分半）
- ひな形：`template.html`（これをコピーして台本を書く）
- 1ファイル化ツール：`inline.py`

動作条件：iPhone 11 / iOS Safari を基準にしています。DPR は最大2、時計は `setInterval` と `Date.now()`、エラーはページ上に表示、効果音とBGMは初期状態でオフです。

---

## 1. いちばん簡単な台本

```html
<div id="manji"></div>
<script src="manji.js"></script>
<script>
Manji.run({
  title: "漫字：はじめての一本",
  script: [
    { type: "fx", fx: "fadein", dur: 1500 },
    { type: "narr", text: "雨の夜だった。", wait: 500 },
    { type: "say", speaker: "left", text: "「傘、ある？」", wait: 2500, dur: 2500 },
    { type: "say", speaker: "right", text: "「……ない」", wait: 2200, dur: 2000, size: 16 },
    { type: "se", text: "ザーッ……", note: "雨音", wait: 1500, dur: 3000, se: "rain" }
  ]
});
</script>
```

`template.html` をコピーしてそのまま書き換えるのがおすすめです。

### 公開用に1ファイルにまとめる

```
python3 inline.py 自分の台本.html 公開用.html
```

`<script src="manji.js"></script>` の行がエンジンの中身に置き換わり、そのファイルひとつで動きます。

---

## 2. 時間の決まり方（いちばん大事）

| 項目 | 意味 |
|---|---|
| `wait` | **直前のイベントが始まってから**何ミリ秒後に始めるか。`0` なら同時。 |
| `dur` | 表示している時間（ミリ秒）。演出（fx）では「変化にかける時間」。 |
| `delay` | このイベントだけ遅らせる。**後ろのイベントの時刻は変わらない**。 |

- 1000 ミリ秒 ＝ 1 秒です。
- 地の文で `dur` を省くと、次の地の文が出るまで残ります。
- `Manji.run({ tempo: 1.2 })` で、全体の `wait` と `dur` をまとめて 1.2 倍にできます。

---

## 3. 全体設定 `Manji.run({...})`

| 設定 | 例 | 説明 |
|---|---|---|
| `title` | `"漫字：四月の朝"` | 開演前の画面に出る題名 |
| `subtitle` | `"▶ タップで開演"` | 題名の下の小さな案内 |
| `endText` | `"— 終 —"` | 最後に出る文字。`"……"` なども可 |
| `script` | `[ ... ]` | イベントの配列（下で説明） |
| `characters` | 下の例 | 登場人物のプリセット |
| `slots` | `{ kitchen: {x:0.2, y:0.3} }` | 自分で名前を付けた立ち位置 |
| `charMs` | `75` | 地の文の文字送り（1文字あたりのミリ秒） |
| `tempo` | `1` | 全体の速さの倍率（大きいほどゆっくり） |
| `endHold` | `4000` | 終わってから止まるまでの時間 |
| `showNames` | `true` | 名前札を出すかどうか |
| `glow` | `true` | 黒背景の中央のかすかな明かり |
| `window` | `true` | `false` で地の文の窓をなくし、舞台全体を使う |
| `bgmPresets` | `{...}` | 自作のBGMパターン（10章） |

### 登場人物プリセット `characters`

```js
characters: {
  "結衣": { side: "right", slot: "right", color: "#f0a8c0" },
  "美智子": { side: "left", slot: { x: 0.22, y: 0.3 }, color: "#ffd84a", showName: false }
}
```

セリフに `who: "結衣"` と書くと、吹き出しの向き（`side`）、立ち位置（`slot`）、名前札と枠の色（`color`）が自動で入ります。
`showName: false` にすると、名前札を出さず色だけ付けます。

### 立ち位置

`pos` には次のどちらかを書きます。

- 名前：`center`、`left`、`right`、`near`（下中央・手前）、`top`、`bottom`、`tl`、`tr`、`bl`、`br`（四隅）、`seC`、`seL`、`seR`（効果音用の下段）
- 数値：`{ x: 0.5, y: 0.3 }`。0〜1 の割合で、y は窓より上の舞台を基準にします。

---

## 4. イベントの種類

| type | 別名 | 中身 |
|---|---|---|
| `narr` | `description`、`text` | 地の文（下の窓） |
| `say` | `dialogue` | セリフの吹き出し |
| `think` | — | 心の声（点線の吹き出し） |
| `shard` | — | 漂ってほどける文字の断片 |
| `se` | — | 効果音の文字（斜体の小さな字） |
| `impact` | — | 漫画風の大きな擬音（ズームで飛び出す） |
| `caption` | — | 左上のテロップ |
| `fx` | — | 画面演出（5章以降） |

### 共通の項目

`text`、`wait`、`dur`、`delay`、`pos`、`size`（文字の大きさ）、`se`（鳴らす効果音、9章）

### `narr`（地の文）

```js
{ type: "narr", text: "四月の朝は、まだ少し肌寒い。", wait: 1000 }
{ type: "narr", text: "夢の中の言葉。", color: "#f4bccf", wait: 3000 }   // 文字色を変える
{ type: "narr", text: "早口で一気に。", speed: 20, wait: 2000 }          // 1文字20ミリ秒
```

### `say`（セリフ）

```js
{ type: "say", who: "結衣", text: "「おはよう」", wait: 2000, dur: 2600 }
{ type: "say", speaker: "left", pos: { x: 0.2, y: 0.3 }, text: "「……うん」", size: 16, wait: 3000, dur: 2400 }
```

| 項目 | 値 |
|---|---|
| `speaker` | `left`、`right`（しっぽの向き）、`center`（しっぽなし） |
| `eff` | `none`（ふわっと）、`pop`（弾む）、`zoom`（ゼロから拡大）、`bounce`（落ちて弾む）、`shake`（震え）、`big`（太字・爆発型） |
| `name` / `nameColor` | 名前札の文字と色（`who` を使えば自動で入る） |
| `color` | 文字色 |
| `bubble` | 吹き出しの色（例 `"#fff4d0"`） |
| `speed` | 文字送り。省くと、13文字以上のときだけ1文字40ミリ秒 |

### `think`（心の声）と `shard`（断片）

```js
{ type: "think", who: "結衣", text: "（それなのに、目が離せない）", size: 15, wait: 3000, dur: 3600 }
{ type: "shard", text: "どこ……？", pos: { x: 0.7, y: 0.2 }, wait: 900, dur: 2600 }
```

### `se`（効果音の文字）

```js
{ type: "se", text: "トン、トン、トン", note: "階段を下りる", pos: "seC", wait: 1000, dur: 2600, se: "steps" }
{ type: "se", text: "コツ、コツ", drift: "approach", wait: 1000, dur: 3000 }   // 近づく（leave で遠ざかる）
```

### `impact`（大きな擬音）

```js
{ type: "impact", text: "ドーン！", pos: { x: 0.5, y: 0.4 }, size: 70, dur: 1700, se: "impact" }
```

ほかに `color`（初期値は黄）、`stroke`（縁どりの色）、`rot`（傾き、度。初期値 −6）、`lines: false`（集中線を消す）が使えます。
画面揺れやフラッシュと組み合わせると効果的です（6章）。

`band: true` にすると、飛び出す擬音ではなく、斜めの白い帯の上に文字を並べます。帯の色は `bandColor`（初期値 `#ffffff`）、傾きは `rot`（このとき初期値 −14 度）です。文字は帯の長さに収まるよう縮み、帯は舞台の外へ出ません。地の文の窓は帯より手前に描かれます。

```js
{ type: "impact", text: "{c:#ff6b9a}キラ{/c}{c:#ffd84a}ッ！{/c}", band: true, rot: -14, dur: 1400 }
```

### `caption`（テロップ）

```js
{ type: "caption", text: "第一話　四月の朝", dur: 3000 }
{ type: "caption", text: "翌朝", pos: "bottom", color: "#7fb4ff" }
```

---

## 5. 文字の装飾（インライン記法）

`text` の中に `{…}` で書きます。地の文・セリフ・心の声・擬音・効果音のどれでも使えます。

| 書き方 | 効果 |
|---|---|
| `{c:#ff6b6b}赤{/c}` | 文字色。`red`、`pink`、`rose`、`blue`、`sky`、`green`、`yellow`、`gold`、`orange`、`purple`、`gray`、`white`、`cream` も使える |
| `{s:1.5}大きく{/s}` | 文字の大きさ（倍率） |
| `{b}太字{/b}` | 太字 |
| `{w}ゆらゆら{/w}` | 波打つ |
| `{sh}ぶるぶる{/sh}` | 震える |
| `{tr}おののき{/tr}` | 小刻みに震える |
| `{r:蕎麦|そば}` | ルビ（ふりがな） |
| `{p:800}` | ここで 0.8 秒止める（間） |
| `{sp:150}ゆっくり{/sp}` | この部分の文字送りを1文字150ミリ秒にする |
| `{{` | 「{」そのもの |

例：

```
"「{c:yellow}{b}{s:1.4}待って{/s}{/b}{/c}……{p:600}{tr}行かないで{/tr}」"
```

---

## 6. 画面演出 `type: "fx"`

`fx` で種類を指定します。「残る演出」（色演算、カメラ、背景、天候など）は、次に同じ種類の fx を書くまで効き続けます。`dur` はそこまでの変化にかける時間です。

### フェード

```js
{ type: "fx", fx: "fadeout", color: "#000000", dur: 1000 }   // 色へ溶ける（初期値は黒）
{ type: "fx", fx: "fadein", dur: 1000 }                       // 戻す
{ type: "fx", fx: "fade", to: 0.5, color: "#ffffff", dur: 800 } // 途中の濃さで止める
{ type: "fx", fx: "fade", to: 1, dur: 0, wait: 0 }            // 最初を真っ暗にしておく（冒頭に）
```

### フラッシュ・画面揺れ・稲光

```js
{ type: "fx", fx: "flash", color: "#ffffff", strength: 0.9, dur: 400 }
{ type: "fx", fx: "shake", power: 10, dur: 600 }    // power は揺れの強さ
{ type: "fx", fx: "lightning", x: 0.6, dur: 900 }   // 稲妻＋二度光る＋揺れ（効果音オンなら雷鳴）
```

### 色演算（スーファミの加算・減算）

```js
{ type: "fx", fx: "tint", preset: "sunset", dur: 2000 }
{ type: "fx", fx: "tint", add: "#300010", sub: "#002020", amount: 1, dur: 1500 }
{ type: "fx", fx: "tint", preset: "none", dur: 1000 }   // 元に戻す
{ type: "fx", fx: "bright", level: -0.4, dur: 1000 }    // −1 で真っ暗、＋1 で真っ白、0 で元
```

- プリセット：`sunset`（夕焼け）、`night`（夜）、`dream`（夢）、`horror`（ホラーの赤）、`sepia`、`cold`、`none`
- `add` は色を足し（明るくなる）、`sub` は色を引きます（その色が抜ける）。`amount` は強さです。
- 色演算は舞台（背景・吹き出し）にかかり、地の文の窓は読みやすいまま残ります。

### ラスター（走査線ごとの演出）

```js
{ type: "fx", fx: "wave", amp: 8, freq: 3, speed: 0.6, dur: 1500 }  // 陽炎・夢・酔い・水中のゆらぎ
{ type: "fx", fx: "wave", amp: 0, dur: 1000 }                       // 止める
```

`amp` は揺れ幅、`freq` は画面の縦に何回波打つか、`speed` は1秒に何回うねるかです。

### モザイク

```js
{ type: "fx", fx: "mosaic", size: 24, dur: 900 }   // 粗くする（size は1マスの大きさ）
{ type: "fx", fx: "mosaic", size: 1, dur: 900 }    // 戻す
```

あいだに `bg` を変えると、スーファミ風の場面転換になります。

### レターボックス

```js
{ type: "fx", fx: "letterbox", size: 0.12, dur: 900 }   // 上に黒帯（下側は描かない）
{ type: "fx", fx: "letterbox", size: 0, dur: 800 }
```

黒帯は画面の上だけです。下側に帯を描くと、文字を大きくしたときの地の文や吹き出しに重なるため、下側は描きません。

### ウィンドウ（アイリス・ワイプ・スポットライト）

```js
{ type: "fx", fx: "iris", dir: "out", x: 0.5, y: 0.5, dur: 1200 }   // 丸く閉じる
{ type: "fx", fx: "iris", dir: "in", dur: 1200 }                    // 丸く開く
{ type: "fx", fx: "wipe", shape: "diamond", dir: "out", dur: 900 }
{ type: "fx", fx: "wipe", shape: "blinds", count: 10, dir: "in", dur: 900 }
{ type: "fx", fx: "spot", who: "結衣", r: 0.25, dim: 0.85, dur: 700 } // 一人を照らす
{ type: "fx", fx: "spot", dim: 0, dur: 600 }                         // 消す
```

- `shape`：`circle`、`diamond`（ひし形）、`blinds`（横ブラインド）、`vblinds`（縦）、`scan`（走査線）、`left`、`right`
- `color`：ワイプの色（初期値は黒）
- `spot` は `who`、`at`（立ち位置の名前）、`x` と `y` のどれかで位置を指定します。`r` は半径（画面幅に対する割合）です。

### カメラ（パン・ズーム・回転）

```js
{ type: "fx", fx: "camera", who: "熊", zoom: 1.4, dur: 1200 }   // 話し手に寄る
{ type: "fx", fx: "camera", x: 0.3, y: 0.6, zoom: 1.2, rot: 10, dur: 2000 }
{ type: "fx", fx: "camera", reset: true, dur: 1000 }            // 元に戻す
```

### 背景（グラデーション空・多重スクロール・Mode7風の床）

```js
{ type: "fx", fx: "bg", bg: "skyline", sky: "night", scroll: 40, dur: 1200 }
{ type: "fx", fx: "bg", bg: "floor", c1: "#5a2a6a", c2: "#12061a", sky: "#05020a", spin: 25, speed: 60, dur: 800 }
{ type: "fx", fx: "bg", bg: "none", dur: 1000 }   // 黒に戻す
```

- `bg`：`sky`（空だけ）、`skyline`（ビル街）、`town`（家並みと電柱）、`hills`（山並み）、`sea`（海）、`room`（部屋と窓）、`floor`（Mode7風の床）、`none`
- `sky`：`day`、`sunset`、`night`（星つき）、`dawn`、`dusk`、`dream`、`horror`、`none`、または `"#203040"` のような色
- `scroll`：横に流れる速さ。手前の層ほど速く動きます（多重スクロール）。
- `dim: 0.4`：背景を暗くします。`stars: true`：星を出します。
- `dur`：前の背景からの切り替えにかける時間です。
- `floor` の設定：`c1` と `c2` は市松模様の2色、`spin` は1秒に回る角度、`speed` は前へ進む速さ、`horizon` は地平線の高さ（0〜1）です。
- 「夢に落ちていく」場面は、`floor` に `camera` の `rot` と `zoom` を組み合わせるのがおすすめです。

### 天候

```js
{ type: "fx", fx: "weather", kind: "rain", amount: 1, wind: 0.3, dur: 1200 }
{ type: "fx", fx: "weather", kind: "rain", amount: 0, dur: 1000 }   // やむ
{ type: "fx", fx: "weather", kind: "clear", dur: 1000 }             // すべて消す
```

- `kind`：`rain`、`snow`、`petals`（花びら）、`dust`（光の粒）、`fog`（霧）、`clear`
- 種類ごとに別々に効くので、たとえば `dust` と `fog` を同時に出せます。
- 雨の音は、効果音がオンのときだけ自動で鳴ります。

### BGM

```js
{ type: "fx", fx: "bgm", preset: "daily" }   // 曲名は下の表、none で止める
```

---

| preset | 曲名 | 使いどころ | 1ループ |
|---|---|---|---|
| `daily` | 日常・おだやか | ふだんの場面、会話、のんびり | 約83秒 |
| `morning` | 朝・学校 | 朝、登校、明るい始まり | 約64秒 |
| `nostalgic` | なつかしい・回想 | 思い出、回想、夕暮れ | 約60秒 |
| `sad` | かなしい | 別れ、涙、喪失 | 約87秒 |
| `tender` | やさしい・ときめき | 恋心、やさしさ、あたたかい場面 | 約101秒 |
| `tense` | 緊迫 | 危機、追跡、急ぐ場面 | 約58秒 |
| `horror` | ホラー・不気味 | 怪談、恐怖、闇 | 約128秒 |
| `drone` | 不穏・重低音 | 不穏な気配、嵐の前、底知れぬもの | 約77秒 |
| `battle` | 戦い・アクション | 対決、鬼退治、アクション | 約51秒 |
| `rakugo` | 落語・軽妙（和風） | 落語、とぼけた会話、江戸の町 | 約69秒 |
| `wa_solemn` | 和風・荘厳 | 寺、神社、武家、厳かな場面 | 約128秒 |
| `mukashi` | 昔話・おとぎ話 | 昔話、童話、むかしむかし | 約77秒 |
| `festive` | 祭り・にぎやか | 祭り、宴、勝利の凱旋 | 約55秒 |
| `mystery` | 謎・探偵 | 謎解き、怪しい人物、こっそり | 約80秒 |
| `ending` | エンディング | 結末、エピローグ、おしまい | 約91秒 |
| `manzai` | 漫才・出囃子 | 漫才の登場、コント、ドタバタ | 約48秒 |
| `jingle` | 出囃子ジングル（短め） | 漫才の幕開け・場面の区切り（明るく短い） | 約46秒 |
| `none` | — | BGMを止める | — |

旧名 `calm`→`daily`、`tension`→`tense`、`eerie`→`horror` もそのまま使えます。アーカイブ（.manjiz）では `asset:ID` で m4a/mp3 の BGM も鳴らせます。

**音源について（スーファミ相当）**：最大8音同時（足りないときは優先度の低い音を止めて譲る）、ADSR・フィルター付きの合成楽器、フィードバックエコー＋ローパス。
楽器：ストリングス、パッド、ピアノ、エレピ、ハープ、撥弦（pluck）、フルート、篠笛（fue）、ブラス、クワイア、オルガン、ベース、シンセベース、オルゴール、鐘（bell）、箏、三味線、琵琶、リード。
打楽器：キック、スネア、クラップ、ハイハット、和太鼓、締太鼓、鼓、ウッドブロック、心音 など。

**曲の選び方**：場面の気分が変わる所で `bgm` を切り替える（切り替えは自動でクロスフェード）。会話中心の漫才・落語本編は `none` か `rakugo` を小さめに、出囃子だけ `jingle`/`manzai`。怪談は `horror`→山場で `drone`、結末で `wa_solemn` や `ending`。

## 7. 効果音の種類（`se: "..."`）

| キー | 音 |
|---|---|
| `steps`、`walk` | 足音 |
| `door` | 扉 |
| `window` | 窓を開ける |
| `fusuma` | ふすま |
| `pour` | 注ぐ |
| `cup` | カップを置く |
| `rustle` | 衣ずれ |
| `wind` | 風 |
| `heart` | 鼓動 |
| `ring` | 耳鳴り |
| `signal` | 電子音 |
| `thunder` | 雷鳴 |
| `rain` | 雨（一度だけ） |
| `chime` | 鐘・チャイム |
| `impact` | ドーン |
| `kira` | キラッ |
| `dosa` | ドサッ |
| `biwa` | 琵琶 |
| `kane` | 寺の鐘 |
| `taiko` `dodon` | 和太鼓・ドドン |
| `tsukkomi` | ツッコミ（ペシッ） |
| `pon` | 鼓 |
| `boing` | ボヨーン |
| `jan` | ジャン！ |
| `mogu` | モグモグ |
| `bowl` | 器 |
| `coin`、`coin-soft` | 小銭 |
| `geta-in`、`geta-out` | 下駄 |

どれも電子音で合成しています。音声ファイルは使いません。

---

## 8. 演出の重ね方のコツ

- **同時に起こす**：`wait: 0` で並べます。例：`impact` → `shake` → `flash` をすべて `wait: 0` に。
- **場面転換**：`fadeout`、`mosaic`、`iris` などで閉じる → `bg` を変える → 開く。
- **間（ま）**：何も出さずに `wait` を長くとるのがいちばん効きます。セリフの中の `{p:…}` でも間を作れます。
- **読みやすさ**：色演算や暗転は舞台側だけにかかり、地の文の窓は常に読めます。暗い場面でも文字は白のままです。

---

## 9. 動作確認の小技

ページを開いて、ブラウザのコンソールで次を実行できます。

```js
__manji.seek(30000)   // 30秒の場面へ飛ぶ
__manji.st.speed = 4  // 4倍速
__manji.perf()        // 1フレームの描画時間（ミリ秒）
```

---

## 10. 上級：BGMを自作する

```js
Manji.run({
  bgmPresets: {
    mine: { bpm: 90, lead: [72, 0, 74, 0, 76, 0, 0, 0], bass: [48, 0, 0, 0, 43, 0, 0, 0], drum: [2, 0, 1, 0], leadVol: 0.02, bassVol: 0.07 }
  },
  script: [ { type: "fx", fx: "bgm", preset: "mine" } ]
});
```

- 数字は音の高さ（MIDIのノート番号、60 がド）、`0` は休みです。1マスは16分音符です。
- `lead` は矩形波、`bass` は三角波で鳴ります。
- `drum` の `1` はハイハット、`2` はキックです。

---

## 11. 漫字プレーヤー（player.html）と .manji / .manjiz

- `player.html` は1ファイルで動く再生アプリです。「漫字スクリプトを読み込む」から `.manji`（1話）か `.manjiz` / `.zip`（複数章のアーカイブ）を選びます。パソコンではドラッグ＆ドロップ、`player.html?src=<URL>` でも開けます。
- 形式の定義：`manji.schema.json`（章・単体の .manji）、`manifest.schema.json`（アーカイブの目次）。AI に書かせるときは `MANJI_AI_GUIDE.md` をそのまま渡します。
- 前回開いたファイルは端末内（IndexedDB）に保存し、章と再生位置も覚えます。

### アーカイブ（.manjiz）の中身

```
manifest.json            {"manji_archive":"1.0","title":…,"cast":{…},"chapters":[{"file":"chapters/01.manji","title":…}],"assets":{"bgm":{id:path},"se":{id:path}}}
chapters/01_xxx.manji    章ファイル（cast を省くと manifest の cast を引き継ぐ）
assets/xxx.m4a / .mp3    任意の音声（ogg は iPhone で鳴らないので m4a か mp3）
```

- manifest.json が無い zip は、中の .manji をファイル名の順に並べて章にします。
- 音声の参照：`"se":"asset:door"`、`{"type":"fx","fx":"bgm","preset":"asset:rain_theme"}`。読めない音は鳴らさずに続行します（注意欄に表示）。
- 外部音声は、効果音／BGM のチェックをオンにした最初のタップの後で読み込まれます（iOS の決まり）。メモリ節約のため、今の章と次の章で使う音だけを展開します。

### 作り方（パソコン）

```
python3 tools/pack_manji.py 作品フォルダ -o 作品.manjiz     # 検査して固める
python3 tools/pack_manji.py --check 作品.manjiz            # 既存のアーカイブを検査
```

### 作り方（iPhone）

「ファイル」アプリで manifest.json・chapters・assets を選ぶ →「…」→「圧縮」→ できた zip をそのまま、または名前を `.manjiz` に変えて読み込みます。

### 全画面（横向き）

再生欄の「⛶ 全画面（横向き）」で、黒い全画面に舞台を大きく出します。縦持ちのときは舞台を90度回して横向きに表示します。タップで「戻る・再生／一時停止・次の章」が出て、3秒で消えます。パソコンや iPad では本物の全画面表示を使います。設定は端末に記憶され、次から「再生」を押すと全画面になります。
iPhone では Safari の共有ボタン →「ホーム画面に追加」から開くと、アドレスバーのない、よりきれいな全画面になります（player.html に `apple-mobile-web-app-capable` と `viewport-fit=cover` を設定済み）。

### お気に入り・履歴

- 「漫字スクリプトを読み込む」の下の「★ お気に入り」「🕘 履歴」から、前に開いたスクリプトやアーカイブを、ファイルを選び直さずに開けます。見本ボタンや `?src=` で開いたものも履歴に入ります。
- 端末内（IndexedDB）にファイルの中身ごと保存します。同じ中身のファイルは1件にまとめます。題名・作者・種類（1話／全N章）・大きさ・最終日時（日本時間）・続きの位置（何章の何分何秒まで）も記録します。
- 各行の「▶ 続きから」「最初から」で開きます。「☆」でお気に入りに追加できます（読み込み後の情報欄にも ☆ があります）。お気に入りでは「名前を変更」で表示名を変えられます。
- 「削除」で1件ずつ、「お気に入り以外の履歴をすべて消す」でまとめて消せます（どちらも確認あり）。
- 履歴はおよそ30件・合計50MBまでです。超えると、お気に入り以外の古いものから自動で消えます。お気に入りは自動では消えません。
- プライベートブラウズなどで IndexedDB が使えないときは、題名と位置だけを localStorage に覚えます。開き直すときは同じファイルを選び直してください（続きの位置から再開します）。
- 以前の版の「前回のファイル」は、初回起動時に自動でこの履歴へ移します。

### サンプル作品（内蔵）

- 「漫字スクリプトを読み込む」の上に、サンプル作品のカードがあります。時そば、まんじゅうこわい、桃太郎、かぐや姫、坊っちゃん（全7話、原作の一〜三）、演出デモの6作品です。すべて player.html の中に入っているので、オフラインでも再生できます。
- カードをタップするとすぐに再生が始まり、履歴にも入ります（お気に入りにもできます）。
- 元のファイルは `samples/builtin/` にあり、一覧は `catalog.json` です。
- アーカイブの manifest.json に `"unit":"話"` と書くと、目次と題名カードが「第一章」ではなく「第一話」になります（坊っちゃんで使用）。


## 文字サイズ（v3）
`Manji.run({ textScale: 1.12 })` で初期値、`api.setTextScale(1.32)` で再生中に変更（0.7〜1.6）。プレーヤーでは「文字：標準」ボタン（全画面中も表示）で 小0.92／標準1.12／大1.32／特大1.55 を切り替え、localStorage `manji.fontSize` に保存。

## 長い文章のスクロール／ページ送り（v3.3）
枠に入りきらない地の文・吹き出しは、既定で上へなめらかにスクロール（1行あたり約0.22秒、窓の内側で切り抜き、上端は薄くぼかす）。
`settings: { narrationOverflow: "page" }` で作品全体をページ送りに、各イベントの `overflow: "page"` / `"scroll"` で個別に切り替え。
スクロール位置は再生時刻だけで決まるため、シークや文字サイズ変更をしても正しい位置に即座に合います。
