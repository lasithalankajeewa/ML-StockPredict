# M5 Dataset Notes

SmartStock AI uses data from the **M5 Forecasting - Accuracy** competition. Place
these files manually in `data/raw/`:

- `calendar.csv`
- `sales_train_evaluation.csv`
- `sell_prices.csv`

Raw dataset files are intentionally excluded from Git. Loading all three files
with `load_raw_data()` validates their schemas, required values, key uniqueness,
numeric ranges, and cross-file relationships before downstream work begins. The
development pipeline currently uses `CA_1` as a validation partition and converts
its sales from wide to memory-optimized long format. Feature calculations group
each series by both `store_id` and `item_id`, preventing cross-store leakage when
all store partitions are processed later.
