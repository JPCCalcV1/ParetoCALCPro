# routes/routes_calc_main.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from core.extensions import limiter
from core.extensions import csrf


main_calc_bp = Blueprint('main_calc_bp', __name__)

@main_calc_bp.route('/maincalc', methods=['GET'])
@login_required
def main_calc_view():
    """
    Rendert die Hauptseite (Tabs 1–5: Projekt, Material, Fertigung, Charts, Baugruppe).
    """
    return render_template('calc/main_calc.html')


@main_calc_bp.route('/compute', methods=['POST'])
@csrf.exempt  # Wenn du globales CSRF benutzt, kannst du hier @csrf.exempt entfernen,
             # falls dein Frontend den Token korrekt mitsendet. Ansonsten bleibts.
@login_required
@limiter.limit("20/minute")  # Rate-Limit (Beispiel)
def maincalc_compute():
    """
    Nimmt die JSON-Daten von calcAll() entgegen,
    ruft calculate_all(data) aus calculations.py auf
    und gibt das Ergebnis als JSON zurück.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        # Rufe deine bereits vorhandene Berechnungsfunktion auf:
        result = calculate_all(data)

        return jsonify(result), 200

    except Exception as e:
        # Fehlerbehandlung
        return jsonify({"error": str(e)}), 500