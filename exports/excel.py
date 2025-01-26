# ==================================================
# FILE: exports/excel.py
# ==================================================
import xlsxwriter
import io
import os
from datetime import datetime
from flask import current_app

# ------------------------------
# (Vorher ggf. weitere Imports)
# ------------------------------

def export_baugruppe_excel(baugruppen_list, filename="baugruppe_export.xlsx"):
    """
    Deine ursprüngliche Funktion, um 'Baugruppen-Liste' in ein schnelles, einfaches Excel zu schreiben.
    baugruppen_list => Liste von Dicts, z.B.:
      [ {name:"TeilA", matEinzel:10, matGemein:5, ...}, {...} ]
    Gibt ein BytesIO zurück, das man als Download schicken kann.
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = workbook.add_worksheet("Baugruppe")

    # Kopfzeile
    headers = ["Bauteilname","Verfahren","MatEinzel","MatGemein","Fremd","Mach",
               "Lohn","FGK","Herstell","SGA","Profit","Total","CO2_100"]
    for col_idx, h in enumerate(headers):
        ws.write(0, col_idx, h)

    # Daten
    row = 1
    for item in baugruppen_list:
        ws.write(row, 0, item.get("name",""))
        ws.write(row, 1, item.get("verfahren",""))
        ws.write(row, 2, round(item.get("matEinzel",0), 2))
        ws.write(row, 3, round(item.get("matGemein",0), 2))
        ws.write(row, 4, round(item.get("fremd",0), 2))
        ws.write(row, 5, round(item.get("mach",0), 2))
        ws.write(row, 6, round(item.get("lohn",0), 2))
        ws.write(row, 7, round(item.get("fgk",0), 2))
        ws.write(row, 8, round(item.get("herstell",0), 2))
        ws.write(row, 9, round(item.get("sga",0), 2))
        ws.write(row, 10, round(item.get("profit",0), 2))
        ws.write(row, 11, round(item.get("total",0), 2))
        ws.write(row, 12, round(item.get("co2_100",0), 2))
        row += 1

    workbook.close()
    output.seek(0)
    return output, filename


# --------------------------------------------------
# NEUE FUNKTION: export_baugruppe_comparison_excel
# --------------------------------------------------

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

# --------------------------------------------------
# (Nachfolgend könnten weitere Hilfsfunktionen sein)
# --------------------------------------------------
