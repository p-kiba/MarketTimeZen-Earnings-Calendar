# iOS / WKWebView連携

iOS側のSwiftソースはこのリポジトリにありません。WKNavigationDelegate、お気に入り永続化、外部リンク処理は未確認・未変更です。

カレンダーカードの既存操作は `window.webkit.messageHandlers.favoriteHandler.postMessage({ symbol })` のままです。共通の `notifyFavorite` はハンドラーの有無を確認し、通常ブラウザーでは何も送らず例外を起こしません。マップへ勝手に遷移するようカード操作を変更していません。送信形式とハンドラー不在はNodeのvmテスト済みですが、ネイティブ受信完了の実証ではありません。

マップは通常の同一サイトURL遷移を使います。新しいネイティブメッセージハンドラーは不要です。favoritesはURLから読むだけで、共通JSONへ保存しません。キャッシュは検証済み公開データだけを保存します。mapのsearch/filtersは既存カレンダー専用グローバル変数へ依存しません。

## 実機で必要な確認（未実施）

1. `index.html / japan.html / map.html` の同一サイト遷移をWKNavigationDelegateが許可するか。favorites/monthが保持されるか。
2. カードタップで従来のsymbolを受信し、元のアプリの保存状態へ反映されるか。マップを経由してもお気に入りが欠落しないか。
3. HTTPSのIBM/Anthropic/SEC根拠リンクが想定するSafari/SFSafariViewController/同WebViewで開くか。相対URLやtarget=_selfをアプリ側が遮断しないか。
4. iPhone縦375px・横向き・iPad、safe-area、下部シート内スクロール、ピンチ、±ズーム、VoiceOverの一覧読み上げ、フォーカス循環、Escape/外部キーボード。
5. オフライン、キャッシュ無効・容量不足、新旧ファイルが混在するCDN反映途中、戻る/進む、再読み込み。
6. Web Crypto SHA-256、ES modules、BigInt、AbortController、inert等のサポート範囲を対象iOS最低バージョンで確認。inertに加えaria-hiddenとフォーカストラップを設定しています。

今回の実ブラウザー確認はCodex In-app Browserです。375px等の表示確認をiPhone実機・アプリ固有WKWebView・VoiceOver合格とは扱いません。専用WebKit自動テストランナーも実行していません。
