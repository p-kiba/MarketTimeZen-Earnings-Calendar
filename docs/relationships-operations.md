# 企業間マップ：収集・精査・反映の運用

2026-09-26時点。候補収集と確認済みデータの反映を分離しています。最新の結果は [大型企業の追加と新着確認工程](relationships-largecap-update-2026-09-26.md) を参照してください。通常の収集では公開JSONを変更しません。

## 定期収集

このCodexタスクに毎日9:00（日本時間）の定期実行「企業間マップの新着収集」を設定済みです。初回の実収集は2026-09-26 14:29–14:31に実行しました。次回以降の無人実行はまだ未実証です。ローカル環境のPC・アプリ・作業フォルダーが利用可能である必要があります。ネットワーク権限の不足などは障害として報告します。[公式の定期実行説明](https://learn.chatgpt.com/docs/automations?surface=app)

実行内容は次の1回分です。全履歴を取り切るまで連続実行するものではありません。

```bash
cd /Users/shigeharafumiya/Desktop/Programing/repos/MarketTimeZen-Earnings-Calendar
bash scripts/collect-relationships-local.sh
```

- `.cache/relationships/sec-contact.env` からSEC連絡先を読み込みます。値を出力・commit・公開しません。
- `large_cap_focus` のSEC提出と設定済み公式IRを増分収集。設定上限40文書/回、SECは最大2リクエスト/秒。IR一覧の取得リクエストは文書件数とは別です。
- 原文は `.cache/relationships/documents/`、耐久キューは `relationships_data/state/processed_documents.json`。
- 結果は `relationships_data/state/collection_round.json`。新候補ID、変更された既存候補、部分失敗、時刻、`published: false`、公開参照先の不変確認を保存します。`collection_runs/`に最新30回を保持します。
- `relationships_data/review/changes.json`で重複候補・変更や終了の記述・原文変更を既存関係IDと照合できます。各項目は未確認で、解除可能条項や否定文も含みます。自動で統合・終了・承認しません。
- 二社候補は `relationships_data/review/candidates.jsonl` と `report.md`。複数社や未解決名の段落は `statements.json`。容量を超えた段落は繰り越し件数を表示します。
- 定期タスクは新しい大型案件や取得障害を知らせます。未検証候補の承認、公開用データの更新、commit/push、デプロイは行いません。
- ユーザーの指示でテスト実行は一時停止中です。定期タスクにもこの指示を保存しています。

SECのみなら `bash scripts/collect-relationships-local.sh --sec-only`。過去分の追加取得は `--mode backfill --months 3` のように指定します。403などの制限を迂回せず、原文が得られない項目は確認待ちにします。

## 一次資料を読んで確認する

1. `changes.json`の関連ID・出典と`report.md`、原文を照合し、当事者・契約対象・方向・日付を確定します。親会社と子会社、同時に列挙された投資家、製品の互換性だけの記載を区別します。
2. 金額は総額、追加額、支払済み、上限、資金枠、買収後報酬を区別します。複数社の共通額や企業評価額を二社間契約へ配賦しません。
3. `$` だけでUSDにしません。契約書のUSD表記、またはSEC inline XBRLの当該数値に結び付く `iso4217:USD` 単位定義を確認します。XBRLのfact ID・桁倍率・数値・原文段落が一致することを適用処理が検証します。
4. `relationships_config/deal_rules.json` に確認済みの主張だけを追加します。原文URL/hash、段落/hash、短い根拠、当事者、金額・期間・条件を固定します。原文hashだけを更新して確認を省いてはいけません。
5. 既存関係のSEC補完は `revises_relationship_id`、`base_event_id`、`base_event_hash` で元記録を指定します。旧イベントは残し、`supersedes_event_id` で新イベントを接続します。同じルールの再適用で古い記録に戻しません。基準イベントが変わったら新たな精査が必要です。
6. `verify-deal-rules` は資料限定の確認内容を再現します。人が確認したと偽る `approved_manual` は使用しません。複数資料の根拠はcontextに記録し、変更した原文を黙って許容しません。

```bash
.venv/bin/python -m relationships_py verify-deal-rules
```

SEC添付契約書の一部は `EX-4.4` のように一般の添付収集対象（10/21/99）以外です。その場合は提出一覧でURLと提出日を確認し、SECクライアントで個別取得してから照合します。契約書の伏せ字は推測で補いません。今回のNebius契約書は個別取得済みです。

多数の候補を整理する場合、`batch-2026-09-26.json` が今回の固定94件の実例です。全候補に一つずつ理由と根拠を付け、採用先関係IDを指定します。

```bash
.venv/bin/python -m relationships_py apply-review-batch \
  --batch relationships_data/review/batch-2026-09-26.json
```

このコマンドは自動承認しません。採用先は事前に確認済みでなければ失敗します。重複・誤抽出候補は却下して再抽出による復活を防ぎ、保留は非公開のまま残します。候補や原文が変わった場合は適用を止めます。適用済みバッチの内容は変更せず、訂正は新しいバッチを作成します。

## 確認済みの内容だけをマップへ反映

精査を終えてから次の操作を行います。

```bash
.venv/bin/python -m relationships_py prepare-release \
  --reviewer '<実際の確認者またはCodex資料限定精査と明記>' \
  --reason '<確認した資料・判断・残した未確認事項>'

# 返されたreview_idをそのまま指定
.venv/bin/python -m relationships_py release-reviewed --review-id '<release-...>'
.venv/bin/python scripts/stage-site.py
```

`prepare-release` は承認済みデータと根拠資料の内容hashを固定します。`release-reviewed` はその内容が現在のデータと一致する場合だけexportします。候補追加だけなら確認済みデータは変わりません。確認済みデータ・根拠が変更された場合は、精査して新しいreview IDを作成する必要があります。通常の運用で直接 `export` を使って確認記録を省略しないでください。

反映前の必須データ整合性確認で、未承認・参照不整合・原文hash不一致・過大な削除・確認待ち上限超過を止めます。これは実データ反映処理の一部で、停止中のテストスイートを実行するものではありません。失敗時は直前の正常buildを維持します。

`stage-site.py` はローカル表示用の `.site-build/` を再生成するだけで、本番へ送信しません。候補、設定、原文cache、運用文書はサイトに含みません。既存プレビューはページを再読み込みすると反映されます。

## GitHub Actionsへの移行に必要な設定

コードは用意済みですが、今回commit/push・Actions有効化・Secret設定・Pages変更は実施していません。

- `relationships.yml`：30分ごとの**収集専用**。`RELATIONSHIPS_ENABLED=true` と `SEC_USER_AGENT` Secretが必要です。原文cacheはActions cache、確認待ちレポートは14日保持のartifactへ保存。公開JSONを生成せず、Pagesの起動元にもなりません。
- `relationships-release.yml`：**手動の確認済み反映専用**。コミットされたreview IDを入力し、内容一致を確認してマップJSONを更新します。承認済みデータ・ルール・レビュー記録を先にレビューし、同じリポジトリ状態へ保存する必要があります。
- `pages.yml`：決算更新と確認済み反映の成功後に起動する構成。収集成功だけでは起動しません。実デプロイは既存の `MTZ_PAGES_ENABLED` とPages設定の別条件です。現時点では有効化していません。
- 初期のCIテスト処理は削除していません。今回そのworkflow自体を実行していません。
- GitHub側へ移行するときはローカルの定期収集と二重運用しないでください。リポジトリ設定・CIランナー・夜間の無人実行は未実証です。

リポジトリ全体をそのままPagesへ公開せず、allowlist成果物だけを配信してください。既存の公開構成の注意点は [設定ガイド](relationships-setup.md) を参照してください。
