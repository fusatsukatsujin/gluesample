# AWS Glue サンプル（ローカル実行 / AWS実行）

Docker Compose 上で AWS 公式の Glue ローカル開発用イメージ (`amazon/aws-glue-libs`) と
S3 互換ストレージの [LocalStack](https://www.localstack.cloud/) を組み合わせ、実際の AWS
アカウントなしで Glue ETL ジョブ（PySpark / DynamicFrame）を動かせます。同じジョブスクリプトを
Terraform で実際の AWS 上（S3 + IAM + Glue Job）にもそのままデプロイできます。

## 構成

```
.
├── docker-compose.yml          # localstack (S3) + glue (aws-glue-libs) の2サービス
├── data/
│   ├── input/sales.csv         # サンプル入力データ（UTF-8）
│   └── input_sjis/sales_sjis.csv  # サンプル入力データ（Shift_JIS/CP932）
├── jobs/
│   ├── etl_job.py               # Glue ETLジョブ本体（CSV→集計→Parquet）
│   ├── read_output.py           # 出力結果を読み戻して確認するスクリプト（ローカル専用）
│   ├── convert_encoding_job.py  # 文字コード変換ジョブ（部品の利用サンプル）
│   └── lib/
│       ├── encoding_converter.py # 文字コード変換の再利用可能な部品
│       └── job_args.py           # ジョブ引数を解析する共通ヘルパー
├── scripts/
│   ├── init-s3.sh            # バケット作成 & 入力データアップロード（ローカル用）
│   ├── convert-encoding.sh   # 文字コード変換ジョブの実行（ローカル用）
│   ├── run-job.sh            # ETLジョブの実行（ローカル用。入力プレフィックスを指定可）
│   └── verify-output.sh      # 出力結果の確認（ローカル用）
└── terraform/                 # 実際の AWS 上にデプロイするための Terraform 一式
```

`jobs/` 配下のスクリプトはローカル・AWS共通です。`--S3_ENDPOINT` 引数を渡すとローカルの
LocalStack を、省略すると（Glue ジョブの IAM ロールを使って）実際の AWS S3 を参照します。

## やっていること

`jobs/etl_job.py` は `sales.csv`（注文明細）を S3 から読み込み、

1. `quantity * price` で `total_amount` を算出
2. `quantity <= 0` の行を除外
3. 商品ごとに数量・売上を集計

した結果を Parquet として S3 に書き戻す、典型的な Glue DynamicFrame ETL ジョブです。
ローカル実行時は `--S3_ENDPOINT` 引数で Hadoop の S3A コネクタを LocalStack に向けることで、
実 AWS 環境なしに同じコードがそのまま動作します。

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

## AWS 上で実行する（Terraform）

`terraform/` に、実際の AWS 上で同じジョブを動かすための最小構成が入っています。

- S3 バケット（スクリプト・入力データ配置用。`terraform apply` 時に自動アップロード）
- Glue ジョブ用 IAM ロール（`AWSGlueServiceRole` + このバケットへの S3 アクセス権のみ）
- Glue Job × 2
  - `<project_name>-etl-job`（Spark / `glueetl`）— `jobs/etl_job.py`
  - `<project_name>-convert-encoding-job`（Python shell）— `jobs/convert_encoding_job.py`

VPC やコネクションは使わないため、ネットワーク周りの設定は不要です。

### 1. 事前準備

- Terraform >= 1.5
- AWS CLI が使える認証情報（`aws configure` 済み、または環境変数）

### 2. デプロイ

```bash
cd terraform
terraform init
terraform apply
```

`bucket_name` を指定しない場合はランダムなサフィックス付きで自動生成されます
（`terraform.tfvars.example` を参考に `terraform.tfvars` を作成してカスタマイズ可能）。

### 3. ジョブを実行

`terraform apply` の出力に表示される AWS CLI コマンドで実行できます。

```bash
# 出力例の run_etl_job_command / run_convert_encoding_job_command を実行
aws glue start-job-run --job-name <project_name>-etl-job --region ap-northeast-1
```

ジョブの実行状況・ログは AWS マネジメントコンソールの Glue ジョブ画面、または
CloudWatch Logs（ロググループ `/aws-glue/jobs/output` など）で確認できます。

変換済みデータに対して ETL ジョブを実行したい場合は、`start-job-run` に
`--arguments` でデフォルト値を上書きします。

```bash
aws glue start-job-run \
  --job-name <project_name>-etl-job \
  --arguments '{"--INPUT_PREFIX":"input_converted/"}'
```

### 4. 後片付け

```bash
terraform destroy
```

S3 バケット・IAM ロール・Glue ジョブには課金が発生し得ます（特に Glue ジョブの実行時間）。
使い終わったら忘れずに `terraform destroy` してください。

## 文字コード変換部品について

`jobs/lib/encoding_converter.py` は Spark/GlueContext に依存しない、boto3 だけで
動く小さな部品です。

- `convert_encoding(body, src_encoding, dst_encoding, errors="strict")`
  bytes を指定エンコーディングでデコードし、別のエンコーディングでエンコードし直します。
- `convert_s3_object(s3_client, bucket, src_key, dst_key, src_encoding="cp932", dst_encoding="utf-8", errors="strict")`
  S3 上のオブジェクトを読み込み、変換した結果を別のキーに書き込みます。

他のジョブから使う場合は次のように import して呼び出すだけです（AWS Glue 上では
`--extra-py-files` でこのファイルを配布すれば普通に import でき、ローカル実行時のみ
`sys.path` にコンテナ内のパスを追加するフォールバックを入れています。
`jobs/convert_encoding_job.py` の実装を参照してください）。

```python
try:
    from encoding_converter import convert_s3_object
except ImportError:
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
- `jobs/` 配下のスクリプトはローカル・AWS共通なので、`terraform/` 側の
  `aws_s3_object` リソースが参照しているファイルを変更すれば、次の
  `terraform apply` で AWS 側のジョブにも反映されます。
