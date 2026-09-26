# ORCL・DELLと金融分野の補完、企業表示名の短縮

## 対象と判断

買収件数だけを増やすのではなく、実際に提供・利用するサービスと製品を優先。今回の調査で本文を確認できた7件を根拠段落とハッシュに固定した。

- Oracle → Uber: 配車・AI・データ基盤へのOCI提供（2024年）。全基盤の独占契約とは扱わない。
- AT&T → Oracle: ECP向けIoT接続とネットワークAPI（2024年）。
- Oracle → Deutsche Bank: 基幹DBのExadata Cloud@Customer移行（2021年）。古い契約のため過去の記録として収録。
- Dell → Ericsson: Cloud RAN向けPowerEdge XR8000・XR5610（2023年）。
- Dell ↔ Nokia: AirFrame顧客のPowerEdge等への移行支援（2024年）。Nokia自身への直接販売額は推測しない。
- Nokia ↔ Dell: NDACとNativeEdgeの統合計画（2024年）。同じ2社でも製品・役割の異なる協業を分ける。
- Visa ↔ AWS: Intelligent CommerceとBedrock AgentCoreによるエージェント決済（2025年）。商用取引額やサンプルの金額を契約額として扱わない。

全件、採用した資料に契約金額の記載がない。金額なしを0ドルにせず、色の階級を推測しない。公開日時点の状態と現在の継続性は区別する。実際の根拠URL・段落・主張は `relationships_config/deal_rules.json` の `focus-orcl-dell-20260927-*` に保存。

## 表示名

CompanyViewの表示層でPalantir Technologies Inc. → Palantir、NETFLIX INC → Netflix、Dell Technologies → Dell、Uber Technologies, Inc. → Uber等へ短縮。法人接尾辞も省略する。元の企業名・正式名称は検索用別名に残し、マスター・契約当事者・証拠資料は変更しない。事業部の表示から「事業」を消して親会社全体と混同しない。

## 未確認・後続

- Dell/CoreWeaveのIR本文・公式PDFは取得タイムアウト。今回の公開関係には追加しない。
- Oracle/Uberの2023年URLはニュース一覧へ転送されたため不採用。利用内容を確認できる2024年公式発表を採用。
- NokiaについてDell公式ページは403。取引相手Nokiaの公式発表を取得して確認。
- 金融・決済の補完はDeutsche Bank・Visaを今回の対象とし、医薬品・エネルギー・産業全体の網羅は継続課題。
- 本番デプロイ・pushなし。テストスイートはユーザーの希望により実施しない。公開データの整合性確認とローカルサイトの再生成を行う。

## 反映結果

- 承認済み関係: 219 → 226件（新規7件）。
- ORCL: 直接相手先1 → 4社、関係1 → 4件。
- DELL: 直接相手先1 → 3社、関係1 → 4件（Nokiaとの2種類の協業を含む）。
- SEC submissionsでORCL・DELLのティッカー/CIKを確認し、既存企業IDに紐付け。既存の決算JSON・ロゴを利用できる。custom / large_cap_focusの収集対象にも追加。
- 規則照合: 189資料規則・242主張を照合済み。この数値は全体の再確認件数であり、今回の追加件数ではない。
- 定期収集のGitHub側設定・実行実績は今回変更していない。SEC_USER_AGENTは取得コマンドの環境変数で指定。
- 公開データ検証: 445ファイルで成功。ローカル配信先 `.site-build` を再生成済み。
- 実画面で正式名称「Palantir Technologies Inc.」から検索し、検索結果とマップ見出しが「Palantir」になることを確認。ORCL・DELLのティッカー検索と追加先の表示も確認。
