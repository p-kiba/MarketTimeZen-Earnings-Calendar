# 企業間マップ：収集・精査・反映の運用

収集後、企業2社・具体的な関係内容・公表日・出典URLがそろい、公式企業発表の見出しと本文抜粋で当事者と行為が一致する候補を自動収録します。その他の候補は掲載条件未達として残します。自動収録は人手による一次資料確認を意味しません。最新の過去の取得結果は [大型企業の追加と新着確認工程](relationships-largecap-update-2026-09-26.md) を参照してください。

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
- 収集結果は `relationships_data/state/collection_round.json`、自動掲載結果は `relationships_data/state/automatic_publication.json` に保存します。`collection_runs/`に最新30回を保持します。
- `relationships_data/review/changes.json`で重複候補・変更や終了の記述・原文変更を既存関係IDと照合できます。各項目は未確認で、解除可能条項や否定文も含みます。自動で統合・終了・承認しません。
- 二社候補は `relationships_data/review/candidates.jsonl` と `report.md`。複数社や未解決名の段落は `statements.json`。容量を超えた段落は繰り越し件数を表示します。
- ローカル定期実行は掲載条件を満たす候補から公開用JSONを生成します。commit/push、デプロイは行いません。GitHub Actionsは同じ条件で生成結果をcommitし、Pages有効時は公開工程に進みます。
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

## 手動精査した内容をマップへ反映する場合

自動掲載できなかった内容を個別精査して追加する場合にだけ、次の操作を使います。自動掲載には不要です。

```bash
.venv/bin/python -m relationships_py prepare-release \
  --reviewer '<実際の確認者またはCodex資料限定精査と明記>' \
  --reason '<確認した資料・判断・残した未確認事項>'

# ローカルで公開JSONを生成する場合だけ、返されたreview_idを指定
.venv/bin/python -m relationships_py release-reviewed --review-id '<release-...>'
.venv/bin/python scripts/stage-site.py
```

`prepare-release` は承認済みデータと根拠資料の内容hashを固定します。確認済みのマスターデータと生成された `relationships_data/review/releases/release-*.json` を既定ブランチへコミットすると、GitHub Actionsが一致するreview IDを特定して `release-reviewed` を実行します。手動でワークフローを起動する必要はありません。`release-reviewed` は内容が現在のデータと一致する場合だけexportします。候補追加だけなら確認済みデータは変わりません。確認済みデータ・根拠が変更された場合は、精査して新しいreview IDを作成する必要があります。通常の運用で直接 `export` を使って確認記録を省略しないでください。

反映前の必須データ整合性確認で、未承認・参照不整合・原文hash不一致・過大な削除・確認待ち上限超過を止めます。これは実データ反映処理の一部で、停止中のテストスイートを実行するものではありません。失敗時は直前の正常buildを維持します。

`stage-site.py` はローカル表示用の `.site-build/` を再生成するだけで、本番へ送信しません。候補、設定、原文cache、運用文書はサイトに含みません。既存プレビューはページを再読み込みすると反映されます。

## GitHub Actionsへの移行に必要な設定

コードは用意済みですが、GitHub側のActions有効化・Secret設定・Pages設定と実行履歴は未確認です。このリポジトリをpushするだけでは収集用の有効化変数は設定されません。

- `relationships.yml`：UTC 00:17・12:17（日本時間09:17・21:17）に収集し、掲載条件を満たす候補を自動で公開JSONへ反映します。`RELATIONSHIPS_ENABLED=true` と `SEC_USER_AGENT` Secretが必要です。原文cacheはActions cache、掲載条件未達の候補と掲載レポートは14日保持のartifactへ保存します。
- `relationships-release.yml`：確認済みのrelease receiptが既定ブランチにpushされたら、内容hashが現在のマスターデータと一致する場合だけマップJSONを更新します。手動起動は再実行用に残しています。承認済みデータ・ルール・レビュー記録を先にレビューし、同じリポジトリ状態へ保存する必要があります。
- `pages.yml`：決算更新・関係収集・手動精査反映の成功後に起動します。実デプロイは既存の `MTZ_PAGES_ENABLED` とPages設定の別条件です。現時点では有効化を確認していません。
- 初期のCIテスト処理は削除していません。今回そのworkflow自体を実行していません。
- GitHub側へ移行するときはローカルの定期収集と二重運用しないでください。リポジトリ設定・CIランナー・夜間の無人実行は未実証です。

リポジトリ全体をそのままPagesへ公開せず、allowlist成果物だけを配信してください。既存の公開構成の注意点は [設定ガイド](relationships-setup.md) を参照してください。
