# AWS Glue ローカル実行サンプル

Docker Compose 上で AWS 公式の Glue ローカル開発用イメージ (`amazon/aws-glue-libs`) と
S3 互換ストレージの [LocalStack](https://www.localstack.cloud/) を組み合わせ、実際の AWS
アカウントなしで Glue ETL ジョブ（PySpark / DynamicFrame）を動かすサンプルです。

## 構成

```
.
├── docker-compose.yml      # localstack (S3) + glue (aws-glue-libs) の2サービス
├── data/input/sales.csv    # サンプル入力データ
├── jobs/
│   ├── etl_job.py          # Glue ETLジョブ本体（CSV→集計→Parquet）
│   └── read_output.py      # 出力結果を読み戻して確認するスクリプト
└── scripts/
    ├── init-s3.sh          # バケット作成 & 入力データアップロード
    ├── run-job.sh           # ETLジョブの実行
    └── verify-output.sh     # 出力結果の確認
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

### 5. 後片付け

```bash
docker compose down -v
```

## カスタマイズのヒント

- `data/input/sales.csv` を差し替えれば、別データでジョブを試せます。
- `jobs/etl_job.py` の集計ロジック（`groupBy` 以降）を変更すれば、任意の変換処理を試せます。
- 実際の AWS 環境に持っていく場合は、`fs.s3a.endpoint` などの LocalStack 向け設定
  （`etl_job.py` 冒頭の `hadoop_conf.set(...)` 部分）を削除するだけで、
  そのまま AWS Glue ジョブとしてデプロイできます。
