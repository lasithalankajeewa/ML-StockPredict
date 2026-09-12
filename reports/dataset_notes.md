# Dataset Source, Access, and Usage

## Source

SmartStock AI uses the **M5 Forecasting - Accuracy** competition dataset hosted
by Kaggle:

- Data page: <https://www.kaggle.com/competitions/m5-forecasting-accuracy/data>
- Competition rules: <https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules>
- Results paper: Makridakis et al., *The M5 accuracy competition: Results,
  findings and conclusions*, International Journal of Forecasting, 2022,
  <https://doi.org/10.1016/j.ijforecast.2021.11.013>.

The dataset contains daily unit sales for 3,049 Walmart products across ten
stores in California, Texas, and Wisconsin. It also includes calendar events,
SNAP indicators, product hierarchies, and weekly selling prices.

## License and usage conditions

Kaggle distributes these files subject to the M5 competition rules. This
repository does not relicense or redistribute the raw data. Every user must have
a Kaggle account, accept the competition rules on the competition page, and use
the data according to those rules. The project source code is separate from the
dataset's usage terms.

The three required files are:

- `calendar.csv`
- `sales_train_evaluation.csv`
- `sell_prices.csv`

The raw files are intentionally excluded from Git because two exceed GitHub's
100 MB per-file limit. Processed feature partitions are also generated locally
and excluded because they total hundreds of megabytes.

## Reproducible download

Install the project dependencies, configure Kaggle credentials, and accept the
competition rules in your browser. Kaggle accepts either a `kaggle.json` token
or `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables. Then run:

```powershell
python scripts/download_m5_data.py
```

The script invokes Kaggle's official API, downloads the competition archive,
extracts only the three required files into `data/raw/`, and verifies that each
file exists and is nonempty. Use `--force` to replace existing raw files and
`--keep-archive` to retain the downloaded ZIP.

Build leakage-safe feature partitions after downloading:

```powershell
python -m src.data.pipeline
```

The pipeline validates schemas, required values, unique keys, demand and price
ranges, and cross-file relationships. It processes stores sequentially and
writes `data/processed/features/store_id=<STORE_ID>/features.parquet` plus a
manifest. Time-series calculations group by both `store_id` and `item_id` to
prevent history from crossing store boundaries.

## Expected local storage

The raw download is several hundred megabytes and the complete processed
feature set is larger. Ensure at least 2 GB of free space before building every
store. These local files can always be recreated from the documented source and
pipeline, so they should remain outside version control.
