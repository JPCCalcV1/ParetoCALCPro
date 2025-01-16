# routes/mycalc_routes.py

import os
import json
import requests
from flask import Blueprint, request, jsonify, render_template, g, session
from datetime import datetime

# Dein DB- & User-Modell
from models import db, User
from core.extensions import csrf  # Falls du @csrf.exempt nutzen willst
import calculations  # Deine calculations.py (mit calculate_all(...))

mycalc_bp = Blueprint("mycalc_bp", __name__)

# CustomGPT API-Einstellungen (ENV oder Hardcode)
CGPT_API_KEY = os.getenv("CUSTOMGPT_API_KEY", "")
CGPT_PROJECT_ID = os.getenv("CUSTOMGPT_PROJECT_ID", "")
BASE_URL = "https://app.customgpt.ai/api/v1/projects"


@mycalc_bp.before_app_request
def load_current_user():
    """
    Wird vor jeder Anfrage in diesem Blueprint aufgerufen.
    Lädt den aktuellen User via session["user_id"] in g.user.
    """
    uid = session.get("user_id")
    if uid:
        user = User.query.get(uid)
        g.user = user
    else:
        g.user = None


@mycalc_bp.route("/", methods=["GET"])
def show_calc_page():
    """
    Rendert die Hauptseite (mycalc.html).
    """
    return render_template("my_calc_final.html")


@mycalc_bp.route("/impressum", methods=["GET"])
def impressum():
    """
    Einfaches Impressum. Gibt reines HTML zurück.
    """
    return "<h1>Impressum</h1><p>Beta ...</p>"


@mycalc_bp.route("/datenschutz", methods=["GET"])
def datenschutz():
    """
    Einfaches Datenschutz-Placeholder.
    """
    return "<h1>Datenschutz</h1><p>...</p>"


@mycalc_bp.route("/material_list", methods=["GET"])
def get_material_list():
    """
    Gibt abhängig vom Lizenz-Level (g.user.license_level())
    die passende JSON-Datei für Materialdaten zurück.
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403
    if not g.user.has_valid_license():
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    lvl = g.user.license_level()
    if lvl in ["test", "premium"]:
        filename = "materialListe_pro.json"
    elif lvl == "plus":
        filename = "materialListe_plus.json"
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


@mycalc_bp.route("/machine_list", methods=["GET"])
def get_machine_list():
    """
    Analog zu material_list.
    Hier könntest du je nach License-Level
    unterschiedliche Maschinenlisten ausgeben.
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403
    if not g.user.has_valid_license():
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    lvl = g.user.license_level()
    # Falls du verschiedene JSONs hast (machineListe_pro.json, etc.)
    # analog wie oben:
    if lvl in ["test", "premium"]:
        filename = "machineListe_pro.json"
    elif lvl == "plus":
        filename = "machineListe_plus.json"
    elif lvl == "extended":
        filename = "machineListe_extended.json"
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


@mycalc_bp.route("/lohn_list", methods=["GET"])
def get_lohn_list():
    """
    Analog zum Material-/Machine-Listing.
    Falls du verschiedene Lohnlisten hast (pro License).
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403
    if not g.user.has_valid_license():
        return jsonify({"error": "Lizenz abgelaufen"}), 403

    lvl = g.user.license_level()
    # Beispiel:
    if lvl in ["test", "premium"]:
        filename = "lohnListe_pro.json"
    elif lvl == "plus":
        filename = "lohnListe_plus.json"
    elif lvl == "extended":
        filename = "lohnListe_extended.json"
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


@mycalc_bp.route("/calc", methods=["POST"])
@csrf.exempt  # Falls dein JS-Frontend keinen CSRF-Token mitsendet
def do_calc():
    """
    Ruft calculations.calculate_all(data_in) auf
    und gibt das Ergebnis als JSON zurück.
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    data_in = request.get_json() or {}
    try:
        result = calculations.calculate_all(data_in)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mycalc_bp.route("/gpt_ask", methods=["POST"])
@csrf.exempt
def gpt_ask():
    """
    Stellt eine Frage an CustomGPT, verbraucht 1 GPT-Call,
    sofern license_level() in ["test","premium","extended"].
    """
    if not g.user:
        return jsonify({"error": "Not logged in"}), 403

    lvl = g.user.license_level()
    if lvl not in ["test", "premium", "extended"]:
        return jsonify({"error": "No GPT access for tier"}), 403

    if g.user.gpt_used_count >= g.user.gpt_allowed_count:
        return jsonify({"error": "GPT limit reached"}), 429

    data = request.get_json() or {}
    prompt = data.get("prompt", "") or data.get("question", "")
    if not prompt.strip():
        return jsonify({"error": "No prompt"}), 400

    # GPT-Session-ID in session[] merken
    session_id = session.get("gpt_session_id", "")
    if not session_id:
        sid = create_gpt_session_internal("AutoSession")
        if not sid:
            return jsonify({"error": "Failed to create GPT session"}), 500
        session["gpt_session_id"] = sid
        session_id = sid

    # Request an CustomGPT
    try:
        r = requests.post(
            f"{BASE_URL}/{CGPT_PROJECT_ID}/conversations/{session_id}/messages",
            headers={
                "Authorization": f"Bearer {CGPT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"response_source": "default", "prompt": prompt},
            timeout=15
        )
        if not r.ok:
            return jsonify({"error": f"CustomGPT: {r.status_code}", "details": r.text}), 500

        data_r = r.json()
        answer_text = data_r.get("data", {}).get("openai_response", "")
        if not answer_text.strip():
            return jsonify({"error": "No valid answer"}), 500

        # GPT-Call verbraucht
        g.user.gpt_used_count += 1
        db.session.commit()

        return jsonify({"answer": answer_text})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


def create_gpt_session_internal(name="AutoSession"):
    """
    Hilfsfunktion, um bei CustomGPT eine Conversation Session zu erzeugen.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/{CGPT_PROJECT_ID}/conversations",
            headers={
                "Authorization": f"Bearer {CGPT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"name": name},
            timeout=15
        )
        if not r.ok:
            return None
        rr = r.json()
        return rr.get("data", {}).get("session_id", None)
    except:
        return None