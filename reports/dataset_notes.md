# M5 Dataset Notes

SmartStock AI uses data from the **M5 Forecasting - Accuracy** competition. Place
these files manually in `data/raw/`:

- `calendar.csv`
- `sales_train_evaluation.csv`
- `sell_prices.csv`

Raw dataset files are intentionally excluded from Git. Loading all three files
with `load_raw_data()` validates their schemas, required values, key uniqueness,
numeric ranges, and cross-file relationships before downstream work begins. The
development pipeline currently filters to `CA_1` and converts its sales from wide
to memory-optimized long format. Scaling that transformation to every store is
deferred until the complete preprocessing pipeline is verified.
