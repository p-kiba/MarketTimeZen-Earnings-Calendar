# MarketTimeZen Earnings Calendar

既存の米国・日本決算カレンダーに、一次資料の根拠から探索する米国企業間マップを追加しています。現状は主要企業15社のSEC識別情報を照合済みで、公開用データ91社・122関係、金額付き28関係です。Google／AlphabetとAmazon／AWSをまとめた画面表示では89社・120関係となり、元の当事者と根拠は詳細に残します。`large_cap_focus` の収集watchlistを使用します。中心企業だけでなく周辺企業同士の確認済み関係も初期表示します。自動抽出した候補は公開されません。変更はローカルで準備済みで、本番公開は実行していません。

追加テストはユーザーの指示で一時停止中です。以下のテストコマンドは再開後の通常手順です。

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m pytest tests/relationships -q
node tests/relationships/browser/unit.mjs
.venv/bin/python generate_html.py --html-only
.venv/bin/python generate_html_jp.py --html-only
.venv/bin/python scripts/build-calendar-universe.py
.venv/bin/python scripts/version-map-assets.py
.venv/bin/python -m relationships_py validate-public
.venv/bin/python scripts/stage-site.py
.venv/bin/python scripts/preview-map.py
```

プレビュー起動時に、未使用ポートで立ち上げた正確なURLが表示されます。古いサーバーのURLを再利用せず、このURLで確認してください。`--html-only` は取得済み決算データからHTMLだけを再生成します。通常の生成モードは従来どおりデータ取得を行います。`map.html` は生成器に依存しない静的エントリで、共通カレンダー用JSを読み込みません。

- [設定・取得・Pages運用](docs/relationships-setup.md)
- [候補の確認・承認・撤回・訂正](docs/relationships-review.md)
- [収録範囲・一次資料](docs/relationships-coverage.md)
- [実証・テスト結果と未確認事項](docs/relationships-validation-report.md)
- [iOSとの連携確認](docs/relationships-ios-integration.md)
- [Product Designの画面検証](design-qa.md)

初期30社、展開後最大150社、一覧30件ずつ。金額色は `relationships_config/settings.json` のUSD境界と色で変更できます。内部の段階番号は画面に表示しません。確認済みの単独総額のみ色を付け、他通貨、通貨未確定、上限、追加オプション、年額、増額分、異なる契約の合算には使用しません。企業ロゴは既存の `assets/logos/us/` を参照し、未保有ロゴは社名を表示します。

Cytoscape.js **3.34.3** を公式npm配布物から取得し固定同梱しています。MITライセンスは `assets/relationships/vendor/LICENSE.cytoscape` にあります。Python 3.10環境の解決済み依存を `requirements-lock.txt` に固定しています。ブラウザーから外部AI APIや書込トークンは使用しません。

大型案件を公表日順に読む「案件一覧」を追加しました。AAPL検索、金額の原文表記・通貨未確認・上限・追加額・条件付き出資を区別します。約600社への拡張と継続的な新着収録は未完了です。[今回の追加と残課題](docs/relationships-investor-update.md)を参照してください。

最新の収録数と精査結果は[大型企業の追加と新着確認工程](docs/relationships-largecap-update-2026-09-26.md)と[残り32候補・大型企業の拡充報告](docs/relationships-expansion-2026-09-26.md)、定期収集と確認後の反映は[運用手順](docs/relationships-operations.md)を参照してください。前回の[一対多の拡張報告](docs/relationships-network-update.md)も残しています。
