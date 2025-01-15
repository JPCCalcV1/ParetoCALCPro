from flask import Blueprint, render_template

landing_bp = Blueprint('landing_bp', __name__)

@landing_bp.route('/')
def landing():
    """
    Rendert die Landingpage für die App.
    """
    return render_template('landing/landing.html')