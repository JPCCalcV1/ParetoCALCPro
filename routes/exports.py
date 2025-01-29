from flask import Blueprint, request, send_file, jsonify
from .excel import export_baugruppe_eight_steps_excel
from .powerpoint import export_baugruppe_pptx
exports_bp = Blueprint("exports_bp", __name__)
# ------------------------------------------------------------------------
# Einige Zeilen Kontext / andere Routen
# ------------------------------------------------------------------------

@exports_bp.route("/baugruppe/excel_8steps", methods=["POST"])
def baugruppe_excel_8steps():
    """
    POST erwartet JSON mit tab1, tab2, tab3, tab4.
    Gibt ein Excel zurück mit 2 Sheets:
    1) "Pareto-Kalk – Gesamtübersicht"
    2) "Lieferanten-Vergleich"
    """
    data = request.get_json() or {}
    tab1 = data.get("tab1", {})  # Projekt/Teil
    tab2 = data.get("tab2", {})  # Material
    tab3 = data.get("tab3", [])  # Fertigungsschritte
    tab4 = data.get("tab4", {})  # Ergebnis-Summen

    try:
        excel_bytes, filename = export_baugruppe_eight_steps_excel(tab1, tab2, tab3, tab4)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(
        excel_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@exports_bp.route("/baugruppe/ppt", methods=["POST"])
def baugruppe_ppt_export():
    """
    Erstellt eine PowerPoint-Präsentation (3 Slides):
      1) Deckblatt (Logo + Projektinfo)
      2) Kalkulation (Tab1-4)
      3) Vergleich (Unsere Kalkulation vs. Lieferant)

    KEIN License-Check.
    Erwartet JSON-Body mit "tab1", "tab2", "tab3" (Liste max.8), "tab4".
    """
    data = request.get_json() or {}
    # Sammle die Dicts, identisch wie beim Excel-Export
    tab1 = data.get("tab1", {})
    tab2 = data.get("tab2", {})
    tab3 = data.get("tab3", [])
    tab4 = data.get("tab4", {})

    try:
        ppt_bytes, filename = export_baugruppe_pptx(tab1, tab2, tab3, tab4)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(
        ppt_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )