# Dataset Source, Access, and Usage

## Stored raw CSV files

SmartStock AI uses three raw CSV files stored in the project under `data/raw/`:

| File | Purpose |
|---|---|
| `calendar.csv` | Maps day identifiers to dates, weekdays, months, events, SNAP indicators, and selling weeks. |
| `sales_train_evaluation.csv` | Contains the product hierarchy, store identifiers, and daily unit demand in wide format. |
| `sell_prices.csv` | Contains weekly product selling prices for each store. |

The pipeline expects this exact layout:

```text
data/
  raw/
    calendar.csv
    sales_train_evaluation.csv
    sell_prices.csv
```

Do not rename the files or change their column names. The loader reads them from
`data/raw/` using the filenames defined in `src/config.py`.

## Validate the stored files

From the repository root, activate the Python environment and run:

```powershell
python -c "from src.data.load_data import load_raw_data; data = load_raw_data(); print({name: frame.shape for name, frame in data.items()})"
```

`load_raw_data()` checks the CSV schemas, required values, unique keys, demand
and price ranges, and relationships between the files. It stops with an
actionable error when a file is missing or invalid.

## Build model-ready data

Build a single store first:

```powershell
python -m src.data.pipeline --stores CA_1
```

Build all stores from the stored raw CSV files:

```powershell
python -m src.data.pipeline --overwrite
```

The pipeline converts daily sales from wide to long format, joins calendar and
price data, removes unavailable pre-release history, creates the seven-day
target, and calculates lag, rolling, price, event, and cyclical time features.
It processes stores sequentially to control memory usage.

Generated partitions are written to:

```text
data/processed/features/store_id=<STORE_ID>/features.parquet
```

The accompanying `manifest.csv` records row counts, date coverage, file sizes,
and output locations. All time-series features are grouped by `store_id` and
`item_id`, preventing demand history from crossing store boundaries.

## Moving the project to another machine

The raw CSV files are local project inputs. Two files exceed GitHub's standard
100 MB per-file limit, so they are excluded from normal Git commits. After
cloning the repository on another machine, copy the same three stored CSV files
into `data/raw/` before rebuilding features or rerunning model training.

The committed selected model, evaluation results, and dashboard catalog do not
need the raw CSV files. They allow FastAPI and the Next.js dashboard to run
immediately after installing dependencies.
