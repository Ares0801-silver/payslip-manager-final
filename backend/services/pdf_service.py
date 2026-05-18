# backend/services/pdf_service.py
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

BLEU     = colors.HexColor("#0F1F3D")
CYAN     = colors.HexColor("#00A8E8")
GRIS     = colors.HexColor("#8FA3B1")
BLANC    = colors.white


def generer_fiche_pdf(fiche, employe) -> str:
    """Génère le PDF d'une fiche de paie et retourne son chemin."""
    filename = f"fiche_{employe.id}_{fiche.mois}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle("titre", fontSize=20, textColor=BLEU,
                                 alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica-Bold")
    sous_titre_style = ParagraphStyle("sous", fontSize=11, textColor=GRIS,
                                      alignment=TA_CENTER, spaceAfter=16)
    section_style = ParagraphStyle("section", fontSize=11, textColor=BLANC,
                                   backColor=BLEU, fontName="Helvetica-Bold",
                                   leftIndent=6, rightIndent=6, spaceAfter=0,
                                   spaceBefore=12, leading=20)
    label_style  = ParagraphStyle("label", fontSize=10, textColor=BLEU)
    value_style  = ParagraphStyle("value", fontSize=10, alignment=TA_RIGHT)
    total_style  = ParagraphStyle("total", fontSize=12, fontName="Helvetica-Bold",
                                  textColor=BLEU)
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=GRIS,
                                  alignment=TA_CENTER, spaceBefore=20)

    story = []

    # ── En-tête ─────────────────────────────────────────
    story.append(Paragraph("BULLETIN DE PAIE", titre_style))
    story.append(Paragraph(f"Période : {fiche.mois}", sous_titre_style))
    story.append(HRFlowable(width="100%", thickness=2, color=CYAN, spaceAfter=12))

    # ── Infos employé ────────────────────────────────────
    story.append(Paragraph("▸  INFORMATIONS EMPLOYÉ", section_style))
    story.append(Spacer(1, 6))

    info_data = [
        ["Nom",    f"{employe.prenom} {employe.nom}"],
        ["Poste",  employe.poste or "—"],
        ["Email",  employe.email],
    ]
    info_table = Table(info_data, colWidths=[5*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("TEXTCOLOR", (0,0), (0,-1), BLEU),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#E8F4FD"), BLANC]),
        ("GRID", (0,0), (-1,-1), 0.5, GRIS),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ── Détail de la rémunération ────────────────────────
    story.append(Paragraph("▸  DÉTAIL DE LA RÉMUNÉRATION", section_style))
    story.append(Spacer(1, 6))

    rem_data = [
        ["Élément",                       "Heures",             "Montant"],
        ["Salaire de base",               f"{fiche.heures:.2f} h", f"{fiche.salaire_brut:.2f} MAD"],
        ["Prime",                         "—",                  f"{fiche.prime:.2f} MAD"],
        ["Total Brut",                    "",                   f"{fiche.salaire_brut + fiche.prime:.2f} MAD"],
        ["Cotisations sociales (CNSS…)",  "—",                  f"- {fiche.cotisations:.2f} MAD"],
    ]
    rem_table = Table(rem_data, colWidths=[9*cm, 3*cm, 4*cm])
    rem_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  BLEU),
        ("TEXTCOLOR",     (0,0), (-1,0),  BLANC),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",      (0,3), (-1,3),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANC, colors.HexColor("#F0F8FF")]),
        ("GRID",          (0,0), (-1,-1), 0.5, GRIS),
        ("ALIGN",         (1,0), (-1,-1), "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(rem_table)
    story.append(Spacer(1, 12))

    # ── Net à payer ──────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=8))
    net_data = [["NET À PAYER", f"{fiche.salaire_net:.2f} MAD"]]
    net_table = Table(net_data, colWidths=[12*cm, 4*cm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#E8F4FD")),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 13),
        ("TEXTCOLOR",     (0,0), (-1,-1), BLEU),
        ("ALIGN",         (1,0), (1,0),   "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("BOX",           (0,0), (-1,-1), 1.5, CYAN),
    ]))
    story.append(net_table)

    # ── Pied de page ─────────────────────────────────────
    story.append(Paragraph(
        "Document généré automatiquement par PaySlip Manager · Confidentiel",
        footer_style
    ))

    doc.build(story)
    return filepath
