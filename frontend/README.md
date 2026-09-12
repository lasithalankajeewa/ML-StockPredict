# SmartStock dashboard

A focused Next.js dashboard for the frozen seven-day demand model. Final model
metrics and forecasts come from the evaluated DNN. Current inventory and safety
stock values are demonstration inputs because the M5 dataset does not contain
live inventory.

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

Open `http://localhost:3000`. The **Refresh with live model** button is proxied
through the Next.js server to `http://127.0.0.1:8000/predict`. Override that URL
with `FASTAPI_URL` in `.env.local`.
