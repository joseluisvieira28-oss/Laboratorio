import math
MONEY_REL_TOL = 1e-12
MONEY_ABS_TOL = 1e-6
BIAS_REL_TOL = 1e-12
BIAS_ABS_TOL = 1e-12

def tiers_equal(a, b):
    if len(a) != len(b):
        return False
    def key(t):
        return (
            -1 if t.get("min") is None else int(t["min"]),
            -1 if t.get("max") is None else int(t["max"]),
            str(t.get("size")),
        )
    for x, y in zip(sorted(a, key=key), sorted(b, key=key)):
        if key(x) != key(y):
            return False
        if int(x["position_count"]) != int(y["position_count"]):
            return False
        for f in ("total_position_value","total_position_value_long","value_close_to_liquidation"):
            if not math.isclose(float(x[f]), float(y[f]), rel_tol=MONEY_REL_TOL, abs_tol=MONEY_ABS_TOL):
                return False
        if not math.isclose(float(x["bias"]), float(y["bias"]), rel_tol=BIAS_REL_TOL, abs_tol=BIAS_ABS_TOL):
            return False
    return True
