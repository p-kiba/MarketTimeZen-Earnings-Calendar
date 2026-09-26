# 企業間マップ：内容の具体化・一対多・収録工程（2026-09-26）

> この文書は以前の実装時点の記録です。現在の件数・SEC接続状況・金額判定は[最新報告](relationships-peer-update.md)を参照してください。

今回の実装はローカルで完成・検証済み。本番デプロイ、push、Actionsの有効化、Pagesの設定変更はしていません。公開用データは **52社・68関係・金額付き12案件、関係の証拠資料25件**。直前の28社・33関係に対し、一次資料10件から24社・35関係を追加しました。企業数の100倍化や主要銘柄全体の網羅は未達です。

## 何が変わったか

- 「提携」の種別だけでなく、一覧と詳細に具体的な内容を表示。新規35関係は製品・サービス、両当事者の役割、確認できる場合は容量と地域も構造化。既存33関係の説明も一覧から読めます。
- 中心企業から直接の相手先へ配置。調達先・サービス提供元、顧客、共同開発・提携、出資・買収、企業グループ、周辺企業同士の分類を±で表示／非表示にします。
- 周辺企業の展開を企業単位で取り消せます。複数の展開で共有する関係を誤って消さないよう、残した企業別データから再構成します。
- 「関係の件数」と「異なる相手先の社数」を分け、資料の公表期間も表示。古い資料の採用予定を現在の稼働・取引実績として表示しません。
- ロゴの正方形、ズーム±、金額帯、Lv文字列の非表示、カレンダーへの戻り先、お気に入りURL連携を維持。保有ロゴと確認済みの銘柄対応がある企業に既存画像を使用します。
- NVIDIA NewsroomとMicrosoft Azure Blogで関連記事カードを本文として選んでいた解析を修正。抽出時も原文hashを照合し、現在の解析処理で再読込します。
- 新しい調査段落キューで、3社以上が登場する資料と未登録名の候補を保持。全社の総当たりの線、合計金額の各社への割当て、未確認名の企業登録は自動実行しません。

## 現在収録している直接相手先

| 中心 | 相手先社数 | 関係件数 |
|---|---:|---:|
| NVIDIA | 24 | 25 |
| Apple | 15 | 15 |
| Meta | 7 | 7 |
| Amazon Web Services | 5 | 5 |
| Microsoft | 4 | 6 |
| Anthropic | 5 | 10 |
| Micron | 2 | 4 |

同じ2社に供給・サービス利用・出資がある場合は複数関係を保持しますが、相手先社数は1社です。AWSとAmazon、GoogleとAlphabet、Qualcomm Technologiesと親会社を同一企業として扱いません。AMD、Google、Teslaなどはまだ相手先1社であり、全銘柄が十分に収録された状態ではありません。

## 今回追加した一次資料

| 一次資料 | 主な収録内容 |
|---|---|
| [NVIDIA Blackwell（2024-03-18）](https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing) | AWSとのProject Ceiba、クラウド／サーバー／設計ソフトウェア各社の製品展開計画、TSMCの製造プロセス等20関係。採用予定を個別の購入契約・納入完了に読み替えない。ページ取得時の列挙に基づくため、公開当時の固定スナップショットではない |
| [Meta・Corning（2026-01-27）](https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/) | データセンター用光ファイバー供給、最大$60億の複数年契約。上限額・通貨未確認として保持 |
| [Meta・AMD（2026-02-24）](https://about.fb.com/news/2026/02/meta-amd-partner-longterm-ai-infrastructure-agreement/) | Instinct GPU、最大6GW。容量を金額にしない |
| [Meta・NVIDIA（2026-02-17）](https://about.fb.com/news/2026/02/meta-nvidia-announce-long-term-infrastructure-partnership/) | AI学習・推論データセンターの複数年協業 |
| [Meta・Broadcom（2026-04-14）](https://about.fb.com/news/2026/04/meta-partners-with-broadcom-to-co-develop-custom-ai-silicon/) | MTIAの設計・先端実装・ネットワーク、初期1GW超の計画 |
| [Metaの原子力案件（2026-01-09）](https://about.fb.com/news/2026/01/meta-nuclear-energy-projects-power-american-ai-leadership/) | Vistraの20年購入契約、TerraPower・Okloの将来開発支援の計3関係。全体6.6GWを個別案件へ重複配賦しない |
| [Micron・Anthropic（2026-06-22）](https://investors.micron.com/news/press-release/2026/Micron-and-Anthropic-Announce-Strategic-Agreement-to-Scale-Next-Generation-AI-Infrastructure/default.aspx) | メモリー・ストレージ供給、Claude利用、Series H出資。金額は記載なし。MU銘柄対応も本文で確認 |
| [Micron・NVIDIA（2025-03-18）](https://investors.micron.com/news/press-release/2025/Micron-Innovates-From-the-Data-Center-to-the-Edge-With-NVIDIA-03-18-2025/default.aspx) | Blackwell向けHBM3EとSOCAMM |
| [Microsoft・Mistral AI（2024-02-26）](https://azure.microsoft.com/en-us/blog/microsoft-and-mistral-ai-announce-new-partnership-to-accelerate-ai-innovation-and-introduce-mistral-large-first-on-azure/) | Azure計算基盤の提供とモデルの販売・配布協業 |
| [AWS・BMW（2023-09-05）](https://press.aboutamazon.com/2023/9/the-bmw-group-selects-aws-to-power-next-generation-automated-driving-platform) | BMWのADASクラウド開発基盤とQualcomm Technologiesとの共同開発 |

`approved_rule`は上記資料のURL・原文hash・段落hashと評価済み主張を固定した検証です。人間の承認を偽装しません。新規資料や内容の変化を自動承認する汎用規則ではありません。原文全文はgit管理外の`.cache`に置き、公開する引用は各ソース合計25語以内。確認待ちの候補と架空テストデータは公開用データに含めません。

## 収集・確認・ローカル生成の運用

既存の`collect`→`extract`に調査段落キューを接続済みです。今回の実行では二者関係の未承認候補75件と調査段落287件を生成しました。段落には会社以外の製品名・人物名や、すでに一部を収録した資料も含まれます。287件を新規の真の関係数とはみなしません。

1. `SEC_USER_AGENT`に実際の運用連絡先を設定。`resolve-universe --universe large_cap_focus`で企業・銘柄を照合し、`collect --mode backfill --months 24 --universe large_cap_focus`で初回収集。その後はincremental。
2. `.venv/bin/python -m relationships_py extract`で二者候補と調査段落を生成。原文取得なしで段落キューだけ作り直す場合は`discover-statements`。
3. `relationships_data/review/statements.json`の出典とlocatorを確認。未解決名は企業候補にすぎません。キューは設定`max_candidates_per_run`までを新しい資料優先で保持し、超過数を`deferred_statements`に記録します。
4. `.venv/bin/python -m relationships_py draft-disclosure --source-id source-5a44e3fab07fdbe47c2e947d`で原文・段落hash付きの確認用JSONを`.cache/relationships/review/`に作成。マスタや承認状態は変更しません。
5. 当事者、実際の役割、製品、日付、状態、金額の範囲・通貨・条件を原文と照合。未知の会社は名前と上場対応を別々に検証します。資料限定の規則を追加する場合は`relationships_config/deal_rules.json`の既存形式に従い、`business`も含めて`date`と`claims`のassertions hashを再評価します。hashの一致だけで内容が正しいとは限りません。個別主張の確認が必要です。
6. `.venv/bin/python -m relationships_py verify-deal-rules`、`export`、`validate-public`、`.venv/bin/python scripts/stage-site.py`の順でローカル成果物を生成。これらはデプロイしません。
7. プレビューは`.site-build`のみを`127.0.0.1`で配信。リポジトリのルートや原文cacheは配信しません。

GitHub Actionsの収集は`RELATIONSHIPS_ENABLED=true`を設定して初めて有効になります。今回は変更していません。公開承認後の運用設定は[セットアップ](relationships-setup.md)参照。公開用スナップショットと解析用ファイルの分離は既存のPages artifact allowlistを維持しています。

## 検証結果

- 既存カレンダーunittest **35件成功**。
- 関係処理pytest **90件成功**。一次資料hash固定の冪等性と改変検知、候補の非公開、共有関係の参照整合、金額と容量の区別等を含む。実原文cacheを使う1件はcacheを持たないCIでskipされます。
- JavaScript **24件成功**。お気に入り・月・市場の引継ぎ、iOSメッセージの既存payload、共有辺の保持、中心に対する役割分類、150社の配置、マップ入口の構文を含む。
- 公開JSON **123ファイル**の参照・hash・承認状態を検証。最終データbuildは`2c06907ca0102678fd73d9ee`。
- 実ブラウザーでAAPL/NVDA/Meta検索、分類開閉、全分類を閉じた説明、周辺展開・取り消し、内容詳細、上限金額、根拠リンク、375pxシートとEscapeを確認。375pxのscrollWidthも375。途中のJS識別子重複は修正し入口構文テストを追加。修正後のアセットで新しいconsole errorなし。
- [NVIDIA・実在24相手先](relationships-evidence/expanded-nvda-readable.png)、[Meta・7相手先](relationships-evidence/expanded-meta-desktop.png)、[375px金額詳細](relationships-evidence/expanded-meta-mobile.png)。QA履歴は[design-qa.md](../design-qa.md)。

## 必要な設定・未実証

- SEC_USER_AGENT未設定。SECライブ横断収集・CIKの一括照合は未実証。原文内の社名は確認できても銘柄対応未確認の会社があります。
- `large_cap_focus`は調査優先watchlistで、リアルタイムの時価総額ランキングではありません。S&P 500構成ファイルは未準備。
- Google、Tesla、AMD等も含む主要企業全体への継続的な収録拡張が必要です。52社を「米国大型企業を網羅」とは扱いません。最新の収録資料日は2026-07-08で、9月までの全新着を確認した意味ではありません。
- IRサイトによって取得拒否、本文不足、PDF/JavaScript依存があります。今回Microsoft・Oracleの公式ページは取得器が本文を取得できず、関係を追加していません。アクセス制限を迂回していません。
- 自動取得は確認候補まで。未登録名の最終企業解決、複数当事者の役割、更新・終了・金額の条件は継続的に確認する必要があります。
- 金額非開示の契約額は推測しません。容量と総投資計画を二社の契約額へ置き換えません。
- 実機WKWebView／VoiceOver、実際のGitHub Actions／Pages実行、数千の実在関係・低速端末での性能は未検証。本番デプロイは禁止されたままです。

## 残作業（2026-09-26 ユーザー指定）

- 対応済み：企業選択時だけ線幅・矢印を拡大する指定を削除し、通常時の太さに戻した。金額帯による通常の線幅と選択中ラベルは維持。後続のユーザー指示により、非選択企業・線の減光も撤去済み。より見分けやすい強調方法の検討は残作業。
- 選択中の企業に接続する線の契約・提携内容ラベルの常時表示は維持する。
