# 企業ロゴの追加取得（2026-09-26）

既存の `ロゴ取得用スクリプト/download_logos.py` を改修して使用。Finnhubから7社のPNGを取得し、既存画像15社分の対応付けと合わせて、マップのロゴ表示対象を17社から39社へ増やしました。公開データの企業数は63社で、残り24社は未対応です。ローカルの `.site-build` へ反映し、本番デプロイや追加テストは行っていません。

新規取得：Applied Digital（APLD）、Cirrus Logic（CRUS）、CoreWeave（CRWV）、GlobalFoundries（GFS）、Nebius（NBIS）、Oklo（OKLO）、Qnity Electronics（Q）。

## 実行方法

```bash
.venv/bin/python ロゴ取得用スクリプト/download_logos.py --missing-map
.venv/bin/python scripts/build-calendar-universe.py
.venv/bin/python scripts/stage-site.py
```

個別指定は `--symbols CRWV NBIS`。引数なしの場合は既存のTARGETリストを使用します。既存のFinnhub設定を引き続き使用し、環境変数 `FINNHUB_API_KEY` でも指定できます。既存ファイルは上書きせず、保存先は作業ディレクトリに依存しないリポジトリ内 `assets/logos/us/` です。API利用枠を消費する実取得処理です。

取得処理はFinnhubのprofile2で銘柄一致を確認し、Finnhub内の画像CDNへの最大5回のHTTPS転送に対応します。画像リクエストにはAPIキーを送信しません。HTTPエラー、認証・アクセス・レート制限、PNG形式・容量・寸法の不適合では保存を見送ります。画像を加工せず保存し、正方形の枠内に全体を表示する既存UIを使います。取得結果・出典URL・画像hashは `.cache/relationships/logo-download-report.json` に記録します。

## 企業への対応付け

既に銘柄登録済みの企業は銘柄経由で表示します。その他20社については、SECの企業名・銘柄一覧を照合して `relationships_config/logo_symbols.json` にロゴ表示用の対応を登録しました。出典は https://www.sec.gov/files/company_tickers.json 。企業名・CIK・元レコードhashを記録しています。これはロゴの対応であり、契約当事者や会社マスタの上場情報を変更しません。

`build-calendar-universe.py` が、実在する画像のみ銘柄キーと企業IDキーで `assets/relationships/logos.json` に登録します。マップは企業IDの画像を優先し、次に登録済み銘柄の画像を参照します。

OpenAI、Anthropicなど未上場企業や、AWSなど事業ブランド、銘柄との対応が未確認の企業は残っています。親会社のロゴを自動で流用していません。これらには公式ブランド素材等を使う別の取得・対応付け経路が必要です。
