
from flask import Blueprint, request, send_file, session, jsonify
from .excel import (
    export_baugruppe_excel,
    export_baugruppe_comparison_excel
)

exports_bp = Blueprint("exports_bp", __name__)

# ------------------------------------------------------------------------
# Einige Zeilen Kontext / andere Routen
# ------------------------------------------------------------------------

@exports_bp.route("/baugruppe/excel", methods=["POST"])
def baugruppe_excel_export():
    """
    EXISTIERENDE Route: Erzeugt das einfache Excel für Baugruppen.
    """
    # 1) License-Check
    license_level = session.get("license_tier", "test")
    #if license_level in ["plus", "test"]:
    #    return jsonify({"error": "Abo zu niedrig für Excel-Export"}), 403

    # 2) Baugruppen-Daten aus JSON Body
    data = request.get_json() or {}
    items = data.get("baugruppenItems", [])
    if not items:
        return jsonify({"error": "Keine Einträge in Baugruppe"}), 400

    # 3) Rufe alte Funktion auf
    excel_bytes, filename = export_baugruppe_excel(items)
    return send_file(
        excel_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ------------------------------------------------------------------------
# NEUE Route: Erzeugt fancy/vergleichende Excel-Auswertung
# ------------------------------------------------------------------------
@exports_bp.route("/baugruppe/excel_comparison", methods=["POST"])
def baugruppe_excel_comparison():
    """
    Neue Route: Erstellt das 'FullOverview' + 'SupplierCompare'-Excel
    mit Ampelfunktion für Delta-Analyse.
    """
    # 1) License-Check
    license_level = session.get("license_tier", "test")
    if license_level in ["plus", "test"]:
        return jsonify({"error": "Abo zu niedrig für Comparison-Excel-Export"}), 403

    # 2) JSON Daten abrufen: Tab1, Tab2, Tab3, Tab4
    data = request.get_json() or {}
    tab1 = data.get("tab1", {})    # dict
    tab2 = data.get("tab2", {})    # dict
    tab3 = data.get("tab3", [])    # list of dict (max. 8)
    tab4 = data.get("tab4", {})    # dict (Ergebnis-Summary)

    # 3) Excel generieren
    excel_bytes, filename = export_baugruppe_comparison_excel(tab1, tab2, tab3, tab4)

    # 4) Download
    return send_file(
        excel_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ------------------------------------------------------------------------
# (Weitere Routen oder Endpunkte könnten folgen)
# ------------------------------------------------------------------------


@exports_bp.route("/baugruppe/pdf", methods=["POST"])
def baugruppe_pdf_export():
    # License-Check
    license_level = session.get("license_tier","test")
    if license_level in ["plus","test"]:
        return jsonify({"error":"Abo zu niedrig für PDF-Export"}),403

    data = request.get_json() or {}
    items = data.get("baugruppenItems",[])
    if not items:
        return jsonify({"error":"Keine Einträge in Baugruppe"}),400

    pdf_io, filename = export_baugruppe_pdf(items)
    return send_file(pdf_io, download_name=filename, as_attachment=True, mimetype="application/pdf")