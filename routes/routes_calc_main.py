# routes/routes_calc_main.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from core.extensions import limiter

main_calc_bp = Blueprint('main_calc_bp', __name__)

@main_calc_bp.route('/maincalc', methods=['GET'])
@login_required
def main_calc_view():
    """
    Rendert die Hauptseite mit den 5 Tabs (Projekt, Material, Fertigung, Charts, Baugruppe).
    Alle Modal-Fenster sind hier (bzw. via includes).
    """
    return render_template('calc/main_calc.html')

@main_calc_bp.route('/maincalc/compute', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def main_calc_compute():
    """
    Die zentrale Berechnung (z. B. „Berechnen“-Button).
    - In V1 war das deine Calculations.py
    - Hier nur Dummy
    """
    data = request.json or {}
    # Bsp: stueckzahl = data.get('stueckzahl', 0)
    # Hier würde dann die "MainCalc" Logik laufen
    result = {
        'total_costs': 1234.56,
        'co2_emission': 78.9,
        'detail': "Dummy result - to be replaced with real logic"
    }
    return jsonify(result)