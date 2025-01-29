import io
from flask import Blueprint, request, jsonify, send_file
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter
exports_bp = Blueprint("exports_bp", __name__)

# ---------------------------------------------------------------
# NEUE FUNKTION: export_baugruppe_eight_steps_excel
# ---------------------------------------------------------------
def export_baugruppe_eight_steps_excel(tab1, tab2, tab3, tab4):
    """
    Erzeugt ein Workbook mit:
      * Sheet1: "Pareto-Kalk – Gesamtübersicht" (Projektdaten + Material + 8 Schritte + Ergebnis)
      * Sheet2: "Lieferanten-Vergleich" (Formeln, bedingte Formatierung)
    """
    wb = Workbook()

    # =========== 1) SHEET1: Pareto-Kalk – Gesamtübersicht ==========
    ws = wb.active
    ws.title = "Pareto-Kalk – Gesamtübersicht"

    # a) Spaltenbreiten
    widths = [20, 17, 17, 17, 17, 17, 17, 17, 17]  # 9 Spalten (A..I)
    for i, w in enumerate(widths, start=1):
        col_letter = get_column_letter(i)
        ws.column_dimensions[col_letter].width = w

    # b) Formatierung: Ränder, Farben
    thin = Side(border_style="thin", color="000000")
    medium = Side(border_style="medium", color="000000")
    all_thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Dunkelblaue Überschrift (z.B. Hex #1F4E78) => oder #003366
    dark_blue_fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
    white_font = Font(color="FFFFFF", bold=True)

    # c) Überschrift in Zeile 1: gemergt über A1..I1
    ws.merge_cells("A1:I1")
    cell_title = ws["A1"]
    cell_title.value = "Pareto-Kalk – Gesamtübersicht"
    cell_title.alignment = Alignment(horizontal="center", vertical="center")
    cell_title.font = white_font
    cell_title.fill = dark_blue_fill
    ws.row_dimensions[1].height = 25

    # (Falls du das Logo einbinden willst)
    # try:
    #     img = Image("static/img/jpc.jpeg")
    #     img.width = 150
    #     img.height = 70
    #     # z.B. in Zelle I1 "platzieren" => Kann je nach Excel-Version variieren
    #     ws.add_image(img, "I1")
    # except:
    #     pass

    # ------------------------------------------------
    # 2) Projekt-Daten (tab1) – ab Zeile 3
    # ------------------------------------------------
    current_row = 3
    project_data = [
        ("Projektname", tab1.get("projectName", "")),
        ("Bauteilname", tab1.get("partName", "")),
        ("Jahresstückzahl", tab1.get("annualQty", 0)),
        ("Losgröße", tab1.get("lotSize", 0)),
        ("Ausschuss (%)", tab1.get("scrapPct", 0)),
        ("SG&A (%)", tab1.get("sgaPct", 0)),
        ("Profit (%)", tab1.get("profitPct", 0)),
    ]
    for label, val in project_data:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # ------------------------------------------------
    # 3) Material-Block (tab2) mit Überschrift
    # ------------------------------------------------
    current_row += 1  # Leerzeile
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=2)
    mat_header_cell = ws.cell(row=current_row, column=1)
    mat_header_cell.value = "Materialdaten"
    mat_header_cell.font = white_font
    mat_header_cell.fill = dark_blue_fill
    mat_header_cell.alignment = Alignment(horizontal="center")
    current_row += 1

    material_data = [
        ("Materialname", tab2.get("matName", "Aluminium")),
        ("Materialpreis (€/kg)", tab2.get("matPrice", 0.0)),
        ("Material-CO₂ (kg/kg)", tab2.get("matCo2", 0.0)),  # falls vorhanden
        ("Material-GK (%)",      tab2.get("matGK", 0.0)),
        ("Bauteilgewicht (kg)",  tab2.get("matWeight", 0.0)),
        ("Fremdzukauf (€/St.)",  tab2.get("fremdValue", 0.0)),
    ]
    for label, val in material_data:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # ------------------------------------------------
    # 4) Fertigungsschritte (tab3)
    # ------------------------------------------------
    current_row += 1
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=9)
    fert_header = ws.cell(row=current_row, column=1)
    fert_header.value = "Fertigungsschritte"
    fert_header.font = white_font
    fert_header.fill = dark_blue_fill
    fert_header.alignment = Alignment(horizontal="center")
    current_row += 1

    # Spaltenköpfe (8..9 Felder?)
    fert_heads = [
        "Arbeitsschritt",
        "Zyklus (s)",
        "MS (€/h)",
        "Lohn (€/h)",
        "Rüst (€/Los)",
        "Tooling/St. (€)",
        "FGK (%)",
        "CO₂ (kg/h)",
        "Kosten/St. (€)"  # Falls du das aus tab3 holst
        # Oder "CO₂/St. (kg)", wenn du es in tab3 Steps berechnest
    ]
    for col_i, h in enumerate(fert_heads, start=1):
        c = ws.cell(row=current_row, column=col_i)
        c.value = h
        c.font = white_font
        c.fill = dark_blue_fill
        c.alignment = Alignment(horizontal="center")
    current_row += 1

    # tab3-Daten befüllen
    for i, step in enumerate(tab3, start=1):
        row_i = current_row + i - 1
        ws.cell(row=row_i, column=1).value = step.get("stepName", f"Step {i}")
        ws.cell(row=row_i, column=2).value = step.get("cycTime", 0)
        ws.cell(row=row_i, column=3).value = step.get("msRate", 0)
        ws.cell(row=row_i, column=4).value = step.get("lohnRate", 0)
        ws.cell(row=row_i, column=5).value = step.get("ruestVal", 0)
        ws.cell(row=row_i, column=6).value = step.get("tooling", 0)
        ws.cell(row=row_i, column=7).value = step.get("fgkPct", 0)
        ws.cell(row=row_i, column=8).value = step.get("co2Hour", 0)
        # Falls du "kosten_100" in tab3 hast und daraus "Kosten/St." ableitest:
        ws.cell(row=row_i, column=9).value = step.get("kosten_100", 0)

    current_row += max(len(tab3), 1) + 1

    # ------------------------------------------------
    # 5) Ergebnis (Zusammenfassung) (tab4)
    # ------------------------------------------------
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=9)
    erg_header = ws.cell(row=current_row, column=1)
    erg_header.value = "Ergebnis (Zusammenfassung)"
    erg_header.font = white_font
    erg_header.fill = dark_blue_fill
    erg_header.alignment = Alignment(horizontal="center")
    current_row += 1

    # Hier packen wir z.B. "Summe Material" und "Summe Fertigung" auch rein:
    # => Der User sagt, er will "Summe Material", "Summe Fertigung" + "Herstellkosten", "SG&A", "Profit", "Gesamtkosten"
    # Beachte: Deine Felder in tab4 heißen evtl. matEinzel, matAusschuss, matGemein, fertAusschuss_cost, herstell, total, usw.
    ergebnis_data = [
        ("Material-Einzelkosten/Stück", tab4.get("matEinzel", 0.0)),
        ("Fremdzukauf/Stück",           tab4.get("fremd", 0.0)),
        ("Ausschuss (Material)/Stück",  tab4.get("matAusschuss", 0.0)),
        ("Material-Gemeinkosten/Stück", tab4.get("matGemein", 0.0)),
        ("Summe Material/Stück",        tab4.get("summe_mat", 0.0)),  # z.B. "summe_mat"
        ("Maschinenkosten/Stück",       tab4.get("mach", 0.0)),       # falls du sie so nennst
        ("Lohnkosten/Stück",            tab4.get("lohn", 0.0)),
        ("Rüstkosten/Stück",            tab4.get("ruest", 0.0)),
        ("Tooling/Stück",               tab4.get("tool_cost", 0.0)),
        ("Ausschuss (Fertigung)/Stück", tab4.get("fertAusschuss_cost", 0.0)),
        ("Fertigungsgemeinkosten/Stück", tab4.get("fgk_cost", 0.0)),
        ("Summe Fertigung/Stück",        tab4.get("summe_fert_cost", 0.0)),
        ("Herstellkosten/Stück",         tab4.get("herstell", 0.0)),
        ("SG&A",                         tab4.get("sga", 0.0)),
        ("Profit",                       tab4.get("profit", 0.0)),
        ("Gesamtkosten/Stück",           tab4.get("total", 0.0)),
        # Optional: ("CO₂/Stück (kg)",   tab4.get("co2_100", 0.0)),
    ]
    for label, val in ergebnis_data:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = val
        current_row += 1

    # ------------------------------------------------
    # 6) Rahmen um alles (A1..I<current_row-1>)
    # ------------------------------------------------
    max_row = current_row - 1
    for r in range(1, max_row + 1):
        for c in range(1, 10):  # 1..9
            cell = ws.cell(row=r, column=c)
            cell.border = all_thin_border

    # Außenkante dicker
    for c in range(1, 10):
        # oben
        top_cell = ws.cell(row=1, column=c)
        top_cell.border = Border(
            top=medium,
            left=top_cell.border.left,
            right=top_cell.border.right,
            bottom=top_cell.border.bottom
        )
        # unten
        bottom_cell = ws.cell(row=max_row, column=c)
        bottom_cell.border = Border(
            top=bottom_cell.border.top,
            left=bottom_cell.border.left,
            right=bottom_cell.border.right,
            bottom=medium
        )

    for r in range(1, max_row + 1):
        # links
        left_cell = ws.cell(row=r, column=1)
        left_cell.border = Border(
            left=medium,
            top=left_cell.border.top,
            right=left_cell.border.right,
            bottom=left_cell.border.bottom
        )
        # rechts
        right_cell = ws.cell(row=r, column=9)
        right_cell.border = Border(
            right=medium,
            top=right_cell.border.top,
            left=right_cell.border.left,
            bottom=right_cell.border.bottom
        )

    # =========== 2) SHEET2: Lieferanten-Vergleich ==========
    ws2 = wb.create_sheet("Lieferanten-Vergleich")

    # a) Spaltenbreiten
    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["B"].width = 18
    ws2.column_dimensions["C"].width = 18
    ws2.column_dimensions["D"].width = 16

    # Überschrift in A1..D1
    ws2.merge_cells("A1:D1")
    ws2["A1"].value = "Lieferanten-Vergleich"
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws2["A1"].font = Font(bold=True, size=12)
    ws2.row_dimensions[1].height = 20

    # b) Hinweis in A2..D2
    ws2["A2"].value = "Hinweis:"
    ws2["B2"].value = "In Spalte C kann der Lieferant seine Werte eintragen. Spalte D zeigt das prozentuale Delta an."
    ws2.merge_cells("B2:D2")

    # c) Kopfzeile ab Zeile 4
    ws2["A4"].value = "Kalkulationsposition"
    ws2["B4"].value = "Unsere Kalkulation"
    ws2["C4"].value = "Lieferant"
    ws2["D4"].value = "Delta"
    for col in range(1, 5):
        cell = ws2.cell(row=4, column=col)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # d) Datenzeilen – Beispiel
    # Hier legen wir einfach 11 Positionen an,
    # so wie im Screenshot (Material-Einzelkosten/100 usw.)
    rows_liefer = [
        "Material-Einzelkosten/100",
        "Material-Gemeinkosten/100",
        "Fremdzukauf/100",
        "Maschinenkosten/100",
        "Lohnkosten/100",
        "Fertigungsgemeinkosten/100",
        "Herstellkosten/100",
        "SG&A",
        "Profit",
        "Gesamtkosten/100",
        "CO₂/100 (kg)",
    ]
    start_row_ = 5
    # Beispielwerte => entnimm sie dem tab4, falls du dort noch "pro 100" Zwischenergebnisse hast,
    # oder rechne dir was aus. Hier tun wir nur Dummy-Values rein:
    default_values_ours = [
        42.00, 2.10, 0.00, 63.53, 31.76, 49.26, 416.20, 41.62, 20.81, 478.62, 0.00
    ]

    for i, label_ in enumerate(rows_liefer):
        r_ = start_row_ + i
        ws2.cell(row=r_, column=1).value = label_
        ws2.cell(row=r_, column=2).value = default_values_ours[i]
        # Spalte C = Lieferantenwert -> bleibt leer, kann vom Lieferanten befüllt werden
        # Spalte D = Delta => Formel: =WENN(C5=0;"#DIV/0!";(C5-B5)/B5)
        formula_ = f'=IF(C{r_}=0,"#DIV/0!",(C{r_}-B{r_})/B{r_})'
        ws2.cell(row=r_, column=4).value = formula_

    # e) Legende ab Zeile (start_row_ + len(rows_liefer) + 2)
    legend_row = start_row_ + len(rows_liefer) + 2
    ws2.cell(row=legend_row, column=1).value = "Legende:"
    ws2.cell(row=legend_row, column=2).value = "Grün = Unter 0% Abweichung (günstiger), Gelb = leichte Abweichung, Rot = deutliche Abweichung"

    # f) Bedingte Formatierung (Spalte D):
    #  - Falls Delta < 0  => Grün
    #  - Falls Delta >= 0 und <= 0.1 => Gelb
    #  - Falls Delta > 0.1  => Rot
    # Wir können das z.B. mit 3 Condition-Rules regeln:
    # 1) Delta < 0 => GREEN
    green_rule = CellIsRule(operator='lessThan', formula=['0'], fill=PatternFill(bgColor="00C0F0A0", fill_type="solid"))
    # 2) Delta <= 0.1 => YELLOW  (wir brauchen "Between(0,0.1)") => also ">=0" AND "<=0.1"
    #   Zwei Rules: >=0 + <=0.1 => trick. Besser: 0 <= Delta <= 0.1
    #   => "between"
    yellow_rule = CellIsRule(operator='between', formula=['0','0.1'], fill=PatternFill(bgColor="00FFFF00", fill_type="solid"))
    # 3) Delta > 0.1 => RED
    red_rule = CellIsRule(operator='greaterThan', formula=['0.1'], fill=PatternFill(bgColor="00FF6666", fill_type="solid"))

    # Bereich D5..D15 (11 Zeilen)
    min_r = 5
    max_r = start_row_ + len(rows_liefer) - 1
    rng = f"D{min_r}:D{max_r}"
    ws2.conditional_formatting.add(rng, green_rule)
    ws2.conditional_formatting.add(rng, yellow_rule)
    ws2.conditional_formatting.add(rng, red_rule)

    # g) Tabellenrahmen (A4..D<max_r>)
    for rr in range(4, max_r + 1):
        for cc in range(1, 5):
            cell_ = ws2.cell(row=rr, column=cc)
            cell_.border = all_thin_border

    # Noch optional dicken Außenrahmen
    for cc in range(1, 5):
        top_cell = ws2.cell(row=4, column=cc)
        top_cell.border = Border(
            top=medium,
            left=top_cell.border.left,
            right=top_cell.border.right,
            bottom=top_cell.border.bottom
        )
        bottom_cell = ws2.cell(row=max_r, column=cc)
        bottom_cell.border = Border(
            top=bottom_cell.border.top,
            left=bottom_cell.border.left,
            right=bottom_cell.border.right,
            bottom=medium
        )
    for rr in range(4, max_r + 1):
        left_cell = ws2.cell(row=rr, column=1)
        left_cell.border = Border(
            left=medium,
            top=left_cell.border.top,
            right=left_cell.border.right,
            bottom=left_cell.border.bottom
        )
        right_cell = ws2.cell(row=rr, column=4)
        right_cell.border = Border(
            right=medium,
            top=right_cell.border.top,
            left=right_cell.border.left,
            bottom=right_cell.border.bottom
        )

    # =========== 3) Workbook speichern ==========
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, "ParetoKalk_Gesamtuebersicht.xlsx"