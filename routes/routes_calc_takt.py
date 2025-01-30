###########################################################
# calc_spritzguss.py
#
# Enthält:
#  - Deine V1-Basis (leicht gekürzt)
#  - Erweiterte Logik (Advanced) für Pareto-Mehrwert
#  - Nur EIN Flask-Endpoint "/spritzguss"
#
# Du kannst das 1:1 übernehmen und in deinem Projekt
# statt der aktuellen calc_spritzguss.py verwenden.
###########################################################

from flask import Blueprint, request, jsonify, session
from models.user import User
from core.extensions import limiter, csrf

takt_calc_bp = Blueprint('takt_calc_bp', __name__)

@takt_calc_bp.route("/spritzguss", methods=["POST"])
@csrf.exempt
@limiter.limit("150/minute")
def calc_spritzguss():
    """
    POST /spritzguss
    Erwartet JSON mit Feldern wie:
      {
        "material": "PP",
        "cavities": 4,
        "partWeight": 50.0,
        "runnerWeight": 10.0,
        "length_mm": 100.0,
        "width_mm": 80.0,
        "wall_mm": 2.0,
        "machineKey": "80t HighSpeed",
        "isMachineAuto": false,
        "safe_pct": 30.0,
        "press_bar": 300,
        "isAutomotive": false,
        "hasRobot": false,
        "hasSlider": false,
        "hold_s": 2.0,
        "min_cool_s": 1.5,
        "hasContour": false,
        ### NEU / OPTIONAL für Advanced:
        "isAdvanced": false,
        "parallelPlast": false
      }
    """
    try:
        # ---------------------------------------------------
        # 0) Sicherheit / Lizenz
        # ---------------------------------------------------
        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 403
        user = User.query.get(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        lvl = user.license_level()
        if lvl not in ["premium", "extended", "plus"]:
            return jsonify({"error": "Feinguss erfordert mindestens Premium."}), 403

        # ---------------------------------------------------
        # 1) JSON-Parameter einlesen
        # ---------------------------------------------------
        data           = request.get_json()
        isAdvanced     = bool(data.get("isAdvanced", False))  # NEU
        parallelPlast  = bool(data.get("parallelPlast", False))

        material       = data.get("material", "PP")
        cavities       = int(data.get("cavities", 4))
        partWeight     = float(data.get("partWeight", 50.0))
        runnerWeight   = float(data.get("runnerWeight", 10.0))
        length_mm      = float(data.get("length_mm", 100.0))
        width_mm       = float(data.get("width_mm", 80.0))
        wall_mm        = float(data.get("wall_mm", 2.0))

        machineKey     = data.get("machineKey", "80t HighSpeed")
        isMachineAuto  = bool(data.get("isMachineAuto", False))
        safe_pct       = float(data.get("safe_pct", 30.0))
        press_bar      = float(data.get("press_bar", 300.0))
        isAutomotive   = bool(data.get("isAutomotive", False))
        hasRobot       = bool(data.get("hasRobot", False))
        hasSlider      = bool(data.get("hasSlider", False))
        hold_s         = float(data.get("hold_s", 2.0))
        min_cool_s     = float(data.get("min_cool_s", 1.5))
        hasContour     = bool(data.get("hasContour", False))

        # ---------------------------------------------------
        # 2) Gemeinsame Maschinen- & Materialdaten
        # ---------------------------------------------------
        # => Wir führen ALLE Maschinen in einem dict,
        #    erweitern sie ggf. um "parallelPlast" & "shotVolumeMax" (optional).
        #    So können wir dieselbe Datengrundlage verwenden,
        #    Basic vs. Advanced macht nur die *Auswertung* anders.

        machineData = {
            "50t Standard": {
                "tons": 50,
                "openclose": 1.8,
                "min_cycle": 3.5,
                "flags": [],
                "parallelPlast": False,    # NEU: ob Maschine plastifizieren parallel kann
                "shotVolumeMax": 80        # NEU: Beispiel cm³
            },
            "80t HighSpeed": {
                "tons": 80,
                "openclose": 1.0,
                "min_cycle": 2.5,
                "flags": ["highspeed"],
                "parallelPlast": True,
                "shotVolumeMax": 120
            },
            "80t Automotive": {
                "tons": 80,
                "openclose": 2.0,
                "min_cycle": 4.5,
                "flags": ["automotive"],
                "parallelPlast": False,
                "shotVolumeMax": 110
            },
            "100t Standard": {
                "tons": 100,
                "openclose": 1.5,
                "min_cycle": 4.0,
                "flags": [],
                "parallelPlast": True,
                "shotVolumeMax": 150
            },
            "120t AllElectric": {
                "tons": 120,
                "openclose": 1.2,
                "min_cycle": 3.5,
                "flags": ["electric"],
                "parallelPlast": True,
                "shotVolumeMax": 180
            },
            "150t Automotive": {
                "tons": 150,
                "openclose": 2.2,
                "min_cycle": 6.0,
                "flags": ["automotive"],
                "parallelPlast": True,
                "shotVolumeMax": 300
            },
            "200t Standard": {
                "tons": 200,
                "openclose": 1.6,
                "min_cycle": 4.5,
                "flags": [],
                "parallelPlast": True,
                "shotVolumeMax": 350
            },
            "250t Standard": {
                "tons": 250,
                "openclose": 2.0,
                "min_cycle": 5.0,
                "flags": [],
                "parallelPlast": True,
                "shotVolumeMax": 450
            },
            "350t Automotive": {
                "tons": 350,
                "openclose": 2.2,
                "min_cycle": 6.0,
                "flags": ["automotive"],
                "parallelPlast": True,
                "shotVolumeMax": 800
            },
            "400t Standard": {
                "tons": 400,
                "openclose": 2.5,
                "min_cycle": 7.0,
                "flags": [],
                "parallelPlast": True,
                "shotVolumeMax": 1000
            }
        }

        materialData = {
            "PP":      { "coolf": 0.30, "density_gcm3": 0.90, "melt_temp": 220, "mold_temp": 40 },
            "ABS":     { "coolf": 0.35, "density_gcm3": 1.04, "melt_temp": 240, "mold_temp": 60 },
            "PA6GF30": { "coolf": 0.45, "density_gcm3": 1.30, "melt_temp": 280, "mold_temp": 80 },
            "PC":      { "coolf": 0.40, "density_gcm3": 1.20, "melt_temp": 280, "mold_temp": 90 },
            "POM":     { "coolf": 0.38, "density_gcm3": 1.42, "melt_temp": 190, "mold_temp": 80 },
            "TPE":     { "coolf": 0.25, "density_gcm3": 0.95, "melt_temp": 190, "mold_temp": 40 },
            "PBT":     { "coolf": 0.42, "density_gcm3": 1.30, "melt_temp": 240, "mold_temp": 60 }
        }

        # ---------------------------------------------------
        # 3) Decision: Basic vs. Advanced
        # ---------------------------------------------------
        if isAdvanced:
            # => Erweitertes Rechenmodell
            result = calculate_advanced_cycle(
                data, machineData, materialData,
                parallelPlast=parallelPlast
            )
        else:
            # => Standard-Berechnung
            result = calculate_basic_cycle(data, machineData, materialData)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


###########################################################
# BASIC (V1) => Unverändert aus deinem bestehenden Code
###########################################################
def calculate_basic_cycle(data, machineData, materialData):
    """
    Deine Standard-V1-Logik:
    - Schließkraft über proj. Fläche + press_bar + safe_pct
    - Einfaches pick_auto_machine (nur Tonnage)
    - Kühlzeit = coolFactor * wall^2 (falls < min_cool => min_cool)
    - Zyklus = openclose + injection + cool + handling
    """
    # Eingabedaten
    material     = data.get("material", "PP")
    cavities     = int(data.get("cavities", 4))
    partWeight   = float(data.get("partWeight", 50.0))
    runnerWeight = float(data.get("runnerWeight", 10.0))
    length_mm    = float(data.get("length_mm", 100.0))
    width_mm     = float(data.get("width_mm", 80.0))
    wall_mm      = float(data.get("wall_mm", 2.0))

    machineKey   = data.get("machineKey", "80t HighSpeed")
    isMachineAuto= bool(data.get("isMachineAuto", False))
    safe_pct     = float(data.get("safe_pct", 30.0))
    press_bar    = float(data.get("press_bar", 300.0))
    isAutomotive = bool(data.get("isAutomotive", False))
    hasRobot     = bool(data.get("hasRobot", False))
    hasSlider    = bool(data.get("hasSlider", False))
    hold_s       = float(data.get("hold_s", 2.0))
    min_cool_s   = float(data.get("min_cool_s", 1.5))
    hasContour   = bool(data.get("hasContour", False))

    # Materialobjekt
    matObj = materialData.get(material, materialData["PP"])
    coolFactor = matObj["coolf"]

    # Schussgewicht
    shotWeight_g = (partWeight + runnerWeight) * cavities

    # Schließkraft
    projArea_cm2 = (length_mm * width_mm) / 100.0
    closure_tons = projArea_cm2 * press_bar * 0.0001 * cavities
    closure_tons *= (1 + safe_pct / 100.0)
    if isAutomotive:
        closure_tons *= 1.2

    # Maschine auswählen
    if machineKey not in machineData:
        machineKey = "80t HighSpeed"
    if isMachineAuto:
        machineKey = pick_auto_machine(closure_tons, machineData)

    chosenMachine = machineData[machineKey]

    # Kühlzeit
    rawCool_s = coolFactor * (wall_mm ** 2)
    if rawCool_s < min_cool_s:
        rawCool_s = min_cool_s
    if hasContour:
        rawCool_s *= 0.8

    # Handling
    handle_s = 2.0 if hasRobot else 0.5
    slider_s = 1.5 if hasSlider else 0.0

    # Einspritzen
    injection_s = 1.0 + hold_s

    # Öffnen/Schließen
    oc_s = chosenMachine["openclose"]

    # Gesamtzyklus
    rawCycleShot = oc_s + injection_s + rawCool_s + handle_s + slider_s
    if rawCycleShot < chosenMachine["min_cycle"]:
        rawCycleShot = chosenMachine["min_cycle"]

    cyclePart_s = rawCycleShot / cavities

    # Erklärung
    machineExplain = (
        f"Maschine '{machineKey}' gewählt, "
        f"da mindestens {round(closure_tons,1)} t benötigt werden."
    )

    result = {
        "ok": True,
        "closure_tons": round(closure_tons, 1),
        "chosenMachine": machineKey,
        "rawCycleShot": round(rawCycleShot, 2),
        "cyclePart_s": round(cyclePart_s, 2),
        "rawSegmentVals": [
            round(oc_s, 2),
            round(injection_s, 2),
            round(rawCool_s, 2),
            round(handle_s + slider_s, 2)
        ],
        "machineExplain": machineExplain,
        "costEach": None,
        "throughput": None,
        "msg": "Spritzguss-Berechnung (Basic)."
    }
    return result


def pick_auto_machine(tons_needed, machineData):
    """
    V1-Version: Wählt kleinste Maschine, die >= tons_needed hat.
    """
    bestKey = None
    bestVal = float("inf")
    for mk, info in machineData.items():
        t = info["tons"]
        if t >= tons_needed and t < bestVal:
            bestVal = t
            bestKey = mk
    if not bestKey:
        bestKey = max(machineData.keys(), key=lambda x: machineData[x]["tons"])
    return bestKey


###########################################################
# ADVANCED => V1 Extended (Pareto)
###########################################################
def calculate_advanced_cycle(data, machineData, materialData, parallelPlast=False):
    """
    Erweiterte Berechnung:
    1) Schließkraft wie gewohnt,
       plus minimaler Variation (z. B. Automotive-Faktor).
    2) Maschine auto => Berücksichtigung von shotVolumeMax
    3) Kühlzeit mit optionaler Thermik-Formel
    4) Paralleles Plastifizieren => Zeitoptimierung
    """
    material     = data.get("material", "PP")
    cavities     = int(data.get("cavities", 4))
    partWeight   = float(data.get("partWeight", 50.0))
    runnerWeight = float(data.get("runnerWeight", 10.0))
    length_mm    = float(data.get("length_mm", 100.0))
    width_mm     = float(data.get("width_mm", 80.0))
    wall_mm      = float(data.get("wall_mm", 2.0))

    machineKey   = data.get("machineKey", "80t HighSpeed")
    isMachineAuto= bool(data.get("isMachineAuto", False))
    safe_pct     = float(data.get("safe_pct", 30.0))
    press_bar    = float(data.get("press_bar", 300.0))
    isAutomotive = bool(data.get("isAutomotive", False))
    hasRobot     = bool(data.get("hasRobot", False))
    hasSlider    = bool(data.get("hasSlider", False))
    hold_s       = float(data.get("hold_s", 2.0))
    min_cool_s   = float(data.get("min_cool_s", 1.5))
    hasContour   = bool(data.get("hasContour", False))

    matObj = materialData.get(material, materialData["PP"])
    coolFactor   = matObj["coolf"]
    density      = matObj["density_gcm3"]
    meltTemp     = matObj["melt_temp"]  # NEU: optional, Du kannst es verfeinern
    moldTemp     = matObj["mold_temp"]

    # Schussgewicht
    shotWeight_g = (partWeight + runnerWeight) * cavities
    # => Shot-Volumen in cm³
    shotVolume_cm3 = shotWeight_g / density  # sehr rudimentär

    # Schließkraft
    projArea_cm2 = (length_mm * width_mm) / 100.0
    closure_tons = projArea_cm2 * press_bar * 0.0001 * cavities
    closure_tons *= (1 + safe_pct / 100.0)
    if isAutomotive:
        closure_tons *= 1.2

    # Maschine wählen => advancedPick mit Schließkraft + shotVolume
    if machineKey not in machineData:
        machineKey = "80t HighSpeed"
    if isMachineAuto:
        machineKey = pick_auto_machine_advanced(closure_tons, shotVolume_cm3, machineData)

    chosenMachine = machineData[machineKey]

    # => Kühlzeit (etwas verfeinert, plus hasContour)
    rawCool_s = advanced_cooling_time(wall_mm, coolFactor, min_cool_s, hasContour, meltTemp, moldTemp)

    # Handling
    handle_s = 2.0 if hasRobot else 0.5
    slider_s = 1.5 if hasSlider else 0.0

    # Einspritzen + Halten
    injection_s = 1.0 + hold_s

    # Plastifizierzeit (sehr rudimentär)
    # => wir tun so, als ob wir 0.5 s pro 100 cm³ brauchen
    plasticize_s = (shotVolume_cm3 / 100.0) * 0.5
    if plasticize_s < 0.5:
        plasticize_s = 0.5  # Mindestens 0.5 s

    # Open/Close
    oc_s = chosenMachine["openclose"]

    # => Wenn parallelPlast und Maschine parallel kann, verringert sich Zyklus
    if parallelPlast and chosenMachine["parallelPlast"]:
        # 2 Haupt-Abschnitte: inj + hold vs. cooling + plast
        # Zeit = open/close + handling + max(injection, plasticize, cool)
        # (sehr vereinfachtes Modell)
        mainStage_s = max(injection_s, rawCool_s, plasticize_s)
        rawCycleShot = oc_s + mainStage_s + handle_s + slider_s
    else:
        # Standard => injection + plast + cooling addieren
        # => injection + plast kann sequentiell sein
        rawCycleShot = oc_s + injection_s + plasticize_s + rawCool_s + handle_s + slider_s

    # Maschinen-min_cycle check
    if rawCycleShot < chosenMachine["min_cycle"]:
        rawCycleShot = chosenMachine["min_cycle"]

    cyclePart_s = rawCycleShot / cavities

    machineExplain = (
        f"[ADV] Maschine '{machineKey}' gewählt, "
        f"da >= {round(closure_tons,1)} t und Volumen OK."
    )

    result = {
        "ok": True,
        "closure_tons": round(closure_tons, 1),
        "chosenMachine": machineKey,
        "rawCycleShot": round(rawCycleShot, 2),
        "cyclePart_s": round(cyclePart_s, 2),
        "rawSegmentVals": [
            round(oc_s, 2),
            round(injection_s, 2),   # NICHT paralleles Plast => injection, s.o.
            round(rawCool_s, 2),
            round(handle_s + slider_s, 2)
        ],
        "machineExplain": machineExplain,
        "costEach": None,
        "throughput": None,
        "msg": "Spritzguss-Berechnung (Advanced)."
    }
    return result


def pick_auto_machine_advanced(tons_needed, shotVolumeNeeded, machineData):
    """
    NEU: Wählt die kleinste Maschine, die:
    1) >= tons_needed
    2) shotVolumeMax >= shotVolumeNeeded
    """
    bestKey = None
    bestVal = float("inf")
    for mk, info in machineData.items():
        t  = info["tons"]
        sv = info["shotVolumeMax"]
        if (t >= tons_needed) and (sv >= shotVolumeNeeded) and (t < bestVal):
            bestVal = t
            bestKey = mk
    if not bestKey:
        # Falls keine Maschine beides erfüllt => größte
        bestKey = max(machineData.keys(), key=lambda x: machineData[x]["tons"])
    return bestKey


def advanced_cooling_time(wall_mm, coolFactor, min_cool_s, hasContour, meltTemp, moldTemp):
    """
    Beispiel einer 'etwas' fortgeschrittenen Kühlzeit:
    - t_cool_base = coolFactor * (wall_mm^2)
    - Abhängig von DeltaT = (meltTemp - moldTemp)
    - Konturnah => -20%
    - minCool_S als Untergrenze
    """
    deltaT = (meltTemp - moldTemp)
    # kleine Variation: +0.002 * deltaT pro mm^2, rein exemplarisch
    t_cool = (coolFactor * (wall_mm**2)) + (0.002 * deltaT)
    if hasContour:
        t_cool *= 0.8
    if t_cool < min_cool_s:
        t_cool = min_cool_s
    return t_cool


@takt_calc_bp.route("/druckguss", methods=["POST"])
@csrf.exempt  # Falls du globalen CSRF nutzt, und dein Frontend den Token nicht mitsendet.
@limiter.limit("150/minute")  # optional
def calc_druckguss():
    """
    POST /calc/takt/druckguss
    JSON-Beispiel:
    {
      "matName": "AlSi9Cu3",
      "partW_g": 500,
      "area_cm2": 80,
      "cav": 1,
      "isDickwand": false,
      "isEntgraten": false,
      "overflow_pct": 0.5,       # => 50%
      "isMachAuto": true,
      "machKey": "200t",
      "isAbgeschr": false,
      "sf_val": 2.0,
      "isSqueeze": false,
      "wall_mm": 6.0,
      "spray_s": 5.0,
      "hold_s": 5.0,
      "automLevel": "Manuell",   # "Manuell", "Halbauto", "Vollauto"
      "util_pct": 0.85
    }
    """
    try:
        # Hole die JSON-Daten aus dem Request
        data = request.get_json()

        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 403

        user = User.query.get(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        lvl = user.license_level()
        if lvl not in ["premium", "extended", "plus"]:
            return jsonify({"error": "Feinguss erfordert mindestens Premium."}), 403

        # (1) Eingaben parsen
        matName       = data.get("matName", "AlSi9Cu3")
        partW_g       = float(data.get("partW_g", 500.0))
        area_cm2      = float(data.get("area_cm2", 80.0))
        cav           = int(data.get("cav", 1))
        isDickwand    = bool(data.get("isDickwand", False))
        isEntgraten   = bool(data.get("isEntgraten", False))
        overflow_pct  = float(data.get("overflow_pct", 0.5))  # z. B. 0.5 = 50%
        isMachAuto    = bool(data.get("isMachAuto", True))
        machKey       = data.get("machKey", "200t")
        isAbgeschr    = bool(data.get("isAbgeschr", False))
        sf_val        = float(data.get("sf_val", 2.0))
        isSqueeze     = bool(data.get("isSqueeze", False))
        wall_mm       = float(data.get("wall_mm", 6.0))
        spray_s       = float(data.get("spray_s", 5.0))
        hold_s        = float(data.get("hold_s", 5.0))
        automLevel    = data.get("automLevel", "Manuell")  # "Manuell","Halbauto","Vollauto"
        util_pct      = float(data.get("util_pct", 0.85))

        # (2) Stammdaten (Maschinen, Materialien, Konstanten)
        machineDataDG = {
            "200t": { "tons":200, "rate":120.0, "openclose":2.0, "min_cycle":15.0, "energy_kW":80.0 },
            "400t": { "tons":400, "rate":170.0, "openclose":2.5, "min_cycle":18.0, "energy_kW":120.0},
            "800t": { "tons":800, "rate":250.0, "openclose":3.0, "min_cycle":25.0, "energy_kW":180.0}
        }
        materialDG = {
            "AlSi9Cu3": { "price":2.50, "co2_kg":10.0, "innendruck":1000.0, "rate_factor":1.0 },
            "AZ91D":    { "price":3.80, "co2_kg":15.0, "innendruck":900.0,  "rate_factor":1.5 },
            "Zamak5":   { "price":2.00, "co2_kg": 5.0, "innendruck":700.0,  "rate_factor":0.9 }
        }

        # Globale Konstanten (analog JS)
        machine_co2_kwh    = 0.4
        schmelz_kwh_per_kg = 1.2
        schmelz_eur_kwh    = 0.25
        schmelz_co2_kwh    = 0.4
        abbrand_alpha      = 0.20

        # Hilfsfunktion: pickDruckgussMachine
        def pickDruckgussMachine(forceNeeded):
            for k, info in machineDataDG.items():
                if info["tons"] >= forceNeeded:
                    return k
            return "800t"  # fallback => größte

        # (3) Material + Kraft
        matObj = materialDG.get(matName, materialDG["AlSi9Cu3"])
        base_force_t = (area_cm2 * matObj["innendruck"] * cav) / 10000.0
        if isDickwand:
            base_force_t *= 1.15  # +15% Kraft

        # => Sicherheitsfaktor
        force_t = base_force_t * sf_val

        # => Squeeze => +20% Kraft, +3s Nachdruck
        if isSqueeze:
            force_t *= 1.2
            hold_s  += 3.0

        # (4) Maschine auto oder manuell
        chosenKey = machKey
        if isMachAuto:
            chosenKey = pickDruckgussMachine(force_t)
        chosenMach = machineDataDG[chosenKey]

        # => base_rate
        base_rate = chosenMach["rate"]
        # Abgeschr => -20%
        if isAbgeschr:
            base_rate *= 0.8
        # => Legierung => rate_factor
        base_rate *= matObj["rate_factor"]

        # (5) Takt-Zeiten
        oc_s  = chosenMach["openclose"]       # z. B. 2.0 s
        fill_s= 0.05 * (partW_g ** 0.7)       # einfache Demo-Formel
        cool_s= 0.3  * (wall_mm ** 2)
        if isDickwand:
            cool_s *= 2.0

        entgr_s   = 2.0 if isEntgraten else 0.0
        takeout_s = 1.0

        if automLevel == "Manuell":
            takeout_s = 5.0
        elif automLevel == "Halbauto":
            takeout_s = 2.5
        # Vollauto => 1.0

        # cycle_shot
        cycle_shot = oc_s + spray_s + fill_s + hold_s + cool_s + entgr_s + takeout_s
        if cycle_shot < chosenMach["min_cycle"]:
            cycle_shot = chosenMach["min_cycle"]

        cyc_part = cycle_shot / max(cav,1)
        realUtil = max(util_pct, 0.0)
        shots_h  = (3600.0 / cycle_shot) * realUtil
        tph      = shots_h * cav

        # (6) Overflow + Abbrand
        part_net_kg = partW_g / 1000.0
        brutto_kg   = part_net_kg * (1 + overflow_pct)
        abbrand_kg  = (brutto_kg - part_net_kg) * abbrand_alpha
        net_plus_abbrand= part_net_kg + abbrand_kg

        # => Material + Schmelzen
        mat_price = matObj["price"]
        mat_co2   = matObj["co2_kg"]

        mat_cost_part= net_plus_abbrand * mat_price
        mat_co2_part = net_plus_abbrand * mat_co2

        # => Schmelzen
        schmelz_eur= brutto_kg * (schmelz_kwh_per_kg * schmelz_eur_kwh)
        schmelz_co2= brutto_kg * (schmelz_kwh_per_kg * schmelz_co2_kwh)

        total_mat_eur= mat_cost_part + schmelz_eur
        total_mat_co2= mat_co2_part + schmelz_co2

        # => Maschinenkosten
        cost_shot     = (base_rate / 3600.0) * cycle_shot
        mach_cost_each= cost_shot / max(cav,1)
        total_cost_each = total_mat_eur + mach_cost_each

        # => Maschine-CO₂ (Strom)
        energy_kWh_shot= chosenMach["energy_kW"] * (cycle_shot / 3600.0)
        co2_proc_each  = (energy_kWh_shot * machine_co2_kwh) / max(cav,1)
        total_co2_each = total_mat_co2 + co2_proc_each

        result = {
            "ok": True,
            "force_t": round(force_t, 1),
            "chosenMachine": chosenKey,
            "cycle_shot": round(cycle_shot, 2),
            "cycle_part": round(cyc_part, 2),
            "tph": round(tph, 1),
            "cost_each": round(total_cost_each, 2),
            "co2_each":  round(total_co2_each, 2)
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@takt_calc_bp.route("/milling", methods=["POST"])
@csrf.exempt  # Falls du global CSRF aktiviert hast und dein Frontend den Token nicht mitsendet
@limiter.limit("150/minute")  # optional
def calc_milling():
    """
    POST /calc/takt/milling

    Erwartet ein JSON, das die gleichen Felder enthält wie dein
    milling_calculator.js:
    {
      "matName": "Stahl S235",
      "isAuto": true,
      "machKey": "3-Achs Standard",
      "L_mm": 100,
      "W_mm": 80,
      "H_mm": 30,
      "Hfin": 28,
      "feed_mmmin": 1500,
      "cutDepth": 3.0,
      "toolChange_s": 20,
      "lot": 100,
      "ruest_min": 30
      // etc.
    }

    Gibt JSON zurück, z. B.:
    {
      "ok": true,
      "chosenMachine": "5-Achs Standard",
      "cycle_s": 120.0,
      "partsPerHour": 30.0,
      "costEach": 1.45,
      "co2Each": 0.28
    }
    """
    try:
        # Hole die JSON-Daten aus dem Request
        data = request.get_json()

        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 403

        user = User.query.get(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        lvl = user.license_level()
        if lvl not in ["premium", "extended", "plus"]:
            return jsonify({"error": "Feinguss erfordert mindestens Premium."}), 403

        # (1) Eingaben parsen
        matName = data.get("matName", "Stahl S235")
        isAuto = bool(data.get("isAuto", True))
        machKey = data.get("machKey", "3-Achs Standard")

        L_mm = float(data.get("L_mm", 100.0))
        W_mm = float(data.get("W_mm", 80.0))
        H_mm = float(data.get("H_mm", 30.0))
        Hfin = float(data.get("Hfin", 28.0))

        feed_mmmin = float(data.get("feed_mmmin", 1500.0))
        cutDepth = float(data.get("cutDepth", 3.0))
        toolChange_s = float(data.get("toolChange_s", 20.0))

        lot = int(data.get("lot", 100))
        ruest_min = float(data.get("ruest_min", 30.0))

        # (2) Stammdaten (Maschinen, Material)
        machineDataMilling = {
            "3-Achs Standard": {"rate": 70.0, "power": 10.0},
            "5-Achs Standard": {"rate": 120.0, "power": 15.0},
            "5-Achs HighEnd": {"rate": 180.0, "power": 25.0},
        }
        materialMilling = {
            "Stahl S235": {"price": 1.5, "dens": 7.85, "co2_kg": 2.5},
            "Alu ENAW6060": {"price": 4.0, "dens": 2.70, "co2_kg": 7.0},
            "GG25 Guss": {"price": 2.2, "dens": 7.10, "co2_kg": 3.5},
        }
        grid_co2_milling = 0.4  # 0.4 kg/kWh
        millUtilFactor = 0.90  # 90% availability

        # Hilfsfunktion => Pick Machine (auto)
        def pickMillingMachine(removedVol_mm3):
            if removedVol_mm3 > 3000:
                return "5-Achs HighEnd"
            elif removedVol_mm3 > 1000:
                return "5-Achs Standard"
            else:
                return "3-Achs Standard"

        # (3) Material
        matObj = materialMilling.get(matName, materialMilling["Stahl S235"])
        dens = matObj.get("dens", 7.85)

        # Volumen-Berechnung
        removal_h = H_mm - Hfin
        if removal_h < 0:
            removal_h = 0
        rawVol_mm3 = L_mm * W_mm * H_mm
        finishVol_mm3 = L_mm * W_mm * Hfin
        removedVol_mm3 = rawVol_mm3 - finishVol_mm3
        if removedVol_mm3 < 0:
            removedVol_mm3 = 0

        # parted_net_kg => (rawVol_mm3 * dens /1000) * 0.2
        parted_net_kg = (rawVol_mm3 * dens / 1000.0) * 0.2
        if parted_net_kg < 0:
            parted_net_kg = 0

        cost_mat = parted_net_kg * matObj["price"]
        co2_mat = parted_net_kg * matObj["co2_kg"]

        # (4) Maschine auto vs manuell
        chosenKey = machKey
        if isAuto:
            chosenKey = pickMillingMachine(removedVol_mm3)
        mch = machineDataMilling.get(chosenKey, machineDataMilling["3-Achs Standard"])
        rate_h = mch["rate"]
        power_kW = mch["power"]

        # (5) Hauptzeit
        removal_h = max(removal_h, 0.0)
        if cutDepth < 0.1:
            cutDepth = 0.1
        layers = int((removal_h / cutDepth) + 0.9999)  # ~ ceiling

        cross_mm2 = W_mm * cutDepth
        if cross_mm2 < 1.0:
            cross_mm2 = 1.0

        removalRate_mm3min = feed_mmmin * cross_mm2
        if removalRate_mm3min < 1:
            removalRate_mm3min = 1

        main_time_min = 0.0
        if removalRate_mm3min > 0:
            main_time_min = (removedVol_mm3 / removalRate_mm3min) * layers

        # Toolchange => 1 pro 5 layers
        if layers < 5:
            main_time_min += (toolChange_s / 60.0)
        else:
            tool_changes = layers // 5
            main_time_min += tool_changes * (toolChange_s / 60.0)

        # => Verfügbarkeit
        total_time_h = (main_time_min / 60.0) / millUtilFactor
        if total_time_h < 0:
            total_time_h = 0

        cycle_s = total_time_h * 3600.0
        # => Maschinenkosten
        cost_mach = rate_h * total_time_h
        # => Energie
        used_kWh = power_kW * total_time_h
        co2_proc = used_kWh * grid_co2_milling

        # => Rüst => (ruest_min/60)*30 €/h => / lot
        if lot <= 0:
            lot = 1
        ruestCost_each = ((ruest_min / 60.0) * 30.0) / lot

        cost_part = cost_mat + cost_mach + ruestCost_each
        co2_part = co2_mat + co2_proc

        # => Takte/h
        tph = 0.0
        if cycle_s > 0:
            tph = 3600.0 / cycle_s

        # (6) Ergebnis
        result = {
            "ok": True,
            "chosenMachine": chosenKey,
            "cycle_s": round(cycle_s, 2),
            "partsPerHour": round(tph, 1),
            "costEach": round(cost_part, 2),
            "co2Each": round(co2_part, 2)
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@takt_calc_bp.route("/stamping", methods=["POST"])
@csrf.exempt   # Falls du globalen CSRF-Schutz hast und dein Frontend den Token nicht mitsendet
@limiter.limit("150/minute")  # optional
def calc_stamping():
    """
    POST /calc/takt/stamping
    Erwartet ein JSON-Body (analog stamping_calculator.js):
    {
      "matName": "Stahl DC01",
      "thick_mm": 1.0,
      "area_cm2": 150.0,
      "scrap_pct": 0.15,
      "los": 10000,
      "ruest_min": 60,
      "isDick": false,
      "isAuto": true,
      "pressKey": "100"
    }
    Gibt u.a. pressForce_t, chosenPress, cycle_s, costEach, co2Each zurück.
    """
    try:
        # Hole die JSON-Daten aus dem Request
        data = request.get_json()

        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 403

        user = User.query.get(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        lvl = user.license_level()
        if lvl not in ["premium", "extended", "plus"]:
            return jsonify({"error": "Feinguss erfordert mindestens Premium."}), 403

        # 1) Eingaben parsen
        matName   = data.get("matName", "Stahl DC01")
        thick_mm  = float(data.get("thick_mm", 1.0))
        area_cm2  = float(data.get("area_cm2", 150.0))
        scrap_pct = float(data.get("scrap_pct", 0.15))  # z. B. 0.15 = 15%
        los       = int(data.get("los", 10000))
        ruest_min = float(data.get("ruest_min", 60.0))
        isDick    = bool(data.get("isDick", False))
        isAuto    = bool(data.get("isAuto", True))
        pressKey  = data.get("pressKey", "100")

        # 2) Stammdaten (Maschinen, Material, Konstanten)
        machineDataST = {
            "100": { "tons":100, "rate":70.0,  "power_kW":30.0,  "hub_min":40 },
            "200": { "tons":200, "rate":100.0, "power_kW":50.0,  "hub_min":30 },
            "400": { "tons":400, "rate":160.0, "power_kW":80.0,  "hub_min":15 },
            "600": { "tons":600, "rate":220.0, "power_kW":120.0, "hub_min":10 },
        }
        materialST = {
            "Stahl DC01":  { "price":1.30, "co2_kg":2.5, "strength":350 },
            "Stahl DP600": { "price":1.60, "co2_kg":3.0, "strength":600 },
            "Alu AW1050":  { "price":3.00, "co2_kg":7.0, "strength":120 },
        }

        stamping_co2_grid = 0.4     # kg CO2/kWh
        dick_blech_factor  = 0.8    # -20% Hub/min
        dens_stahl         = 7.85
        dens_alu           = 2.70

        # Hilfsfunktionen
        def pickStampingMachine(forceNeeded):
            # wir picken die erste, deren tons >= forceNeeded
            keys = sorted(machineDataST.keys(), key=lambda x: int(x))
            for k in keys:
                if machineDataST[k]["tons"] >= forceNeeded:
                    return k
            return "600"  # fallback => größte

        def getDensity(materialName):
            if "Alu" in materialName:
                return dens_alu
            return dens_stahl

        # 3) Berechnung

        # (A) Material (z. B. "Stahl DC01")
        matObj   = materialST.get(matName, materialST["Stahl DC01"])
        strength = matObj["strength"]
        dens     = getDensity(matName)

        # Presskraft:
        # => area (mm2) = area_cm2*100
        area_mm2   = area_cm2*100
        baseForce  = (strength * area_mm2) / (9.81e3)* 1.2* 0.25  # so wie in JS
        eff_thick  = max(thick_mm, 0.5)
        pressForce_t = baseForce * eff_thick
        if pressForce_t < 0.5:
            pressForce_t = 0.5

        # Maschine => auto oder manuell
        chosenKey = pressKey
        if isAuto:
            chosenKey = pickStampingMachine(pressForce_t)
        chosenPress = machineDataST[chosenKey]  # z. B. {"tons":100, "rate":70, "power_kW":30, "hub_min":40}

        baseRate = chosenPress["rate"]
        powerKW  = chosenPress["power_kW"]
        hub_min  = chosenPress["hub_min"]  # nominal
        # Dickes Blech => factor *0.8 => real hub_min
        thickFactor = 1.0
        if thick_mm > 1.0:
            # optional: kleine Heuristik => ab 1 mm
            # z. B. -0.1 pro mm ...
            # Aus JS: max(1.0 -0.1*(thick_mm-1), 0.3)
            thickFactor = max(1.0 - 0.1*(thick_mm-1.0), 0.3)
        if isDick:  # + dein Checkbox
            thickFactor *= dick_blech_factor  # 0.8
        real_hub_min = hub_min* thickFactor
        if real_hub_min < 1.0:
            real_hub_min = 1.0

        # Shots/h
        shots_h = real_hub_min*60.0
        if shots_h < 1.0:
            shots_h = 1.0
        cyc_s = 3600.0 / shots_h

        # (B) Material-Kosten & -CO2
        # parted_vol = area_cm2 * thick_cm => parted_mass => +scrap => parted_total_kg
        thick_cm  = thick_mm / 10.0
        parted_vol_cm3 = area_cm2* thick_cm
        parted_mass_kg = parted_vol_cm3* dens/ 1000.0
        parted_total_kg= parted_mass_kg*(1+ scrap_pct)

        cost_mat_each = parted_total_kg* matObj["price"]
        co2_mat_each  = parted_total_kg* matObj["co2_kg"]

        # (C) Rüst
        if los <= 0:
            los = 1
        ruestCost_each = ((ruest_min / 60.0)* 30.0)/ los

        # (D) Maschine
        costMachEach = baseRate / shots_h

        # (E) Strom => powerKW*(cyc_s/3600)* stamping_co2_grid
        energy_kWh_shot= powerKW* (cyc_s/3600.0)
        co2_proc_each  = energy_kWh_shot* stamping_co2_grid

        costEach = cost_mat_each+ ruestCost_each+ costMachEach
        co2Each  = co2_mat_each+ co2_proc_each

        result = {
            "ok": True,
            "pressForce_t": round(pressForce_t, 1),
            "chosenPress": chosenKey + " t",
            "cycle_s": round(cyc_s, 2),
            "partsPerHour": round(shots_h, 1),
            "costEach": round(costEach, 2),
            "co2Each": round(co2Each, 2)
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500