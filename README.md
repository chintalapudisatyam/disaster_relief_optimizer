# Disaster Relief Distribution Optimizer (OT project)

Linear Programming (PuLP + CBC) + FastAPI + plain HTML/JS frontend (no npm needed).

## Run (Windows)
```
cd disaster-relief-optimizer
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```
Open https://disaster-relief-optimizer-m8hg.onrender.com



## Model (see optimization/model.py — fully commented)
- x[i,j,k] >= 0: quantity of resource k sent from warehouse i to area j
- u[j,k] >= 0: unmet demand of resource k at area j
- Minimize  sum c[i][j]*x[i,j,k] + P * sum w[j]*u[j,k]   (w: High=5, Medium=3, Low=1)
- Supply:   sum_j x[i,j,k] <= S[i][k]
- Demand:   sum_i x[i,j,k] + u[j,k] = D[j][k]
- Vehicles: sum x <= sum(capacity*trips)   (aggregate version)

## Status
Done: Phases 1-7 (input workflow, LP model, multi-resource, unmet demand, priority, vehicle capacity, results tables/KPIs).
Next: charts, scenario comparison, baselines, export, SQLite storage, presentation mode, "About the Model" page.
