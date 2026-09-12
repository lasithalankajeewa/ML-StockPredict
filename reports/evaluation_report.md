# SmartStock AI Evaluation Report

## Objective and protocol

The task is to predict total unit demand for the next seven days for each M5
product-store series. Evaluation compares a seasonal naive baseline, a small
artificial neural network (ANN), the original mixed-input deep neural network
(DNN), and five controlled DNN architecture variants.

Splits are chronological. Training ends on 6 March 2016. Validation covers
14 March through 10 April 2016, and the untouched final test covers 18 April
through 15 May 2016. A seven-day purge gap precedes validation and test because
each target contains the following seven days. Model selection uses validation
WAPE only. The selected DNN and fitted preprocessing are frozen before final
test evaluation; the test set is not used for tuning or refitting.

The final test includes all 853,720 available rolling origins across 3,049
products and ten stores. Adjacent origins have overlapping target windows, so
these rows are not independent observations.

## Metrics

- **MAE** measures average absolute unit error and is easy to interpret.
- **RMSE** gives additional weight to large misses.
- **WAPE** divides total absolute error by total actual demand. It is the primary
  selection metric and is not an accuracy percentage.

## Validation and model selection

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| Seasonal naive | 3.9683 | 8.7626 | 41.0953% |
| ANN | 3.3936 | 7.6667 | 35.1436% |
| Tuned DNN D | 3.3532 | 7.7894 | 34.7256% |
| Original DNN | **3.3449** | **7.6535** | **34.6389%** |

The original DNN had the lowest validation WAPE and was selected. Five tuning
runs changed hidden-layer width/depth, dropout, and learning rate while keeping
the training and validation samples fixed. None beat the original DNN, so the
evaluation retained the preselected model.

## Final test results

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| Seasonal naive | 3.9368 | 8.3140 | 39.2464% |
| Original DNN | **3.3743** | **7.4473** | **33.6388%** |

The DNN reduces WAPE by 5.61 percentage points, or 14.29% relative to the
baseline. It also achieves lower MAE, RMSE, and WAPE in every store. Store-level
DNN WAPE ranges from 29.70% in CA_3 to 38.45% in CA_4.

## Error analysis

The model improves WAPE in all three categories. FOODS has the lowest DNN WAPE
at 31.26%, HOUSEHOLD reaches 36.28%, and HOBBIES is hardest at 44.26%. Relative
improvement over the naive baseline is largest for HOBBIES at 18.41%.

Demand-level analysis shows the largest relative gain for low-demand nonzero
targets: WAPE falls from 67.51% to 50.18%, a 25.67% improvement. Medium-demand
WAPE improves by 13.18%. High-demand items remain challenging; WAPE improves
from 25.47% to 24.03%, only 5.63% relative. WAPE is undefined for zero-demand
targets, so MAE and RMSE are reported for that group instead.

The DNN has negative aggregate bias in every product category and in the medium
and high demand groups, indicating underforecasting. This matters operationally
because persistent underforecasting can increase stockout risk even when total
absolute error improves.

## Limitations

- M5 reflects historical Walmart demand in three US states and may not transfer
  to other retailers or current conditions.
- Rolling seven-day targets overlap and should not be interpreted as independent
  repeated trials.
- The model returns point forecasts without prediction intervals.
- The feature set does not represent lead times, supplier constraints,
  substitutions, case packs, margins, or spoilage.
- M5 has no inventory levels. Dashboard stock and safety-stock quantities are
  deterministic demonstration values and are not part of model evaluation.
- The dashboard catalog is a frozen forecast snapshot dated 15 May 2016.

## Reproducibility artifacts

Detailed tables, plots, predictions, evaluation metadata, and artifact hashes
are saved under [`reports/results/final_test`](results/final_test/). The selected
model bundle is stored under `models/trained/best_model_20260912T132137305253Z/`.
Its model and preprocessing SHA-256 hashes are recorded in `evaluation.json`.
