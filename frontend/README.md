# SmartStock dashboard

A focused Next.js dashboard for the frozen seven-day demand model. It includes
all 30,490 product-store forecasts, server-side search, store and risk filters,
and pagination. Final model metrics and forecasts come from the evaluated DNN.
Current inventory and safety stock values are demonstration inputs because the
M5 dataset does not contain live inventory.

Rebuild the dashboard catalog from the repository root when final predictions
change:

```powershell
.\.venv\Scripts\python.exe scripts\build_dashboard_catalog.py
```

Run FastAPI from the repository root:

```powershell
python -m uvicorn api.main:app --reload
```

Then run the dashboard:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3000`. The dashboard reads the frozen final forecast
catalog locally. The `/api/predict` route remains available for live requests
and proxies to `http://127.0.0.1:8000/predict`; override that URL with
`FASTAPI_URL` in `.env.local`.
