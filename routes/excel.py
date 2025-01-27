import io
import os
import xlsxwriter
from flask import current_app
from datetime import datetime


# ==========================================================
# FILE: routes/excel.py
# ==========================================================
import io
import os
import xlsxwriter
from flask import current_app
from datetime import datetime

# (Mindestens 20 Zeilen Kontext: ggf. weitere Imports / Funktionen)
# ---------------------------------------------------------------
# Beispiel: Vorhandene, ältere export-Funktionen
# ---------------------------------------------------------------

def export_baugruppe_excel(baugruppen_list, filename="baugruppe_export.xlsx"):
    """
    Eine ältere Minimalfunktion für Baugruppen-Exporte...
    (hier nur als Platzhalter, damit wir >20 Zeilen Kontext haben)
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = workbook.add_worksheet("Baugruppe")

    headers = ["Bauteilname","Verfahren","MatEinzel","MatGemein","Fremd","Mach",
               "Lohn","FGK","Herstell","SGA","Profit","Total","CO2_100"]
    for col_idx, h in enumerate(headers):
        ws.write(0, col_idx, h)

    row = 1
    for item in baugruppen_list:
        ws.write(row, 0, item.get("name",""))
        # ...
        row += 1

    workbook.close()
    output.seek(0)
    return output, filename


# ---------------------------------------------------------------
# NEUE FUNKTION: export_baugruppe_eight_steps_excel
# ---------------------------------------------------------------
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


# ---------------------------------------------------------------
# (Hiernach könnten weitere Hilfsfunktionen / Routen folgen)
# ---------------------------------------------------------------
def export_baugruppe_comparison_excel(
    tab1_data,
    tab2_data,
    tab3_steps,  # Liste mit max 8 Dict-Einträgen
    tab4_summary,
    filename="ParetoKalk_Comparison.xlsx"
):
    """
    Erstellt ein Excel mit zwei Worksheets:
      1) FullOverview  => Alle Daten aus Tab1-Tab4 (ähnlich wie "episch")
      2) SupplierCompare => Vergleichstabelle (Unsere Kalkulation vs. Lieferantenangaben + Delta)

    tab1_data   => dict mit Daten aus Tab1 (projectName, partName, annualQty, lotSize, etc.)
    tab2_data   => dict mit Daten aus Tab2 (Materialname, Preise, etc.)
    tab3_steps  => bis zu 8 Fertigungsschritte (Tab3)
    tab4_summary=> dict mit Ergebniswerten (Tab4: matEinzel, lohn, total usw.)

    Gibt ein BytesIO zurück, das man per send_file ausliefern kann.
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ------------------------
    # Formatierungen
    # ------------------------
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
        "border": 1,
        "align": "center"
    })
    bold_format = workbook.add_format({"bold": True})
    normal_border_format = workbook.add_format({"border": 1})
    number_border_format = workbook.add_format({"border": 1, "num_format": "#,##0.00"})
    percent_format = workbook.add_format({"border": 1, "num_format": "0.0%"})
    # Für conditional formatting (Ampel) verwenden wir Worksheet-Methoden später.

    # =========================================
    # 1) Worksheet "FullOverview"
    # =========================================
    ws_full = workbook.add_worksheet("FullOverview")
    ws_full.set_column("A:A", 30)
    ws_full.set_column("B:B", 18)
    ws_full.set_column("C:D", 14)

    # Titel
    ws_full.merge_range("A1:D1", "Pareto-Kalk – Gesamtübersicht", title_format)

    # Projekt-Parameter
    row = 2
    ws_full.write(row, 0, "Projektname", bold_format)
    ws_full.write(row, 1, tab1_data.get("projectName", ""))
    row += 1
    ws_full.write(row, 0, "Bauteilname", bold_format)
    ws_full.write(row, 1, tab1_data.get("partName", ""))
    row += 1
    ws_full.write(row, 0, "Jahresstückzahl", bold_format)
    ws_full.write_number(row, 1, tab1_data.get("annualQty", 0))
    row += 1
    ws_full.write(row, 0, "Losgröße", bold_format)
    ws_full.write_number(row, 1, tab1_data.get("lotSize", 0))
    row += 1
    ws_full.write(row, 0, "Ausschuss (%)", bold_format)
    ws_full.write_number(row, 1, tab1_data.get("scrapPct", 0))
    row += 1
    ws_full.write(row, 0, "SG&A (%)", bold_format)
    ws_full.write_number(row, 1, tab1_data.get("sgaPct", 0))
    row += 1
    ws_full.write(row, 0, "Profit (%)", bold_format)
    ws_full.write_number(row, 1, tab1_data.get("profitPct", 0))
    row += 1

    # Material-Parameter
    row += 1
    ws_full.write(row, 0, "Materialname", bold_format)
    ws_full.write(row, 1, tab2_data.get("matName", ""))
    row += 1
    ws_full.write(row, 0, "Materialpreis (€/kg)", bold_format)
    ws_full.write_number(row, 1, tab2_data.get("matPrice", 0), number_border_format)
    row += 1
    ws_full.write(row, 0, "Material-CO₂ (kg/kg)", bold_format)
    ws_full.write_number(row, 1, tab2_data.get("matCo2", 0), number_border_format)
    row += 1
    ws_full.write(row, 0, "Material-GK (%)", bold_format)
    ws_full.write_number(row, 1, tab2_data.get("matGK", 0), number_border_format)
    row += 1
    ws_full.write(row, 0, "Bauteilgewicht (kg)", bold_format)
    ws_full.write_number(row, 1, tab2_data.get("matWeight", 0), number_border_format)
    row += 1
    ws_full.write(row, 0, "Fremdzukauf (€)", bold_format)
    ws_full.write_number(row, 1, tab2_data.get("fremdValue", 0), number_border_format)
    row += 2

    # Fertigungsschritte (max. 8 Zeilen)
    ws_full.write(row, 0, "Fertigungsschritte", header_format)
    row += 1
    fert_headers = [
        "Arbeitsschritt", "Zyklus (s)", "MS (€/h)", "Lohn (€/h)",
        "Rüst (€/Los)", "Tooling/100", "FGK (%)", "CO₂ (kg/h)",
        "Kosten/100 (€)", "CO₂/100 (kg)"
    ]
    for col_idx, h in enumerate(fert_headers):
        ws_full.write(row, col_idx, h, header_format)
    row += 1

    start_row_fert = row
    for i, step in enumerate(tab3_steps[:8]):
        ws_full.write(row, 0, step.get("stepName", f"Step {i+1}"), normal_border_format)
        ws_full.write_number(row, 1, step.get("zyklus_s", 0), number_border_format)
        ws_full.write_number(row, 2, step.get("ms_eur_h", 0), number_border_format)
        ws_full.write_number(row, 3, step.get("lohn_eur_h", 0), number_border_format)
        ws_full.write_number(row, 4, step.get("ruest_eur_los", 0), number_border_format)
        ws_full.write_number(row, 5, step.get("tooling_eur_100", 0), number_border_format)
        ws_full.write_number(row, 6, step.get("fgk_pct", 0), number_border_format)
        ws_full.write_number(row, 7, step.get("co2_kg_h", 0), number_border_format)
        ws_full.write_number(row, 8, step.get("kosten_100", 0), number_border_format)
        ws_full.write_number(row, 9, step.get("co2_100", 0), number_border_format)
        row += 1

    row += 2

    # Zusammenfassung (Tab 4)
    ws_full.write(row, 0, "Ergebnis (Zusammenfassung)", header_format)
    row += 1
    summary_items = [
        ("Material-Einzelkosten/100", "matEinzel"),
        ("Material-Gemeinkosten/100", "matGemein"),
        ("Fremdzukauf/100", "fremd"),
        ("Maschinenkosten/100", "mach"),
        ("Lohnkosten/100", "lohn"),
        ("Fertigungsgemeinkosten/100", "fgk"),
        ("Herstellkosten/100", "herstell"),
        ("SG&A", "sga"),
        ("Profit", "profit"),
        ("Gesamtkosten/100", "total"),
        ("CO₂/100 (kg)", "co2_100")
    ]
    for label, key in summary_items:
        ws_full.write(row, 0, label, bold_format)
        ws_full.write_number(row, 1, tab4_summary.get(key, 0), number_border_format)
        row += 1

    # Logo (optional) oben rechts
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        ws_full.insert_image("D1", logo_path, {"x_scale": 0.5, "y_scale": 0.5})

    # =========================================
    # 2) Worksheet "SupplierCompare"
    # =========================================
    ws_comp = workbook.add_worksheet("SupplierCompare")
    ws_comp.set_column("A:A", 35)
    ws_comp.set_column("B:D", 16)

    ws_comp.merge_range("A1:D1", "Lieferanten-Vergleich", title_format)
    ws_comp.write("A2", "Hinweis:", bold_format)
    ws_comp.merge_range("B2:D2",
        "In Spalte C kann der Lieferant seine Werte eintragen. Spalte D zeigt das prozentuale Delta an.",
        workbook.add_format({"text_wrap": True}))

    # Kopfzeilen
    ws_comp.write(3, 0, "Kalkulationsposition", header_format)
    ws_comp.write(3, 1, "Unsere Kalkulation", header_format)
    ws_comp.write(3, 2, "Lieferant", header_format)
    ws_comp.write(3, 3, "Delta", header_format)

    # Ab Zeile 4 => summary items
    start_row = 4
    for idx, (label, key) in enumerate(summary_items):
        row_i = start_row + idx
        ws_comp.write(row_i, 0, label, normal_border_format)
        # Unsere Kalkulation
        ws_comp.write_number(
            row_i, 1,
            tab4_summary.get(key, 0),
            number_border_format
        )
        # Lieferant (leer, kann vom Kunden befüllt werden)
        ws_comp.write(row_i, 2, "", number_border_format)
        # Delta => Formel (Spalte D = (C - B)/B ), Index = row_i + 1 (1-based in Excel)
        ws_comp.write_formula(
            row_i, 3,
            f"=(C{row_i+1}-B{row_i+1})/B{row_i+1}",
            percent_format
        )

    # Conditional Formatting für Delta-Spalte (Spalte D), 0 => Spalte A, D => 3
    comp_range = f"D{start_row+1}:D{start_row+len(summary_items)}"
    ws_comp.conditional_format(
        comp_range,
        {
            "type": "3_color_scale",
            "min_color": "#63BE7B",  # Grün
            "mid_color": "#FFEB84",  # Gelb
            "max_color": "#F8696B"   # Rot
        }
    )

    # Footer
    end_row = start_row + len(summary_items) + 2
    ws_comp.write(end_row, 0, "Legende:", bold_format)
    ws_comp.merge_range(end_row, 1, end_row, 3,
        "Grün = Unter 0% Abweichung (günstiger), Gelb = leichte Abweichung, Rot = deutliche Abweichung",
        workbook.add_format({"text_wrap": True, "italic": True})
    )

    # workbook schließen und zurückgeben
    workbook.close()
    output.seek(0)
    return output, filename


