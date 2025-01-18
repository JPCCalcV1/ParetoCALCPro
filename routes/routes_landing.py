# routes/routes_landing.py

from flask import Blueprint, render_template
from helpers.sendgrid_helper import send_email
landing_bp = Blueprint("landing_bp", __name__)

@landing_bp.route("/")
def landing():
    """
    Rendert die Landingpage für die App.
    => Sucht template "landing/landing.html"
    """
    return render_template("landing/landing.html")

from flask import Blueprint, jsonify
from helpers.sendgrid_helper import send_email  # Import SendGrid-Helper


@landing_bp.route("/test_email", methods=["GET"])
def test_email():
    """
    Öffentlich zugängliche Test-Route für E-Mail-Versand.
    """
    to_email = "jochen.pfeffer@web.de"  # Deine echte E-Mail-Adresse
    subject = "Test-E-Mail von SendGrid (Render)"
    body_text = "Hallo Jochen, dies ist ein Test direkt aus der Render-Umgebung."
    body_html = "<strong>Hallo Jochen, dies ist ein Test direkt aus der Render-Umgebung.</strong>"

    try:
        status = send_email(to_email, subject, body_text, body_html)
        return jsonify({"status": status, "message": "Test-E-Mail erfolgreich gesendet!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500