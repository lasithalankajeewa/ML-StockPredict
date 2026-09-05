# M5 Dataset Notes

SmartStock AI uses data from the **M5 Forecasting - Accuracy** competition. Place
these files manually in `data/raw/`:

- `calendar.csv`
- `sales_train_evaluation.csv`
- `sell_prices.csv`

Raw dataset files are intentionally excluded from Git. Loading all three files
with `load_raw_data()` now validates their schemas, required values, key
uniqueness, numeric ranges, and cross-file relationships before downstream work
begins. Wide-to-long transformation and exploratory analysis remain deferred.
