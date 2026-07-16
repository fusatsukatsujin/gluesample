# AWS Glue ローカル実行サンプル

Docker Compose 上で AWS 公式の Glue ローカル開発用イメージ (`amazon/aws-glue-libs`) と
S3 互換ストレージの [LocalStack](https://www.localstack.cloud/) を組み合わせ、実際の AWS
アカウントなしで Glue ETL ジョブ（PySpark / DynamicFrame）を動かすサンプルです。

## 構成

```
.
├── docker-compose.yml          # localstack (S3) + glue (aws-glue-libs) の2サービス
├── data/
│   ├── input/sales.csv         # サンプル入力データ（UTF-8）
│   └── input_sjis/sales_sjis.csv  # サンプル入力データ（Shift_JIS/CP932）
├── jobs/
│   ├── etl_job.py               # Glue ETLジョブ本体（CSV→集計→Parquet）
│   ├── read_output.py           # 出力結果を読み戻して確認するスクリプト
│   ├── convert_encoding_job.py  # 文字コード変換ジョブ（部品の利用サンプル）
│   └── lib/
│       └── encoding_converter.py # 文字コード変換の再利用可能な部品
└── scripts/
    ├── init-s3.sh            # バケット作成 & 入力データアップロード
    ├── convert-encoding.sh   # 文字コード変換ジョブの実行
    ├── run-job.sh            # ETLジョブの実行（入力プレフィックスを指定可）
    └── verify-output.sh      # 出力結果の確認
```

## やっていること

`jobs/etl_job.py` は `sales.csv`（注文明細）を S3 から読み込み、

1. `quantity * price` で `total_amount` を算出
2. `quantity <= 0` の行を除外
3. 商品ごとに数量・売上を集計

した結果を Parquet として S3 に書き戻す、典型的な Glue DynamicFrame ETL ジョブです。
Hadoop の S3A コネクタのエンドポイントを LocalStack に向けることで、実 AWS 環境なしに
同じコードがそのまま動作します。

## 前提条件

- Docker / Docker Compose
- Apple Silicon Mac の場合、`amazon/aws-glue-libs` は amd64 イメージのため
  エミュレーション経由で起動します（`docker-compose.yml` に `platform: linux/amd64` を指定済み）。
  初回起動やジョブ実行は数分かかることがあります。

## 使い方

### 1. コンテナ起動

```bash
docker compose up -d
```

LocalStack の起動完了（ヘルスチェック通過）を待ってから次に進んでください。

```bash
docker compose ps
```

### 2. サンプルデータを S3(LocalStack) に配置

```bash
./scripts/init-s3.sh
```

### 3. Glue ETL ジョブを実行

```bash
./scripts/run-job.sh
```

ジョブ内の `summary_df.show()` によって、集計結果がコンソールに表示されます。

### 4. 出力結果の確認

```bash
./scripts/verify-output.sh
```

`s3://glue-sample-bucket/output/sales_summary/` 配下の Parquet ファイル一覧と、
その中身が表示されます。

### 5. （任意）文字コード変換部品を試す

現場でよくある「Shift_JIS(CP932) で出力された CSV を UTF-8 に変換してから処理する」
というシナリオのサンプルです。`jobs/lib/encoding_converter.py` が変換処理そのものを
行う部品で、`jobs/convert_encoding_job.py` がその部品を S3 上のオブジェクトに対して
適用するジョブです。

`data/input_sjis/sales_sjis.csv`（`./scripts/init-s3.sh` で
`s3://glue-sample-bucket/input_sjis/` にアップロード済み）を CP932 → UTF-8 に変換し、
`s3://glue-sample-bucket/input_converted/` に書き出します。

```bash
./scripts/convert-encoding.sh
```

変換後、同じ ETL ジョブを変換済みデータに対して実行できます（第一引数で入力
プレフィックスを指定）。

```bash
./scripts/run-job.sh input_converted/
```

日本語の商品名・顧客名が文字化けせずに集計結果へ反映されることを確認できます。

### 6. 後片付け

```bash
docker compose down -v
```

## 文字コード変換部品について

`jobs/lib/encoding_converter.py` は Spark/GlueContext に依存しない、boto3 だけで
動く小さな部品です。

- `convert_encoding(body, src_encoding, dst_encoding, errors="strict")`
  bytes を指定エンコーディングでデコードし、別のエンコーディングでエンコードし直します。
- `convert_s3_object(s3_client, bucket, src_key, dst_key, src_encoding="cp932", dst_encoding="utf-8", errors="strict")`
  S3 上のオブジェクトを読み込み、変換した結果を別のキーに書き込みます。

他のジョブから使う場合は次のように import して呼び出すだけです。

```python
import sys
sys.path.insert(0, "/home/glue_user/workspace/jobs/lib")
from encoding_converter import convert_s3_object

convert_s3_object(s3_client, "my-bucket", "raw/data.csv", "converted/data.csv",
                   src_encoding="cp932", dst_encoding="utf-8")
```

`errors` 引数（`"strict"` / `"ignore"` / `"replace"` など、Python標準の
`bytes.decode`/`str.encode` の仕様に準拠）を変えることで、変換できない文字が
含まれる場合の挙動も制御できます。

## カスタマイズのヒント

- `data/input/sales.csv` を差し替えれば、別データでジョブを試せます。
- `jobs/etl_job.py` の集計ロジック（`groupBy` 以降）を変更すれば、任意の変換処理を試せます。
- 実際の AWS 環境に持っていく場合は、`fs.s3a.endpoint` などの LocalStack 向け設定
  （`etl_job.py` 冒頭の `hadoop_conf.set(...)` 部分）を削除するだけで、
  そのまま AWS Glue ジョブとしてデプロイできます。
