# routes/routes_calc_takt.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from core.extensions import limiter

takt_calc_bp = Blueprint('takt_calc_bp', __name__)

@takt_calc_bp.route('/spritzguss', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_spritzguss():
    data = request.json or {}
    return jsonify({'result': "Taktzeit-Spritzguss", 'dummy': True})

@takt_calc_bp.route('/druckguss', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_druckguss():
    data = request.json or {}
    return jsonify({'result': "Taktzeit-Druckguss", 'dummy': True})

@takt_calc_bp.route('/zerspanung', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_zerspanung():
    data = request.json or {}
    return jsonify({'result': "Taktzeit-Zerspanung", 'dummy': True})

@takt_calc_bp.route('/stanzen', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def calc_stanzen():
    data = request.json or {}
    return jsonify({'result': "Taktzeit-Stanzen", 'dummy': True})