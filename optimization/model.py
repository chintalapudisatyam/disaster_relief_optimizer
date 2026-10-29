"""
Linear Programming model for relief distribution (solved with PuLP / CBC).

SETS      i = warehouses, j = affected areas, k = resources (Food, Water, Medicine)
DATA      c[i][j]    transport cost per unit from warehouse i to area j
          S[i][k]    supply of resource k at warehouse i
          D[j][k]    demand of resource k at area j
          w[j]       priority weight of area j (High=5, Medium=3, Low=1)
          Cap        total vehicle capacity = sum(capacity * trips)
          P          unmet-demand penalty scale (configurable)

VARIABLES x[i,j,k] >= 0  quantity of k sent from i to j
          u[j,k]   >= 0  unmet demand of k at j (keeps the model feasible when supply is short)

OBJECTIVE minimize  sum c[i][j]*x[i,j,k]  +  sum P*w[j]*u[j,k]
          Cost term + priority-weighted shortage penalty. Equivalent to
          "cost minus priority satisfaction benefit", since
          sum w*u = sum w*D - sum w*(demand served).

CONSTRAINTS
 (1) Supply  : sum_j x[i,j,k] <= S[i][k]
 (2) Demand  : sum_i x[i,j,k] + u[j,k] = D[j][k]
 (3) Vehicle : sum_{i,j,k} x[i,j,k] <= Cap   (aggregate capacity version)
"""
import pulp

def solve(d):
    R = d["resources"]; W = d["warehouses"]; A = d["areas"]
    cost = d["cost"]; pw = d["priority_weights"]
    nW, nA, nR = len(W), len(A), len(R)
    cap = sum(v["capacity"] * v["trips"] for v in d["vehicles"])
    max_cost = max(max(r) for r in cost)
    # Default penalty: one unit of unmet Low-priority demand costs more than
    # the most expensive shipment, so the model prefers shipping when it can.
    P = d.get("unmet_penalty") or (max_cost + 1)
    w = [pw[a["priority"]] for a in A]

    m = pulp.LpProblem("relief", pulp.LpMinimize)
    x = [[[pulp.LpVariable(f"x_{i}_{j}_{k}", lowBound=0) for k in range(nR)]
          for j in range(nA)] for i in range(nW)]
    u = [[pulp.LpVariable(f"u_{j}_{k}", lowBound=0) for k in range(nR)] for j in range(nA)]

    m += (pulp.lpSum(cost[i][j] * x[i][j][k] for i in range(nW) for j in range(nA) for k in range(nR))
          + pulp.lpSum(P * w[j] * u[j][k] for j in range(nA) for k in range(nR)))

    for i in range(nW):
        for k in range(nR):
            m += pulp.lpSum(x[i][j][k] for j in range(nA)) <= W[i]["supply"][k]
    for j in range(nA):
        for k in range(nR):
            m += pulp.lpSum(x[i][j][k] for i in range(nW)) + u[j][k] == A[j]["demand"][k]
    m += pulp.lpSum(x[i][j][k] for i in range(nW) for j in range(nA) for k in range(nR)) <= cap

    m.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[m.status]
    if status != "Optimal":
        return {"status": status, "message": "Solver did not find an optimal solution."}

    val = lambda v: round(v.value() or 0, 4)
    alloc = []
    for i in range(nW):
        for j in range(nA):
            q = [val(x[i][j][k]) for k in range(nR)]
            alloc.append({"warehouse": W[i]["name"], "area": A[j]["name"], "qty": q,
                          "total": sum(q), "cost": sum(q) * cost[i][j]})
    unmet = [[val(u[j][k]) for k in range(nR)] for j in range(nA)]
    demand_tot = sum(sum(a["demand"]) for a in A)
    unmet_tot = sum(map(sum, unmet))
    hi = [j for j in range(nA) if A[j]["priority"] == "High"]
    hi_dem = sum(sum(A[j]["demand"]) for j in hi)
    hi_un = sum(sum(unmet[j]) for j in hi)
    shipped = demand_tot - unmet_tot
    areas = []
    for j in range(nA):
        dem = sum(A[j]["demand"]); un = sum(unmet[j])
        areas.append({"area": A[j]["name"], "priority": A[j]["priority"], "population": A[j]["population"],
                      "demand": dem, "unmet": un, "received": dem - un,
                      "satisfaction": 100 * (1 - un / dem) if dem else 100})
    # Vehicles used: fill largest vehicle trips first until shipped quantity is covered
    left, used = shipped, 0
    for v in sorted(d["vehicles"], key=lambda v: -v["capacity"]):
        for _ in range(int(v["trips"])):
            if left > 1e-9:
                used += 1; left -= v["capacity"]
    warnings = []
    if unmet_tot > 1e-6:
        warnings.append("Available resources are insufficient to satisfy all demand.")
        if shipped >= cap - 1e-6:
            warnings.append("Vehicle capacity limits the amount that can be shipped.")
    return {"status": "Optimal", "objective": round(m.objective.value(), 2),
            "total_cost": round(sum(a["cost"] for a in alloc), 2),
            "allocations": alloc, "areas": areas, "resources": R,
            "demand_satisfaction": 100 * shipped / demand_tot if demand_tot else 100,
            "high_priority_satisfaction": 100 * (1 - hi_un / hi_dem) if hi_dem else 100,
            "total_unmet": unmet_tot, "total_distributed": shipped,
            "vehicle_capacity": cap, "vehicles_used": used, "warnings": warnings}
