# 実装・検証結果

> この文書は以前の実装時点の記録です。現在の件数・SEC接続状況・金額判定は[最新報告](relationships-peer-update.md)を参照してください。

確認日：2026-09-26 JST。ローカル実装と公開用静的成果物を用意しました。**本番へのcommit/push・workflow実行・Pages設定変更・デプロイはしていません。** 一時ローカルgitリポジトリを使う競合テストは実施しています。

## 実装範囲

- Step A：既存生成器・共有JS・iOSメッセージ形式・35既存テスト・既存Actionsを調査。スキーマ、公開ゲート、独立map.html、テスト用大規模マップを実装。
- Step B：SEC submissionsの新着/履歴/改訂・EX-10/21/99添付キュー、公式IR RSS/Atom/HTML、Decimal金額候補、企業照合、review/approve/reject/withdraw/link-duplicate、原文hashでの再確認を実装。15の関係証拠ソースから33公開関係を検証。SECライブ取得、20社横断評価は未実施。
- Step C：生成元から消えない機能ナビ、独立検索入口、URL引継ぎ、既存favorites bridge、決算データ再利用、英日辞書、ロゴ、±ズーム、初期30/展開150社、一覧、詳細、フィルターを実装。
- Step D：耐久キュー、原文cache分離、cron、公開版/hash検証、旧版保持、競合時停止、allowlist artifact、単一Pages所有者、ロールバック、運用文書を実装。Actions/Pagesは無効のまま。実際の公開環境は未実証。

## 自動検証

| 実行 | 結果 |
|---|---|
| `python -m unittest discover -s tests -p 'test_*.py' -v` | 既存35件成功 |
| `python -m pytest tests/relationships -q` | 82件成功（ローカル。うち原文キャッシュ統合テスト1件はCIでキャッシュがなければskip） |
| `node tests/relationships/browser/unit.mjs` | 20件成功 |
| `validate-config / validate-public` | 成功。公開JSON64ファイルの参照・hash・承認・fixture排除を検証 |
| 両HTML生成器の `--html-only` | 成功。既存決算データを変更せず再生成 |
| `scripts/stage-site.py` | 成功。米国/日本カレンダー・マップ同梱、候補・テスト・設定・raw cache除外 |
| Python compile、workflow YAML parse、git diff --check、pip check | 成功 |

合計137件。ローカルPython 3.10、Node 16で確認。CIにはUbuntu 24.04 / Python 3.10 / Node 22を固定しましたが、このランナー構成での実行は未実施です。Cytoscape 3.34.3は実取得したnpm配布物を同梱し、今回の実ブラウザーで使用しています。

## 受け入れ項目の証拠と限界

| ID | 確認範囲 |
|---|---|
| T01–T02 | 既存35回帰テスト＋実画面でMonthly/Weekly、月移動、検索、NY→Tokyo、両市場から入口、HTML再生成 |
| T03 | Node vmでbridgeの `{symbol}` と未実装時の無例外を確認。ネイティブ受信は未確認 |
| T04–T05 | URL安全性・favorites/month、銘柄重複の単一化、完全一致検索、同名保持、複数株式クラス、記号入り銘柄 |
| T06 | 初期30/170社、展開150/170社の上限、一覧30→60件、同じフィルター/件数を実画面で確認 |
| T07–T08 | 親会社・短い略称・匿名当事者を無条件で同一視しない。サービス方向と支払者フィールド分離をfixture確認 |
| T09–T14 | 11.6 billion→116億米ドル、9 billion別オプション、7年開始未定、null、EUR/$、範囲、capex/loan/revenue/per-share除外 |
| T15–T16 | 複数当事者の共通総額を自動複製しない、warrantを買収済みと分類しないfixture。後者はテストで見つけて修正 |
| T17–T20 | 日付/検出時刻分離、同一再実行、手動duplicate-link、改定総額の旧履歴保持、原文変更の再確認。資料間の意味的重複判定は担当者が行う |
| T21–T22 | SEC列形式/履歴/改訂/issuer CIK、過去キュー添付の再開、429/503/403、共有SEC rate gateをfixture確認 |
| T23–T24 | 承認外/fixture/不正参照/stale hashを拒否、関係承認と金額承認分離、却下を再抽出で保持 |
| T25–T26 | 一社/IR失敗、空・破損、異常削除/候補数で旧版保持。Nodeで新build不完全→前版と完全オフラインキャッシュ、混在拒否 |
| T27 | changed除外、unconfirmed保持、New York/Tokyoの日付、当日以降・対象外/未上場/取得期間外/未収録をテスト |
| T28 | In-app Browserで375px、812×375、768×1024、1440×1024、シート、Tab循環/Escape、検索HTML非実行、危険URL拒否。VoiceOver実機は未確認 |
| T29 | 一時bare repoで「先に他ジョブが更新」を再現しremote上書き拒否、allowlist以外をcommitしないことをテスト。実GitHub同時実行は未確認 |
| T30–T31 | 公式IR3資料を実取得、IBMの約340億米ドルと根拠を実画面で照合。Anthropic/IBM一覧から10/23URL検出 |
| T32 | pilot表示・設定・sp500出典必須を確認。現在sp500は未設定 |

## ブラウザー実測

Codex In-app Browserで実操作。スクリーンショットは `docs/relationships-evidence/`。最終の新規プレビューでブラウザーconsole errorは0件。再読み込み時に古いmoduleが残るimportエラーを検出したため、JS/CSS/module graph全体へ内容hashのversion queryを付けて修正しました。初期のCytoscape wheelSensitivity警告を解消するため独自wheel倍率指定を削除しています。フィルターで0件になってから戻した際の古い空メッセージ、同じ銘柄の重複入力、非同期詳細表示の古い応答、モバイル背景フォーカス、密集時のノード重なりを修正しました。

キャッシュ済み30社fixtureは同期初期化 **10.3ms**、次の2回のanimation frameまで **15.6ms**。150社は同期初期化 **23.8ms**（この測定ではframe値未記録）。同一ローカル端末の限定的観測であり、低速iPhoneやネットワークを含む性能保証ではありません。

初回JSON（pointer、manifest、companies、coverage、recent events、Anthropic近傍）のgzip換算は約4.3KB。JS/CSS/ロゴ索引の合計は約503KB、gzip換算約158KB。4企業ロゴ合計約138KB。1MB程度の目標内ですが、これはローカルファイルのサイズ見積もりで、Pagesの実転送・圧縮・CDNキャッシュは未測定です。

## 必要な設定と未実証

1. 実連絡先の `SEC_USER_AGENT`、SEC企業対応のライブ再確認と20社backfill。既存決算側のSECクライアントにある例示User-Agentは今回変更していません。既存運用側の見直しも必要です。
2. 公式IRの利用条件の運用者確認、必要な追加企業・別名の確認、実在関係の追加。現在の実データは28社33関係であり、大量マップのfixtureを公開データにはしません。
3. 実際のPages Source設定確認、allowlist成果物へ公開方式を一本化、GitHub Pagesの用途/容量/帯域条件への適合判断。`RELATIONSHIPS_ENABLED` / `MTZ_PAGES_ENABLED` はまだ有効にしていません。
4. iOSアプリ内WKWebView、WKNavigationDelegate、実機VoiceOver、対象iOS最低版。専用WebKit自動テストランナーも未実施。
5. 20社横断の人手ベンチマーク、一般抽出の精度/取りこぼし、実際の検出・確認・公開遅延。S&P 500の出典/確認日/利用条件付き構成ファイル。
6. PDF/OCR・JS専用ページ・自動の資料間意味的統合・複雑な子会社階層は未対応。単純抽出に合わない関係は根拠付きで担当者が登録・確認する運用です。

詳細は [設定](relationships-setup.md)、[確認手順](relationships-review.md)、[一次資料](relationships-coverage.md)、[iOS](relationships-ios-integration.md) を参照してください。

2026-09-26追記：[案件一覧・金額・日付・追加データの検証](relationships-investor-update.md)。上記の初回パフォーマンス数値は追加前の版であり、28社版の再測定値ではありません。

2026-09-26追加：[具体的な取引内容・一対多・自動調査段落キューの検証](relationships-network-update.md)。最新は52社68関係、unittest 35件・pytest 90件・JS 24件、公開JSON123ファイル。先行実装の数値は上記の時点記録として残します。
