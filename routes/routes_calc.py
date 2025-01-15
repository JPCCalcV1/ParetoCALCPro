# routes/routes_calc.py

from flask import Blueprint, request, jsonify
from flask_login import login_required
from core.extensions import limiter

calc_bp = Blueprint('calc_bp', __name__)

@calc_bp.route('/taktzeit', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_taktzeit():
    """Dummy-Endpoint für Taktzeit-Berechnung."""
    data = request.json or {}
    cycle_time = float(data.get('cycle_time', 0.0))
    stations = int(data.get('stations', 1))

    taktzeit_result = 0.0
    if stations > 0:
        taktzeit_result = cycle_time / stations

    return jsonify({
        'cycle_time': cycle_time,
        'stations': stations,
        'calculated_taktzeit': taktzeit_result
    }), 200

@calc_bp.route('/parametrik', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_parametrik():
    """Dummy-Endpoint für Parametrik-Berechnungen."""
    data = request.json or {}
    base_value = float(data.get('base_value', 0.0))
    factor = float(data.get('factor', 1.0))

    param_result = base_value * factor
    return jsonify({
        'base_value': base_value,
        'factor': factor,
        'result': param_result
    }), 200