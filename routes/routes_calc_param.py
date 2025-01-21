from flask import Blueprint, request, jsonify, session  # session ist wichtig
from core.extensions import limiter, csrf
from models.user import User  # Damit du User.query.get(...) nutzen kannst
# ACHTUNG: Du musst hier auch dein User-Modell importieren, z.B.:
# from your_app.models import User

param_calc_bp = Blueprint('param_calc_bp', __name__)

@param_calc_bp.route("/feinguss", methods=["POST"])
@csrf.exempt
@limiter.limit("20/minute")
def calc_feinguss():
    """
    POST /calc/param/feinguss
    Erwartet JSON-Felder wie (siehe JS 'buildFeingussPayload'):
      fgMatSelect        = "Stahl"   # Key (Stahl, Alu, Titan, NickelAlloy)
      fgLocationSelect   = "DE"      # (DE, CN, PL)
      fgWeight           = 50.0      # g
      fgScrapRate        = 5.0       # % => 0.05
      fgQuantity         = 1000      # Jahresmenge

      fgComplexitySelect = "Medium"  # (Low, Medium, High)
      fgSetupTimeMin     = 60.0      # min
      fgOverheadRate     = 15.0      # % => 0.15
      fgProfitRate       = 10.0      # % => 0.10
      fgToolCost         = 0.0
      fgPostProcMin      = 0.5       # Nachbearb. min/Teil

    Rechnet (Material+Shell, Fertigung, Overhead, Gewinn) => Endpreis
    Gibt JSON zurück wie:
      {
        "ok": True,
        "costMatShell": 3.25,
        "costFertigung": 2.10,
        "overheadVal": 0.83,
        "profitVal": 0.59,
        "endPrice": 6.77,
        "msg": "..."
      }
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    lvl = user.license_level()
    if lvl not in ["premium", "extended", "plus"]:
        return jsonify({"error": "Feinguss erfordert mindestens Premium."}), 403

        # --------------------------------------------------
        # 3) Eingaben extrahieren (V1 Namenskonvention)
        # --------------------------------------------------
        matKey    = data.get("fgMatSelect", "Stahl")
        locKey    = data.get("fgLocationSelect", "DE")
        partWeight= float(data.get("fgWeight", 50.0))   # in g
        scrapRate = float(data.get("fgScrapRate", 5.0)) # 5 => 5% => 0.05
        annualQty = float(data.get("fgQuantity", 1000))

        compKey   = data.get("fgComplexitySelect", "Medium")
        ruestMin  = float(data.get("fgSetupTimeMin", 60.0))
        overheadP = float(data.get("fgOverheadRate", 15.0))
        profitP   = float(data.get("fgProfitRate", 10.0))
        toolCost  = float(data.get("fgToolCost", 0.0))
        postProc  = float(data.get("fgPostProcMin", 0.5))

        # --------------------------------------------------
        # 4) Material-Daten, Standorte, Complexity
        #    => 1:1 aus V1, inkl. shellBase & shellBonus
        # --------------------------------------------------
        materials = {
            "Stahl": {
                "name": "Stahl (Allg.)",
                "pricePerKg": 2.5,
                "shellBase":  0.4
            },
            "Alu": {
                "name": "Aluminium",
                "pricePerKg": 5.0,
                "shellBase":  0.5
            },
            "Titan": {
                "name": "Titan",
                "pricePerKg": 25.0,
                "shellBase":  1.0
            },
            "NickelAlloy": {
                "name": "Nickelbasis-Legierung",
                "pricePerKg": 20.0,
                "shellBase":  0.8
            }
        }
        locations = {
            "DE": {
                "name": "Deutschland",
                "wageFactor": 1.0
            },
            "CN": {
                "name": "China",
                "wageFactor": 0.35
            },
            "PL": {
                "name": "Polen",
                "wageFactor": 0.6
            }
        }
        complexity = {
            "Low": {
                "factorTime": 0.7,
                "shellBonus": 0.0
            },
            "Medium": {
                "factorTime": 1.0,
                "shellBonus": 0.3
            },
            "High": {
                "factorTime": 1.3,
                "shellBonus": 0.6
            }
        }

        baseHourlyWage = 60.0  # z. B. 60 €/h in DE
        maxScrapRate   = 0.5   # 50% Limit

        # --------------------------------------------------
        # 5) parsePercent & parseScrap (V1 analog)
        # --------------------------------------------------
        def parse_percent(x):
            """
            parsePercent(15) => 0.15, parsePercent(0.2) => 0.2
            Obergrenze für Overhead oder Profit theoret. nicht fix
            """
            if x < 0:
                return 0.0
            if x > 1.0:
                return x / 100.0
            return x

        def parse_scrap(x):
            """
            parseScrap(5) => 0.05
            parseScrap(45) => 0.45
            maxScrapRate = 0.5 => 50% max
            """
            if x < 0:
                return 0.0
            if x > 1.0:
                x /= 100.0
            if x > maxScrapRate:
                # optional Warning
                pass
            return x

        overheadRate = parse_percent(overheadP)  # 15 => 0.15
        profitRate   = parse_percent(profitP)    # 10 => 0.10
        sRate        = parse_scrap(scrapRate)    # 5 => 0.05

        # --------------------------------------------------
        # 6) Plausiprüfung (V1 warnt in console.log)
        #    => Hier brechen wir einfach ab
        # --------------------------------------------------
        if partWeight <= 0:
            return jsonify({"error": "Bauteilgewicht <= 0"}), 400
        if annualQty < 1:
            return jsonify({"error": "Jahresmenge <1"}), 400

        matInfo = materials.get(matKey, materials["Stahl"])
        locInfo = locations.get(locKey, locations["DE"])
        compInfo= complexity.get(compKey, complexity["Medium"])

        # --------------------------------------------------
        # 7) Material + Shell (aus V1)
        # --------------------------------------------------
        weight_kg      = partWeight / 1000.0
        totalWeight_kg = weight_kg * (1.0 + sRate)
        costMaterial   = totalWeight_kg * matInfo["pricePerKg"]
        costShell      = matInfo["shellBase"] + compInfo["shellBonus"]
        costMatShell   = costMaterial + costShell

        # --------------------------------------------------
        # 8) Fertigung (V1 => timePartMin, wagePerMin, etc.)
        # --------------------------------------------------
        fertigungStundensatz = baseHourlyWage * locInfo["wageFactor"]  # z.B. 60 * 1 = 60
        wagePerMin = fertigungStundensatz / 60.0

        baseTimeMin = 1.0 + postProc
        timePartMin = baseTimeMin * compInfo["factorTime"]

        costLaborMachinePerPart = wagePerMin * timePartMin

        costRuestPerPart = 0.0
        if annualQty > 0 and ruestMin > 0:
            costRuestPerPart = (ruestMin * wagePerMin) / annualQty

        costToolPerPart = 0.0
        if annualQty > 0 and toolCost > 0:
            costToolPerPart = toolCost / annualQty

        # Energie => minimal 0.05
        costEnergy = 0.05

        costFertigung = (costLaborMachinePerPart
                         + costRuestPerPart
                         + costToolPerPart
                         + costEnergy)

        # --------------------------------------------------
        # 9) Overhead & Profit
        # --------------------------------------------------
        baseCosts   = costMatShell + costFertigung
        overheadVal = baseCosts * overheadRate
        withOverhead= baseCosts + overheadVal
        profitVal   = withOverhead * profitRate
        endPrice    = withOverhead + profitVal

        # --------------------------------------------------
        # 10) JSON-Ergebnis
        # --------------------------------------------------
        return jsonify({
            "ok": True,
            "costMatShell":  round(costMatShell, 2),
            "costFertigung": round(costFertigung, 2),
            "overheadVal":   round(overheadVal, 2),
            "profitVal":     round(profitVal, 2),
            "endPrice":      round(endPrice, 2),
            # Weitere Felder nach Bedarf
            "msg": "Feinguss-Berechnung aus V1-Logik (Backend)."
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@param_calc_bp.route('/kaltfliess', methods=['POST'])
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