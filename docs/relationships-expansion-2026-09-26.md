# 残り32候補の精査と大型企業の関係拡充

2026-09-26。前回の[94候補の精査](relationships-review-2026-09-26.md)に続き、残り32候補と主要15銘柄の収録不足を調査しました。Solが公式IR・SECから探索し、Astraが原文を独立照合、統合担当が主張・当事者・数値を確認して取り込みました。モデル間の一致だけを根拠に承認したものではなく、人による承認とも記録していません。

確認済みの公開用データは **84社・112関係・120イベント・61根拠資料**。前回から20社・28関係を追加し、既存2関係の条件を訂正・補完しました。ユーザー指定のGoogle／Alphabet・Amazon／AWS統合表示では **82社・110関係**（内部の所属線2件を非表示）です。金額付きは16→21関係、単独USD総額として着色できる関係は3→5件です。原文の関係が網羅されたという意味ではありません。本番には送信していません。

## 残り32候補

| 判定 | 件数 | 対応 |
|---|---:|---|
| 重複 | 18 | 既存の確認済み関係に対応付け、元候補を却下 |
| 誤抽出 | 13 | 投資先同士・個人の株売却・保証とサービス契約の混同などを除外 |
| 保留 | 1 | MicronとDRIVE AGX Orinの技術統合。独立した記録の範囲を追加確認 |

32候補そのものを新規承認したものはありません。ただし、誤抽出候補の原文にあったAMDのワラント2件とNVIDIA–SB Energyの提携・出資予定は、正しい当事者・関係分類で別途追加しました。保証上限USD1,050億をOpenAI→NVIDIAのサービス契約額とする誤抽出は採用していません。

監査記録：`relationships_data/review/batch-2026-09-26-remaining32.json`、`receipt-review-2026-09-26-remaining32.json`。候補ごとにhash、原文URL/hash、段落hash、判断理由、重複先を固定しています。

## 追加した内容

- **Berkshire Hathaway**：OxyChem化学品事業の取得とTaylor Morrisonの買収。Occidental全社を買収した線にはしていません。
- **Lilly**：Verveの買収、NVIDIAとのAI創薬研究所。共同研究所の両社合計投資予定は個社の支払額へ配賦していません。
- **JPMorganChase**：Coinbaseとの口座・カード・ポイント連携、ChaseブランドのApple Card発行事業移行。移管対象カード残高や信用損失引当を契約対価にしていません。
- **Walmart**：Constellationからの原子力電力購入、OpenAIとの従業員研修。電力容量・全社研修予算は取引金額と区別しました。
- **Costco**：Instacartによる当日配送・EC基盤、Uber Eats配送の拡大。会員割引は契約額にしません。
- **Tesla**：Panasonic・CATLの電池セル供給、GMへのSupercharger利用開放。開示時点と現在の状況を区別しました。
- **Micron**：AMD Instinct MI350向けHBM3E採用、MicrochipとのCXL製品共同開発。
- **その他**：Google–Salesforce、Microsoft–LSEG、Apple–OpenAI、Amazon–Rivian、Meta–EssilorLuxottica、Broadcom–VMware、NVIDIA–Accenture、AMD–OpenAIのGPU供給、NVIDIA–SB Energyの提携・出資予定。
- **権利・所属**：AMD→OpenAI OpCoおよびMetaのワラント2件、AmazonのAWS事業セグメント所属1件。株式保有や企業間の売買契約とは区別しています。

## 金額・条件の確認

| 関係 | 反映した意味 |
|---|---|
| Berkshire–OxyChem | 取得後調整込みの現金対価約94億USD。SECのXBRL fact・単位・原文位置を照合。紫色 |
| Berkshire–Taylor Morrison | 全普通株取得の現金対価約68億USD。1株価格や企業価値と加算しない。紫色 |
| Lilly–Verve | 取得現金控除後5.49億USDと、別の最大約3億USDの条件付きCVR。グロス取得総額へ合算せず、着色しない |
| Microsoft–LSEG | 10年間の最低クラウド関連支出、原文$28億。最終総額・上限ではない。ドル種類未確認のため着色しない |
| NVIDIA–SB Energy | 原文$15億の出資予定。払込完了とUSDはこの資料から確定せず着色しない |
| AMDのワラント | 各最大1.6億株、原文行使価格$0.01。2026年6月27日時点で権利未確定。株数×価格を投資額にしない |
| Nebius–Microsoft（補完） | SOW発効日2025-09-07、署名完了日09-08、月次後払い、解除時の前払金返金条件を区別 |
| Pinterest–AWS（訂正） | 予定コミットメントについて「無条件」とは確認できないため、条件の有無を未確認へ訂正。旧イベントを保持 |

主な一次資料：

- [Berkshire 2026年Q2 10-Q](https://www.sec.gov/Archives/edgar/data/1067983/000119312526341032/brka-20260630.htm)（提出日2026-08-10を提出一覧でも照合）
- [Lilly 2026年Q1 10-Q](https://www.sec.gov/Archives/edgar/data/59478/000005947826000045/lly-20260331.htm)
- [AMD 2026年Q2 10-Q](https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm)
- [LSEGとMicrosoftの契約](https://www.lseg.com/en/media-centre/press-releases/2022/lseg-and-microsoft-launch-strategic-partnership)
- [NVIDIAのSB Energy案件8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000069/nvda-20260817.htm)
- [WalmartとConstellationのPPA](https://corporate.walmart.com/news/2026/06/23/constellation-and-walmart-announce-longterm-agreement-to-support-reliable-emissionsfree-nuclear-energy-in-illinois)
- [ChaseのApple Card移行発表](https://www.jpmorganchase.com/newsroom/press-releases/2026/chase-to-become-new-issuer-of-apple-card)

## 15銘柄の収録状況

根拠データ上の直接の関係数です。同じ相手への供給とワラントなどは別関係として数えます。「相手数」は重複を除いた企業・事業ノード数です。Google／AlphabetとAmazon／AWSは下記の表示統合により、画面では両者を合わせた件数になります。

| 銘柄 | 追加前の関係数 | 追加後 | 相手数 |
|---|---:|---:|---:|
| NVDA | 25 | 29 | 27 |
| AAPL | 16 | 18 | 17 |
| GOOGL | 1 | 1 | 1 |
| MSFT | 8 | 9 | 6 |
| AMZN | 4 | 6 | 5 |
| META | 7 | 9 | 8 |
| AVGO | 4 | 5 | 4 |
| TSLA | 1 | 4 | 4 |
| MU | 4 | 6 | 4 |
| BRK-B | 0 | 2 | 2 |
| LLY | 0 | 2 | 2 |
| AMD | 3 | 7 | 6 |
| JPM | 0 | 2 | 2 |
| WMT | 0 | 2 | 2 |
| COST | 0 | 2 | 2 |

根拠データではGOOGLの直接線はGoogleへの所属関係です。画面ではGoogle側の関係をまとめて表示するため、Googleノードを経由して展開する必要はありません。AmazonについてもAWS側をまとめています。

## 指定された企業の表示統合

- Google／Alphabetは`co-googl`、Amazon／AWSは`co-amzn`を表示上の共通IDとして使います。Google・Alphabet・GOOG・GOOGL・AWS・Amazon Web Services等の検索から同じ企業を選べます。
- 検索結果、マップ、一覧、新着、クイック選択、お気に入りの企業表示をまとめ、内部の所属線・自己ループを非表示にします。過去の`co-google`・`co-aws`リンクも共通表示へ解決します。
- 両者の近隣データを同じ公開buildから取得し、周辺企業同士の線も補います。関係IDを基準に重複を除き、異なる契約額は加算しません。
- 詳細には「資料上の当事者」を表示します。元の法人・事業ID、契約条件、原文根拠、イベント履歴は変更しません。承認済みデータのhash検証・古いbuildへのフォールバックも元のDataClientを使用します。
- 表示統合は`assets/relationships/company-view.js`の明示リストのみで行い、他の親子会社を自動統合しません。検索・お気に入りで使う上場銘柄情報を引き継ぎます。コードの独立レビューを実施しましたが、指示に従い実ブラウザー確認・テストは未実施です。

## 実行・運用・未確認

- 資料限定ルールの適用、32候補の判定適用、確認済み内容を固定した反映、ローカルサイト生成を実施。処理内のスキーマ・原文hash・数値単位・参照整合性の確認が通っています。
- ユーザーの指示どおり、テストスイート・ブラウザーQAは実行していません。カレンダー・iOSメッセージ連携のコード変更は今回ありません。マップ内のお気に入り表示は統合した企業情報を参照し、保存・受渡しの処理は変更していません。
- 追加設定は不要。既存のSEC連絡先をローカルで使用し、値は公開用データや文書に出していません。新しい定期タスクは作らず、[既存の収集→精査→反映手順](relationships-operations.md)を継続します。
- Lilly公式IRのタイムアウト・公式サイト403、Tesla IR403、Microsoft発表の本文解析失敗は迂回せず、相手企業の公式発表・SEC提出資料を利用しました。
- 保留はMicronの1候補。別途、NVIDIAの保証は匿名関連会社の扱いが未解決、Berkshire–Pilotは追加探索候補として今回未収録です。段落調査キューと今回取得した資料全体の再抽出・全件精査は未完了であり、「確認待ち1件」が調査全体の残作業を意味するものではありません。
- 今回の確認は資料時点の事実です。古い発表後の稼働・終了・条件変更をすべて追跡したものではありません。主要企業ごとに取引先を網羅するには継続収集と精査が必要です。
- 無人定期実行、GitHub Actions、iOS実機、Pages公開は引き続き未実証。commit/push・本番デプロイは行っていません。

機械可読の差分・銘柄別件数：`relationships_data/review/expansion-2026-09-26.json`。独立照合の記録：`expansion-source-reviews-2026-09-26.json`。確認済み反映のIDとbuildは `relationships_data/state/last_reviewed_release.json` を参照してください。
