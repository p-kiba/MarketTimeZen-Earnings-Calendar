# 重点銘柄の事業関係補完（2026-09-27）

ユーザー指定の NFLX・PLTR・CSCO・AVGO を最初の重点対象にした。調査順位は、買収以外の事業関係、ティッカー・決算の紐付け、金額・期間・条件の順。全業種の網羅完了を意味しない。

## 今回の反映

- 15件の新規関係を一次資料の本文・段落ハッシュに固定して収録。全件に具体的な短い線ラベル、製品、当事者の役割を付けた。
- NFLX: Sony Picturesの映画配信権、TKO傘下WWEの番組配信権、2022年のMicrosoft広告基盤・広告販売。Microsoftの記録は当時の内容として扱い、現在も独占契約が続くとは表示しない。
- PLTR: Panasonic Energyの電池工場へのFoundry導入、Accentureとの企業向けAI導入支援、Sovereign AIのデータセンター運用ソフト。
- CSCO: Teams対応会議端末、Samsungディスプレイ統合、AMDおよびHUMAINとのAI基盤構築計画。将来計画を稼働済みとしない。
- AVGO: SEC 2024年度10-KからTSMC、Amkor、ASE、Foxconn、Siliconwareの製造委託関係。現時点の継続性や個社別金額を推測しない。
- 4銘柄のティッカー・CIKをSEC submissionsで再確認し、既存の企業IDへ紐付けた。NFLXのみ企業を新規追加。PLTR・CSCO・AVGOは既存IDを使用。
- 4銘柄の既存決算JSONとロゴファイルの対応を確認。ブラウザー操作・テストスイートはユーザーの希望により未実施。

## 金額の補完

WWEのニュースリリースには金額がなかったが、TKOの2024-01-23付SEC 8-Kに初期10年の権利料が原文「$50億超」、5年後の離脱権、追加10年の延長権と記載されている。元の関係IDを維持し、SECによる補完を履歴イベントとして追加した。追加10年分を合算しない。日付は月しか示されていないため、開始日を1月1日と推測しない。

金額の値は下限として保存し、通貨欄はUSDが明示されていないため未確認、条件付きとして保存する。現在の分類方針では固定総額の色は付かない。その他14件の確認資料には対象契約の金額が記載されていない。「企業が金額を非公表と断言した」とは扱わない。

## 継続運用

`relationships_config/universe.json` の `custom` に4銘柄を登録し、既存 `large_cap_focus` に未登録の3銘柄を追加した。既存の収集ワークフローは同リストを参照する。GitHub側の有効化設定・実行実績は今回確認していない。push・本番デプロイは実施していない。

```bash
python -m relationships_py resolve-universe --universe custom
python -m relationships_py collect-round --mode incremental --sec-only
```

上記のSECアクセスには `SEC_USER_AGENT` が必要。ローカル検証にはユーザー指定の運用連絡先を使用した。収集は候補作成までで、自動承認・自動反映ではない。公開前には一次資料を確認し、既存の承認・export手順を使う。

## 残作業

- 金融・決済、医薬品、エネルギー・産業の主要企業も同じ基準で深掘りする。
- 今回は取得できなかったNetflix/Universal、Palantir/BP・Rio Tinto、Broadcomのクラウド連携は未追加。取得結果は候補であり、検索結果だけで公開しない。
- 重点4銘柄以外の上場企業にも残るティッカー欠落を補う。略称だけで自動的に別法人へ紐付けない。
- 各社について顧客側・供給側・共同開発側の偏りと、古い資料の更新状況を追う。

## 主な一次資料

- Sony Pictures: https://www.sonypictures.com/corp/press_releases/2026/0115
- WWE: https://corporate.wwe.com/about/news/2024/01-23-2024
- TKO SEC 8-K: https://www.sec.gov/Archives/edgar/data/1973266/000119312524012600/d715345d8k.htm
- Panasonic: https://na.panasonic.com/news/palantir-and-panasonic-energy-of-north-america-sign-multi-year-agreement
- Accenture: https://newsroom.accenture.com/news/2025/accenture-and-palantir-expand-global-strategic-partnership-to-drive-ai-reinvention
- Cisco: https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2025/m11/amd-cisco-and-humain-to-form-joint-venture-to-deliver-world-leading-ai-infrastructure.html
- Broadcom SEC 10-K: https://www.sec.gov/Archives/edgar/data/1730168/000173016824000139/avgo-20241103.htm

全資料・根拠段落・主張は `relationships_config/deal_rules.json` の `focus-20260927-*` を参照。

## ローカル反映結果

| 銘柄 | 直接相手先（前→後） | 反映後の関係数 |
|---|---:|---:|
| NFLX | 未収録→3 | 3 |
| PLTR | 1→4 | 4 |
| CSCO | 1→5 | 5 |
| AVGO | 4→9 | 10 |

マップ配信用の承認済み関係は204件から219件。公開データ検証は434ファイルに対して成功し、設定検証も成功。SEC連絡先は今回の取得コマンドに環境変数として渡したため、通常シェルでの設定検証では `sec_contact_configured: false`。定期運用には既存の `SEC_USER_AGENT` 設定を確認する必要がある。テストスイートと実画面の操作確認は実施していない。
