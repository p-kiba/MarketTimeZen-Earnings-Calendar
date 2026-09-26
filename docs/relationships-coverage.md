# 収録範囲と根拠

> この文書は以前の実装時点の記録です。現在の件数・SEC接続状況・金額判定は[最新報告](relationships-peer-update.md)を参照してください。

検証日：2026-09-25〜26。**収集対象設定はpilot 20社、公開用には28社・33関係、金額付き11案件（12の金額表示）**です。S&P 500全構成、20社全提出資料、全米企業の全取引を調査済みという意味ではありません。確認待ちの一般抽出候補4件は公開していません。

追加の関係は[大型案件の収録記録](relationships-investor-update.md)に記載。以下の3資料・6関係は初回検証分です。

## 一次資料の実証

| 公式資料 | 確認できた内容 | 本実装の扱い |
|---|---|---|
| [IBM: Red Hat acquisition completion](https://www.ibm.com/investor/news/ibm-completes-acquisition-of-red-hat) | 本文の2019-07-09買収完了、total equity value approximately USD 34 billion | IBM→Red Hat買収1件、約340億米ドル、当初総額・株式価値。100億〜500億ドル未満の金色。2019年の完了事実で、現在の売上/取引額ではない |
| [Anthropic: Microsoft / NVIDIA partnerships](https://www.anthropic.com/news/microsoft-nvidia-anthropic-announce-strategic-partnerships) | 2025-11-18、NVIDIAとAnthropicの技術提携、Microsoftとの提携拡大、2社からの投資コミットメント発表 | 提携2件、投資発表2件。資料の「$」や上限値をUSD確定額として着色しない。金額は確認待ち |
| [Anthropic: Amazon Trainium](https://www.anthropic.com/news/anthropic-amazon-trainium) | 2024-11-22、Amazonからの新たな投資と累計投資の説明 | Amazon→Anthropic投資発表1件。新規額と累計額を足さない。通貨/法的対象範囲を確認できない金額は公開しない |

3URLを実際にHTTP取得し、ローカルcacheの本文・locator・hashを照合しています。IBMページのmeta日付は本文の歴史的発表日と異なったため、表示された2019-07-09を採用。これは汎用日付抽出ではなく、この資料の限定ルールでの補正です。

法人名・上場銘柄は [IBM FAQ](https://www.ibm.com/investor/help/general-faqs)、[NVIDIA FAQ](https://investor.nvidia.com/investor-resources/faqs/)、[Amazon FAQ](https://ir.aboutamazon.com/faqs/)、[Microsoft Board](https://www.microsoft.com/en-us/investor/corporate-governance/board-of-directors) も照合。今回確認できないCIKや国はnullのままです。Anthropic/Red Hatの現在の上場状態や正式法人名を推測しません。Red HatをIBMと同一法人IDにしていません。AWSブランドをAmazon法人と無条件で統合していません。

一般候補と資料限定ルールの重複候補は候補側のまま残っています。今後担当者が同一案件として照合して却下/リンクする対象で、二重公開していません。

## 取得経路の確認範囲

- 初回の公式IR3資料のURL直接取得：成功3 / 対象3。本文の事実と照合した6主張、金額1件を記録。人手評価による精度・再現率の母集団ではありません。
- 公式IR一覧：Anthropic 10URL、IBM 23URLを検出。重複と本文取得済みのURLを除いた32URLは未取得キューに保存（一覧の件数と関係の件数は別）。robots.txtを含む経路を確認済み。
- SEC：連絡先未設定。API履歴・改訂・添付・レート処理はfixture検証のみで、今回ライブ取得0件。実連絡先を設定してresolve-universe/backfillを行う必要があります。
- 画像PDF/OCR、暗号化PDF、JavaScriptのみのページ、深い子会社階層、匿名当事者、意味的な資料間重複判定：自動対応していません。
- 約20社の横断評価表、人による見落とし比較、一般文書の正確性、発表→検出→確認→公開遅延：未測定です。既知の少数資料のみを実証した段階です。

## 金額の色と表示制限

USDが明記され、金額・意味が承認済み、exact/approximately、当初総額または改定総額、非条件付きと確認された単独の取引額に適用します。金額の大きさは株価への影響や重要性の推定ではありません。

| 表示帯 | 色 |
|---|---|
| 1億米ドル未満 | 灰色 |
| 1億〜10億米ドル未満 | 水色 |
| 10億〜100億米ドル未満 | 紫 |
| 100億〜500億米ドル未満 | 金 |
| 500億米ドル以上 | 赤 |

Lv番号は内部実装用でUIには出しません。通貨換算、年額化、オプション加算、複数契約の合算はしません。複数関係をまとめた線は中立色＋関係件数で、内訳を開けます。金額未記載でも確認済み関係は表示します。

## 大量表示の検証データ

`python tests/relationships/build_demo.py` は `.cache/relationships-demo/` のみに架空企業・架空関係を生成します。必ずTEST FIXTURE帯を表示し、実在企業のロゴ/銘柄を割り当てません。初期30ノードと80社・103関係への展開、さらに114社・254関係への展開を実ブラウザーで確認。テストデータはマスタにも公開artifactにも混ぜません。UIの対応規模と、実在資料の収録件数を混同しないでください。

2026-09-26追記：テキストPDFのページ根拠に対応。最新の金額・通貨の精査範囲は[補完報告](relationships-amount-review-2026-09-26.md)を参照。
