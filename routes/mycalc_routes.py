# routes/mycalc_routes.py

import os
import json
import requests
from flask import Blueprint, request, jsonify, render_template, session, g
from datetime import datetime
from models.user import db, User
from core.extensions import csrf, limiter  # NEU: limiter import
import calculations  # Deine file: calculations.py


# => def taktzeit_calc(...), def param_calc(...), def calculate_all(data)...

mycalc_bp = Blueprint("mycalc_bp", __name__)


@mycalc_bp.before_app_request
def load_current_user():
    uid = session.get("user_id")
    if uid:
        g.user = User.query.get(uid)
    else:
        g.user = None


@mycalc_bp.route("/material_list", methods=["GET"])
def get_material_list():
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    lvl = g.user.license_level()
    if lvl == "no_access":
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    if lvl in ["plus"]:
        filename = "materialListe_plus.json"
    elif lvl == "premium":
        filename = "materialListe_premium.json"
    elif lvl == "extended":
        filename = "materialListe_extended.json"
    else:
        return jsonify({"error": "Lizenz nicht ausreichend"}), 403

    try:
        file_path = os.path.join("data", filename)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"{filename} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------
#   MASCHINEN-LISTE
# ---------------------------------------------
@mycalc_bp.route("/machine_list", methods=["GET"])
def get_machine_list():
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    lvl = g.user.license_level()
    if lvl == "no_access":
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    if lvl in ["plus"]:
        filename = "machines_test.json"
    elif lvl == "premium":
        filename = "machines_premium.json"
    elif lvl == "extended":
        filename = "machines_extended.json"
    else:
        return jsonify({"error": "Lizenz nicht ausreichend"}), 403

    try:
        file_path = os.path.join("data", filename)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"{filename} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------
#   LOHN-LISTE
# ---------------------------------------------
@mycalc_bp.route("/lohn_list", methods=["GET"])
def get_lohn_list():
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    lvl = g.user.license_level()
    if lvl == "no_access":
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    if lvl in ["plus"]:
        filename = "lohnliste_plus.json"
    elif lvl == "premium":
        filename = "lohnliste_premium.json"
    elif lvl == "extended":
        filename = "lohnliste_extended.json"
    else:
        return jsonify({"error": "Lizenz nicht ausreichend"}), 403

    try:
        file_path = os.path.join("data", filename)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"{filename} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------
#   CALC MACHINE (optional)
#   => Wenn du Maschinenkosten
#   => programmatisch berechnen willst
# ---------------------------------------------
@mycalc_bp.route("/calc_machine", methods=["POST"])
def calc_machine():
    """
    Liest JSON-Body, z. B. { "purchasePrice":..., "hoursPerYear":..., ... }
    Rechnet via calculations.calc_machine(...) => returns JSON
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    try:
        result = calculations.calc_machine(data_in)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------
#   CALC LABOR (optional)
#   => Wenn du Lohnberechnung
#   => programmatisch machen willst
# ---------------------------------------------
@mycalc_bp.route("/calc_labor", methods=["POST"])
def calc_labor():
    """
    Liest JSON-Body, z. B.: {
      "baseWage":20.0, "socialChargesPct":0.5, "shiftSurchargePct":0.2
    }
    => calculations.calc_labor(...) => returns { "labor_rate": ... }
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    try:
        result = calculations.calc_labor(data_in)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mycalc_bp.route("/", methods=["GET"])
def show_calc_page():
    return render_template("my_calc_coloradmin.html")


@mycalc_bp.route("/taktzeit", methods=["POST"])
def calc_taktzeit():
    """Ex-V1 Taktzeitrechner."""
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    cycle_time = float(data_in.get("cycle_time", 0.0))
    stations = int(data_in.get("stations", 1))
    result_val = calculations.taktzeit_calc(cycle_time, stations)

    return jsonify({
        "cycle_time": cycle_time,
        "stations": stations,
        "calculated_taktzeit": result_val
    }), 200


@mycalc_bp.route("/parametrik", methods=["POST"])
def calc_parametrik():
    """Ex-V1 Parametrik."""
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    base_val = float(data_in.get("base_value", 0.0))
    factor = float(data_in.get("factor", 1.0))
    result_val = calculations.param_calc(base_val, factor)

    return jsonify({
        "base_value": base_val,
        "factor": factor,
        "result": result_val
    }), 200


@mycalc_bp.route("/calc", methods=["POST"])
@csrf.exempt  # falls dein JS keinen CSRF-Token sendet
def do_calc():
    """Ex-V1: Gesamtkalkulation => calculations.calculate_all(data_in)."""
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    try:
        res = calculations.calculate_all(data_in)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mycalc_bp.route("/gpt_ask", methods=["POST"])
@csrf.exempt  # falls dein JS keinen CSRF-Token sendet
@limiter.limit("50 per day")  # NEU: max. 50 GPT-Calls pro Tag
def gpt_ask():
    """
    GPT => userQuestion => check license => custom GPT usage -> +1 gpt_used_count
    EINE Route => /mycalc/gpt_ask
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    lvl = g.user.license_level()
    if lvl not in ["test", "plus", "premium", "extended"]:
        return jsonify({"error": "No GPT in this tier"}), 403

    if g.user.gpt_used_count >= g.user.gpt_allowed_count:
        return jsonify({"error": "GPT limit reached"}), 429

    data_in = request.get_json() or {}
    prompt = data_in.get("question", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt"}), 400

    # Falls du eine Remote-API an customGPT.ai nutzt:
    CGPT_API_KEY = os.getenv("CUSTOMGPT_API_KEY", "")
    CGPT_PROJECT_ID = os.getenv("CUSTOMGPT_PROJECT_ID", "")
    if not CGPT_API_KEY or not CGPT_PROJECT_ID:
        return jsonify({"error": "No CustomGPT config"}), 500

    # Session-basierte Konversation
    sess_id = session.get("gpt_session_id", "")
    if not sess_id:
        # auto create conversation
        sid = create_gpt_session_internal("AutoSession")
        if not sid:
            return jsonify({"error": "GPT session creation fail"}), 500
        session["gpt_session_id"] = sid
        sess_id = sid

    endpoint = f"https://app.customgpt.ai/api/v1/projects/{CGPT_PROJECT_ID}/conversations/{sess_id}/messages"
    headers = {
        "Authorization": f"Bearer {CGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "response_source": "default",
        "prompt": prompt
    }

    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if not r.ok:
            return jsonify({"error": f"CustomGPT: {r.status_code}", "details": r.text}), 500

        rd = r.json()
        answer_txt = rd.get("data", {}).get("openai_response", "")
        if not answer_txt.strip():
            return jsonify({"error": "No valid answer"}), 500

        # usage
        g.user.gpt_used_count += 1
        db.session.commit()

        return jsonify({"answer": answer_txt}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


def create_gpt_session_internal(name="AutoSession"):
    CGPT_API_KEY = os.getenv("CUSTOMGPT_API_KEY", "")
    CGPT_PROJECT_ID = os.getenv("CUSTOMGPT_PROJECT_ID", "")
    if not CGPT_API_KEY or not CGPT_PROJECT_ID:
        return None
    endpoint = f"https://app.customgpt.ai/api/v1/projects/{CGPT_PROJECT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {CGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"name": name}
    try:
        rr = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if not rr.ok:
            return None
        dd = rr.json()
        return dd.get("data", {}).get("session_id", None)
    except:
        return None
