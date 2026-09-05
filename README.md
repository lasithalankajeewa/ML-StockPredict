# SmartStock AI

SmartStock AI is a retail inventory decision-support project based on the M5
Forecasting - Accuracy dataset.

## Problem Statement

Retail businesses must maintain enough inventory to satisfy future demand while
avoiding unnecessary overstock. SmartStock AI will use historical retail sales
data and a Deep Neural Network to forecast product-level short-term demand and
convert those predictions into inventory risk alerts and reorder recommendations.

## ML Objective

Predict total product demand for the next 7 days.

## Planned Pipeline

```text
M5 Raw Data
-> Data Cleaning
-> Wide-to-Long Transformation
-> Feature Engineering
-> Chronological Train/Validation/Test Split
-> Naive Baseline
-> ANN
-> DNN
-> Evaluation
-> FastAPI
-> Next.js Application
-> Reorder Recommendations
```

## Planned Evaluation Metrics

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Weighted Absolute Percentage Error (WAPE)

## Dataset Files

Download the M5 data manually and place these files in `data/raw/`:

- `calendar.csv`
- `sales_train_evaluation.csv`
- `sell_prices.csv`

The raw files are ignored by Git and must not be committed. The application does
not download the dataset automatically.

Load and validate all three files from Python with:

```python
from src.data.load_data import load_raw_data

raw_data = load_raw_data()
```

Validation fails fast with one actionable summary if schemas, required values,
unique keys, demand or price ranges, or cross-file relationships are invalid.
Use `load_raw_data(validate=False)` only when intentionally inspecting invalid
source data.

## Project Structure

```text
data/          Raw, processed, and demonstration data
notebooks/     EDA, feature-engineering, and model experiment notebooks
src/           Data pipeline, models, configuration, and utilities
models/        Generated trained models and preprocessing artifacts
api/           FastAPI application and future service layer
reports/       Project notes, evaluation results, and figures
tests/         Automated tests
```

## Setup in VS Code (Windows PowerShell)

Use Python 3.11, 3.12, or 3.13. Python 3.14 is not currently supported because
TensorFlow does not publish a compatible wheel for it. Python 3.11 is the
recommended interpreter for this project.

Verify that Python 3.11 is installed:

```powershell
py -0p
py -3.11 --version
```

If it is missing, install it with Windows Package Manager, then reopen the VS
Code terminal:

```powershell
winget install --exact --id Python.Python.3.11
```

Then, from the repository root, run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.version); assert sys.version_info[:2] == (3, 11)"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation for the current process, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

If `.venv` was accidentally created with Python 3.14, deactivate it, remove only
the repository's `.venv` directory, and recreate it with `py -3.11 -m venv
.venv`. A virtual environment keeps the Python version with which it was created;
installing another Python version does not change an existing environment.

Select `.venv` as the Python interpreter in VS Code. Then start Jupyter with:

```powershell
jupyter notebook
```

Start the API development server with:

```powershell
python -m uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000/health` to check the service, or
`http://127.0.0.1:8000/docs` for the generated API documentation.

Run the tests with:

```powershell
python -m pytest
```

## Current Scope

This repository currently contains the project scaffold, configuration, raw M5
CSV loaders, schema and data-quality validation, minimal notebooks, and an API
health endpoint. It intentionally does not yet implement preprocessing, feature
engineering, model architectures, training, predictions, inventory calculations,
or exploratory analysis.
