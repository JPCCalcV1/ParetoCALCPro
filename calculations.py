import math


def calculate_all(data):
    print("[calculate_all] Eingehende Daten:", data)
    scrap_pct = data.get("scrapPct", 0.0)  # Ausschuss in %
    sga_pct = data.get("sgaPct", 0.0)
    profit_pct = data.get("profitPct", 0.0)
    lot_size = data.get("lotSize", 100)

    # --------------------------------------------------
    # A) MATERIAL-KOSTEN (pro STÜCK, NICHT pro 100)
    # --------------------------------------------------
    mat_price = data["material"]["price"]  # €/kg
    mat_weight = data["material"]["weight"]  # kg/Stk
    mat_gk_pct = data["material"]["gk"]  # in %
    fremd_val = data["material"]["fremdValue"]  # €/Stk
    mat_co2 = data["material"]["co2"]  # kg CO2 / kg (falls du CO2 aufsplitten willst)

    # 1) Einzelkosten (ohne Ausschuss)
    mat_einzel_no_scrap = mat_price * mat_weight  # €/Stk
    fremd_no_scrap = fremd_val  # €/Stk

    # 2) Material-Ausschuss
    mat_scrap_value = (mat_einzel_no_scrap + fremd_no_scrap) * (scrap_pct / 100.0)

    # 3) Material-Gemeinkosten auf (Einzel + Fremd + Ausschuss)
    mat_base_plus_scrap = mat_einzel_no_scrap + fremd_no_scrap + mat_scrap_value
    mat_gemein_value = mat_base_plus_scrap * (mat_gk_pct / 100.0)

    # 4) Summen
    sum_mat_per_piece = mat_base_plus_scrap + mat_gemein_value  # €/Stk

    # --------------------------------------------------
    # B) FERTIGUNGS-KOSTEN (pro STÜCK)
    # --------------------------------------------------
    steps = data.get("steps", []) or []
    sum_mach_no_scrap = 0.0  # Summe Maschinenkosten (ohne Ausschuss)
    sum_lohn_no_scrap = 0.0  # Summe Lohnkosten (ohne Ausschuss)
    sum_tool_no_scrap = 0.0  # Summe Tooling (ohne Ausschuss)
    sum_ruest = 0.0  # Summe Rüstkosten (kein Ausschuss!)
    sum_fgk = 0.0  # Fertigungs-Gemeinkosten
    sum_fert_scrap = 0.0  # Fertigungsausschuss
    sum_co2_proc = 0.0  # CO₂ in der Fertigung (falls du's getrennt haben willst)

    for idx, step in enumerate(steps):
        cyc_sec = step.get("cycTime", 0.0)
        ms_rate = step.get("msRate", 0.0)  # €/h
        lohn_rate = step.get("lohnRate", 0.0)  # €/h
        ruest_val = step.get("ruestVal", 0.0)  # €/Los
        tool_val = step.get("tooling100", 0.0)  # €/Stk (oder €/100 je nach Interpretation)
        fgk_pct = step.get("fgkPct", 0.0)  # %
        co2_hour = step.get("co2Hour", 0.0)

        cyc_hours = cyc_sec / 3600.0

        # 1) Maschinen + Lohn + Tooling (ohne Ausschuss)
        mach_cost_piece = cyc_hours * ms_rate  # €/Stk
        lohn_cost_piece = cyc_hours * lohn_rate  # €/Stk
        # Achtung: tooling100 kann bedeuten "pro 100" => hier als Bsp. /100
        # Falls du tooling100 schon "pro 1 Stk" pflegst, nimmst du das 1:1
        tool_cost_piece = tool_val  # z.B. "2€ pro 1 Stk"

        # 2) Ausschuss Fertigung (nur auf Maschine, Lohn, Tooling)
        step_base_no_scrap = mach_cost_piece + lohn_cost_piece + tool_cost_piece
        step_scrap_value = step_base_no_scrap * (scrap_pct / 100.0)

        # 3) Fertigungs-Gemeinkosten (auf base + scrap)
        step_base_plus_scrap = step_base_no_scrap + step_scrap_value
        step_fgk_value = step_base_plus_scrap * (fgk_pct / 100.0)

        # 4) Rüstkosten verteilen
        #   Rüstkosten/Los => Rüstkosten / lot_size => €/Stk
        ruest_per_piece = ruest_val / lot_size

        # 5) Summen und CO₂
        sum_mach_no_scrap += mach_cost_piece
        sum_lohn_no_scrap += lohn_cost_piece
        sum_tool_no_scrap += tool_cost_piece
        sum_ruest += ruest_per_piece
        sum_fert_scrap += step_scrap_value
        sum_fgk += step_fgk_value

        # CO₂ nur auf Maschinenlaufzeit => cyc_hours * co2_hour pro Stück
        # Ggf. mit Ausschuss multiplizieren, wenn du willst, dass
        # Ausschussanteil auch "mehr Maschinenzeit" bedeutet – optional.
        proc_co2_piece = cyc_hours * co2_hour
        sum_co2_proc += proc_co2_piece

    sum_fert_per_piece = (
            sum_mach_no_scrap
            + sum_lohn_no_scrap
            + sum_tool_no_scrap
            + sum_fert_scrap
            + sum_fgk
            + sum_ruest
    )

    # --------------------------------------------------
    # C) HERSTELLKOSTEN => SG&A => PROFIT => TOTAL
    # --------------------------------------------------
    herstell_per_piece = sum_mat_per_piece + sum_fert_per_piece
    sga_per_piece = herstell_per_piece * (sga_pct / 100.0)
    profit_per_piece = herstell_per_piece * (profit_pct / 100.0)
    total_per_piece = herstell_per_piece + sga_per_piece + profit_per_piece

    # --------------------------------------------------
    # D) Optional: CO₂ Material
    # --------------------------------------------------
    # Nur als grobe Schätzung:
    mat_co2_piece = mat_weight * mat_co2  # kgCO2 pro Stück (ohne Ausschuss)
    # Willst du den Material-Ausschuss auch in CO2 einrechnen?
    # => mat_co2_piece += mat_co2_piece * (scrap_pct / 100.0)

    total_co2_piece = mat_co2_piece + sum_co2_proc

    # --------------------------------------------------
    # E) Zusammenstellen: dictionary
    # --------------------------------------------------
    # => pro Stück
    # => Du kannst pro 100 noch ableiten, wenn du willst
    out = {
        # Material Details
        "matEinzel": round(mat_einzel_no_scrap, 2),
        "fremd": round(fremd_no_scrap, 2),
        "matScrap": round(mat_scrap_value, 2),
        "matGemein": round(mat_gemein_value, 2),
        "matSum": round(sum_mat_per_piece, 2),

        # Fertigungs-Details
        "mach": round(sum_mach_no_scrap, 2),
        "lohn": round(sum_lohn_no_scrap, 2),
        "tooling": round(sum_tool_no_scrap, 2),
        "ruest": round(sum_ruest, 2),
        "scrapFert": round(sum_fert_scrap, 2),
        "fgk": round(sum_fgk, 2),
        "fertSum": round(sum_fert_per_piece, 2),

        # Gesamtergebnis
        "herstell": round(herstell_per_piece, 2),
        "sga": round(sga_per_piece, 2),
        "profit": round(profit_per_piece, 2),
        "total": round(total_per_piece, 2),

        # CO2
        "co2Mat": round(mat_co2_piece, 3),
        "co2Fert": round(sum_co2_proc, 3),
        "co2Total": round(total_co2_piece, 3),
    }

    print("[calculate_all] => Ergebnis:", out)
    return out


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

