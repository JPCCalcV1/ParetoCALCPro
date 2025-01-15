# routes/routes_calc_param.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from core.extensions import limiter

param_calc_bp = Blueprint('param_calc_bp', __name__)

# — Feinguss
@param_calc_bp.route('/feinguss', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_feinguss():
    data = request.json or {}
    # Hier deine echte Logik... dummy:
    return jsonify({'result': "Feinguss-Ergebnis", 'dummy': True})

# — Kaltfließpressen
@param_calc_bp.route('/kaltflies', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_kaltflies():
    data = request.json or {}
    return jsonify({'result': "Kaltfließpressen-Ergebnis", 'dummy': True})

# — Schmieden
@param_calc_bp.route('/schmieden', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_schmieden():
    data = request.json or {}
    return jsonify({'result': "Schmieden-Ergebnis", 'dummy': True})

# — PCB/Leiterplatte
@param_calc_bp.route('/pcb', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_pcb():
    data = request.json or {}
    return jsonify({'result': "PCB-Ergebnis", 'dummy': True})