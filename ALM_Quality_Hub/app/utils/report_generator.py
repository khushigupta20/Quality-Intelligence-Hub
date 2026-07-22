"""
RCA Report Generator - Adapted for web application
"""

import pandas as pd
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

from app.utils import watsonx_agent


class RCAReportGenerator:
    def __init__(self, defect_file, output_dir='output',
                 watsonx_api_key: str = "",
                 watsonx_project_id: str = "",
                 watsonx_model_id: str = ""):
        """Initialize report generator with optional watsonx credentials."""
        self.defect_file        = defect_file
        self.output_dir         = output_dir
        self.df                 = None
        self.watsonx_api_key    = watsonx_api_key
        self.watsonx_project_id = watsonx_project_id
        self.watsonx_model_id   = watsonx_model_id
        
    def load_data(self):
        """Load defect data"""
        try:
            if self.defect_file.endswith('.csv'):
                encodings = ['utf-16', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                delimiters = ['\t', ',', ';']
                
                for encoding in encodings:
                    for delimiter in delimiters:
                        try:
                            self.df = pd.read_csv(
                                self.defect_file, 
                                encoding=encoding, 
                                delimiter=delimiter,
                                on_bad_lines='skip', 
                                engine='python'
                            )
                            if len(self.df) > 0 and len(self.df.columns) > 1:
                                self.df.columns = [col.strip().strip('"').replace(' ', '') 
                                                 for col in self.df.columns]
                                return True
                        except (UnicodeDecodeError, pd.errors.ParserError):
                            continue
                return False
            elif self.defect_file.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(self.defect_file)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False

    def _find_column(self, possible_names):
        """Find column by trying multiple possible names"""
        if self.df is None:
            return None
        for name in possible_names:
            if name in self.df.columns:
                return name
        return None

    # ------------------------------------------------------------------
    # PDF report using ReportLab
    # ------------------------------------------------------------------
    def generate_pdf_report(self, session_id):
        """Generate a rich PDF summary report using ReportLab"""
        if self.df is None:
            return None

        from collections import defaultdict, Counter
        import re
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether,
        )
        from reportlab.graphics.shapes import Drawing, Rect, String
        from reportlab.graphics import renderPDF

        report_file = (
            f"{self.output_dir}/RCA_PDF_Report_{session_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        # ── palette ───────────────────────────────────────────────────────────
        C_ACCENT  = colors.HexColor('#3b82d4')
        C_PURPLE  = colors.HexColor('#7c5cd8')
        C_TEXT    = colors.HexColor('#1f2328')
        C_MUTED   = colors.HexColor('#57606a')
        C_BORDER  = colors.HexColor('#e5e7eb')
        C_SURFACE = colors.HexColor('#f7f8fa')
        C_RED     = colors.HexColor('#dc2626')
        C_GREEN   = colors.HexColor('#16a34a')
        C_AMBER   = colors.HexColor('#d97706')
        C_CRIT_BG = colors.HexColor('#fee2e2')
        C_HIGH_BG = colors.HexColor('#fef3c7')
        C_PILL_BG = colors.HexColor('#dbeafe')
        C_PILL_FG = colors.HexColor('#1d4ed8')
        C_WHITE   = colors.white

        # ── styles ────────────────────────────────────────────────────────────
        base = getSampleStyleSheet()
        def S(name, parent='Normal', **kw):
            return ParagraphStyle(name, parent=base[parent], **kw)

        sty = {
            'h1':   S('h1', 'Heading1', fontSize=18, textColor=C_TEXT,
                       spaceAfter=2, spaceBefore=0, leading=22),
            'sub':  S('sub',  fontSize=8, textColor=C_MUTED, spaceAfter=1),
            'meta': S('meta', fontSize=8, textColor=C_MUTED, spaceAfter=8),
            'h2':   S('h2', 'Heading2', fontSize=11, textColor=C_TEXT,
                       spaceBefore=14, spaceAfter=4, leading=14,
                       borderPadding=(0,0,2,0)),
            'h3':   S('h3', 'Heading3', fontSize=9, textColor=C_TEXT,
                       spaceBefore=8, spaceAfter=3, leading=12),
            'body': S('body', fontSize=8, textColor=C_TEXT,
                       spaceAfter=3, leading=11),
            'small':S('small', fontSize=7, textColor=C_MUTED,
                       spaceAfter=2, leading=10),
            'note': S('note', fontSize=7.5, textColor=C_MUTED,
                       spaceAfter=4, leading=10, italic=1),
            'li':   S('li', fontSize=8, textColor=C_TEXT,
                       leftIndent=10, spaceAfter=1, leading=11,
                       bulletIndent=4, bulletText='•'),
            'rc_label': S('rc_label', fontSize=8, textColor=C_RED,
                          leading=11, spaceAfter=0),
            'rc_val':   S('rc_val',   fontSize=8, textColor=C_TEXT,
                          leading=11, spaceAfter=0, bold=1),
            'why_q':    S('why_q',    fontSize=7.5, textColor=C_ACCENT,
                          leading=10, spaceAfter=0),
            'why_a':    S('why_a',    fontSize=7.5, textColor=C_TEXT,
                          leading=10, spaceAfter=3),
            'footer':   S('footer',   fontSize=7,   textColor=C_MUTED,
                          alignment=TA_CENTER, leading=9),
            'card_num': S('card_num', fontSize=9,   textColor=C_TEXT,
                          alignment=TA_CENTER, leading=26, spaceAfter=0),
            'card_lbl': S('card_lbl', fontSize=7,   textColor=C_MUTED,
                          alignment=TA_CENTER, leading=9,  spaceAfter=0),
        }

        # ── locate columns ────────────────────────────────────────────────────
        status_col  = self._find_column(['Status', 'status', 'State'])
        sev_col     = self._find_column(['Severity', 'severity', 'Priority'])
        module_col  = self._find_column(['Module', 'Component', 'module', 'Area'])
        id_col      = self._find_column(['Id', 'ID', 'Defect_ID', 'DefectID'])
        summary_col = self._find_column(['Summary', 'summary', 'Title', 'Description'])

        total  = len(self.df)
        closed = open_ = crit = 0
        if status_col:
            closed = len(self.df[self.df[status_col].astype(str).str.contains('Closed', case=False, na=False)])
            # "Open" statuses: Open, New, Inprogress, In Progress, In-Progress, Reopen, Reopened
            open_  = len(self.df[self.df[status_col].astype(str).str.contains(
                r'Open|New|In[\s\-]?[Pp]rogress|Reopen', case=False, na=False, regex=True)])
        if sev_col:
            crit = len(self.df[self.df[sev_col].astype(str).str.contains(
                'Kritisk|1 -|High|Critical', case=False, na=False)])

        project = 'N/A'
        if summary_col and total > 0:
            m = re.match(r'(VO-\d+)', str(self.df[summary_col].iloc[0]), re.IGNORECASE)
            if m:
                project = m.group(1).upper()

        if open_ == 0 and closed == total:
            status_label = 'All Closed'
        elif open_ == total:
            status_label = 'All Open'
        else:
            status_label = f'{open_} Open / {closed} Closed'

        sev_dist = {}
        if sev_col:
            sev_dist = self.df[sev_col].value_counts().to_dict()

        module_dist = {}
        if module_col:
            module_dist = dict(self.df[module_col].value_counts().head(10))
        elif summary_col:
            kws = ['login','auth','password','user','database','db','api',
                   'ui','server','client','file','upload','admin','security']
            cnt = Counter()
            for _, row in self.df.iterrows():
                s = str(row[summary_col]).lower()
                for kw in kws:
                    if kw in s:
                        cnt[kw.capitalize()] += 1
                        break
            module_dist = dict(cnt.most_common(10))

        # ── defect grouping ───────────────────────────────────────────────────
        groups = defaultdict(list)
        group_kws = [
            'error','display','update','uploaded','upload','login','password',
            'schedule','server','user','validation','data','database',
            'navigation','search','timeout','connection',
        ]
        if id_col and summary_col and sev_col:
            for _, row in self.df.iterrows():
                s   = str(row[summary_col]).lower()
                did = str(row[id_col])
                sev = str(row[sev_col])
                mod = str(row[module_col]) if module_col and module_col in self.df.columns else 'General'
                matched = [kw for kw in group_kws if kw in s]
                gkey = f"{mod}_{matched[0]}" if matched else (
                    f"{mod}_{re.findall(r'[A-Za-z]{5,}', s)[0]}"
                    if re.findall(r'[A-Za-z]{5,}', s) else f"{mod}_other"
                )
                groups[gkey].append({'id': did, 'summary': str(row[summary_col]),
                                     'severity': sev, 'module': mod})

        reps = []
        for gkey, defects in groups.items():
            defects.sort(key=lambda x: (
                0 if 'kritisk' in x['severity'].lower() or '1' in x['severity'] else
                1 if '2' in x['severity'] else 2
            ))
            rep = defects[0].copy()
            rep['group_size']      = len(defects)
            rep['group_key']       = gkey
            rep['similar_defects'] = [d['id'] for d in defects[1:]]
            reps.append(rep)
        reps.sort(key=lambda x: (-x['group_size'], x['severity']))
        grouped    = [r for r in reps if r['group_size'] >= 2]
        standalone = [r for r in reps if r['group_size'] == 1]

        pname_map = {
            'error':'Error Handling', 'display':'Display / Rendering',
            'update':'Role / Update', 'uploaded':'File Upload',
            'upload':'File Handling', 'schedule':'Scheduling',
            'server':'Server', 'user':'User Mgmt',
            'validation':'Input Validation', 'password':'Security',
        }

        five_whys_map = {
            'error': {
                'title': 'Error Handling',
                'w': [
                    ('Why errors occur?',          'Errors not properly caught and handled in application layer'),
                    ('Why not handled?',            'No standardised error handling framework across modules'),
                    ('Why no framework?',           'Error handling patterns were never formally established'),
                    ('Why not established?',        'Error handling requirements not documented in design phase'),
                    ('Why not documented?',         'Architecture review did not include exception management strategy'),
                ],
                'root': 'Lack of error handling architecture and exception management strategy',
            },
            'display': {
                'title': 'Display & Rendering',
                'w': [
                    ('Why display issues?',         'UI rendering incorrectly across navigation and different locales'),
                    ('Why incorrect?',              'CSS and layout not tested across browsers/devices/locales'),
                    ('Why not tested?',             'No cross-browser / locale testing strategy defined'),
                    ('Why no strategy?',            'UI/UX requirements did not cover locale scenarios'),
                    ('Why gaps in requirements?',   'Responsive design and encoding guidelines never formalised'),
                ],
                'root': 'Lack of responsive design guidelines and visual regression / locale testing',
            },
            'update': {
                'title': 'Role / Access Control',
                'w': [
                    ('Why role-based failures?',    'Access control logic has unhandled non-admin paths'),
                    ('Why unhandled?',              'Permission matrix not fully implemented for all roles'),
                    ('Why not implemented?',        'Role-based requirements were incompletely specified'),
                    ('Why incomplete?',             'Security review did not cover all role/permission combos'),
                    ('Why not covered?',            'Lack of access-control test matrix in QA process'),
                ],
                'root': 'Incomplete role-based access control specification and security test coverage',
            },
            'uploaded': {
                'title': 'File Upload / Handling',
                'w': [
                    ('Why file issues?',            'File content and metadata not validated after upload'),
                    ('Why not validated?',          'No server-side file integrity checks implemented'),
                    ('Why no checks?',              'File handling requirements lacked content validation'),
                    ('Why incomplete?',             'File upload edge cases not considered in design'),
                    ('Why not considered?',         'Lack of file processing testing framework'),
                ],
                'root': 'Lack of file validation framework and upload integrity testing',
            },
            'validation': {
                'title': 'Input Validation',
                'w': [
                    ('Why validation failures?',    'Input validation is inconsistent or missing across screens'),
                    ('Why inconsistent?',           'No centralised validation framework used'),
                    ('Why no framework?',           'Validation logic scattered across individual components'),
                    ('Why scattered?',              'No validation design pattern established at architecture level'),
                    ('Why no pattern?',             'Input validation strategy not in coding standards'),
                ],
                'root': 'Lack of centralised input validation framework and data integrity strategy',
            },
        }

        # ── helpers ───────────────────────────────────────────────────────────
        gen_ts    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gen_date  = gen_ts[:10]
        short_sid = session_id[:8]
        W = A4[0] - 30*mm   # usable content width

        def sev_color(sev):
            sl = sev.lower()
            if 'kritisk' in sl or '1 -' in sl or 'critical' in sl or 'high' in sl:
                return C_RED
            return C_AMBER

        def mini_bar_drawing(pct, bar_color, width=80, height=8):
            d = Drawing(width, height)
            d.add(Rect(0, 0, width, height, fillColor=C_SURFACE,
                       strokeColor=C_BORDER, strokeWidth=0.5))
            fill_w = max(1, width * pct / 100)
            d.add(Rect(0, 0, fill_w, height, fillColor=bar_color,
                       strokeColor=None, strokeWidth=0))
            return d

        def module_bar_drawing(label, count, max_count, is_sec, row_h=12):
            total_w = W - 10*mm
            label_w = 28*mm
            count_w = 8*mm
            bar_w   = total_w - label_w - count_w - 4*mm
            d = Drawing(total_w, row_h)
            # label
            d.add(String(label_w - 2, 2, str(label),
                         fontSize=7, fillColor=C_MUTED.hexval(),
                         textAnchor='end'))
            # track
            d.add(Rect(label_w, 1, bar_w, row_h - 3,
                       fillColor=C_SURFACE, strokeColor=C_BORDER, strokeWidth=0.4))
            fill = max(1, bar_w * count / max_count) if max_count else 0
            bar_c = C_PURPLE if is_sec else C_ACCENT
            d.add(Rect(label_w, 1, fill, row_h - 3,
                       fillColor=bar_c, strokeColor=None, strokeWidth=0))
            # count
            d.add(String(label_w + bar_w + 3, 2, str(count),
                         fontSize=7, fillColor=C_TEXT.hexval()))
            return d

        # ── document setup ────────────────────────────────────────────────────
        doc = SimpleDocTemplate(
            report_file,
            pagesize=A4,
            leftMargin=15*mm, rightMargin=15*mm,
            topMargin=15*mm,  bottomMargin=15*mm,
            title=f'RCA Summary Report – {project}',
            author='ALM RCA Web Application',
        )

        story = []

        # ── header ────────────────────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=2, color=C_ACCENT,
                                spaceAfter=6))
        story.append(Paragraph('Root Cause Analysis – Summary Report', sty['h1']))
        story.append(Paragraph(
            f'ALM RCA Web Application &nbsp;&nbsp;|&nbsp;&nbsp; Session: {session_id}',
            sty['sub']))
        story.append(Paragraph(
            f'<b>Generated:</b> {gen_ts} &nbsp;&nbsp; '
            f'<b>Project:</b> {project} &nbsp;&nbsp; '
            f'<b>Status:</b> {status_label}',
            sty['meta']))
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER,
                                spaceAfter=8))

        # ── LLM executive summary paragraph ──────────────────────────────────
        if watsonx_agent.is_configured(self.watsonx_api_key, self.watsonx_project_id):
            pattern_names = list({
                g['group_key'].split('_')[-1].capitalize()
                for g in grouped if g.get('group_key')
            })
            exec_result = watsonx_agent.generate_executive_summary(
                total=total,
                open_=open_,
                closed=closed,
                crit=crit,
                top_modules=list(module_dist.keys())[:3],
                pattern_names=pattern_names,
                watsonx_api_key=self.watsonx_api_key,
                watsonx_project_id=self.watsonx_project_id,
                watsonx_model_id=self.watsonx_model_id,
            )
            if "error" not in exec_result and exec_result.get("summary"):
                story.append(Paragraph('AI-Generated Executive Narrative', sty['h2']))
                story.append(Paragraph(exec_result["summary"], sty['body']))
                story.append(Spacer(1, 8))

        # ── executive summary cards ───────────────────────────────────────────
        story.append(Paragraph('Executive Summary', sty['h2']))
        cards_data = [
            [
                Paragraph(f'<font size="20" color="{C_ACCENT.hexval()}"><b>{total}</b></font>', sty['card_num']),
                Paragraph(f'<font size="20" color="{C_GREEN.hexval()}"><b>{closed}</b></font>', sty['card_num']),
                Paragraph(f'<font size="20" color="{C_TEXT.hexval()}"><b>{open_}</b></font>', sty['card_num']),
                Paragraph(f'<font size="20" color="{C_RED.hexval()}"><b>{crit}</b></font>', sty['card_num']),
            ],
            [
                Paragraph('Total Defects', sty['card_lbl']),
                Paragraph('Closed',        sty['card_lbl']),
                Paragraph('Open',          sty['card_lbl']),
                Paragraph('Critical Severity', sty['card_lbl']),
            ],
        ]
        col_w = W / 4
        cards_tbl = Table(cards_data, colWidths=[col_w]*4, rowHeights=[28, 14])
        cards_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_SURFACE),
            ('BOX',        (0,0), (0,-1),  0.5, C_BORDER),
            ('BOX',        (1,0), (1,-1),  0.5, C_BORDER),
            ('BOX',        (2,0), (2,-1),  0.5, C_BORDER),
            ('BOX',        (3,0), (3,-1),  0.5, C_BORDER),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ROUNDEDCORNERS', (0,0), (-1,-1), 4),
        ]))
        story.append(cards_tbl)
        story.append(Spacer(1, 8))

        # ── severity distribution ─────────────────────────────────────────────
        story.append(Paragraph('Severity Distribution', sty['h2']))
        sev_rows = [[
            Paragraph('<b>Severity</b>', sty['small']),
            Paragraph('<b>Count</b>', sty['small']),
            Paragraph('<b>%</b>', sty['small']),
            Paragraph('<b>Visual</b>', sty['small']),
        ]]
        for sev, cnt in sev_dist.items():
            pct = round(cnt / total * 100, 1) if total else 0
            bc  = sev_color(sev)
            sev_rows.append([
                Paragraph(str(sev), sty['body']),
                Paragraph(str(cnt), sty['body']),
                Paragraph(f'{pct}%', sty['body']),
                mini_bar_drawing(pct, bc, width=100, height=9),
            ])
        sev_tbl = Table(sev_rows, colWidths=[W*0.45, W*0.1, W*0.1, W*0.35])
        sev_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  C_SURFACE),
            ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ]))
        story.append(sev_tbl)
        story.append(Spacer(1, 8))

        # ── module distribution bar chart ─────────────────────────────────────
        story.append(Paragraph('Module Distribution', sty['h2']))
        if module_dist:
            max_m = max(module_dist.values())
            for i, (label, cnt) in enumerate(module_dist.items()):
                story.append(module_bar_drawing(label, cnt, max_m, i >= 2))
        story.append(Spacer(1, 8))

        # ── defect clustering table ───────────────────────────────────────────
        story.append(Paragraph('Defect Grouping & Clustering', sty['h2']))
        grp_total = sum(g['group_size'] for g in grouped)
        story.append(Paragraph(
            f'{total} defects → <b>{len(grouped)} groups</b> ({grp_total} defects) '
            f'+ <b>{len(standalone)} standalone</b> defects (keyword similarity)',
            sty['note']))
        if grouped:
            clust_hdr = [[
                Paragraph('<b>Group</b>', sty['small']),
                Paragraph('<b>Lead ID</b>', sty['small']),
                Paragraph('<b>Size</b>', sty['small']),
                Paragraph('<b>Severity</b>', sty['small']),
                Paragraph('<b>Similar IDs</b>', sty['small']),
                Paragraph('<b>Summary (Lead)</b>', sty['small']),
            ]]
            clust_rows = []
            for g in grouped:
                kw  = g['group_key'].split('_')[-1]
                pn  = pname_map.get(kw, kw.capitalize())
                sim = ', '.join(g['similar_defects'][:6])
                clust_rows.append([
                    Paragraph(f'<b>{pn}</b><br/>'
                              f'<font size="6" color="#57606a">{g["group_key"]}</font>', sty['body']),
                    Paragraph(str(g['id']), sty['body']),
                    Paragraph(f'<b>{g["group_size"]}</b>', sty['body']),
                    Paragraph(str(g['severity'])[:20], sty['body']),
                    Paragraph(f'<font size="6.5">{sim}</font>', sty['body']),
                    Paragraph(str(g['summary'])[:90], sty['body']),
                ])
            clust_tbl = Table(
                clust_hdr + clust_rows,
                colWidths=[W*0.17, W*0.08, W*0.05, W*0.14, W*0.20, W*0.36],
            )
            clust_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0),  C_SURFACE),
                ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING',   (0,0), (-1,-1), 4),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_SURFACE]),
            ]))
            story.append(clust_tbl)
        story.append(Spacer(1, 6))

        # ── standalone defects ────────────────────────────────────────────────
        story.append(Paragraph(f'Standalone Defects ({len(standalone)})', sty['h3']))
        story.append(Paragraph(
            'Each defect below has no close keyword-match sibling in the dataset.',
            sty['note']))
        if standalone:
            sa_hdr = [[
                Paragraph('<b>ID</b>', sty['small']),
                Paragraph('<b>Severity</b>', sty['small']),
                Paragraph('<b>Summary</b>', sty['small']),
            ]]
            sa_rows = []
            for s in standalone:
                sa_rows.append([
                    Paragraph(str(s['id']), sty['body']),
                    Paragraph(str(s['severity'])[:22], sty['body']),
                    Paragraph(str(s['summary'])[:120], sty['body']),
                ])
            sa_tbl = Table(
                sa_hdr + sa_rows,
                colWidths=[W*0.09, W*0.20, W*0.71],
            )
            sa_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0),  C_SURFACE),
                ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING',   (0,0), (-1,-1), 4),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_SURFACE]),
            ]))
            story.append(sa_tbl)
        story.append(Spacer(1, 8))

        # ── patterns detected ─────────────────────────────────────────────────
        pattern_bullets = {
            'error':    ['Incorrect / misleading error messages shown to users',
                         'Validation errors triggered at wrong thresholds',
                         'No standardised exception messages across screens',
                         'Errors not distinguishing field-level from system-level issues'],
            'display':  ['Danish / special characters rendered incorrectly',
                         'UTF-8 encoding breaks after screen navigation',
                         'Text overflow / overlapping in list views',
                         'No cross-browser / locale regression tests in place'],
            'update':   ['Non-Admin role bypass for sequence / job updates',
                         'Insufficient permission checks on update operations',
                         'CHANGESEQUENCE/CHANGEJOBS flags not respected'],
            'uploaded': ['Blank content after file upload; job runs silently',
                         'MIME type not validated on upload',
                         'Uploaded file details not persisted correctly'],
            'validation':['Special characters accepted in restricted fields',
                          'Special characters blocked in fields that allow them',
                          'Incorrect job order accepted by system'],
        }
        if grouped:
            story.append(Paragraph('Patterns Detected', sty['h2']))
            # 2-column layout via a Table
            pat_cells = []
            row = []
            for g in grouped[:6]:
                kw      = g['group_key'].split('_')[-1]
                pn      = pname_map.get(kw, kw.capitalize()) + ' Pattern'
                bullets = pattern_bullets.get(kw, [
                    f'Multiple defects with "{kw}" keyword detected',
                    'Review related code paths for similar issues',
                    'Add regression tests for this area',
                ])
                note = (f'{g["group_size"]} defects  |  Largest cluster'
                        if g is grouped[0] else f'{g["group_size"]} defects')
                cell_parts = [
                    Paragraph(f'<b>{pn}</b>', sty['body']),
                    Paragraph(f'<font size="7" color="#57606a">{note}</font>', sty['small']),
                ]
                for b in bullets:
                    cell_parts.append(Paragraph(b, sty['li']))
                row.append(cell_parts)
                if len(row) == 2:
                    pat_cells.append(row)
                    row = []
            if row:  # odd card
                row.append('')
                pat_cells.append(row)

            if pat_cells:
                pat_tbl = Table(
                    pat_cells,
                    colWidths=[W/2 - 2*mm, W/2 - 2*mm],
                    hAlign='LEFT',
                )
                pat_tbl.setStyle(TableStyle([
                    ('BOX',           (0,0), (-1,-1), 0.4, C_BORDER),
                    ('INNERGRID',     (0,0), (-1,-1), 0.4, C_BORDER),
                    ('BACKGROUND',    (0,0), (-1,-1), C_SURFACE),
                    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING',    (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING',   (0,0), (-1,-1), 8),
                    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
                ]))
                story.append(pat_tbl)
            story.append(Spacer(1, 8))

        # ── 5-Whys ────────────────────────────────────────────────────────────
        story.append(Paragraph('5-Whys Root Cause Analysis', sty['h2']))
        seen_kws   = set()
        fallback   = ['error', 'display', 'update', 'uploaded']
        fb_idx     = 0
        shown      = 0
        for g in grouped[:4]:
            kw = g['group_key'].split('_')[-1]
            if kw in seen_kws or kw not in five_whys_map:
                while fb_idx < len(fallback) and fallback[fb_idx] in seen_kws:
                    fb_idx += 1
                kw = fallback[fb_idx] if fb_idx < len(fallback) else 'error'
                fb_idx += 1
            seen_kws.add(kw)
            fw = five_whys_map.get(kw, five_whys_map['error'])
            shown += 1

            block_rows = []
            for j, (q, a) in enumerate(fw['w'], 1):
                block_rows.append([
                    Paragraph(f'<b>Why {j}: {q}</b>', sty['why_q']),
                    Paragraph(a, sty['why_a']),
                ])
            block_rows.append([
                Paragraph('<b>Root Cause:</b>', sty['rc_label']),
                Paragraph(fw['root'], sty['rc_val']),
            ])
            block_tbl = Table(block_rows, colWidths=[W*0.30, W*0.70])
            block_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-2), C_SURFACE),
                ('BACKGROUND',    (0,-1),(  -1,-1), colors.HexColor('#fff8f8')),
                ('BOX',           (0,0), (-1,-1), 0.5, C_BORDER),
                ('LINEBELOW',     (0,-2),(-1,-2), 0.5, C_BORDER),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING',   (0,0), (-1,-1), 6),
            ]))
            cat_title = (
                f'Pattern {shown} — {fw["title"]}  '
                f'<font size="7" color="#57606a">({g["group_size"]} defects affected)</font>'
            )
            whys_block = KeepTogether([
                Paragraph(cat_title, sty['h3']),
                block_tbl,
                Spacer(1, 6),
            ])
            story.append(whys_block)

        # ── preventive measures ───────────────────────────────────────────────
        story.append(Paragraph('Preventive Measures', sty['h2']))

        # Static fallback lists
        immediate = [
            'Implement comprehensive error handling framework with standardised user-facing messages',
            'Add user-friendly, field-level error messages across all screens',
            'Implement error logging and monitoring (centralised log aggregation)',
            'Implement visual regression testing and cross-browser compatibility checks',
            'Review CSS and layout implementations for locale/character encoding correctness',
            'Fix role-based access control gaps',
            'Mask sensitive data in job logs immediately',
            'Add MIME-type and file-content validation on upload',
        ]
        longterm = [
            'Establish comprehensive automated test framework covering critical paths and regression',
            'Implement continuous integration with automated lint, unit, and integration tests',
            'Conduct mandatory code reviews with focus on error handling and security',
            'Define and enforce responsive design and internationalisation (i18n) standards',
            'Implement continuous monitoring and alerting for production anomalies',
            'Provide team training on best practices for error handling and access control',
            'Document lessons learned and update coding standards after each release',
            'Establish design review checkpoints and quality gates before each release',
        ]
        top_mods = ', '.join(list(module_dist.keys())[:3]) if module_dist else 'key modules'
        general = [
            'Conduct regular code reviews focusing on identified problem areas',
            f'Implement automated testing for high-defect modules ({top_mods})',
            'Establish coding standards and best-practices documentation',
            'Conduct knowledge-sharing sessions on common defect patterns',
            'Implement continuous integration with automated testing pipeline',
        ]

        # LLM-enhanced preventive measures for the top grouped pattern
        if watsonx_agent.is_configured(self.watsonx_api_key, self.watsonx_project_id) and grouped:
            top_group = grouped[0]
            top_kw    = top_group['group_key'].split('_')[-1]
            top_sums  = [top_group.get('summary', '')] + \
                        [top_group.get('full_summary', '')]
            top_mods_list = list({g.get('module', '') for g in grouped[:3] if g.get('module')})
            llm_measures = watsonx_agent.generate_measures(
                top_kw, top_sums, top_mods_list,
                self.watsonx_api_key, self.watsonx_project_id, self.watsonx_model_id
            )
            if "error" not in llm_measures:
                immediate = llm_measures.get('immediate', immediate)
                longterm  = llm_measures.get('long_term', longterm)

        def numbered_list(title, items):
            out = [Paragraph(title, sty['h3'])]
            for i, item in enumerate(items, 1):
                out.append(Paragraph(f'{i}. {item}', sty['body']))
            out.append(Spacer(1, 4))
            return out

        story.extend(numbered_list('Immediate Actions (Next Sprint)', immediate))
        story.extend(numbered_list('Long-term Prevention (3–6 Months)', longterm))
        story.extend(numbered_list('General Best Practices', general))

        # ── footer ────────────────────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER,
                                spaceBefore=12, spaceAfter=4))
        ai_label = ' &nbsp;·&nbsp; ✦ AI Enhanced' if watsonx_agent.is_configured(self.watsonx_api_key, self.watsonx_project_id) else ''
        story.append(Paragraph(
            f'Report generated by the ALM RCA Web Application &nbsp;·&nbsp; '
            f'Session {short_sid}… &nbsp;·&nbsp; {gen_date}{ai_label}',
            sty['footer']))
        story.append(Paragraph('Made with IBM Bob', sty['footer']))

        doc.build(story)
        return report_file


    def export_to_json(self, session_id):
        """Export analysis data to JSON format"""
        if self.df is None:
            return None
        
        json_file = f"{self.output_dir}/analysis_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Find columns
        status_col = self._find_column(['Status', 'status', 'State'])
        sev_col = self._find_column(['Severity', 'severity', 'Priority'])
        module_col = self._find_column(['Module', 'Component', 'module', 'Area'])
        rc_col = self._find_column(['Root_Cause', 'RootCause', 'root_cause'])
        
        analysis_data = {
            'generated_at': datetime.now().isoformat(),
            'total_defects': len(self.df),
            'summary': {}
        }
        
        if status_col:
            analysis_data['summary']['open'] = len(self.df[self.df[status_col].astype(str).str.contains('Open', case=False, na=False)])
            analysis_data['summary']['closed'] = len(self.df[self.df[status_col].astype(str).str.contains('Closed', case=False, na=False)])
            analysis_data['status_distribution'] = self.df[status_col].value_counts().to_dict()
        
        if sev_col:
            analysis_data['summary']['high_severity'] = len(self.df[self.df[sev_col].astype(str).str.contains('Kritisk|1 -|High|Critical', case=False, na=False)])
            analysis_data['severity_distribution'] = self.df[sev_col].value_counts().to_dict()
        
        if module_col:
            analysis_data['module_distribution'] = self.df[module_col].value_counts().to_dict()
        
        if rc_col:
            df_with_rc = self.df[self.df[rc_col].notna() & (self.df[rc_col] != '')]
            if len(df_with_rc) > 0:
                analysis_data['root_cause_distribution'] = df_with_rc[rc_col].value_counts().to_dict()
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        return json_file

# Made with Bob
