import io
import os
import xlsxwriter
from flask import current_app
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, PatternFill, Alignment
from flask import Blueprint
exports_bp = Blueprint("exports_bp", __name__)

# ---------------------------------------------------------------
# NEUE FUNKTION: export_baugruppe_eight_steps_excel
# ---------------------------------------------------------------
def export_baugruppe_eight_steps_excel(tab1, tab2, tab3, tab4):
    """
    Erzeugt ein OnePager-Excel mit den Projekt-/Material-/Fertigungs- und Ergebnisdaten,
    plus optional ein 2. Tabellenblatt für Supplier-Breakdown.
    """
    # Neues Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Kalkulation OnePager"

    # ----------------------------------------------------------------
    # 1) Allgemeines Layout: Spaltenbreiten, Schrift, Farben
    # ----------------------------------------------------------------
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 16
    ws.column_dimensions["H"].width = 16
    ws.column_dimensions["I"].width = 16
    ws.column_dimensions["J"].width = 16

    # Rand-Styles
    thin = Side(border_style="thin", color="000000")
    medium = Side(border_style="medium", color="000000")
    all_border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill(start_color="FFCCE5FF", end_color="FFCCE5FF", fill_type="solid")

    # ----------------------------------------------------------------
    # 2) Kopfzeile mit Logo & Titel
    # ----------------------------------------------------------------
    # Zusammenführen (A1..D2 als Beispiel, E1..J8 für Logo).
    # Oder du kannst A1..J1 mergen und das Logo einfach positionieren.
    ws.merge_cells("A1:D2")
    ws["A1"].value = "Pareto-Kalk – Gesamtübersicht"
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws["A1"].font = Font(bold=True, size=14)
    ws.row_dimensions[1].height = 40

    # Logo in Spalte F1 (z.B.). Pfad musst du anpassen:
    # try:
    #     img = Image("static/img/jpc.jpeg")
    #     img.width = 200  # Anpassen an gewünschte Größe
    #     img.height = 80
    #     ws.add_image(img, "F1")
    # except:
    #     pass

    # ----------------------------------------------------------------
    # 3) Projekt-Daten (tab1) – ab Zeile 4
    # ----------------------------------------------------------------
    current_row = 4
    project_fields = [
        ("Projektname",   tab1.get("projectName", "")),
        ("Bauteilname",   tab1.get("partName", "")),
        ("Jahresstückzahl", tab1.get("annualQty", 0)),
        ("Losgröße",        tab1.get("lotSize", 0)),
        ("Ausschuss (%)",   tab1.get("scrapPct", 0)),
        ("SG&A (%)",        tab1.get("sgaPct", 0)),
        ("Profit (%)",      tab1.get("profitPct", 0)),
    ]
    for label, val in project_fields:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # Schöne Überschrift "Material" (z.B. in Zeile current_row+1)
    current_row += 1
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=2)
    ws.cell(row=current_row, column=1).value = "Materialdaten"
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=1).fill = header_fill
    current_row += 1

    # ----------------------------------------------------------------
    # 4) Material-Daten (tab2)
    # ----------------------------------------------------------------
    # Felder: Name, Preis, CO2, GK, Gewicht, Fremdzukauf
    mat_fields = [
        ("Materialname",   tab2.get("matName", "Aluminium")),
        ("Materialpreis (€/kg)", tab2.get("matPrice", 0.0)),
        # (Optional) CO2 z.B. "Material-CO₂ (kg/kg)" – nur wenn du willst:
        # ("Material-CO₂ (kg/kg)",  ???  ),
        ("Material-GK (%)",       tab2.get("matGK", 0.0)),
        ("Bauteilgewicht (kg)",   tab2.get("matWeight", 0.0)),
        ("Fremdzukauf (€/Stück)", tab2.get("fremdValue", 0.0)),
    ]
    for label, val in mat_fields:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # Leerzeile
    current_row += 1

    # ----------------------------------------------------------------
    # 5) Fertigungsschritte (tab3)
    # ----------------------------------------------------------------
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
    ws.cell(row=current_row, column=1).value = "Fertigungsschritte"
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=1).fill = header_fill
    current_row += 1

    # Tabellen-Kopf (Arbeitsschritt, Zyklus, MS, Lohn, Rüst, Tooling, FGK, CO2, Kosten, ...)
    fert_headers = [
        "Arbeitsschritt", "Zyklus (s)", "MS (€/h)", "Lohn (€/h)",
        "Rüst (€/Los)",   "Tooling/Stück (€)", "FGK (%)",
        # (Optional) CO2 => "CO₂ (kg/h)",
        "Kosten/Stück"
    ]
    # Wenn du CO2 gar nicht willst, einfach rauslassen.
    for col_i, title in enumerate(fert_headers, start=1):
        ws.cell(row=current_row, column=col_i).value = title
        ws.cell(row=current_row, column=col_i).font = Font(bold=True)
        ws.cell(row=current_row, column=col_i).alignment = Alignment(horizontal="center")

    current_row += 1

    # Jetzt die bis zu 8 Schritte eintragen
    for i, step in enumerate(tab3, start=1):
        row_i = current_row + (i - 1)
        ws.cell(row=row_i, column=1).value = step.get("stepName", f"Step {i}")
        ws.cell(row=row_i, column=2).value = step.get("cycTime", 0.0)
        ws.cell(row=row_i, column=3).value = step.get("msRate", 0.0)
        ws.cell(row=row_i, column=4).value = step.get("lohnRate", 0.0)
        ws.cell(row=row_i, column=5).value = step.get("ruestVal", 0.0)
        ws.cell(row=row_i, column=6).value = step.get("tooling", 0.0)
        ws.cell(row=row_i, column=7).value = step.get("fgkPct", 0.0)
        # (Optional) CO2 => ws.cell(row=row_i, column=8).value = step.get("co2Hour", 0.0)
        # (Optional) Kosten => ws.cell(row=row_i, column=9).value = step.get("kosten_100", 0.0)

    current_row += max(len(tab3), 1)  # Falls tab3 leer, mach +1
    current_row += 1

    # ----------------------------------------------------------------
    # 6) Ergebnis (Tab4) – Material- und Fertigungskosten
    # ----------------------------------------------------------------
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
    ws.cell(row=current_row, column=1).value = "Ergebnis (Zusammenfassung)"
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=1).fill = header_fill
    current_row += 1

    # Liste der Zeilen, die direkt aus tab4 befüllt werden
    # Du hast in Tab4 z.B.:
    #   matEinzel, fremd, matAusschuss, matGemein, [summeMaterial?]
    #   mach, lohn, ruest, tooling, fertAusschuss_cost, fgk_cost, [summeFert?]
    #   herstell, sga, profit, total
    ergebnis_fields = [
        ("Material-Einzelkosten/Stück", tab4.get("matEinzel", 0.0)),
        ("Fremdzukauf/Stück",          tab4.get("fremd", 0.0)),
        ("Ausschuss (Material)/Stück", tab4.get("matAusschuss", 0.0)),
        ("Material-Gemeinkosten/Stück", tab4.get("matGemein", 0.0)),
        ("Maschinenkosten/Stück",      tab4.get("mach", 0.0)),   # Falls du es so nennst
        ("Lohnkosten/Stück",           tab4.get("lohn", 0.0)),
        ("Rüstkosten/Stück",           tab4.get("ruest", 0.0)),
        ("Tooling/Stück",              tab4.get("tool_cost", 0.0)),
        ("Ausschuss (Fertigung)/Stück", tab4.get("fertAusschuss_cost", 0.0)),
        ("Fertigungsgemeinkosten/Stück", tab4.get("fgk_cost", 0.0)),
        ("Herstellkosten/Stück",       tab4.get("herstell", 0.0)),
        ("SG&A",                       tab4.get("sga", 0.0)),
        ("Profit",                     tab4.get("profit", 0.0)),
        ("Gesamtkosten/Stück",         tab4.get("total", 0.0)),
        # (Optional) CO₂-Gesamt/Stück => ("CO₂/Stück (kg)", tab4.get("co2_100", 0.0)),
    ]
    for label, val in ergebnis_fields:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # ----------------------------------------------------------------
    # 7) Rahmen um alles
    # ----------------------------------------------------------------
    # Wir wollen von A1..J<current_row-1> einfassen:
    max_row = current_row - 1
    for r in range(1, max_row + 1):
        for c in range(1, 11):
            cell = ws.cell(row=r, column=c)
            cell.border = all_border  # dünner Rahmen an jeder Zelle

    # Außenkante noch etwas dicker (optional):
    # Oben (r=1, c=1..10), Unten (r=max_row, c=1..10),
    # Links (r=1..max_row, c=1), Rechts (r=1..max_row, c=10):
    for c in range(1, 11):
        top_cell = ws.cell(row=1, column=c)
        top_cell.border = Border(
            top=medium,
            left=top_cell.border.left,
            right=top_cell.border.right,
            bottom=top_cell.border.bottom,
        )
        bottom_cell = ws.cell(row=max_row, column=c)
        bottom_cell.border = Border(
            top=bottom_cell.border.top,
            left=bottom_cell.border.left,
            right=bottom_cell.border.right,
            bottom=medium,
        )
    for r in range(1, max_row + 1):
        left_cell = ws.cell(row=r, column=1)
        left_cell.border = Border(
            left=medium,
            top=left_cell.border.top,
            right=left_cell.border.right,
            bottom=left_cell.border.bottom,
        )
        right_cell = ws.cell(row=r, column=10)
        right_cell.border = Border(
            right=medium,
            top=right_cell.border.top,
            left=right_cell.border.left,
            bottom=right_cell.border.bottom,
        )

    # ----------------------------------------------------------------
    # 8) (Optional) 2. Tabellenblatt für Supplier Breakdown
    # ----------------------------------------------------------------
    ws2 = wb.create_sheet("Supplier-Breakdown")
    ws2["A1"].value = "Lieferant kann hier seine eigenen Daten eintragen"
    ws2["A1"].font = Font(bold=True)
    # usw. – hier kannst du ein Skeleton für den Lieferanten anlegen.

    # ----------------------------------------------------------------
    # 9) In Bytes schreiben und zurückgeben
    # ----------------------------------------------------------------
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return output, "ParetoKalk_Gesamtuebersicht.xlsx"
# ---------------------------------------------------------------
# (Hiernach könnten weitere Hilfsfunktionen / Routen folgen)
# ---------------------------------------------------------------
