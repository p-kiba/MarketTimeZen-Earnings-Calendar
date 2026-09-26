# 大型企業の取引先追加と新着の確認工程

2026-09-26。着手前に、それまでの変更を日本語メッセージ「企業間マップと一次資料の収集・精査基盤を追加し表示を調整」でローカルコミットしました（`3244cd5`）。今回は一次資料を照合して10関係を追加し、既存のAmazon–Anthropicの1関係を訂正・補完しました。Codexによる精査であり、人間・別モデルによる独立承認とは記録していません。

## 件数と収録範囲

| 指標 | 着手前 | 今回 |
|---|---:|---:|
| 根拠データの企業数 | 84 | 91 |
| 根拠データの関係数 | 112 | 122 |
| 金額付き関係 | 24 | 28 |
| 金額付きで通貨確定 | 21 | 25 |
| 通貨未確認 | 3 | 3 |
| 金額帯の着色対象 | 7 | 8 |

グループ統合後の画面表示は89社・120関係。根拠データは142イベント・85資料・255根拠です。金額なしは88→94関係ですが、これは新規の金額未開示関係が加わり、既存1件に金額を補った結果です。元の88件すべてを調べたわけではなく、金額が非公開だと確定した件数でもありません。

| 主な企業 | 関係数の変化 | 追加した内容 |
|---|---:|---|
| Walmart | 2→5 | VIZIO買収、Symbotic LLCの店舗向け自動化、Microsoftのクラウド導入 |
| Costco | 2→4 | Citi提携カード、Visaカード受入 |
| JPMorganChase | 2→4 | Payments事業とPayPalの欧州展開、Visa Directとの米国内送金協業 |
| Lilly | 2→5 | Morphic買収、Citiによる買収助言、POINT買収 |

CitiやVisaは複数の企業につながるため、中心企業からの線だけでなく周辺企業同士の関係も増えます。古い契約を現在も同条件で継続しているとみなさず、資料時点と未確認事項を詳細に表示します。

## 金額・契約内容

- **Walmart → VIZIO**：公表された希薄化後株式価値は約23億USD。2024年12月3日の買収完了を公式発表、米ドル建てを合併契約で確認。最終会計取得対価ではありません。取得現金控除後の19億、1株11.50USDと加算しません。
- **Symbotic LLC → Walmart**：店舗受取・配送向けの自動化システム。開発費5.2億USDは締結時2.3億・1周年1.65億・2周年1.25億を含む。400拠点の導入は性能条件付きで、追加200拠点は別オプション。契約の当初期間12年、個々のシステムの保守は仮受入から最低15年。開発費を全導入費用に置き換えず、最終的な支払・解除条件が残るため着色を保留。契約法人を親会社Symbotic Inc.へ置き換えていません。
- **Lilly → POINT**：取得現金控除後の約10億USDをSECの数値とXBRLの通貨単位で確認。総買収額として着色しません。
- **Amazon → Anthropic（既存関係の補完）**：2024年Q4の追加転換債投資で13億USD実行済み、27億USDは2025年Q4までの予定として2024年10-Kが開示。後日の払込完了は今回未確認。転換債の公正価値138億USD、過去の投資、2026年の別ラウンドを合算しません。旧イベントを残しています。
- **Lilly → Morphic**：経口IBD治療薬MORF-057等の取得と完了を確認。研究開発費の会計計上額を買収対価にせず、1株価格から総額を独自計算していません。
- Citiの助言報酬、カードの還元率、JPMorganの日次決済取扱高は契約額として採用していません。

主な一次資料：

- [WalmartのVIZIO買収完了](https://corporate.walmart.com/news/2024/12/03/walmart-completes-acquisition-of-vizio)、[SEC合併契約](https://www.sec.gov/Archives/edgar/data/1835591/000119312524040047/d794432dex21.htm)
- [Symbotic 2025年10-K](https://www.sec.gov/Archives/edgar/data/1837240/000183724025000278/sym-20250927.htm)、[Walmartとの自動化契約](https://www.sec.gov/Archives/edgar/data/1837240/000119312525013845/d905462dex101.htm)
- [Costco・Citi・Visaの公式発表](https://www.citigroup.com/global/news/press-release/2016/us-new-costco-anywhere-visa-card-by-citi-offers-cash-back-rewards-on-every-purchase)
- [PayPalとJ.P. Morgan Payments](https://newsroom.paypal-corp.com/2025-02-25-PayPal-and-JP-Morgan-Payments-Broaden-their-Strategic-Relationship-to-Launch-Fastlane-and-Expand-Merchant-Acquiring-in-the-UK-and-European-Markets)、[Visa Directの協業](https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.20636.html)
- [LillyのMorphic買収完了](https://www.sec.gov/Archives/edgar/data/59478/000119312524201684/d873721dex99a5b.htm)、[Lilly 2025年10-K](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm)
- [Amazon 2024年10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231.htm)

## 収集から確認・更新まで

`collect-round`に確認用の`relationships_data/review/changes.json`を追加しました。本文や企業IDを根拠に、原文変更、重複候補、既存相手との別案件候補、変更・完了・終了の記述、新規候補を区別して表示します。同じ二社・同じ種別でも同じ契約とは限らないため、自動で統合・終了・承認しません。

変更らしい記述には、解除オプション、リスク、否定文、別契約も混ざります。原文URL・hash・段落・既存関係IDを示す調査用の一覧です。終了の単語を検出してもマップの関係状態は変えません。保留分は件数を残し、保存済み原文から再生成します。

収集結果は`collection_runs/`にも保存し、最新30回を保持。公開用データの参照先が収集前後で同じかを記録します。GitHub Actions用の確認artifactと実行要約にも新しい一覧を含めました。GitHub上の有効化や実行は行っていません。既存の毎朝9時のローカル定期収集にも、この確認一覧を読む手順を追加しました。時刻と通知方針は維持しています。

実収集をSEC限定で1回実行（2026-09-26 17:10–17:12 JST）。7文書の取得試行、取得エラー0。新しい解析処理で手元の資料も再抽出した結果、確認待ちの二社候補は89件となりました。これを「新しい実在の関係89件」とは扱いません。収集時点の変更確認候補131件には、重複候補29件・既存相手との別案件候補39件・状態変更らしい記述42件・新規候補21件が含まれます。自動判定0、公開用データの参照先は不変でした。

JPMorganの公式ページで記事のサイドパネルだけを読む問題も補い、本文を別の`aem-text` locatorで追加。既存locatorは維持しています。解析バージョンは`rules-1.8`です。

## 検証・設定・未完了

- 実データの反映処理で84資料ルール・137主張の原文hash、段落hash、引用上限、スキーマと参照を照合。これはテストの実行件数ではありません。
- ユーザー指示によりテストスイート、ブラウザーQA、iOS実機テストは未実施。新しい確認一覧・実行履歴保持・本文抽出の回帰テストは再開後に必要です。
- 追加の連絡先や有料API設定は不要。既存SEC連絡先は非公開cacheに保持。無人の定期実行と実際のGitHub Actionsは引き続き未実証です。
- Symbotic IRはタイムアウト、Lilly IRは接続終了のため、SECの対応資料で確認しました。アクセス制限の迂回はしていません。
- Broadcom–Apple、CoreWeave–OpenAI、Corning–Metaの通貨3件は未解消。前回の保留理由を維持し、二次情報の米ドル表記だけでは確定しません。
- 新しい89候補、段落の繰越分、主要企業全体の網羅、契約の現在の有効性の継続確認は残ります。今回の10件で全体を完成とするものではありません。
- push、本番デプロイ、Pages設定、GitHub Secrets・有効化設定は変更していません。

機械可読記録：`relationships_data/review/largecap-enrichment-2026-09-26.json`。反映IDは`release-2f6a8218d083c79d7873c073`、buildは`99c23d66fd1f3b091a14a757`。詳細は`relationships_data/state/last_reviewed_release.json`。
