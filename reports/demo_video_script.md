# SmartStock AI Demo Video Script

Target duration: 6–8 minutes. Record the screen at 1080p with readable terminal
text and narration. Replace the pending link in the root README after upload.

## 0:00–0:45 — Problem and objective

- Introduce the stockout versus overstock problem.
- State the objective: predict total product demand for the next seven days.
- Explain that the forecast becomes a reorder quantity and risk level.

## 0:45–1:30 — Repository and data

- Show the root README and repository structure.
- Open `reports/dataset_notes.md` and identify the M5 source and usage rules.
- Mention 3,049 products, ten stores, and 30,490 product-store series.
- Explain that the download script recreates raw data on a fresh machine.

## 1:30–2:30 — EDA and feature pipeline

- Open `notebooks/01_eda.ipynb` and show two or three visualizations.
- State the key findings: zero-heavy demand, weekday effects, store/category
  differences, events, and price changes.
- Show `notebooks/02_feature_engineering.ipynb` or `src/data/pipeline.py`.
- Mention lag, rolling, calendar, event, and price features and store-item
  grouping that prevents cross-store history leakage.

## 2:30–4:00 — Models and evaluation

- Open `notebooks/03_model_experiments.ipynb`.
- Show the seasonal naive, ANN, original DNN, and five tuning architectures.
- Explain chronological splits and seven-day purge gaps.
- Show the final test metric plot and evaluation report.
- State DNN WAPE 33.64% versus naive WAPE 39.25%, a 14.29% relative reduction.
- Briefly show per-store and category/demand-level error plots and mention the
  model's underforecasting limitation.

## 4:00–4:45 — FastAPI

- Start `python -m uvicorn api.main:app --reload`.
- Open `/health` and `/docs`.
- Run one `/predict` example and explain forecast, safety stock, reorder, and
  HIGH/MEDIUM/LOW risk.

## 4:45–6:30 — Dashboard

- Start the Next.js dashboard and open `http://localhost:3000`.
- Show the four summary cards.
- Search for `FOODS_3_090`.
- Filter by `CA_1`, then filter by `Needs reorder`.
- Move between pages and select a product row.
- Explain historical demand, seven-day forecast, current inventory, safety
  stock, stock coverage, and the recommended reorder.
- State clearly that inventory values are demonstration inputs because M5 does
  not contain live stock.

## 6:30–7:15 — Reproducibility and close

- Return to the README quick-start commands.
- Show the committed model bundle and final report artifacts.
- Summarize the achieved improvement and practical limitations.
- End with the GitHub repository URL.
