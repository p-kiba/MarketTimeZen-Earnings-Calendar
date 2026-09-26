# ChatGPTへの企業間取引調査の依頼

## 使い方

過去の企業間取引の調査結果はJSONで受け取ります。一つの取引に複数の金額・条件・根拠を保持できるためです。CSVは人が一覧を読む用途には使えますが、今回の受け渡しにはJSONを使います。

下の「依頼文」をコピーし、対象企業と期間を変更してChatGPTへ渡してください。この文書ごと添付し、「この依頼文と形式に従って調査してください」と指定しても構いません。最初は5社程度、1回につき最大20件を目安にします。件数を埋めるために弱い根拠を採用しません。途中結果は未調査範囲とともに保存し、続きを依頼するときは前回のJSONを渡します。

記入用JSONは [chatgpt-relationship-research.template.json](examples/chatgpt-relationship-research.template.json) です。テンプレートの空欄は未調査であり、実際の企業・取引データではありません。配列内の見本を実際の調査結果に置き換えます。金額が見つからなければ `amounts: []` にします。

この形式は**調査結果の受け渡し用**です。現時点でこのJSONを読み込む専用コマンドは未実装です。既存の `apply-review-batch` や `deal_rules.json` に直接渡さないでください。取り込み時に原文との照合、企業名の解決、重複確認を行い、確認できた項目だけを公開データへ移します。承認状態、内部ID、根拠のハッシュはChatGPTに生成させません。

既存の灰色の線の金額補完には、[金額補完専用の依頼文と調査対象](chatgpt-amount-research.md) を併用してください。そこでは新しい関係を増やすより、現在の関係に足りない金額・通貨・条件の根拠を探すことを優先します。

## 依頼文（ここからコピー）

投資家向け企業間マップのため、以下の企業の過去の取引関係を、ウェブ検索で一次資料を実際に開いて調査してください。

- 対象企業：［調査する企業名またはティッカーを5社程度記入］
- 発表・開示日の対象期間：［YYYY-MM-DD］〜［YYYY-MM-DD］
- 調査基準日：［YYYY-MM-DD］
- 優先順位：大型契約、出資、買収、重要な供給契約・クラウド契約、事業内容が具体的に分かる提携。
- 相手企業は対象リスト外、非上場、米国外でも収録対象です。対象企業ごとに複数の相手先を探してください。
- 1回の出力は最大20レコードです。見つかった件数と調査が完了した範囲を正直に報告し、件数合わせをしないでください。

### 調査と記録のルール

1. 企業公式IR、公式ニュースルーム、SEC提出資料・添付契約書の公開ページやPDFを根拠にしてください。特定APIの使用は不要です。報道記事は一次資料を探す手がかりには使えますが、報道のみ・検索結果の要約のみ・モデルの記憶のみでレコードを作らないでください。
2. 実際に開いて本文を確認できた一次資料の直接URLだけを `sources` に入れてください。閲覧不能なら推測で埋めず、`coverage.remaining_work` に記録してください。提出一覧や検索ページを取引内容の根拠にしないでください。
3. 1レコードは「二社間の一つの取引について、一つの発表・変更・完了などの出来事」です。同じ出来事の複数資料は一つにまとめます。同じ二社でも異なる契約は分け、同じ契約の変更・完了は別レコードにし、分かる範囲で `related_record_ids` で結んでください。
4. 二社が同じページに載っているだけでは関係にしません。共同出資者同士、顧客一覧に並んだ企業同士、複数社の会議参加者同士に関係を作らないでください。直接の取引関係が明示されたペアだけを収録してください。
5. `company_a` と `company_b` は資料に記載された当事者名を残してください。子会社や部門を推測で親会社へ置き換えず、Google／Alphabet、AWS／Amazonも原文どおり記録します。表示上の統合は取り込み後に行います。ティッカーやCIKの推測は不要です。
6. `summary_ja` は「誰が、誰に、何を提供・購入・共同開発するか」を日本語で1〜2文にしてください。「戦略的提携」のみでは不十分です。資料の事実と将来計画・条件付き事項を区別してください。
7. 金額は原文表記を残し、契約総額・追加額・年額・上限・実際の支払額・支払予定額を別要素にしてください。年額×年数、為替換算、複数発表の足し算、株数×株価などの推計はしないでください。企業評価額や企業全体の設備投資額を二社間取引の金額にしないでください。
8. 複数社に共通の資金調達総額などは二社へ配分しません。関係の文脈として金額を残す場合は `scope: "multi_party"` とし、`conditions` に二社間金額ではないと記載してください。単独の二社間金額は `bilateral`、範囲不明は `unknown` です。
9. `$` のみでUSDと決めないでください。USD・US$・U.S. dollarsなどの明示、契約書の通貨定義、該当数値に結び付くSEC XBRL単位の根拠がなければ `currency: null` にします。通貨根拠が別資料ならその資料も追加してください。
10. 金額未記載は `amount_disclosure: "not_stated_in_source"`、明示的な非開示は `"explicitly_undisclosed"`、伏せ字は `"redacted"`、読み取れても意味不明なら `"ambiguous"` です。金額がなくても具体的な取引が確認できれば収録してください。
11. 発表日、契約開始日、契約終了日、調査日を混同しないでください。日まで確認できた日付はYYYY-MM-DD、確認できない日付は `null` とし、年・月のみ分かる場合は `notes` に記載します。発表済みを完了済みにしたり、昔の契約が現在も有効と推測したりしないでください。
12. `evidence` に、どの資料のどの箇所がどの項目を裏付けるかを書いてください。ページ番号、見出し、表名、段落の位置など、人が原文で見つけられる所在を使用します。内部パーサーの段落IDやハッシュは生成しないでください。`summary_ja` は根拠箇所の短い要約であり、全文の転載は不要です。
13. 不明は `null`、該当要素なしは `[]` とし、推測値や説明用の架空例を入れないでください。根拠のない項目は `unknowns` に残してください。`records` に一次資料のない候補を混ぜず、その探索状況は `coverage` に残します。
14. 次のJSON形式で、長文レポートを付けずに結果を返してください。可能ならUTF-8の `.json` ファイルにしてください。ファイル作成ができなければJSONコードブロック一つで返してください。承認済みとの自己判定や、自信度スコアは不要です。

### 出力形式

以下は空欄を示すテンプレートです。`is_template` は実際の調査結果では `false` にしてください。既存キーを保持し、必要な配列要素だけ追加します。調査が終わっても、確認できた出来事がなければ `records: []` としてください。

```json
{
  "schema_version": "mtz-research-candidates/1",
  "is_template": true,
  "scope": {
    "target_companies": [],
    "disclosure_date_from": null,
    "disclosure_date_to": null,
    "as_of": null
  },
  "sources": [
    {
      "id": "s1",
      "url": null,
      "title": null,
      "publisher": null,
      "published_date": null
    }
  ],
  "records": [
    {
      "id": "r1",
      "existing_relationship_id": null,
      "company_a": null,
      "company_b": null,
      "relationship_type": null,
      "direction": null,
      "summary_ja": null,
      "disclosed_on": null,
      "event_type": null,
      "status_as_disclosed": "unknown",
      "amount_disclosure": "not_stated_in_source",
      "amounts": [
        {
          "original_text": null,
          "value": null,
          "min_value": null,
          "max_value": null,
          "currency": null,
          "qualifier": "unspecified",
          "kind": "other",
          "scope": "unknown",
          "value_semantics": "unknown",
          "contingent": null,
          "conditions": null
        }
      ],
      "term": {
        "start_date": null,
        "end_date": null,
        "duration_text": null
      },
      "conditions": [],
      "evidence": [
        {
          "source_id": "s1",
          "locator": null,
          "supports": [
            "company_a",
            "company_b",
            "summary_ja"
          ],
          "summary_ja": null
        }
      ],
      "related_record_ids": [],
      "amount_research": {
        "findings": [],
        "checked_source_ids": [],
        "remaining_work": null
      },
      "unknowns": [],
      "notes": null
    }
  ],
  "coverage": [
    {
      "target_company": null,
      "searched_source_ids": [],
      "remaining_work": null
    }
  ]
}
```

### 値の指定

- `sources[].id` はファイル内だけの参照名です。URLが同じ資料は重複登録せず、複数レコードから参照します。`records[].id` もファイル内だけの番号で、本番の企業・関係IDではありません。
- `existing_relationship_id` は補完対象として渡された既存IDだけをそのまま記入します。新規の取引や対応が確定できない場合は `null`。他の契約に既存IDを流用したり、IDを生成したりしません。
- `relationship_type`：`supplier`（商品・部品の供給）、`service_provider`（サービス提供）、`partnership`（共同開発などの提携）、`investment`（出資）、`acquisition`（買収）、`subsidiary`（親子会社）、`group_member`（グループ所属）、`equity_right`（株式取得権）。関係は分かるが分類未確定なら `null`。
- `direction`：`a_to_b`、`b_to_a`、`undirected`、`unknown`。矢印は供給者→購入者、サービス提供者→顧客、出資者→出資先、買収者→買収対象、親会社→子会社です。共同提携は `undirected`、原文で判断できないものは `unknown`。
- `event_type`：`new_agreement`、`expansion`、`amendment`、`acquisition_announced`、`acquisition_closed`、`termination`、`correction`、`newly_indexed`。過去の記載を収録するだけなら `newly_indexed`、分類できなければ `null`。
- `status_as_disclosed`：`announced`、`signed`、`active`、`completed`、`terminated`、`historical`、`unknown`。**その資料が述べる時点の状態**であり、現在の有効性を意味しません。`as_of` は調査の基準日であり、全契約をその日まで追跡できたという意味ではありません。
- `amount_disclosure`：`disclosed`、`not_stated_in_source`、`explicitly_undisclosed`、`redacted`、`ambiguous`。数値は判明し通貨だけ不明なら `disclosed` のまま、`currency: null` にします。
- 金額の `value`、`min_value`、`max_value` は最小通貨単位ではなく**通貨の通常単位**の数字文字列です。例えば百万や十億という原文の倍率だけを展開し、桁区切り・通貨記号・指数表記は入れません。計算で新たな経済的意味を作らないでください。未知は `null` です。
- `qualifier`：`exact`、`approximately`、`up_to`、`at_least`、`more_than`、`range`、`unspecified`。`exact` / `approximately` は `value`、`up_to` は `max_value`、`at_least` / `more_than` は `min_value`、`range` は上下限を使い、それ以外の数値欄は `null` にします。「multi-billion」など不定の表現は原文だけ残し、数値欄をすべて `null` にします。
- `kind`：`contract_total`（契約総額）、`increment`（追加額）、`annual`（年額）、`paid`（支払済み）、`planned`（支払予定）、`purchase_price`（買収価格）、`investment`（出資額）、`other`。上限や条件付きかどうかは `qualifier` と `conditions` にも残します。買収価格は総額、株式価値、企業価値、取得現金控除後などの範囲を `conditions` に明記します。
- `currency` は根拠のあるISO 4217コード（USDなど）または `null`。`evidence[].supports` に `amounts[0].currency` などを指定し、通貨根拠をたどれるようにしてください。同様に `amounts[0].value`、`term`、`disclosed_on`、`status_as_disclosed` などを根拠箇所に結び付けます。
- `value_semantics`：`original_total`（その取引の当初総額）、`revised_total`（変更後の総額）、`increment`（追加分）、`periodic`（年額等）、`contingent`（条件付き部分）、`unknown`。取得現金控除後など総額との対応が未確定なものを `original_total` にしないでください。
- `contingent` は成果条件・追加購入オプションなどに依存する金額なら `true`、金額がそれらに依存しないという根拠を確認できた場合だけ `false`、確認できなければ `null`。条項が見つからないことだけで `false` にしないでください。
- `amount_research.findings` は金額調査を行った場合だけ、`amount_found`、`currency_resolved`、`terms_resolved`、`explicitly_undisclosed`、`redacted`、`not_found_in_reviewed_sources`、`access_blocked` から該当する結果を列挙します。未着手は `[]`。調査した資料を `checked_source_ids` に残し、結果の根拠は `evidence` へ対応付けます。これは調査者の報告で、公開承認や色付けの指示ではありません。
- `coverage` は対象企業ごとに必ず残してください。確認した資料IDと未調査期間・未確認契約・閲覧不能URLなどを `remaining_work` に簡潔に書きます。見つからなかったことを「取引関係が存在しない」と断定しないでください。

## 次の回を依頼するとき

前回のJSONを渡し、次のように依頼します。

> 前回JSONのcoverage.remaining_workから調査を続けてください。同じ出来事の重複を除き、追加分だけ同じ形式で返してください。既存出来事への補足・訂正はnotesに前回ファイル名とレコードID、変更点を明記してください。今回のsourcesには今回参照する資料を含め、source_idは今回ファイル内で解決できるようにしてください。今回ファイル外のレコードIDをrelated_record_idsに入れないでください。
