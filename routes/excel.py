import io
import os
import xlsxwriter
from flask import current_app
from datetime import datetime


def export_baugruppe_eight_steps_excel(
        tab1_data,  # dict (Projekt: scrapPct, sgaPct, profitPct, ...)
        tab2_data,  # dict (Material: matPrice, matWeight, fremdValue, ...)
        tab3_steps,  # list of dict (bis zu 8 Schritte)
        tab4_summary,  # dict (Gesamt-Summary)
        filename="ParetoKalk_OnePager_8Steps.xlsx"
):
    """
    Erstellt ein Worksheet mit (mind.) 18 Spalten:
      - Spalte A: Zeilen-Beschriftung (Material, Fremd, Step-Namen, Rüst etc.)
      - Spalten B..Y: Jeweils 8 Doppelsäulen (Kosten/100 + CO₂/100) für Step 1..8
      - Dazu 2 Summenspalten (Spalte R und S oder weiter hinten),
        um die Gesamt-Kosten und -CO₂ anzuzeigen.

    Layout grob (Zeile 1..2 als Beispiel):

    Row1:
      A1 = Titel "Pareto Kalk – 8-Schritt-Übersicht"
      B1..Y1 = zusammengeführter Header / Logo / ...

    Row2 (nur Überschriften):
      A2 = "Kostenblöcke"
      B2 = "Step1-Cost/100"
      C2 = "Step1-CO₂/100"
      D2 = "Step2-Cost/100"
      E2 = "Step2-CO₂/100"
      ...
      P2 = "Step8-Cost/100"
      Q2 = "Step8-CO₂/100"
      R2 = "Gesamt-Cost"
      S2 = "Gesamt-CO₂"

    Dann Zeilen 3..N für "Material", "Fremd", "Tooling", "Rüst", "Herstellkosten", "SG&A" etc.
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ------------------------------------------------
    # 1) Format-Definitionen
    # ------------------------------------------------
    title_format = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter"
    })
    header_format = workbook.add_format({
        "bg_color": "#1F4E78",
        "font_color": "#FFFFFF",
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "border": 1
    })
    label_format = workbook.add_format({
        "bold": True,
        "border": 1,
        "valign": "vcenter"
    })
    normal_border = workbook.add_format({"border": 1})
    number_format = workbook.add_format({"border": 1, "num_format": "#,##0.00"})

    # ------------------------------------------------
    # 2) Worksheet anlegen + Spaltenbreiten
    # ------------------------------------------------
    ws = workbook.add_worksheet("8StepsOverview")
    # Wir brauchen mind. 18 Spalten (A..R oder A..S).
    # In diesem Beispiel: A..S
    # B..Q => 8 Doppelsäulen + Summenspalten R und S
    # Setze Breiten:
    ws.set_column("A:A", 28)  # Beschriftungen
    for col in range(1, 19):
        ws.set_column(col, col, 12)  # Spalten B..S = 12er Breite

    # ------------------------------------------------
    # 3) Titelzeile (Row=0)
    # ------------------------------------------------
    ws.merge_range("A1:S1", "Pareto-Kalk – 8-Schritt-Übersicht", title_format)
    ws.set_row(0, 40)  # Zeile 1 höher

    # Optional: Logo oben links
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        # Logo in A1 (mit x_offset,y_offset anpassen):
        ws.insert_image("A1", logo_path, {"x_scale": 0.6, "y_scale": 0.6, "x_offset": 0, "y_offset": 0})

    # ------------------------------------------------
    # 4) Spaltenüberschriften in Row=1
    # ------------------------------------------------
    ws.write(1, 0, "Kosten-Blöcke", header_format)

    # Je 2 Spalten pro Step (cost, co2)
    step_headers = []
    for i in range(8):
        step_headers.append((f"Step{i + 1} Cost/100", f"Step{i + 1} CO₂/100"))

    col_start = 1
    for i, (costLabel, co2Label) in enumerate(step_headers):
        ws.write(1, col_start, costLabel, header_format)
        ws.write(1, col_start + 1, co2Label, header_format)
        col_start += 2

    # Summenspalten
    ws.write(1, col_start, "Σ-Cost", header_format)  # col_start -> R
    ws.write(1, col_start + 1, "Σ-CO₂", header_format)  # col_start+1 -> S

    # ------------------------------------------------
    # 5) Inhaltliche Zeilen definieren
    # ------------------------------------------------
    # Ab Zeile 2 (Index=2) beginnen wir mit Material, Fremd, ...
    row_idx = 2

    # Hilfsfunktion, um pro Zeile: label, 8 cost-Werte, 8 co2-Werte, sum cost, sum co2 zu schreiben
    def write_cost_line(label, row, cost_values, co2_values):
        """
        label: Zeilenbeschriftung
        cost_values: list[float] oder None => bis zu 8
        co2_values:  list[float] oder None => bis zu 8
        Schreibt in Spalten B..Q, Summen in R,S
        """
        ws.write(row, 0, label, label_format)
        # 8 Steps
        c_col = 1
        total_cost = 0.0
        total_co2 = 0.0
        for i in range(8):
            c_val = cost_values[i] if i < len(cost_values) else 0
            co2_val = co2_values[i] if i < len(co2_values) else 0
            ws.write_number(row, c_col, c_val, number_format)  # cost
            ws.write_number(row, c_col + 1, co2_val, number_format)  # co2
            total_cost += c_val
            total_co2 += co2_val
            c_col += 2

        # Summen in Spalte R,S
        ws.write_number(row, c_col, total_cost, number_format)
        ws.write_number(row, c_col + 1, total_co2, number_format)

    # ------------------------------------------------------------------
    # 5.1) Material-Zeilen (Bsp: Material, Fremd, MGK, Scrap, Summen)
    # ------------------------------------------------------------------
    # Du kannst aus tab2_data oder tab4_summary ableiten.
    # Hier als DEMO:
    material_cost = tab4_summary.get("matEinzel", 0)  # z.B. reiner Materialeinzel-Anteil
    mat_gemein = tab4_summary.get("matGemein", 0)  # Material-Gemeinkosten
    mat_fremd = tab4_summary.get("fremd", 0)
    # Zusammen als 1-D array => "in Step 1..8" könnte man es verteilen.
    # Wenn du nur *einen* Wert hast, und alles in Summe steckst, nimmst du "cost_values = [0,0,..., deinWert]" oder du verteilst den Wert uniform.
    # Hier vereinfachend: alle in Step1 => (material_cost, 0,0, ...). Oder komplett in Summenspalte? Du entscheidest.

    #  – Zeile Material-Einzel
    write_cost_line("Material-Einzel", row_idx, [material_cost, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    row_idx += 1

    #  – Zeile Fremdzukauf
    write_cost_line("Fremdzukauf", row_idx, [mat_fremd, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    row_idx += 1

    #  – Zeile Material-Gemein
    write_cost_line("Material-GK", row_idx, [mat_gemein, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    row_idx += 1

    #  – Summen-Zeile Material
    mat_sum = material_cost + mat_gemein + mat_fremd
    write_cost_line("Material-Gesamt", row_idx, [mat_sum, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    row_idx += 1

    # ------------------------------------------------------------------
    # 5.2) Acht Fertigungsschritte
    # ------------------------------------------------------------------
    # In tab3_steps liegen pro Step i.d.R. Zyklus, msRate, lohnRate, ...
    # Falls du Dir *pro Step* schon "cost/100" + "co2/100" aus tab3 holst:
    #   step["kosten_100"], step["co2_100"]
    # Dann kannst du es hier 1:1 in die Spalten packen:

    # Im Normalfall: cost_values[i] = step i Kosten, co2_values[i] = step i CO₂
    fert_cost_arr = [0] * 8
    fert_co2_arr = [0] * 8

    for i in range(min(len(tab3_steps), 8)):
        fert_cost_arr[i] = tab3_steps[i].get("kosten_100", 0)
        fert_co2_arr[i] = tab3_steps[i].get("co2_100", 0)

    write_cost_line("Fertigung (8 Steps)", row_idx, fert_cost_arr, fert_co2_arr)
    row_idx += 1

    # ------------------------------------------------------------------
    # 5.3) Rüst & Tooling als Extra-Zeilen
    # ------------------------------------------------------------------
    ruest_100 = tab4_summary.get("ruest", 0)
    tooling_100 = tab4_summary.get("tooling", 0)
    # Ggf. verteilen auf Steps oder alles in Summenspalte => hier Example:
    write_cost_line("Rüstkosten", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    # Du könntest den Wert z.B. in den Summenspalten (Spalte R = total cost) packen =>
    ws.write_number(row_idx, 17, ruest_100, number_format)  # Spalte R = index 17
    row_idx += 1

    write_cost_line("Tooling", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    ws.write_number(row_idx, 17, tooling_100, number_format)
    row_idx += 1

    # ------------------------------------------------------------------
    # 5.4) Gesamt-Herstellkosten
    # ------------------------------------------------------------------
    herstell = tab4_summary.get("herstell", 0)
    write_cost_line("Herstellkosten", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    ws.write_number(row_idx, 17, herstell, number_format)
    row_idx += 1

    # ------------------------------------------------------------------
    # 5.5) SG&A und Profit
    # ------------------------------------------------------------------
    sga_val = tab4_summary.get("sga", 0)
    profit_val = tab4_summary.get("profit", 0)

    write_cost_line("SG&A", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    ws.write_number(row_idx, 17, sga_val, number_format)
    row_idx += 1

    write_cost_line("Profit", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    ws.write_number(row_idx, 17, profit_val, number_format)
    row_idx += 1

    # ------------------------------------------------------------------
    # 5.6) Gesamtkosten/100 (Endpreis)
    # ------------------------------------------------------------------
    total_val = tab4_summary.get("total", 0)
    write_cost_line("Finaler Preis/100", row_idx, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    ws.write_number(row_idx, 17, total_val, number_format)
    row_idx += 1

    # ------------------------------------------------
    # 6) Footer / Erstell-Datum
    # ------------------------------------------------
    footer_row = row_idx + 1
    ws.write(footer_row, 0, "Export-Datum:")
    ws.write(footer_row, 1, datetime.now().strftime("%d.%m.%Y %H:%M"))

    # Workbook abschließen
    workbook.close()
    output.seek(0)
    return output, filename


def export_baugruppe_eight_steps_excel(
    tab1_data,    # dict (z.B. scrapPct, sgaPct, profitPct, ...)
    tab2_data,    # dict (z.B. matPrice, matWeight, fremdValue, ...)
    tab3_steps,   # list of dict (bis zu 8 Schritte => {kosten_100, co2_100, ...})
    tab4_summary, # dict (z.B. matEinzel, matGemein, fremd, herstell, sga, profit, total, etc.)
    filename="ParetoKalk_OnePager_8Steps.xlsx"
):
    """
    Erstellt ein Worksheet im 'Breit-Layout':
      - Spalte A: Zeilenbeschriftungen (Material, Fremd, Rüst, Steps, Summen, usw.)
      - Spalten B..Q (16 Spalten = 8x2) => pro Step: [Cost, CO2]
      - Spalten R,S => Summen-Spalten für Gesamtkosten bzw. Gesamt-CO2

    Keine Excelformeln: Wir tragen direkt fertige Werte ein,
    so wie es dein JS/Backend berechnet (tab3_steps[i].kosten_100 etc.).
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ------------------------------------------------
    # 1) Format-Definitionen
    # ------------------------------------------------
    title_format = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter"
    })
    header_format = workbook.add_format({
        "bg_color": "#1F4E78",
        "font_color": "#FFFFFF",
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "border": 1
    })
    label_format = workbook.add_format({
        "bold": True,
        "border": 1,
        "valign": "vcenter"
    })
    normal_border = workbook.add_format({"border": 1})
    number_format = workbook.add_format({"border": 1, "num_format": "#,##0.00"})

    # ------------------------------------------------
    # 2) Worksheet anlegen + Spaltenbreiten
    # ------------------------------------------------
    ws = workbook.add_worksheet("8StepsOverview")
    # Wir brauchen mind. Spalten A..S => 19 Spalten (Index 0..18)
    #   A = Index 0
    #   B..Q = Index 1..16 (8 Doppelsäulen)
    #   R..S = Index 17..18
    # Stelle Spaltenbreiten ein
    ws.set_column("A:A", 30)  # Beschriftungen
    for col in range(1, 19):
        ws.set_column(col, col, 12)

    # ------------------------------------------------
    # 3) Titelzeile (Row=0)
    # ------------------------------------------------
    ws.merge_range("A1:S1", "Pareto-Kalk – 8-Schritt OnePager", title_format)
    ws.set_row(0, 40)  # Zeile 1 höher machen

    # Optional: Logo (falls vorhanden)
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        ws.insert_image("A1", logo_path, {"x_scale": 0.5, "y_scale": 0.5, "x_offset": 0, "y_offset": 0})

    # ------------------------------------------------
    # 4) Spaltenüberschriften in Row=1
    # ------------------------------------------------
    ws.write(1, 0, "Kostenblöcke", header_format)
    col_pos = 1
    for step_idx in range(1, 9):
        ws.write(1, col_pos,   f"Step{step_idx} Cost/100", header_format)
        ws.write(1, col_pos+1, f"Step{step_idx} CO₂/100",  header_format)
        col_pos += 2
    # Summen-Spalten
    ws.write(1, col_pos,   "Gesamt-Cost", header_format)
    ws.write(1, col_pos+1, "Gesamt-CO₂",  header_format)

    # ------------------------------------------------
    # Hilfsfunktion zum Befüllen einer Zeile
    # ------------------------------------------------
    def write_cost_line(label, row_idx, cost_vals, co2_vals):
        """
        label: Zeilen-Label in Spalte A
        cost_vals, co2_vals: Listen mit max. 8 Einträgen
        => Spalten B..Q => Summen in R..S
        """
        ws.write(row_idx, 0, label, label_format)
        total_cost = 0.0
        total_co2 = 0.0
        col_pos = 1
        for i in range(8):
            c_val = cost_vals[i] if i < len(cost_vals) else 0
            co2_val = co2_vals[i] if i < len(co2_vals) else 0
            ws.write_number(row_idx, col_pos,   c_val, number_format)
            ws.write_number(row_idx, col_pos+1, co2_val, number_format)
            total_cost += c_val
            total_co2 += co2_val
            col_pos += 2
        # Summen in Spalte R..S => col_pos=17,18
        ws.write_number(row_idx, col_pos,   total_cost, number_format)
        ws.write_number(row_idx, col_pos+1, total_co2,  number_format)

    # ------------------------------------------------
    # 5) Zeilen aufbauen: Material, Fremd, ...
    # ------------------------------------------------
    row_idx = 2

    # (a) Material-Einzel
    mat_einzel = tab4_summary.get("matEinzel", 0.0)
    # Möchtest du es nur in Step1 & 0 in anderen Steps => cost_vals=[mat_einzel,0,0,...]
    write_cost_line("Material-Einzel", row_idx, [mat_einzel,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    row_idx += 1

    # (b) Fremdzukauf
    fremd_val = tab4_summary.get("fremd", 0.0)
    write_cost_line("Fremdzukauf", row_idx, [fremd_val,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    row_idx += 1

    # (c) Material-Gemeinkosten
    mat_gemein = tab4_summary.get("matGemein", 0.0)
    write_cost_line("Material-GK", row_idx, [mat_gemein,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    row_idx += 1

    # (d) Material-Gesamt
    mat_sum = mat_einzel + fremd_val + mat_gemein
    write_cost_line("Material-Gesamt", row_idx, [mat_sum,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    row_idx += 1

    # (e) Fertigung (8 Steps)
    # Falls du pro Step bereits "kosten_100"/"co2_100" hast:
    fert_cost_arr = [0]*8
    fert_co2_arr  = [0]*8
    for i in range(min(len(tab3_steps), 8)):
        fert_cost_arr[i] = tab3_steps[i].get("kosten_100", 0)
        fert_co2_arr[i]  = tab3_steps[i].get("co2_100", 0)
    write_cost_line("Fertigung (8 Steps)", row_idx, fert_cost_arr, fert_co2_arr)
    row_idx += 1

    # (f) Rüst & Tooling
    ruest_val = tab4_summary.get("ruest", 0)
    write_cost_line("Rüstkosten", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, ruest_val, number_format)  # Summenspalte R
    row_idx += 1

    tooling_val = tab4_summary.get("tooling", 0)
    write_cost_line("Tooling", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, tooling_val, number_format)
    row_idx += 1

    # (g) Herstellkosten
    herstell_val = tab4_summary.get("herstell", 0)
    write_cost_line("Herstellkosten", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, herstell_val, number_format)
    row_idx += 1

    # (h) SG&A, Profit
    sga_val = tab4_summary.get("sga", 0)
    write_cost_line("SG&A", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, sga_val, number_format)
    row_idx += 1

    profit_val = tab4_summary.get("profit", 0)
    write_cost_line("Profit", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, profit_val, number_format)
    row_idx += 1

    # (i) Gesamtkosten
    total_val = tab4_summary.get("total", 0)
    write_cost_line("Finaler Preis/100", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 17, total_val, number_format)
    row_idx += 1

    # (j) CO₂-Gesamt
    co2_val = tab4_summary.get("co2_100", 0)
    write_cost_line("CO₂ Total/100 (kg)", row_idx, [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0])
    ws.write_number(row_idx, 18, co2_val, number_format)
    row_idx += 1

    # ------------------------------------------------
    # 6) Footer / Erstell-Datum
    # ------------------------------------------------
    footer_row = row_idx + 1
    ws.write(footer_row, 0, "Export-Datum:")
    ws.write(footer_row, 1, datetime.now().strftime("%d.%m.%Y %H:%M"))

    # Workbook abschließen
    workbook.close()
    output.seek(0)
    return output, filename
