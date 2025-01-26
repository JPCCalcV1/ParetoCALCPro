# FILE: calc_core.py

def calc_einzelteil(inputs: dict) -> dict:
    """
    inputs kann z.B. Felder aus Tab1–4 enthalten
    Rechnen => dict output (z.B. total, cost, co2, etc.)
    """
    # Bsp:
    mat_cost = inputs.get("matCost", 0.0)
    overhead = inputs.get("overhead", 0.0)
    total = mat_cost + overhead
    return {
      "mat_cost": mat_cost,
      "overhead": overhead,
      "total": total
    }

def calc_baugruppe(parts: list) -> dict:
    """
    parts => Liste von Einzelteil-Dict
    Summiere z.B. total, co2, ...
    """
    total_sum = 0.0
    for p in parts:
        total_sum += p.get("total", 0)
    return {"parts_count": len(parts), "total_sum": total_sum}