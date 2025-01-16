# routes/routes_gpt.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from core.extensions import db, limiter
from models.gpt_session import GPTSession

gpt_bp = Blueprint('gpt_bp', __name__)


@gpt_bp.route('/create-session', methods=['POST'])
@login_required
@limiter.limit("5/minute")
def create_gpt_session():
    """Erzeugt / reaktiviert eine GPT-Session mit Kontingent (allowed_count)."""
    allowed_count = 10
    existing = GPTSession.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify({
            'message': 'Already have a GPT session.',
            'session_id': existing.id,
            'used_count': existing.used_count,
            'allowed_count': existing.allowed_count
        }), 200
    else:
        new_session = GPTSession(
            user_id=current_user.id,
            allowed_count=allowed_count,
            used_count=0
        )
        db.session.add(new_session)
        db.session.commit()

        return jsonify({
            'message': 'Created new GPT session.',
            'session_id': new_session.id,
            'used_count': new_session.used_count,
            'allowed_count': new_session.allowed_count
        }), 201


@gpt_bp.route('/ask', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def gpt_ask():
    """Verbraucht 1 GPT-Call. Nur erlaubt, solange used_count < allowed_count."""
    gpt_session = GPTSession.query.filter_by(user_id=current_user.id).first()
    if not gpt_session:
        return jsonify({'error': 'No GPT session found'}), 400

    if gpt_session.used_count >= gpt_session.allowed_count:
        return jsonify({'error': 'GPT usage limit exceeded'}), 403

    data = request.json or {}
    user_prompt = data.get('prompt', '')
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    # Hier ggf. CustomGPT.ai aufrufen. Wir mocken es:
    mock_response = f"GPT response to prompt: {user_prompt}"

    # used_count erhöhen
    gpt_session.used_count += 1
    db.session.commit()

    return jsonify({
        'prompt': user_prompt,
        'response': mock_response,
        'remaining': gpt_session.allowed_count - gpt_session.used_count
    }), 200