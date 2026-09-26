# 金額・通貨・契約条件の追加精査

> この精査後の更新は[通貨・条件と線幅修正の続報](relationships-amount-followup-2026-09-26.md)を参照してください。

2026-09-26。通貨未確認の8関係と、主要企業の金額未反映案件を優先確認しました。元の関係IDを維持し、8関係に訂正イベントを追加。旧イベントは残しています。Codexによる一次資料の精査であり、人による承認や別モデルによる独立レビューとは記録していません。

## 今回の結果

| 指標 | 前回 | 今回 |
|---|---:|---:|
| 根拠データの関係数 | 112 | 112 |
| 金額付き関係 | 21 | 24 |
| 金額付きで通貨もすべて確定 | 13 | 19 |
| 金額付きで通貨未確認が残る | 8 | 5 |
| 金額なし | 91 | 88 |
| 確認済み単独USD総額の着色対象 | 5 | 6 |

84社・112関係・128イベント・68資料。Google／Alphabet、Amazon／AWSを統合した表示は82社・110関係。これは全取引の網羅率ではありません。今回、金額なしの88関係すべてを再調査したわけではなく、「非公開が確定した88件」という意味でもありません。

## 通貨未確認8件の確認結果

| 関係 | 結果と反映 | 残る確認事項 |
|---|---|---|
| NVIDIA → OpenAI | 300億USD。OpenAI公式発表のポルトガル語版でUS$表記を確認し、元の英語発表と照合 | 払込完了・詳細な実行条件。発表額として表示 |
| Microsoft → LSEG | 最低28億USD。公式2022年決算資料52ページ、注記17の表を画像と抽出テキストで確認 | 最終支出総額ではない。現在の残額・詳細な起算日は未確認 |
| AWS → Pinterest | 2031年までの40億USD予定コミットメント。AWS公式顧客事例の韓国語版にUSD表記 | 原文のplanned commitmentを維持。無条件・取消不能とは判定しない |
| MP Materials → Apple | 総額の通貨は保留。SECの2025年10-Kで前払条件を補完 | 総額原文$5億の通貨。財務注記のUSDを別の発表額へ機械的に転用しない |
| CoreWeave → OpenAI | 通貨は保留。2025年9月23日の追加注文、2031年5月31日期限、提供要件・解除条件を補完 | 原文のドル種類。相手法人はOpenAI OpCo, LLCと詳細に明記 |
| Broadcom → Apple | 今回確認したApple発表・Broadcom最新10-Qでは見込み額$300億超の通貨を確定できず | 契約別の通貨条項・注文最低額。$15億の設備投資を契約対価へ転用しない |
| Corning → Meta | 通貨は保留。公式ドイツ語発表には米ドル表記が見つかったが、原文取得がHTTP 403で停止 | 原文hashを固定できる許可された一次資料の追加。確認済みデータには未反映 |
| NVIDIA → SB Energy | 通貨は保留。追加取得したS-1には前払契約と別のIPO同時私募の記載あり | Energy Global, LP経由の資金移動・法的当事者・取引段階の整理。別々の$15億を合算・重複登録しない |

「保留」は金額非公開の断定ではありません。資料の記載不足、取得制限、当事者や取引範囲の追加確認を区別しています。

## 金額がなかった主要案件の補完

- **Broadcom → VMware**：2024年10-K注記4の取得対価総額 **862.90億USD** を補完。現金・株式公正価値等を含む会計上の総対価であり、全額現金ではありません。取得現金控除後の796.48億USD、引受債務、買収資金調達額とは合算しません。2023年11月22日の買収完了として赤色の対象です。
- **NVIDIA → Anthropic**：**最大100億USD** の出資コミットメント。
- **Microsoft → Anthropic**：**最大50億USD** の出資コミットメント。上の案件とともにAnthropic公式英語発表とNVIDIA公式繁体字中国語版を照合。上限・未確認の払込状態を保持し、確定総額の色は付けません。

MP Materialsの前払金は、所定マイルストーンに応じた合計2億USD、2025年9月の4,000万USD受領、同年12月の3,200万USD追加請求権を区別して詳細に記載。いずれも総額$5億に上乗せしません。

## 主な一次資料

- [OpenAI公式発表（ポルトガル語）](https://openai.com/pt-BR/index/scaling-ai-for-everyone/)
- [LSEG 2022年決算資料、52ページ・注記17](https://www.lseg.com/content/dam/lseg/en_us/documents/investor-relations/financial-results/preliminary-results/rns/lseg-preliminary-results-fy2022-rns-2mar2023.pdf)
- [AWS公式顧客事例（韓国語）](https://aws.amazon.com/ko/solutions/case-studies/)
- [MP Materials 2025年10-K、注記16](https://www.sec.gov/Archives/edgar/data/1801368/000180136826000008/mp-20251231.htm)
- [CoreWeave 2025-09-25提出8-K](https://www.sec.gov/Archives/edgar/data/1769628/000119312525216497/d17274d8k.htm)、[MSA](https://www.sec.gov/Archives/edgar/data/1769628/000119312525216497/d17274dex101.htm)
- [Broadcom 2024年10-K、注記4](https://www.sec.gov/Archives/edgar/data/1730168/000173016824000139/avgo-20241103.htm)
- [Anthropic公式発表](https://www.anthropic.com/news/microsoft-nvidia-anthropic-announce-strategic-partnerships)、[NVIDIA公式繁体字中国語版](https://blogs.nvidia.com.tw/blog/microsoft-nvidia-anthropic-announce-partnership/)
- [SB Energy S-1（追加調査対象、未反映）](https://www.sec.gov/Archives/edgar/data/2133037/000162828026059639/sbenergy-sx1.htm)

## 取得・検証処理と設定

- テキストPDFをページ単位で読み取り、原文hash・ページ番号・ページテキストhashを根拠にできるようにしました。`pypdf==6.10.0`を依存ファイルに固定し、ローカル環境には導入済みです。別環境は`pip install -r requirements-lock.txt`で更新します。
- PDFは最大200ページ・抽出テキスト200万文字。OCR、暗号化PDF、画像だけのPDFは対象外です。自動抽出だけで承認はしません。既存キャッシュの拡張子`.html`は互換性のため残し、実際のバイト列でPDFを識別します。
- AWSの公開顧客事例カードの本文spanを独立したlocatorで読み取るようにしました。既存のHTML段落locatorは変更しません。
- 訂正済みイベントをさらに訂正した場合も、旧ルールが現在のイベントを巻き戻さないよう、訂正履歴の参照を補いました。
- 通常の取得上限10MBは維持。SB EnergyのS-1は今回の個別調査だけ30MBを上限に取得しました。403を回避する取得はしていません。
- SEC連絡先の追加設定、外部有料API、為替換算は不要です。

今回の反映処理では、原文hash・段落/ページhash・公開引用上限・スキーマ・参照整合性を確認します。ユーザー指示によりテストスイート、ブラウザーQA、iOS実機確認は実行しません。PDF解析・訂正の再適用を含む回帰テストは再開後の残作業です。本番デプロイ、commit/push、Actions設定変更は行いません。

機械可読記録：`relationships_data/review/amount-enrichment-2026-09-26.json`。最新の反映ID・buildは`relationships_data/state/last_reviewed_release.json`。線を太くしない選択強調の見直しは[ネットワーク表示の残作業](relationships-network-update.md)に記録し、今回は変更しません。
