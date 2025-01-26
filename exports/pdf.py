# FILE: exports/pdf.py

# Minimal Skeleton z.B. mit WeasyPrint
from weasyprint import HTML
import io

def export_baugruppe_pdf(baugruppen_list):
    """
    Erzeugt ein PDF aus baugruppen_list
    """
    html_content = "<h2>Baugruppe</h2><table border='1'>"
    html_content += "<tr><th>Bauteil</th><th>Total</th></tr>"
    for item in baugruppen_list:
        html_content += f"<tr><td>{item.get('name','')}</td><td>{item.get('total',0)}</td></tr>"
    html_content += "</table>"

    pdf_io = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)
    return pdf_io, "baugruppe_export.pdf"