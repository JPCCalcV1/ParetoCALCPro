import io
from flask import request, jsonify, send_file, Blueprint
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
# Ggf. openpyxl.worksheet.worksheet import Worksheet



from flask import Blueprint, request, send_file, session, jsonify
from .excel import (
    export_baugruppe_eight_steps_excel,
    export_baugruppe_comparison_excel,
    export_pareto_kalk_epic
)
from .powerpoint import export_baugruppe_pptx

exports_bp = Blueprint("exports_bp", __name__)

# ------------------------------------------------------------------------
# Einige Zeilen Kontext / andere Routen
# ------------------------------------------------------------------------


# ------------------------------------------------------------------------
# NEUE Route: Erzeugt fancy/vergleichende Excel-Auswertung
# ------------------------------------------------------------------------
@exports_bp.route("/baugruppe/excel_comparison", methods=["POST"])
def baugruppe_excel_comparison():
    """
    Neue Route: Erstellt das 'FullOverview' + 'SupplierCompare'-Excel
    mit Ampelfunktion für Delta-Analyse.
    """


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


    data = request.get_json() or {}
    items = data.get("baugruppenItems",[])
    if not items:
        return jsonify({"error":"Keine Einträge in Baugruppe"}),400

    pdf_io, filename = export_baugruppe_pdf(items)
    return send_file(pdf_io, download_name=filename, as_attachment=True, mimetype="application/pdf")

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




@exports_bp.route("/baugruppe/excel_8steps", methods=["POST"])
def baugruppe_excel_8steps():
    """
    Erstellt ein breites OnePager-Excel (8 Schritte + Summen).
    Erwartet JSON mit tab1, tab2, tab3, tab4.
    Erstellt einen "OnePager"-Excel-Export mit 8 Schritten + Summen,
    in dem u.a. Material-/Fertigungskosten und Ausschuss etc. abgebildet sind.
    """
    data = request.get_json() or {}
    tab1 = data.get("tab1", {})
    tab2 = data.get("tab2", {})
    tab3 = data.get("tab3", [])  # list of dict
    tab4 = data.get("tab4", {})

    try:
        excel_bytes, filename = export_baugruppe_eight_steps_excel(
            tab1_data=tab1,
            tab2_data=tab2,
            tab3_steps=tab3,
            tab4_summary=tab4
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(
        excel_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@exports_bp.route("/baugruppe/excel_epic", methods=["POST"])
def baugruppe_excel_epic():
    """
    Route für das 'epische' Excel nach dem Layout deines Screenshots.
    Erwartet JSON Body mit tab1, tab2, tab3, tab4.
    Keine License-Checks, 1:1 Copy-Paste.
    """
    data = request.get_json() or {}
    tab1 = data.get("tab1", {})
    tab2 = data.get("tab2", {})
    tab3 = data.get("tab3", [])
    tab4 = data.get("tab4", {})

    try:
        excel_bytes, filename = export_pareto_kalk_epic(tab1, tab2, tab3, tab4)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(
        excel_bytes,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )