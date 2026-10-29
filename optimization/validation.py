"""Input validation. Returns a list of human-readable error strings."""

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def validate(d):
    errs = []
    W, A, V = d.get("warehouses", []), d.get("areas", []), d.get("vehicles", [])
    nr = len(d.get("resources", []))
    if not W: errs.append("Add at least one warehouse.")
    if not A: errs.append("Add at least one affected area.")
    if not V: errs.append("Add at least one vehicle.")
    for w in W:
        if len(w["supply"]) != nr or any(not _num(s) or s < 0 for s in w["supply"]):
            errs.append(f"Warehouse '{w['name']}': supply must be numbers >= 0.")
    for a in A:
        if len(a["demand"]) != nr or any(not _num(s) or s < 0 for s in a["demand"]):
            errs.append(f"Area '{a['name']}': demand must be numbers >= 0.")
        if a.get("priority") not in d["priority_weights"]:
            errs.append(f"Area '{a['name']}': invalid priority.")
    c = d.get("cost", [])
    if len(c) != len(W) or any(len(r) != len(A) for r in c) or any(not _num(v) or v < 0 for r in c for v in r):
        errs.append("Cost matrix must be numeric (>= 0) with one row per warehouse and one column per area.")
    for v in V:
        if not _num(v["capacity"]) or v["capacity"] <= 0 or not _num(v["trips"]) or v["trips"] < 0:
            errs.append(f"Vehicle '{v['name']}': capacity must be > 0 and trips >= 0.")
    return errs
