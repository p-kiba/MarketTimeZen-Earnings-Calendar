# 大型契約・出資を調べるための改善（2026-09-26）

> この文書は以前の実装時点の記録です。現在の件数・SEC接続状況・金額判定は[最新報告](relationships-peer-update.md)を参照してください。

このページは前回実装時点の記録です。最新は[52社・68関係への拡張報告](relationships-network-update.md)を参照してください。

ユーザーの優先用途は「大型契約・出資の金額と新着情報を追う」。本番デプロイ、push、GitHub設定変更は行っていません。ローカルの公開用JSONは28社・33関係・金額付き11案件（12の金額表示）です。約600社の収録と、継続的な新着監視の実運用は未完了であり、投資家向け製品全体の完成とは扱いません。

## 今回追加した操作

- 公表日順の案件一覧。金額、意味（総額・増額分）、条件、期間、資料リンクからマップへ移動。
- 会社を選ぶ前でも、関係種別・状態・期間・金額有無で絞り込み。過去の資料を取得した日で上位にしない。
- AAPLとPINSの検索に対応。Appleを起点にした15関係に加え、Pinterest（NYSE: PINS）を追加。Broadcom–OpenAIの協業によりApple周辺からAI案件の企業へたどれる。
- 原文の`$`をUSDと断定せず金額自体は表示。条件付き出資、上限・超過見込み、追加額は指定済みの金額ティアへ勝手に割り当てない。
- 正式法人名が確認できない組織はnull。一次資料内の呼称を表示し、AWSをAmazonへ自動統合しない。AAPL、CRWV、NBISは公式資料の銘柄表記を確認。
- 無関係の企業カードを線が横切る誤読を減らす曲線経路。すべての交差を排除するものではなく、正確な当事者は関係一覧・詳細でも確認できる。

## 追加の一次資料と収録範囲

| 公式資料 | 収録した事実 / 制約 |
|---|---|
| [Apple / Broadcom、2026-07-08](https://www.apple.com/newsroom/2026/07/apple-to-increase-spend-with-broadcom-to-produce-billions-more-us-chips/) | 新たな部品契約1件。$300億超の**見込み**。設備投資や全社計画の額を使わない |
| [Apple / MP Materials、2025-07-15](https://www.apple.com/newsroom/2025/07/apple-expands-us-supply-chain-with-500-million-usd-commitment/) | 磁石調達等の複数年コミットメント1件、$5億。全社計画を分離 |
| [Apple AMP、2025-08-06](https://www.apple.com/newsroom/2025/08/apple-increases-us-commitment-to-600-billion-usd-announces-ambitious-program/) | 初期パートナー8関係、TSMCの供給1関係。個社別金額を推測しない |
| [Apple AMP拡大、2026-03-26](https://www.apple.com/newsroom/2026/03/apple-adds-new-partners-to-its-american-manufacturing-program/) | 追加4社、TSMC–Bosch、GlobalFoundries–Cirrus Logicの6関係。4社合計支出を各社へ割り当てない |
| [OpenAI / Amazon、2026-02-27](https://openai.com/index/amazon-partnership/) | Amazonの$500億出資（条件付き）、AWSの8年間$1,000億追加契約。既存$380億を重ねて計上しない |
| [OpenAI資金調達、2026-02-27](https://openai.com/index/scaling-ai-for-everyone/) | NVIDIAの$300億出資発表1件。ラウンド全体・評価額を個社の額にしない |
| [SoftBank Group、2026-02-27](https://group.softbank/en/news/press/20260227) | SVF2を通じたUSD300億の出資契約1件。クロージング条件付き。過去投資の累計額と分離 |
| [CoreWeave、2025-09-25](https://www.coreweave.com/news/coreweave-expands-agreement-with-openai-by-up-to-6-5b) | OpenAI向け追加契約1件、最大$65億。合計最大約$224億とは別 |
| [OpenAI / Broadcom、2025-10-13](https://openai.com/index/openai-and-broadcom-announce-strategic-collaboration/) | AIアクセラレーター協業1件。10GWは金額ではない |
| [Nebius / Microsoft、2025-09-08](https://nebius.com/newsroom/nebius-announces-multi-billion-dollar-agreement-with-microsoft-for-ai-infrastructure) | AI計算基盤提供1件。本文に具体的金額はなく、6-Kの追加確認が必要 |
| [Amazon / Anthropic、2026-04-20](https://www.aboutamazon.com/news/company-news/amazon-invests-additional-5-billion-anthropic-ai) | AnthropicのAWS支出$1,000億超（10年間）と、Amazonからの今回追加$50億・将来条件付き最大$200億出資を別の関係に収録。過去累計$80億と足さない |
| [Pinterest / AWS、2026-06-04](https://press.aboutamazon.com/aws/2026/6/pinterest-works-with-aws-to-power-next-chapter-of-ai-driven-visual-search-discovery) | PinterestのAWSクラウドサービス契約予定額$40億、2031年まで。銘柄NYSE: PINSを発表本文で確認 |

今回の3関係は取得した一次資料と段落hash、短い引用、評価した主張、日付、当事者、金額条件を固定。計27主張・33公開関係を15の関係証拠ソースから収録。`approved_rule`は再現可能なルール評価で、人が承認したという記録ではありません。Amazon Newsの本文領域に合わせた抽出処理を追加し、関連リンクの混入を防止。原文全文はgit管理外cache、公開JSONには短い根拠のみ。収録した関係の最新発表日は2026-07-08であり、2026-09-26までの新着を調査し尽くした意味ではありません。

## 実行した検証

- 既存unittest 35件、関係処理pytest 82件、JS 20件が成功（計137件）。pytestの1件はローカルの実取得cacheを使う冪等性・改変検知の統合テストで、cacheを含まないCIではskip。
- 公開用64ファイルの参照・hash・承認状態を検証。
- 関連記事のmeta日付を誤って拾うケースを再現し、本文冒頭の公表日を優先するテストを追加。
- 金額の上限、増額分、未確認通貨、条件付き金額の着色対象外、過去資料の新着扱い回避、AAPLの公式銘柄対応を確認。
- SEC企業解決で構造化されたuniverse_membershipsに文字列を混ぜて失敗する問題も、fixtureで再現して修正。SECライブ成功を意味しない。

## 残る課題

優先順は、(1) 主要銘柄と大型案件の収録・通貨／正式当事者／後続開示の照合、(2) 公式新着の取得と確認待ち処理の継続運用、(3) 業種分散した約600社規模への拡張です。公開契約金額のない関係も収録できますが、収録数だけを満たすための架空線・企業一覧だけの水増しは行いません。

SEC_USER_AGENT未設定、S&P 500構成ファイル未準備、Actions/Pages無効、iOS実機未検証は継続。公式IRへの追加接続には成功・timeout・ブロック・本文不足が混在します。AMD公式IRページは今回のソース取得器でブロック応答となったため、AMD–Anthropic発表は本文のhash固定を完了できず収録していません。制限を迂回していません。設定を追加したことを、全ページの取得や自動確認が成功したこととは扱いません。新しい資料を未確認のまま本番へ自動承認する機能はありません。
