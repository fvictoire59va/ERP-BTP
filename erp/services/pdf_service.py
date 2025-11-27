from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak, Frame, PageTemplate, FrameBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def _on_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFont('Helvetica', 8)
    footer_text = 'Devis établi sur la base des informations fournies. TVA selon taux en vigueur.'
    canvas.drawString(15*mm, 10*mm, footer_text)
    page_num = f'Page {doc.page} / {doc.page}'
    canvas.drawRightString(width - 15*mm, 10*mm, page_num)
    canvas.restoreState()


def generate_pdf(devis, data_manager, pdf_path: Path, company_info: dict | None = None):
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=2, fontSize=18)

    # Use a BaseDocTemplate with two frames: main content and a fixed bottom frame for totals
    page_width, page_height = A4
    left_margin = 12 * mm
    right_margin = 12 * mm
    top_margin = 12 * mm
    bottom_margin = 12 * mm
    totals_frame_height = 30 * mm

    doc = BaseDocTemplate(str(pdf_path), pagesize=A4,
                          leftMargin=left_margin, rightMargin=right_margin,
                          topMargin=top_margin, bottomMargin=bottom_margin)

    content_frame = Frame(left_margin,
                          bottom_margin + totals_frame_height,
                          page_width - left_margin - right_margin,
                          page_height - top_margin - bottom_margin - totals_frame_height,
                          id='content')

    totals_frame = Frame(left_margin,
                         bottom_margin,
                         page_width - left_margin - right_margin,
                         totals_frame_height,
                         id='totals')

    template = PageTemplate(id='TwoFrame', frames=[content_frame, totals_frame], onPage=_on_page)
    doc.addPageTemplates([template])

    elems = []

    # Header: logo left, company info and DEVIS on right
    logo_path = Path(data_manager.data_dir) / 'logo.png'
    logo = None
    if logo_path.exists():
        try:
            logo = Image(str(logo_path), width=50*mm, height=18*mm)
        except Exception:
            logo = None

    comp = company_info or {}
    # if no explicit company_info passed, try to get it from the data manager
    if not comp:
        if hasattr(data_manager, 'organisation') and data_manager.organisation:
            org = data_manager.organisation
            address_line = getattr(org, 'adresse', '') or '35 route de Valenciennes'
            comp = {
                'name': getattr(org, 'nom', '') or 'VICTOIRE SA',
                'phone': getattr(org, 'telephone', '') or '0689962910',
                'address': address_line
            }
            if getattr(org, 'cp', '') or getattr(org, 'ville', ''):
                comp['address'] = f"{address_line}\n{getattr(org, 'cp', '')} {getattr(org, 'ville', '')}"
        elif hasattr(data_manager, 'get_company_info'):
            try:
                comp = data_manager.get_company_info() or {}
            except Exception:
                comp = {}
    
    company_name = comp.get('name', 'VICTOIRE SA')
    company_phone = comp.get('phone', '0689962910')
    company_address = comp.get('address', '35 route de Valenciennes\n59252 Orsinval')
    
    company_lines = [Paragraph(f"<b>{company_name}</b>", normal)]
    if company_address:
        # Diviser l'adresse par \n et créer un Paragraph pour chaque ligne
        for addr_line in company_address.split('\n'):
            if addr_line.strip():
                company_lines.append(Paragraph(addr_line, normal))
    company_lines.append(Paragraph(f"Tel: {company_phone}", normal))
    
    # Create header with company info on left and DEVIS on right
    devis_title = ParagraphStyle('devis_title', parent=styles['Heading1'], alignment=2, fontSize=16, textColor=colors.HexColor('#1f2937'), spaceAfter=0)
    devis_text = Paragraph('<b>DEVIS</b>', devis_title)
    
    # Create header table with only DEVIS title
    if logo is not None:
        header_table = Table([[logo, devis_text]], colWidths=[60*mm, None])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    else:
        header_table = Table([[devis_text]], colWidths=[None])
        header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
    
    elems.append(header_table)
    
    # Calculate content width for layout
    content_width = page_width - left_margin - right_margin
    
    elems.append(Spacer(1, 3*mm))

    # Addresses: chantier / facturation
    client = data_manager.get_client_by_id(getattr(devis, 'client_id', None))
    def _build_addr_block(lines):
        return [Paragraph(l, normal) for l in lines]

    if client:
        chantier = [ '<b>Adresse de chantier</b>', f"{getattr(client,'nom','')} {getattr(client,'prenom','')}", getattr(client,'adresse',''), f"{getattr(client,'cp','')} {getattr(client,'ville','')}" ]
        fact = [ '<b>Adresse de facturation</b>', f"{getattr(client,'nom','')}", getattr(client,'adresse',''), f"{getattr(client,'cp','')} {getattr(client,'ville','')}" ]
    else:
        chantier = ['Client non renseigné']
        fact = ['-']

    left = _build_addr_block(chantier)
    right = _build_addr_block(fact)
    
    # compute the table width (must match the widths used for the lines table)
    table_col_widths = [12*mm, 80*mm, 16*mm, 10*mm, 20*mm, 22*mm, 12*mm]
    table_width = sum(table_col_widths)
    
    # Calculate desired_right for address table alignment with lines table
    desired_right = table_width
    
    # Create left column: organization address stacked with chantier address
    org_and_chantier = company_lines + [Spacer(1, 4*mm)] + left
    
    # Create address table with org+chantier on left, facturation on right
    addr_table = Table([[org_and_chantier, right]], colWidths=[110*mm, 80*mm])
    addr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))

    # Add address table directly
    elems.append(addr_table)
    elems.append(Spacer(1, 15*mm))

    # Description - in a table format like addresses (left aligned like VICTOIRE SA block)
    desc = getattr(devis, 'description', '') or getattr(devis, 'objet', '') if hasattr(devis, 'objet') else ''
    desc_style = ParagraphStyle('desc_title', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1f2937'), spaceAfter=3)
    
    # Create description content in a two-column table to match address table structure
    desc_para = Paragraph('<b>Descriptif des travaux</b><br/>' + (desc or '&nbsp;'), normal)
    
    desc_table = Table([[desc_para, '']], colWidths=[110*mm, 80*mm])
    desc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elems.append(desc_table)
    elems.append(Spacer(1, 8*mm))

    # Lines table with repeating header
    header = ['N°', 'Description', 'Qté', 'U.', 'P.U. HT', 'TOTAL HT', 'TVA']
    data = [header]
    lignes = getattr(devis, 'lignes', []) or []
    
    # Inclure les lignes de type 'ouvrage', 'chapitre' et 'texte'
    lignes_affichees = [l for l in lignes if getattr(l, 'type', 'ouvrage') in ['ouvrage', 'chapitre', 'texte']]
    
    row_num = 1
    for ligne in lignes_affichees:
        ligne_type = getattr(ligne, 'type', 'ouvrage')
        designation = getattr(ligne, 'designation', getattr(ligne, 'label', ''))
        
        if ligne_type == 'chapitre':
            # Pour les chapitres, utiliser le champ 'titre'
            chapitre_text = getattr(ligne, 'titre', designation if designation else 'CHAPITRE SANS NOM')
            data.append([
                '',  # N° vide
                chapitre_text,
                '',
                '',
                '',
                '',
                ''
            ])
        elif ligne_type == 'texte':
            # Pour les textes, utiliser 'texte' ou 'designation'
            texte_text = getattr(ligne, 'texte', designation if designation else 'TEXTE SANS NOM')
            data.append([
                '',  # N° vide
                texte_text,
                '',
                '',
                '',
                '',
                ''
            ])
        else:  # 'ouvrage'
            quantite = getattr(ligne, 'quantite', getattr(ligne, 'qte', 0))
            unite = getattr(ligne, 'unite', '')
            pu = getattr(ligne, 'prix_unitaire', getattr(ligne, 'pu', 0.0))
            prix_ht = getattr(ligne, 'prix_ht', pu * quantite)
            tva_val = getattr(ligne, 'tva', getattr(devis, 'tva', 20))
            data.append([
                str(row_num),
                Paragraph(designation, normal),
                f"{quantite:.2f}",
                unite,
                f"{pu:.2f} €",
                f"{prix_ht:.2f} €",
                f"{tva_val:.0f}%"
            ])
            row_num += 1

    # Narrower, centered table with small paddings so it leaves a tight margin on both sides
    # define column widths in a variable so we can reuse the total width for alignment
    table_col_widths = table_col_widths if 'table_col_widths' in locals() else [12*mm, 80*mm, 16*mm, 10*mm, 20*mm, 22*mm, 12*mm]
    table = Table(
        data,
        colWidths=table_col_widths,
        repeatRows=1,
        hAlign='CENTER'
    )
    
    # Créer le style de table
    tbl_style = TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # center header text
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('ALIGN', (4,1), (5,-1), 'RIGHT'),
        ('ALIGN', (6,1), (6,-1), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ])
    
    # Ajouter des styles pour les chapitres et textes
    row_idx = 1
    for ligne in lignes_affichees:
        ligne_type = getattr(ligne, 'type', 'ouvrage')
        if ligne_type == 'chapitre':
            # Fond bleu clair pour les chapitres
            tbl_style.add('BACKGROUND', (0, row_idx), (6, row_idx), colors.HexColor('#e8f4f8'))
            # Mettre en gras la colonne Description pour les chapitres
            tbl_style.add('FONTNAME', (1, row_idx), (1, row_idx), 'Helvetica-Bold')
        row_idx += 1
    
    table.setStyle(tbl_style)
    
    # push the lines a bit lower on the page
    elems.append(Spacer(1, 6*mm))
    elems.append(table)
    elems.append(Spacer(1, 15*mm))

    # Totals (place in bottom fixed frame using FrameBreak)
    # Calculer les totaux basés uniquement sur les lignes de type 'ouvrage'
    lignes_ouvrages = [l for l in lignes if getattr(l, 'type', 'ouvrage') == 'ouvrage']
    
    total_ht = getattr(devis, 'total_ht', None)
    if total_ht is None:
        total_ht = sum(getattr(l, 'prix_ht', getattr(l, 'prix_unitaire', 0.0) * getattr(l, 'quantite', 1)) for l in lignes_ouvrages)
    tva_rate = getattr(devis, 'tva', 20)
    total_tva = getattr(devis, 'total_tva', total_ht * (tva_rate/100.0))
    total_ttc = getattr(devis, 'total_ttc', total_ht + total_tva)

    totals_data = [['Total HT', f"{total_ht:.2f} €"], [f"TVA ({tva_rate:.0f}%)", f"{total_tva:.2f} €"], ['Total TTC', f"{total_ttc:.2f} €"]]
    totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,0), (-1,0), 0.6, colors.black),
    ]))
    # Insert a FrameBreak so the totals render in the bottom frame
    # Place the following content directly after the table (not a page footer)
    # It will appear on the page after the table if there's not enough room.
    from collections import defaultdict

    # compute breakdown per TVA rate
    tva_map = defaultdict(float)
    for l in lignes_ouvrages:
        rate = getattr(l, 'tva', getattr(devis, 'tva', 20))
        tva_map[rate] += getattr(l, 'prix_ht', getattr(l, 'prix_unitaire', 0.0) * getattr(l, 'quantite', 1))

    tva_rows = []
    for rate in sorted(tva_map.keys(), reverse=True):
        base = tva_map[rate]
        montant = base * (rate / 100.0)
        tva_rows.append([f'TVA {rate:.0f}% base', f"{base:.2f} €", f"{montant:.2f} €"])

    # Left block: build a simple paragraph listing legal note
    left_block = []
    left_block.append(Spacer(1, 4*mm))  # Add space at the top
    left_block.append(Paragraph('Réserve de propriété: Les biens vendus restent la propriété du vendeur jusqu\'au paiement intégral.', normal))

    # Right block: totals summary and payment lines
    right_rows = [[ 'Total HT', f"{total_ht:.2f} €" ], [ f"TVA ({tva_rate:.0f}%)", f"{total_tva:.2f} €" ], [ 'Total TTC', f"{total_ttc:.2f} €" ]]
    right_table = Table(right_rows, colWidths=[50*mm, 30*mm])
    right_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
    ]))

    right_block = [right_table, Spacer(1, 12*mm)]

    # Use KeepTogether to group left and right content
    from reportlab.platypus import Spacer as SpacerElement
    
    # Create a simple wrapper that puts left and right side by side
    left_col_width = content_width - desired_right + 70*mm  # Augmenter la largeur de la colonne gauche
    right_col_width = desired_right - 70*mm
    bottom_table = Table([[left_block, right_block]], colWidths=[left_col_width, right_col_width], splitByRow=0)
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))

    # Ensure footer content is kept together and not split across pages
    elems.append(KeepTogether([bottom_table]))
    
    # Add signature lines on the same line at the bottom
    sig_left = Paragraph('Pour l\'entreprise (signature et cachet)', normal)
    sig_right = Paragraph('Pour le client (signature)', ParagraphStyle('right_align', parent=normal, alignment=2))
    
    sig_table = Table([[sig_left, sig_right]], colWidths=[left_col_width, right_col_width])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    
    elems.append(sig_table)

    # Footer handled by PageTemplate._on_page
    doc.build(elems)

    return pdf_path
