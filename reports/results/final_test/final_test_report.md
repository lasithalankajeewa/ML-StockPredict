# Final test evaluation

The saved original DNN was selected using validation results before this evaluation. Its weights and fitted preprocessing were loaded unchanged; no retraining or model selection used the test scores.

- Forecast-origin dates: 18 April through 15 May 2016 (28 days).
- Coverage: all 853,720 available item-store origins across ten stores, without sampling.
- Target: total demand over the following seven days.
- Protocol: rolling origins with observed history available at each origin; seven-day target windows overlap.
- Separation: a seven-day purge gap follows the validation origins ending 10 April 2016.

| Model | MAE | RMSE | WAPE (%) |
|---|---:|---:|---:|
| Seasonal Naive | 3.9368 | 8.3140 | 39.2464 |
| DNN (original) | 3.3743 | 7.4473 | 33.6388 |

The DNN reduces WAPE by 5.6076 percentage points (14.29% relative to naive). Its MAE, RMSE, and WAPE are lower in all ten stores.

Overall metrics pool observation-level errors across stores. WAPE is total absolute error divided by total actual demand, multiplied by 100. It is not an accuracy percentage.

The original validation WAPE was 34.6389%. Test WAPE is 33.6388%; the periods differ, so this is not a paired comparison or an uncertainty estimate. These overlapping rolling forecasts do not measure a single fixed-origin 28-day forecast.

## Saved results

- [Overall metrics](test_summary.csv)
- [Per-store metrics](test_by_store.csv)
- [Metrics chart](test_metrics.png)
- [Per-store WAPE chart](test_wape_by_store.png)
- [Evaluation metadata and artifact hashes](evaluation.json)
- [Individual predictions by store](predictions/)

All saved predictions were independently checked against the reported overall metrics. Model and preprocessing SHA-256 hashes match before and after evaluation. The model bundle metadata now records the completed test evaluation.
