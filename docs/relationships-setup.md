# 設定と運用

## 調査結果と採用判断

2026-09-25〜26にリポジトリと上位ディレクトリを調査。AGENTS.md、Swift/iOSアプリ本体は見つかりませんでした。既存HTML生成器はトップレベルにネットワーク取得があり、定数取得目的ではimportせずASTで読みます。市場切替のNew York/Tokyo、Monthly/Weekly、カードのお気に入り操作は維持しました。追加入口は共通生成元 `html_template.py` にあります。

既存 `update.yml` は毎日UTC 0時に取得・HTML生成・対象パスをgitへpushする構成でした。Pagesの公開専用workflowはなく、GitHub上の実際のPages Source設定は未確認です。この実装では設定切替、workflow起動、commit/push、デプロイを行っていません。

## 初回セットアップ

READMEの依存導入後、`python -m relationships_py validate-config` を実行。以下のpythonコマンドは `.venv/bin/python` またはvenv有効化後のpythonを使います。

SECには実際に運用できる連絡先が必要です。`SEC_USER_AGENT` をアプリ名＋実連絡先で環境変数またはActions Secretに設定してください。例示メールアドレスは拒否します。連絡先はマスタ・公開JSONへ書き込みません。2026-09-26にユーザー指定の連絡先をローカルの `.cache/relationships/sec-contact.env`（git除外・公開対象外、権限600）へ設定し、SEC公式APIへ接続しました。GitHub ActionsのSecret設定は未実施です。

```bash
python -m relationships_py resolve-universe --universe pilot
python -m relationships_py collect --mode backfill --months 24 --universe pilot
python -m relationships_py extract
python -m relationships_py review-report
```

`resolve-universe` は設定CIKとSECのCIK・銘柄を照合し、検証できた企業だけマスタへ登録します。既存のpilot CIKは既存リポジトリの対応表からの初期入力で、large_cap_focusの15社はライブ再照合済みです。結果は `relationships_data/state/sec_identities.json` に出典URL・応答hashとともに保存します。未知の取引相手を全履歴の再帰収集対象にはしません。

時価総額上位企業を優先調査する場合は `--universe large_cap_focus` を指定できます。この日付付き watchlist は時価総額ランキングをもとにした**収集優先順位**で、指数構成表ではありません。順位・時価総額を製品データとしては保存せず、リストは定期的に見直してください。新規企業はまず SEC submissions でCIKと銘柄を照合します。現状のリストにはMETA、TSLA、AMD、MUなどを追加しました。例えば `python -m relationships_py resolve-universe --universe large_cap_focus` で企業IDを登録し、`python -m relationships_py collect --mode backfill --months 24 --universe large_cap_focus` で開示を収集します。`SEC_USER_AGENT` に実在の運用連絡先を設定する必要があります。

GitHub Actions は有効化後、12時間ごとにlarge_cap_focusのSECと公式IRから候補を収集します。`SEC_USER_AGENT` secretに実在の運用連絡先が必要です。手動運用は `collect --mode incremental --universe pilot` または `large_cap_focus`。初回のincrementalは7日重複窓で、24か月の初回履歴取得にはbackfillを明示します。SECの履歴ファイル、改訂提出、EX-10/21/99の添付一覧を読みます。Exhibit 21の記載から直接親子関係を自動推定しません。1回の原文取得40件・添付15件/提出、添付一覧40件まで。残りはgit管理stateのキューに保持します。SEC全ホスト共通2req/s、複数プロセス共通ロック、Actions全体の直列化を併用します。**他のマシンや外部システムから同じ連絡先で走るジョブはこのロックの対象外**です。

公式IRは `official_sources.json` に許可ホスト、parser_type、RSS/Atom URLまたは一覧URLとCSS selector、確認日、利用メモ、取得間隔を設定します。ホスト外リダイレクト、内部IP、巨大応答、ブロック画面は拒否。robots.txtを取得し、禁止・取得失敗なら保留します。公開前に権利者の利用条件も運用者が確認してください。今回の `usage_note` は公開情報と短い引用に限定する収集方針で、法的適合性の承認記録ではありません。

```bash
python -m relationships_py discover-ir
python -m relationships_py ingest-url --url 'https://www.ibm.com/investor/news/ibm-completes-acquisition-of-red-hat'
python -m relationships_py extract
python -m relationships_py review-report
```

`discover-ir` は一覧からURLをキュー登録するだけです。`ingest-url` は許可済みホストだけを取得します。生HTML・HTTPキャッシュは `.cache/relationships/`、耐久的なID・確認・失敗・処理待ちは `relationships_data/` に分離しています。公開リポジトリの候補ファイルも秘密ではありません。全文・秘密・個人情報を入れないでください。

## 対象拡張

`relationships_config/universe.json` のpilot/custom/sp500を設定し、settingsのuniverseとworkflowの `--universe` を同時に変更。1企業に複数証券を対応させ、証券数を500固定にしません。sp500にはas_of/source_url/license_note/securitiesが必須で、SEC銘柄表を指数構成表の代用にしません。現在custom/sp500は未設定です。large_cap_focusはmarket-cap優先リストとして個別設定済みです。

別名は一次資料を照合してcompaniesのaliasesへ出典とともに登録。`aliases.json` は運用者が確認した同一法人表記だけに使い、ブランド・子会社を無条件で親会社へ寄せないでください。

## 公開物と復旧

掲載条件を満たす公式発表は、収集後に `auto-publish` で自動反映します。手動で精査した例外だけ [運用手順](relationships-operations.md) の `prepare-release` → `release-reviewed` を使います。以下の直接exportは低水準の生成処理です。

```bash
python -m relationships_py export
python -m relationships_py validate-public
python scripts/stage-site.py
```

承認済みの関係と、独立に承認された金額だけをimmutableなbuildディレクトリに書き、全件検証後にlatestを切り替えます。公開JSONは会社近傍と関係詳細へ分割。マップのmodule import / CSS / vendorには内容hashのversion queryを付け、古いブラウザーキャッシュとの混在を防ぎます。JS/CSS変更後は `python scripts/version-map-assets.py` を実行してください。stage-siteでも自動実行します。SHA-256照合、旧manifestへのfallback、同一版のブラウザーキャッシュを使用。直前画面のロード失敗は0件表示に置き換えません。SHAは配信整合性確認で、発行者の電子署名ではありません。

`.site-build/` は米国・日本カレンダー、必要JSON、ロゴ、マップ、現行と直前の検証済み関係buildを含む一つのallowlist成果物です。候補、設定、テスト、raw cache、docsを含みません。バージョンはgit内で保持し、自動削除しません。肥大化時は現行・直前・ロールバック対象を残して運用者が整理します。settingsのretained_buildsは将来の整理方針用で、現在自動削除には使いません。

大量削除（既定50%超）または確認待ち件数上限超過はexportを停止します。削除が正しい場合だけ `export --allow-removal`。取得失敗で旧関係の状態を終了にしません。ソース本文が変わると承認を再確認待ちに戻します。

```bash
python -m relationships_py rollback --build-id '<既存の正常build_id>'
python scripts/stage-site.py
```

原文キャッシュ消失時、downloadedのまま抽出できない項目はretryable_errorとして再取得できます。403は連続再試行しません。429/503のRetry-Afterを尊重し、60秒を超える待機は次回へ繰り越します。テキストPDFはページ単位で解析します（pypdf 6.10.0、最大200ページ・200万文字）。原文不明・画像PDF/OCR・暗号化PDF・JS専用ページはunsupportedとして隔離します。

## Actions / Pages（初期無効）

- `relationships.yml`：UTC 00:17・12:17、`RELATIONSHIPS_ENABLED=true` のときだけ既定ブランチで稼働。公式発表から掲載条件を満たす候補を自動収録します。SEC_USER_AGENT Secretが必要。IRだけ取得できた場合もSEC未設定が結果に残ります。
- `relationships-release.yml`：確認済みのrelease receiptを既定ブランチへpushすると、現在のデータと内容hashが一致する場合だけ公開JSONを生成します。手動起動は再実行用です。
- `update.yml`：既存の決算更新。共通のgit保存スクリプトを使い、ステージ対象を限定。remote HEADが進んでいたら自動rebaseせず失敗し、最新版から再実行します。
- `pages.yml`：唯一の公開所有者。決算更新・関係収集・手動精査反映workflowの正常終了を `workflow_run` で明示的に接続し、ロック取得後に既定ブランチの最新状態をcheckoutします。GITHUB_TOKENのpushが別workflowを起動すると仮定しません。手動では既定でartifact生成のみです。
- 実デプロイには `MTZ_PAGES_ENABLED=true` と、手動なら `deploy=true` が必要。Pages SourceをGitHub Actionsに切り替え、github-pages環境保護を設定する作業は未実施です。現在のbranch公開と二重運用しないでください。
- 収集・確認済み反映・決算更新・Pagesの4workflowは既存と同じconcurrency groupを共有。schedule遅延やpending runの置換、確認待ちがあるため、12時間ごとの収集も公開時刻の保証にはなりません。別のローカル処理も同時にデータを書かないでください。

Legacy Jekyll branch公開向けの `_config.yml` に候補等のexcludeを追加しましたが、`.nojekyll`を使う既存設定が別に存在する場合は無効です。**候補を配信しないallowlist artifactへの移行確認を公開前の条件**にしています。実際のGitHub設定を確認せず、この変更をpushしないでください。

公式資料： [Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[GITHUB_TOKEN起動条件](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)、[schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。2026-09-25に参照。実際のActionsランナー・remote push・Pages反映は未実証です。

[Pages利用条件](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)は商用SaaS等の用途制限と容量・帯域条件を定めています。このアプリ運用への適合は未判断です。静的成果物は別ホストへそのまま移設できます。新たな有料APIを必須にはしませんが、GitHub実行・配信費用を無条件無料とは扱いません。

## 大型案件の追加経路

初回の少数資料に加え、`verify-deal-rules`で確認済み主張を再現できます。クリーンな環境では`deal_rules.json`の`proof.url`と各企業のidentity/listing proofのURLを`ingest-url`で取得してから実行します。原文が変わってhashが合わない場合は停止するのが正常で、確認を省くためにhashだけを書き換えないでください。

```bash
python -m relationships_py verify-deal-rules
python -m relationships_py export
python -m relationships_py validate-public
python scripts/stage-site.py
```

定期運用と直近の取得結果は[運用手順](relationships-operations.md)と[最新報告](relationships-review-2026-09-26.md)を参照してください。以下は以前の取得制約の記録です。2026-09-26の追加実証は[最新報告](relationships-peer-update.md)を参照してください。直接取得できた記事と、未実証の新着検出を分けて扱ってください。Broadcom IRはrobots取得timeout、MP MaterialsとAMDの一部ページはブロック判定、NVIDIAの対象ページは本文不足でした。いずれも制限を回避していません。実データと未収録部分は`relationships-investor-update.md`を参照。

## 複数社・未登録名を含む資料の調査

`extract`は二者候補に加え、`relationships_data/review/statements.json`を生成します。未解決名は企業と確定したものではありません。`discover-statements`でキューの再生成、`draft-disclosure --source-id <source-id>`でhash付き原文確認用JSONのローカル生成が可能です。詳細は[運用手順](relationships-network-update.md#収集確認ローカル生成の運用)を参照してください。未承認候補・調査キュー・原文cacheをPages artifactへ含めないでください。

## SECのみの接続・再収集

連絡先をローカルへ設定済みの環境では次の手順を使います。`.cache`消失時は実運用連絡先を再設定してください。ファイルの中身をREADMEや公開成果物へコピーしないでください。

```bash
source .cache/relationships/sec-contact.env
.venv/bin/python -m relationships_py validate-config
.venv/bin/python -m relationships_py resolve-universe --universe large_cap_focus
.venv/bin/python -m relationships_py collect --sec-only --mode backfill --months 3 --universe large_cap_focus
.venv/bin/python -m relationships_py extract
.venv/bin/python -m relationships_py review-report
```

`--sec-only` はIRの新着一覧取得を省きます。初回3か月・40件上限の実行は全履歴取得完了を意味しません。未取得文書は耐久キューに残り、次回のincrementalでも処理します。候補の承認は別工程です。
