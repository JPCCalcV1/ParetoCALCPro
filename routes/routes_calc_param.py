# routes/routes_calc_param.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from core.extensions import limiter
from core.extensions import csrf

param_calc_bp = Blueprint('param_calc_bp', __name__)


@param_calc_bp.route('/feinguss', methods=['POST'])
@login_required
@csrf.exempt   # Falls du globales CSRF hast und dein Frontend den Token NICHT mitsendet.
@limiter.limit("20/minute")  # optionales Rate-Limit
def calc_feinguss():
    """
    Nimmt JSON-Daten vom Frontend entgegen (Feinguss-Parameter) und
    führt die gesamte Feinguss-Berechnung durch.

    BEISPIEL POST-Body (JSON):
    {
      "matName": "Stahl 1.4408",
      "landName": "DE",
      "shellName": "Medium",
      "gw_g": 50.0,
      "qty": 10000,
      "ruest_min": 90,
      "post_factor": 1.0
    }

    GIBT JSON zurück:
    {
      "ok": true,
      "cost_per_part": 2.37,
      "co2_per_part": 1.09,
      "cost_material_total": ...,
      "cost_process": ...,
      "cost_ruest_each": ...,
      "cost_overhead": ...,
      "debug": ...
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        # 1) Eingaben extrahieren
        matName   = data.get("matName", "Stahl 1.4408")
        landName  = data.get("landName", "DE")
        shellName = data.get("shellName", "Medium")
        gw_g      = float(data.get("gw_g", 50.0))
        qty       = float(data.get("qty", 10000.0))
        ruest_min = float(data.get("ruest_min", 90))
        post_factor = float(data.get("post_factor", 1.0))

        # 2) Interne Tabellen (könntest du später in DB auslagern)
        material_data = {
            "Stahl DC01":   { "price":1.30, "co2_kg":2.5,  "vac":False },
            "Stahl 1.4408": { "price":2.50, "co2_kg":3.5,  "vac":False },
            "Alu Si7Mg":    { "price":7.00, "co2_kg":10.0, "vac":False },
            "Titan Ti64":   { "price":30.0, "co2_kg":40.0, "vac":True }
        }
        country_data = {
            "DE":    { "lohnfactor":1.0,  "energy_co2":0.38, "energy_eur":0.20 },
            "China": { "lohnfactor":0.35, "energy_co2":0.60, "energy_eur":0.10 },
            "Polen": { "lohnfactor":0.6,  "energy_co2":0.45, "energy_eur":0.14 }
        }
        shell_data = {
            "Low":    { "shell_eur":0.30, "shell_time_min":1.0 },
            "Medium": { "shell_eur":0.60, "shell_time_min":2.0 },
            "High":   { "shell_eur":1.00, "shell_time_min":3.5 }
        }

        global_base_lohn = 30.0
        energy_factor_stahl = 0.07
        energy_factor_alu   = 0.04
        energy_factor_titan = 0.12

        # 3) Lookups
        mat_info   = material_data.get(matName, material_data["Stahl 1.4408"])
        land_info  = country_data.get(landName, country_data["DE"])
        shell_info = shell_data.get(shellName, shell_data["Medium"])

        lohnfactor   = land_info["lohnfactor"]
        energy_co2   = land_info["energy_co2"]
        energy_eur   = land_info["energy_eur"]

        # 4) Hauptberechnung
        part_kg          = gw_g / 1000.0
        cost_mat_leg     = part_kg * mat_info["price"]
        co2_mat_leg      = part_kg * mat_info["co2_kg"]
        shell_labor_eur  = (global_base_lohn * lohnfactor / 60.0) * shell_info["shell_time_min"]
        cost_shell_eur   = shell_info["shell_eur"]
        cost_material_total = cost_mat_leg + shell_labor_eur + cost_shell_eur

        co2_shell      = 0.05 * part_kg
        co2_mat_total  = co2_mat_leg + co2_shell

        # Energie
        energy_kWh = 0.0
        if mat_info["vac"]:
            energy_kWh = energy_factor_titan * (gw_g / 100.0)
        elif "Alu" in matName:
            energy_kWh = energy_factor_alu * (gw_g / 100.0)
        else:
            energy_kWh = energy_factor_stahl * (gw_g / 100.0)

        cost_energy = energy_kWh * energy_eur
        co2_energy  = energy_kWh * energy_co2

        # Gieß-Lohn
        giess_time_min = 0.5 + 0.5 * part_kg
        if mat_info["vac"]:
            giess_time_min *= 1.3
        giess_labor_eur = (global_base_lohn * lohnfactor / 60.0) * giess_time_min

        # Nachbearbeitung
        postproc_labor_min = 0.2 + 0.8 * (gw_g / 500.0) * post_factor
        if postproc_labor_min < 0.2:
            postproc_labor_min = 0.2
        postproc_labor_eur = (global_base_lohn * lohnfactor / 60.0) * postproc_labor_min

        cost_process = cost_energy + giess_labor_eur + postproc_labor_eur
        co2_process  = co2_energy + 0.01 * (gw_g / 100.0)

        # Rüst => pro Teil
        cost_ruest_each = ((ruest_min / 60.0) * (global_base_lohn * lohnfactor)) / max(qty,1)

        cost_per_part = cost_material_total + cost_process + cost_ruest_each
        co2_per_part  = co2_mat_total + co2_process

        # Overhead
        overhead_pct    = 0.08
        cost_overhead   = cost_per_part * overhead_pct
        cost_per_part  += cost_overhead
        co2_per_part   += 0.05 * co2_per_part

        # 5) Ergebnis
        result = {
            "ok": True,
            "cost_per_part": round(cost_per_part, 3),
            "co2_per_part":  round(co2_per_part, 3),
            "cost_material_total": round(cost_material_total, 3),
            "cost_process": round(cost_process, 3),
            "cost_ruest_each": round(cost_ruest_each, 3),
            "cost_overhead": round(cost_overhead, 3),
            "debug": {
                "matName": matName,
                "landName": landName,
                "shellName": shellName,
                "gw_g": gw_g,
                "qty": qty,
                "ruest_min": ruest_min,
                "post_factor": post_factor
            }
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@param_calc_bp.route('/kaltfliess', methods=['POST'])
@login_required
@csrf.exempt   # Falls du globales CSRF hast und dein Frontend den Token NICHT mitsendet.
@limiter.limit("20/minute")  # optionales Rate-Limit
def calc_kaltfliess():
    """
    Nimmt JSON-Daten vom Frontend entgegen (Kaltfließpressen-Parameter)
    und führt die gesamte Berechnung durch.

    Beispiel-Aufruf:
      POST /calc/param/kaltfliess
      {
        "matName": "C35 (Stahl)",
        "landName": "CN",
        "gw_g": 50.0,
        "los": 10000,
        "stufen": 3,
        "ruest_min": 60,
        "isKomplex": true,
        "isAuto": true,
        "machineIndex": 0  # nur relevant falls isAuto=false
      }

    Gibt JSON zurück (kosten, co2 etc.).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        # (1) Eingaben
        matName    = data.get("matName", "C10 (Stahl)")
        landName   = data.get("landName", "DE")
        gw_g       = float(data.get("gw_g", 50.0))
        los        = float(data.get("los", 10000.0))
        stufen     = int(data.get("stufen", 3))
        ruest_min  = float(data.get("ruest_min", 60.0))
        isKomplex  = bool(data.get("isKomplex", False))
        isAuto     = bool(data.get("isAuto", True))
        # Falls manuelle Auswahl:
        machineIndex = int(data.get("machineIndex", 0))

        # (2) Stammdaten (analog zu kaltfData in JS)
        material_data = {
            "C10 (Stahl)":    { "price":1.20, "co2_kg":2.5,  "strength":350 },
            "C35 (Stahl)":    { "price":1.40, "co2_kg":2.8,  "strength":500 },
            "Alu6060":        { "price":3.50, "co2_kg":7.0,  "strength":140 },
            "Edelstahl304":   { "price":4.00, "co2_kg":6.0,  "strength":600 }
        }

        machine_list = [
            { "tons":200, "rate_eur_h":80.0,  "power_kW":50.0 },
            { "tons":400, "rate_eur_h":120.0, "power_kW":80.0 },
            { "tons":600, "rate_eur_h":180.0, "power_kW":120.0 }
        ]

        country_data = {
            "DE": { "machFactor":1.0, "co2_kwh":0.38 },
            "CN": { "machFactor":0.8, "co2_kwh":0.60 }
        }

        # (3) Hilfswerte
        mat_info    = material_data.get(matName, material_data["C10 (Stahl)"])
        land_info   = country_data.get(landName, country_data["DE"])

        # (4) Presskraft (t) => 0.0005 * strength * gw_g
        pressforce_t = 0.0005 * mat_info["strength"] * gw_g
        if pressforce_t < 1.0:
            pressforce_t = 1.0

        # (5) Maschine => auto oder manuell
        chosenMach = None
        if isAuto:
            # Finde erste Machine, die >= pressforce
            for m in machine_list:
                if pressforce_t <= m["tons"]:
                    chosenMach = m
                    break
            if not chosenMach:
                # Nimm größte, falls pressforce > 600 t
                chosenMach = machine_list[-1]
        else:
            # manuell => Index
            if machineIndex < 0 or machineIndex >= len(machine_list):
                machineIndex = 0
            chosenMach = machine_list[machineIndex]

        # landmachFactor => Multiplikator für rate_eur_h
        landmachFactor = land_info["machFactor"]
        base_rate = chosenMach["rate_eur_h"] * landmachFactor

        # (6) Taktzeit (cyc_s)
        cyc_s = 0.5 + 0.2* stufen
        if isKomplex:
            cyc_s *= 1.2  # +20%

        # Schuss/h
        sh_h = 0.0
        if cyc_s > 0:
            sh_h = 3600.0 / cyc_s

        # (7) Kosten:
        # Material => (gw_g/1000) * mat_info.price
        cost_mat = (gw_g / 1000.0) * mat_info["price"]

        # Maschine => base_rate / shots/h
        cost_mach_each = 0.0
        if sh_h > 0:
            cost_mach_each = base_rate / sh_h

        # Rüst => (ruest_min/60 * base_rate)/ los
        if los <= 0:
            los = 1
        cost_ruest_each = ((ruest_min / 60.0) * base_rate) / los

        cost_sum = cost_mat + cost_mach_each + cost_ruest_each

        # (8) CO2:
        # mat_co2= (gw_g/1000)* mat_info.co2_kg
        co2_mat = (gw_g / 1000.0) * mat_info["co2_kg"]
        # maschine => chosenMach.power_kW*( cyc_s/3600 ) * land_info.co2_kwh
        co2_mach = chosenMach["power_kW"] * (cyc_s / 3600.0) * land_info["co2_kwh"]

        co2_sum = co2_mat + co2_mach

        # (9) Ergebnis
        result = {
            "ok": True,
            "pressforce_t": round(pressforce_t, 2),
            "machine": {
                "tons": chosenMach["tons"],
                "rate_eur_h": chosenMach["rate_eur_h"],
                "power_kW": chosenMach["power_kW"]
            },
            "cyc_s": round(cyc_s, 3),
            "parts_per_h": round(sh_h, 1),
            "cost_mat": round(cost_mat, 4),
            "cost_mach_each": round(cost_mach_each, 4),
            "cost_ruest_each": round(cost_ruest_each, 4),
            "cost_sum": round(cost_sum, 3),
            "co2_mat": round(co2_mat, 3),
            "co2_mach": round(co2_mach, 3),
            "co2_sum": round(co2_sum, 3),
            "debug": {
                "matName": matName,
                "landName": landName,
                "gw_g": gw_g,
                "los": los,
                "stufen": stufen,
                "ruest_min": ruest_min,
                "isKomplex": isKomplex,
                "isAuto": isAuto,
                "machineIndex": machineIndex
            }
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@param_calc_bp.route('/schmieden', methods=['POST'])
@login_required
@csrf.exempt   # Falls du globales CSRF hast und dein Frontend den Token NICHT mitsendet.
@limiter.limit("20/minute")  # optionales Rate-Limit
def calc_schmieden():
    """
    Nimmt die JSON-Daten (Material, Land, Teilgewicht, Losgröße, etc.) entgegen,
    führt die gesamte "Schmieden"-Berechnung durch und liefert das Ergebnis
    als JSON zurück.

    Beispiel POST-Body:
      {
        "mat_str": "C45 (Stahl)",
        "land_str": "DE",
        "part_w": 0.5,
        "losg": 10000,
        "scrapPct": 15.0,
        "area_cm2": 10.0,
        "ruest_min": 60.0
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        # (1) Eingaben aus JSON
        mat_str   = data.get("mat_str", "C45 (Stahl)")
        land_str  = data.get("land_str", "DE")
        part_w    = float(data.get("part_w", 0.50))
        losg      = float(data.get("losg", 10000.0))
        scrapPct  = float(data.get("scrapPct", 15.0))
        area_cm2  = float(data.get("area_cm2", 10.0))
        ruest_min = float(data.get("ruest_min", 60.0))

        # (2) Stammdaten (analog zu schmiedenData in JS)
        machine_data = [
            { "tons": 1000, "rate": 80.0,  "shots_h": 1200 },
            { "tons": 2000, "rate": 120.0, "shots_h": 1800 },
            { "tons": 4000, "rate": 200.0, "shots_h": 2400 }
        ]
        material_data = {
            "C45 (Stahl)":   { "price":1.20, "co2_kg":2.0, "flow_MPa":400 },
            "42CrMo4":       { "price":1.70, "co2_kg":2.7, "flow_MPa":600 },
            "Alu 6082":      { "price":2.50, "co2_kg":7.0, "flow_MPa":150 }
        }
        country_data = {
            "DE": { "elec_eur":0.20, "grid_co2":0.38, "lohnfactor":1.0 },
            "CN": { "elec_eur":0.10, "grid_co2":0.60, "lohnfactor":0.4 }
        }

        global_ofen_kwh_per_kg = 0.5  # 0.5 kWh pro kg
        base_machine_lhr = 30.0       # optional, falls du noch was damit rechnen willst

        # (3) Mappings
        mat_info  = material_data.get(mat_str, material_data["C45 (Stahl)"])
        land_info = country_data.get(land_str, country_data["DE"])

        # (4) Brutto-Gewicht
        scrap     = scrapPct / 100.0
        brutto_kg = part_w * (1 + scrap)

        # (5) Presskraft-Berechnung (vereinfacht)
        flow      = mat_info["flow_MPa"]
        area_mm2  = area_cm2 * 100.0
        pressforce_t = (flow * area_mm2) / (9.81e3) * 1.2
        pressforce_t *= 0.3  # "Korrektur"
        if pressforce_t < 200:
            pressforce_t = 200

        # => Maschine auswählen
        chosen_mach = None
        for mm in machine_data:
            if pressforce_t <= mm["tons"]:
                chosen_mach = mm
                break
        if not chosen_mach:
            chosen_mach = machine_data[-1]

        shots_h = chosen_mach["shots_h"]  # Bsp: 1200/h
        cyc_s   = 3600.0 / shots_h

        # (6) Kosten
        # Material
        cost_mat = brutto_kg * mat_info["price"]
        # Ofen
        power_eur = land_info["elec_eur"]
        co2_kwh   = land_info["grid_co2"]
        ofen_kWh  = global_ofen_kwh_per_kg * brutto_kg
        cost_ofen = ofen_kWh * power_eur

        # Maschine => rate ggf. an Land anpassen (wie in JS, land_str=="CN" => *0.6 ?)
        base_rate = chosen_mach["rate"]
        if land_str == "CN":
            base_rate *= 0.6  # z. B. dein "China-Faktor"

        cost_machine_each = 0.0
        if shots_h > 0:
            cost_machine_each = base_rate / shots_h

        # Rüst
        lohnfact = land_info["lohnfactor"]
        if losg <= 0:
            losg = 1
        cost_ruest_each = ((ruest_min / 60.0) * (30.0 * lohnfact)) / losg

        cost_sum = cost_mat + cost_ofen + cost_machine_each + cost_ruest_each

        # (7) CO2
        mat_co2   = brutto_kg * mat_info["co2_kg"]
        ofen_co2  = ofen_kWh * co2_kwh
        mach_co2  = 0.01  # minimal
        co2_sum   = mat_co2 + ofen_co2 + mach_co2

        result = {
            "ok": True,
            "pressforce_t": round(pressforce_t, 2),
            "chosen_mach": {
                "tons": chosen_mach["tons"],
                "rate": chosen_mach["rate"],
                "shots_h": chosen_mach["shots_h"]
            },
            "cyc_s": round(cyc_s, 3),
            "cost_mat": round(cost_mat, 3),
            "cost_ofen": round(cost_ofen, 3),
            "cost_machine_each": round(cost_machine_each, 3),
            "cost_ruest_each": round(cost_ruest_each, 3),
            "cost_sum": round(cost_sum, 2),
            "mat_co2": round(mat_co2, 2),
            "ofen_co2": round(ofen_co2, 2),
            "mach_co2": round(mach_co2, 2),
            "co2_sum": round(co2_sum, 2),
            "debug": {
                "mat_str": mat_str,
                "land_str": land_str,
                "part_w": part_w,
                "losg": losg,
                "scrapPct": scrapPct,
                "area_cm2": area_cm2,
                "ruest_min": ruest_min
            }
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@param_calc_bp.route("/pcb", methods=["POST"])
@login_required
@csrf.exempt   # Falls du globales CSRF hast und dein Frontend den Token NICHT mitsendet
@limiter.limit("20/minute")  # optionales Rate-Limit
def calc_pcb():
    """
    Nimmt JSON-Daten für den PCB-Kalkulator entgegen und führt
    die komplette PCB-Berechnung (Kosten + CO₂) serverseitig durch.

    Beispiel-POST-Body (JSON):
    {
      "l_mm": 100.0,
      "b_mm": 80.0,
      "layer": 4,
      "qty": 1000,
      "land": "China",
      "thick": 1.6,
      "cu": "35µm",
      "finish": "HASL",
      "tooling": 200.0,
      "do_assembly": true,
      "smd_count": 50,
      "tht_count": 10
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        # (1) Eingaben aus dem JSON
        l_mm       = float(data.get("l_mm", 100.0))
        b_mm       = float(data.get("b_mm", 80.0))
        layer      = int(data.get("layer", 2))
        qty        = int(data.get("qty", 1000))
        land       = data.get("land", "China")
        thick      = float(data.get("thick", 1.6))
        cu_        = data.get("cu", "35µm")      # "35µm" oder "70µm"
        finish     = data.get("finish", "HASL")  # "HASL","ENIG","OSP"
        tooling    = float(data.get("tooling", 200.0))
        do_assembly= bool(data.get("do_assembly", False))
        smd_count  = int(data.get("smd_count", 50))
        tht_count  = int(data.get("tht_count", 10))

        # (2) Stammdaten (analog zu pcbData in JS)
        finish_data = {
            "HASL": 1.0,
            "ENIG": 1.25,
            "OSP":  1.05
        }
        layer_factor_base = {
            2: 1.0,
            4: 1.8,
            6: 2.5,
            8: 3.2
        }
        cu_factor = {
            "35µm": 1.0,
            "70µm": 1.2
        }
        land_factor = {
            "China": 0.8,
            "Europa": 1.0,
            "Sonst": 1.1
        }
        grid_co2 = {
            "China": 0.6,
            "Europa": 0.4,
            "Sonst": 0.5
        }

        # (3) Berechnung

        # Board-Fläche in dm²
        area_dm2 = (l_mm * b_mm) / 10000.0

        # Baseline => 2.5 €/dm² für 2 Layer
        baseline_eur_dm2 = 2.5

        # Faktor (Lagen, Finish, Cu, Land)
        layer_fac  = layer_factor_base.get(layer, 2.0)
        fin_fac    = finish_data.get(finish, 1.0)
        cu_fac     = cu_factor.get(cu_, 1.0)
        land_fac   = land_factor.get(land, 1.0)

        # Rohpreis pro Stück (ohne Tooling)
        raw_unit_cost = area_dm2 * baseline_eur_dm2
        raw_unit_cost *= layer_fac * fin_fac * cu_fac * land_fac

        # Stückzahl-Staffel
        if qty < 100:
            raw_unit_cost *= 1.2
        elif qty >= 1000:
            raw_unit_cost *= 0.9

        # Dickenzuschlag (±20 % max)
        thick_rel = thick / 1.6
        thick_corr = 1.0 + 0.2*(thick_rel - 1.0)
        if thick_corr > 1.2:
            thick_corr = 1.2
        if thick_corr < 0.8:
            thick_corr = 0.8
        raw_unit_cost *= thick_corr

        # Tooling aufteilen
        tooling_each = 0.0
        if qty > 0:
            tooling_each = tooling / qty

        pcb_unit_cost = raw_unit_cost + tooling_each

        # Bestückung (SMD + THT)
        assembly_cost = 0.0
        if do_assembly:
            # 0.002 €/SMD + 0.01 €/THT => * land_fac
            assembly_cost = (0.002*smd_count) + (0.01*tht_count)
            assembly_cost *= land_fac

        total_unit_cost = pcb_unit_cost + assembly_cost

        # (4) CO2-Berechnung
        # Baseline => ~0.6 kg/dm² für 2 Layer in "Europa"
        base_co2_2layer_eu = 0.6
        # Layer-Faktor
        layer_co2_fac = layer_fac
        # Land-Faktor (CO2 => grid_co2)
        co2_eu  = grid_co2["Europa"]
        co2_lnd = grid_co2.get(land, 0.5)
        land_co2_fac = 1.0
        if co2_eu > 0:
            land_co2_fac = co2_lnd / co2_eu

        # Roh-CO2 pro Board
        raw_co2_board = area_dm2 * base_co2_2layer_eu * layer_co2_fac * land_co2_fac

        # Dickenzuschlag => nur zur Hälfte des thick_corr
        thick_co2_corr = 1.0 + (thick_corr - 1.0)*0.5
        raw_co2_board *= thick_co2_corr

        # Finish-Zuschlag
        if finish == "ENIG":
            raw_co2_board *= 1.1
        elif finish == "OSP":
            raw_co2_board *= 1.02

        # Cu-Zuschlag
        if cu_ == "70µm":
            raw_co2_board *= 1.05

        # Bestückungs-CO2
        assembly_co2 = 0.0
        if do_assembly:
            # z. B. 0.025 kWh => * grid_co2[land]
            # (Diesen Wert kannst du anpassen)
            kwh_assembly = 0.025
            assembly_co2 = kwh_assembly * co2_lnd

        total_co2_board = raw_co2_board + assembly_co2

        # (5) Ergebnis
        result = {
            "ok": True,
            "pcb_unit_cost": round(pcb_unit_cost, 2),
            "assembly_cost": round(assembly_cost, 2),
            "total_unit_cost": round(total_unit_cost, 2),
            "raw_co2_board": round(raw_co2_board, 3),
            "assembly_co2": round(assembly_co2, 3),
            "total_co2_board": round(total_co2_board, 3),
            "debug": {
                "l_mm": l_mm,
                "b_mm": b_mm,
                "layer": layer,
                "qty": qty,
                "land": land,
                "thick": thick,
                "cu": cu_,
                "finish": finish,
                "tooling": tooling,
                "do_assembly": do_assembly,
                "smd_count": smd_count,
                "tht_count": tht_count
            }
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500