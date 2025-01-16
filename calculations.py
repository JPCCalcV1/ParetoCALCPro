# calculations.py
# -----------------------------------------------------------
# Dieses Modul enthält alle Rechenfunktionen für das Projekt.
# - calculate_all(data): Umfangreiche "große" Kalkulation (Material, Steps, etc.)
# - calc_machine(data): Dummy-Funktion zur Maschinenberechnung
# - calc_labor(data):  Dummy-Funktion zur Lohnberechnung
# - calc_material(data): Dummy-Funktion zur Materialberechnung
# - avg_fgk_percent(steps): Hilfsfunktion zur Ermittlung des FGK-Durchschnitts
#
# Du kannst jede Funktion nach Bedarf erweitern oder verfeinern.

import math

# -----------------------------------------------------------
# 1) GROSSE KALKULATION => "calculate_all" (Masterlizenz-Code)
# -----------------------------------------------------------
def calculate_all(data):
    print("[calculate_all] Eingehende Daten:", data)

    scrap_pct   = data.get("scrapPct",   0.0)
    sga_pct     = data.get("sgaPct",     0.0)
    profit_pct  = data.get("profitPct",  0.0)
    lot_size    = data.get("lotSize",    100)

    # ---------- A) MATERIALKOSTEN ----------
    mat_price   = data["material"]["price"]   # €/kg
    mat_weight  = data["material"]["weight"]  # kg/Stk
    mat_gk_pct  = data["material"]["gk"]      # in %
    fremd_val   = data["material"]["fremdValue"]
    mat_co2     = data["material"]["co2"]     # kgCO2/kg?

    mat_einzel_pro_stk = mat_price * mat_weight
    mat_einzel_pro_stk *= (1 + scrap_pct / 100.0)
    mat_einzel_100 = mat_einzel_pro_stk * 100.0

    fremd_100 = fremd_val * 100.0 * (1 + scrap_pct / 100.0)

    # Material-GK z. B. 5% auf (Material + Fremd)
    mat_gemein_100 = (mat_einzel_100 + fremd_100) * (mat_gk_pct / 100.0)

    # ---------- B) PROZESSKOSTEN (alle Steps) ----------
    sum_mach_100 = 0.0
    sum_lohn_100 = 0.0
    sum_ruest_100 = 0.0
    sum_tooling_100 = 0.0
    sum_co2_100 = 0.0

    # Neu: FGK wird pro Step berechnet und addiert
    sum_fgk_100 = 0.0

    steps = data.get("steps", []) or []
    for step in steps:
        cyc_sec = step.get("cycTime", 0.0)
        ms_rate = step.get("msRate", 0.0)
        lohn_rate = step.get("lohnRate", 0.0)
        ruest_val = step.get("ruestVal", 0.0)
        tool_100 = step.get("tooling100", 0.0)  # €/100
        fgk_pct = step.get("fgkPct", 0.0)
        co2_hour = step.get("co2Hour", 0.0)

        cyc_hours = cyc_sec / 3600.0

        # Maschine + Lohn pro 100 Stk
        mach_100 = cyc_hours * ms_rate * 100.0
        lohn_100 = cyc_hours * lohn_rate * 100.0

        # Rüst pro 100 => ruest_val / lot_size * 100
        ruest_100 = (ruest_val / lot_size) * 100.0

        # Tooling/100 => direkt
        tooling_100 = tool_100

        # Prozess-CO2 => cyc_hours * co2_hour * 100
        co2_100 = cyc_hours * co2_hour * 100.0

        # => Hier OHNE FGK => fertCost_100 für diesen Step
        step_fert_100 = mach_100 + lohn_100 + ruest_100 + tooling_100

        # => FGK => step_fert_100 * (fgk_pct / 100)
        step_fgk_100 = step_fert_100 * (fgk_pct / 100.0)

        # => Summieren
        sum_mach_100 += mach_100
        sum_lohn_100 += lohn_100
        sum_ruest_100 += ruest_100
        sum_tooling_100 += tooling_100
        sum_co2_100 += co2_100
        sum_fgk_100 += step_fgk_100

    # GLOBALER AUSSCHUSS auf Maschine + Lohn + Tooling + CO2
    factor_scrap = (1 + scrap_pct / 100.0)
    sum_mach_100 *= factor_scrap
    sum_lohn_100 *= factor_scrap
    sum_tooling_100 *= factor_scrap
    sum_co2_100 *= factor_scrap
    # Rüstkosten bleiben unberührt => ruest_100

    # => FGK summiert => das bleibt, wir haben es bereits pro Step berechnet.
    # => Falls du willst, *auch* FGK mit Ausschuss => dann "sum_fgk_100 *= factor_scrap;"
    # => hier optional:
    sum_fgk_100 *= factor_scrap

    # ---------- HERSTELLKOSTEN ----------
    # Fertigung = sum(mach+lohn+ruest+tooling + FGK)
    # ---------- HERSTELLKOSTEN ----------
    # Fertigung = sum(mach+lohn+ruest+tooling + FGK)
    fert_cost_100 = sum_mach_100 + sum_lohn_100 + sum_ruest_100 + sum_tooling_100 + sum_fgk_100

    # Material = mat_einzel_100 + fremd_100 + mat_gemein_100
    mat_sum_100 = mat_einzel_100 + fremd_100 + mat_gemein_100

    herstell_100 = mat_sum_100 + fert_cost_100

    # SG&A
    sga_100 = herstell_100 * (sga_pct / 100.0)
    profit_100 = herstell_100 * (profit_pct / 100.0)
    total_all_100 = herstell_100 + sga_100 + profit_100

    # ---------- CO2 ----------
    # => Material-CO2: mat_weight * 100 * mat_co2 * factor_scrap
    mat_co2_100 = (mat_weight * 100.0) * mat_co2 * factor_scrap
    total_co2_100 = mat_co2_100 + sum_co2_100

    # ---------- Ergebnis ----------
    return {
        "matEinzel100": round(mat_einzel_100, 2),
        "matGemein100": round(mat_gemein_100, 2),
        "fremd100": round(fremd_100, 2),

        "mach100": round(sum_mach_100, 2),
        "lohn100": round(sum_lohn_100, 2),
        "ruest100": round(sum_ruest_100, 2),
        "tooling100": round(sum_tooling_100, 2),
        "fgk100": round(sum_fgk_100, 2),

        "herstell100": round(herstell_100, 2),
        "sga100": round(sga_100, 2),
        "profit100": round(profit_100, 2),
        "totalAll100": round(total_all_100, 2),

        "co2Mat100": round(mat_co2_100, 2),
        "co2Proc100": round(sum_co2_100, 2),

        "co2Total100": round(total_co2_100, 2)
    }
# -----------------------------------------------------------
# 2) WEITERE FUNKTIONEN => Maschinen, Lohn, Material etc.
# -----------------------------------------------------------

def calc_machine(data):
    """
    Dummy-Funktion zur Maschinenberechnung.
    Erwartet z. B.:
    {
      "kaufpreis": 100000,
      "jahresauslastung": 6000
    }
    Gibt eine einfache Formel aus ms_rate und co2_per_hour zurück.
    """
    print("[calc_machine] Eingehende Daten:", data)
    kaufpreis = float(data.get("kaufpreis", 300000))
    jahresauslastung = float(data.get("jahresauslastung", 6000))
    if jahresauslastung <= 0:
        ms_rate = 0.0
    else:
        ms_rate = kaufpreis / jahresauslastung

    co2_per_hour = ms_rate * 0.1  # Dummy-Formel
    return {
        "ms_rate": round(ms_rate, 2),
        "co2_per_hour": round(co2_per_hour, 2)
    }

def calc_labor(data):
    """
    Dummy-Funktion zur Lohnberechnung. Erwartet z. B.:
    {
      "baseWage": 20.0,
      "socialChargesPct": 0.5,
      "shiftSurchargePct": 0.2
    }
    Gibt labor_rate = baseWage * (1+socialChargesPct)*(1+shiftSurchargePct) zurück.
    """
    print("[calc_labor] Eingehende Daten:", data)
    base_wage = float(data.get("baseWage", 20.0))
    social_pct = float(data.get("socialChargesPct", 0.5))
    shift_pct = float(data.get("shiftSurchargePct", 0.2))

    labor_rate = base_wage * (1 + social_pct) * (1 + shift_pct)
    return {
        "labor_rate": round(labor_rate, 2)
    }

def calc_material(data):
    """
    Dummy-Funktion zur Materialberechnung. Erwartet z. B.:
    {
      "preis": 2.5,
      "gewicht": 0.2,
      "gemeinkosten": 5.0
    }
    Gibt material_cost = preis*gewicht + (preis*gemeinkosten/100) zurück.
    """
    print("[calc_material] Eingehende Daten:", data)
    preis = float(data.get("preis", 2.5))
    gewicht = float(data.get("gewicht", 0.2))
    gemeinkosten = float(data.get("gemeinkosten", 5.0))

    material_cost = preis * gewicht + (preis * (gemeinkosten / 100.0))
    return {
        "material_cost": round(material_cost, 2)
    }

