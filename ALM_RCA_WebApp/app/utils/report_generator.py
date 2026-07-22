"""
RCA Report Generator - Adapted for web application
"""

import pandas as pd
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')


class RCAReportGenerator:
    def __init__(self, defect_file, output_dir='output'):
        """Initialize report generator"""
        self.defect_file = defect_file
        self.output_dir = output_dir
        self.df = None
        
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
    
    def generate_summary_report(self, session_id):
        """Generate executive summary report"""
        if self.df is None:
            return None
        
        report_file = f"{self.output_dir}/RCA_Summary_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # Find columns
        status_col = self._find_column(['Status', 'status', 'State'])
        sev_col = self._find_column(['Severity', 'severity', 'Priority'])
        module_col = self._find_column(['Module', 'Component', 'module', 'Area'])
        rc_col = self._find_column(['Root_Cause', 'RootCause', 'root_cause'])
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Root Cause Analysis - Summary Report\n\n")
            f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            total_defects = len(self.df)
            
            open_defects = 0
            closed_defects = 0
            if status_col:
                open_defects = len(self.df[self.df[status_col].astype(str).str.contains('Open', case=False, na=False)])
                closed_defects = len(self.df[self.df[status_col].astype(str).str.contains('Closed', case=False, na=False)])
            
            high_severity = 0
            if sev_col:
                high_severity = len(self.df[self.df[sev_col].astype(str).str.contains('Kritisk|1 -|High|Critical', case=False, na=False)])
            
            f.write(f"- **Total Defects Analyzed**: {total_defects}\n")
            f.write(f"- **Open Defects**: {open_defects}\n")
            f.write(f"- **Closed Defects**: {closed_defects}\n")
            f.write(f"- **High/Critical Severity**: {high_severity}\n\n")
            
            # Severity Breakdown
            if sev_col:
                f.write("## Severity Distribution\n\n")
                severity_counts = self.df[sev_col].value_counts()
                f.write("| Severity | Count | Percentage |\n")
                f.write("|----------|-------|------------|\n")
                for severity, count in severity_counts.items():
                    percentage = (count / total_defects) * 100
                    f.write(f"| {severity} | {count} | {percentage:.1f}% |\n")
                f.write("\n")
            
            # Module Analysis
            if module_col:
                f.write("## Top 10 Affected Modules/Components\n\n")
                module_counts = self.df[module_col].value_counts().head(10)
                f.write("| Module/Component | Defect Count |\n")
                f.write("|------------------|-------------|\n")
                for module, count in module_counts.items():
                    f.write(f"| {module} | {count} |\n")
                f.write("\n")
            
            # Root Cause Analysis
            if rc_col:
                df_with_rc = self.df[self.df[rc_col].notna() & (self.df[rc_col] != '')]
                if len(df_with_rc) > 0:
                    f.write("## Root Cause Distribution\n\n")
                    rc_counts = df_with_rc[rc_col].value_counts()
                    f.write("| Root Cause | Count | Percentage |\n")
                    f.write("|------------|-------|------------|\n")
                    for rc, count in rc_counts.items():
                        percentage = (count / len(df_with_rc)) * 100
                        f.write(f"| {rc} | {count} | {percentage:.1f}% |\n")
                    f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            f.write("### Immediate Actions\n")
            f.write(f"1. Address {high_severity} high/critical severity defects as priority\n")
            if module_col and 'module_counts' in locals():
                f.write(f"2. Focus on top 3 modules: {', '.join(module_counts.head(3).index.tolist())}\n")
            f.write("3. Conduct RCA for defects without identified root causes\n\n")
            
            f.write("### Process Improvements\n")
            f.write("1. Implement preventive measures based on identified root causes\n")
            f.write("2. Enhance testing in high-defect modules\n")
            f.write("3. Conduct knowledge sharing sessions on common defect patterns\n")
            f.write("4. Review and update coding standards and best practices\n\n")
            
            # Add 5 WHYs Analysis section
            f.write("## Root Cause Analysis (5 WHYs Method)\n\n")
            f.write("The 5 WHYs technique helps identify the root cause by repeatedly asking 'Why?' to drill down from symptoms to underlying issues.\n\n")
            
            if rc_col:
                df_with_rc = self.df[self.df[rc_col].notna() & (self.df[rc_col] != '')]
                if len(df_with_rc) > 0:
                    f.write("### Example 5 WHYs Analysis\n\n")
                    f.write("**Problem Statement:** Multiple defects occurring in the system\n\n")
                    f.write("1. **Why are defects occurring?**\n")
                    f.write("   → Code quality and testing gaps exist\n\n")
                    f.write("2. **Why do quality gaps exist?**\n")
                    f.write("   → Development processes not consistently followed\n\n")
                    f.write("3. **Why aren't processes followed?**\n")
                    f.write("   → Processes not well-defined or enforced\n\n")
                    f.write("4. **Why aren't processes well-defined?**\n")
                    f.write("   → Quality standards not established\n\n")
                    f.write("5. **Why weren't standards established?**\n")
                    f.write("   → Lack of quality assurance framework and development best practices\n\n")
                    f.write("**ROOT CAUSE:** Lack of comprehensive quality assurance framework and standardized development practices\n\n")
            
            # Add Preventive Measures section
            f.write("## Preventive Measures\n\n")
            f.write("### Immediate Actions (Next Sprint)\n\n")
            f.write("1. **Technical Fixes**\n")
            f.write("   - Fix all critical and high-severity defects\n")
            f.write("   - Implement comprehensive input validation\n")
            f.write("   - Add proper error handling and logging\n")
            f.write("   - Optimize performance bottlenecks\n\n")
            
            f.write("2. **Testing Improvements**\n")
            f.write("   - Create automated test suite for critical paths\n")
            f.write("   - Implement regression testing\n")
            f.write("   - Add integration tests for high-defect modules\n")
            f.write("   - Conduct security testing\n\n")
            
            f.write("3. **Documentation**\n")
            f.write("   - Document coding standards and best practices\n")
            f.write("   - Create troubleshooting guides\n")
            f.write("   - Update technical documentation\n\n")
            
            f.write("### Long-term Prevention (Next 3-6 Months)\n\n")
            f.write("1. **Process Improvements**\n")
            f.write("   - Implement mandatory code review process\n")
            f.write("   - Establish design review checkpoints\n")
            f.write("   - Create quality gates for releases\n")
            f.write("   - Implement continuous integration/deployment\n\n")
            
            f.write("2. **Architecture Improvements**\n")
            f.write("   - Refactor high-defect modules\n")
            f.write("   - Implement monitoring and alerting\n")
            f.write("   - Add performance optimization\n")
            f.write("   - Improve error handling framework\n\n")
            
            f.write("3. **Team Development**\n")
            f.write("   - Conduct training on best practices\n")
            f.write("   - Share lessons learned from defects\n")
            f.write("   - Establish knowledge sharing sessions\n")
            f.write("   - Implement mentoring program\n\n")
            
            f.write("---\n\n")
            f.write("*This report was automatically generated by the ALM RCA Web Application*\n")
        
        return report_file

    # ------------------------------------------------------------------
    # Rich HTML report (PDF-printable)
    # ------------------------------------------------------------------
    def generate_html_report(self, session_id):
        """Generate a rich HTML summary report (PDF-printable)"""
        if self.df is None:
            return None

        from collections import defaultdict, Counter
        import re
        import html as html_lib

        report_file = (
            f"{self.output_dir}/RCA_HTML_Report_{session_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        # locate columns
        status_col  = self._find_column(['Status', 'status', 'State'])
        sev_col     = self._find_column(['Severity', 'severity', 'Priority'])
        module_col  = self._find_column(['Module', 'Component', 'module', 'Area'])
        id_col      = self._find_column(['Id', 'ID', 'Defect_ID', 'DefectID'])
        summary_col = self._find_column(['Summary', 'summary', 'Title', 'Description'])

        total  = len(self.df)
        closed = open_ = crit = 0
        if status_col:
            closed = len(self.df[self.df[status_col].astype(str).str.contains('Closed', case=False, na=False)])
            open_  = len(self.df[self.df[status_col].astype(str).str.contains('Open',   case=False, na=False)])
        if sev_col:
            crit = len(self.df[self.df[sev_col].astype(str).str.contains(
                'Kritisk|1 -|High|Critical', case=False, na=False)])

        # project name from first defect summary
        project = 'N/A'
        if summary_col and total > 0:
            first = str(self.df[summary_col].iloc[0])
            m = re.match(r'(VO-\d+)', first, re.IGNORECASE)
            if m:
                project = m.group(1).upper()

        # status label
        if open_ == 0 and closed == total:
            status_label = 'All Closed'
        elif open_ == total:
            status_label = 'All Open'
        else:
            status_label = f'{open_} Open / {closed} Closed'

        # severity distribution
        sev_dist = {}
        if sev_col:
            sev_dist = self.df[sev_col].value_counts().to_dict()

        # module distribution
        module_dist = {}
        if module_col:
            module_dist = dict(self.df[module_col].value_counts().head(10))
        elif summary_col:
            keywords = [
                'login', 'authentication', 'auth', 'password', 'user',
                'database', 'db', 'data', 'api', 'interface',
                'ui', 'frontend', 'backend', 'server', 'client',
                'payment', 'checkout', 'cart', 'order', 'invoice',
                'report', 'dashboard', 'analytics', 'search', 'filter',
                'notification', 'email', 'sms', 'message',
                'file', 'upload', 'download', 'export', 'import',
                'settings', 'configuration', 'admin', 'profile',
                'security', 'permission', 'access', 'role',
            ]
            cnt = Counter()
            for _, row in self.df.iterrows():
                s = str(row[summary_col]).lower()
                for kw in keywords:
                    if kw in s:
                        cnt[kw.capitalize()] += 1
                        break
            module_dist = dict(cnt.most_common(10))

        # defect grouping
        groups = defaultdict(list)
        group_keywords = [
            'login', 'password', 'authentication', 'timeout', 'connection',
            'error', 'crash', 'performance', 'slow', 'loading', 'display',
            'button', 'link', 'navigation', 'search', 'filter', 'save',
            'delete', 'update', 'create', 'validation', 'format', 'data',
            'database', 'api', 'integration', 'email', 'notification',
            'uploaded', 'upload', 'schedule', 'server', 'user', 'message',
        ]
        if id_col and summary_col and sev_col:
            for _, row in self.df.iterrows():
                s   = str(row[summary_col]).lower()
                did = str(row[id_col])
                sev = str(row[sev_col])
                mod = str(row[module_col]) if module_col and module_col in self.df.columns else 'General'
                matched = [kw for kw in group_keywords if kw in s]
                if matched:
                    gkey = f"{mod}_{matched[0]}"
                else:
                    words = re.findall(r'\b\w{5,}\b', s)
                    gkey = f"{mod}_{words[0]}" if words else f"{mod}_other"
                groups[gkey].append({
                    'id': did, 'summary': str(row[summary_col]),
                    'severity': sev, 'module': mod,
                })

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

        # pattern name map
        pattern_name_map = {
            'error':      'Error Handling',
            'display':    'Display / Rendering',
            'update':     'Role / Update',
            'uploaded':   'File Upload',
            'upload':     'File Handling',
            'schedule':   'Scheduling',
            'server':     'Server',
            'user':       'User Mgmt',
            'validation': 'Input Validation',
            'password':   'Security',
        }

        # 5 Whys templates
        five_whys_map = {
            'error': {
                'title': 'Error Handling',
                'w': [
                    ('Why errors occur?',           'Errors not properly caught and handled in application layer'),
                    ('Why not handled?',             'No standardised error handling framework across modules'),
                    ('Why no framework?',            'Error handling patterns were never formally established'),
                    ('Why not established?',         'Error handling requirements were not documented in design phase'),
                    ('Why not documented?',          'Architecture review did not include exception management strategy'),
                ],
                'root': 'Lack of error handling architecture and exception management strategy',
            },
            'display': {
                'title': 'Display & Rendering',
                'w': [
                    ('Why display issues?',          'UI rendering incorrectly across navigation and different locales'),
                    ('Why incorrect?',               'CSS and layout not tested across browsers/devices/locales'),
                    ('Why not tested?',              'No cross-browser / locale testing strategy defined'),
                    ('Why no strategy?',             'UI/UX requirements did not comprehensively cover locale scenarios'),
                    ('Why gaps in requirements?',    'Responsive design and encoding guidelines were never formalised'),
                ],
                'root': 'Lack of responsive design guidelines and visual regression / locale testing',
            },
            'update': {
                'title': 'Role / Access Control',
                'w': [
                    ('Why role-based failures?',     'Access control logic has unhandled non-admin permission paths'),
                    ('Why unhandled?',               'Permission matrix not fully implemented for all roles'),
                    ('Why not implemented?',         'Role-based requirements were incompletely specified'),
                    ('Why incomplete?',              'Security review did not cover all role/permission combinations'),
                    ('Why not covered?',             'Lack of access-control test matrix in QA process'),
                ],
                'root': 'Incomplete role-based access control specification and security test coverage',
            },
            'uploaded': {
                'title': 'File Upload / Handling',
                'w': [
                    ('Why file issues?',             'File content and metadata not validated after upload'),
                    ('Why not validated?',           'No server-side file integrity checks implemented'),
                    ('Why no checks?',               'File handling requirements did not include content validation'),
                    ('Why incomplete requirements?', 'File upload edge cases not considered in design'),
                    ('Why not considered?',          'Lack of file processing testing framework'),
                ],
                'root': 'Lack of file validation framework and upload integrity testing',
            },
            'validation': {
                'title': 'Input Validation',
                'w': [
                    ('Why validation failures?',     'Input validation is inconsistent or missing across screens'),
                    ('Why inconsistent?',            'No centralised validation framework used'),
                    ('Why no framework?',            'Validation logic scattered across individual components'),
                    ('Why scattered?',               'No validation design pattern established at architecture level'),
                    ('Why no pattern?',              'Input validation strategy not included in coding standards'),
                ],
                'root': 'Lack of centralised input validation framework and data integrity strategy',
            },
        }

        # HTML helpers
        def esc(s):
            return html_lib.escape(str(s))

        def sev_badge(sev):
            sl = sev.lower()
            if 'kritisk' in sl or '1 -' in sl or 'critical' in sl or 'high' in sl:
                return f'<span class="badge badge-crit">{esc(sev)}</span>'
            return f'<span class="badge badge-high">{esc(sev)}</span>'

        def bar_rows_html(dist, max_val=None):
            rows = ''
            mv = max_val or (max(dist.values()) if dist else 1)
            for i, (label, cnt) in enumerate(dist.items()):
                pct = round(cnt / mv * 100, 1)
                cls = '' if i < 2 else ' sec'
                rows += (
                    f'    <div class="bar-row">'
                    f'<span class="bar-label">{esc(label)}</span>'
                    f'<div class="bar-track"><div class="bar-fill{cls}" style="width:{pct}%"></div></div>'
                    f'<span class="bar-count">{cnt}</span>'
                    f'</div>\n'
                )
            return rows

        # severity table rows
        sev_rows = ''
        for sev, cnt in sev_dist.items():
            pct = round(cnt / total * 100, 1) if total else 0
            sl  = sev.lower()
            col = '#dc2626' if ('kritisk' in sl or '1 -' in sl or 'critical' in sl) else '#d97706'
            sev_rows += (
                f'      <tr><td>{sev_badge(sev)}</td><td>{cnt}</td><td>{pct}%</td>'
                f'<td><div class="bar-track" style="height:10px">'
                f'<div class="bar-fill" style="width:{pct}%;background:{col}"></div>'
                f'</div></td></tr>\n'
            )

        # cluster table rows
        cluster_rows = ''
        for g in grouped:
            kw  = g['group_key'].split('_')[-1]
            pn  = pattern_name_map.get(kw, kw.capitalize())
            sim = ', '.join(g['similar_defects'][:8])
            pill_cls = 'pill' if g['group_size'] > 1 else 'pill-1'
            cluster_rows += (
                f'      <tr>'
                f'<td><strong>{esc(pn)}</strong><br>'
                f'<span style="font-size:11px;color:#57606a">{esc(g["group_key"])}</span></td>'
                f'<td>{esc(g["id"])}</td>'
                f'<td><span class="{pill_cls}">{g["group_size"]}</span></td>'
                f'<td>{sev_badge(g["severity"])}</td>'
                f'<td style="font-size:11px">{esc(sim)}</td>'
                f'<td style="font-size:12px">{esc(g["summary"][:100])}</td>'
                f'</tr>\n'
            )

        # standalone table rows
        standalone_rows = ''
        for s in standalone:
            standalone_rows += (
                f'      <tr><td>{esc(s["id"])}</td>'
                f'<td>{sev_badge(s["severity"])}</td>'
                f'<td style="font-size:12px">{esc(s["summary"][:120])}</td></tr>\n'
            )

        # pattern cards
        pattern_bullets_map = {
            'error': [
                'Incorrect / misleading error messages shown to users',
                'Validation errors triggered at wrong thresholds',
                'No standardised exception messages across screens',
                'Errors not distinguishing field-level from system-level issues',
            ],
            'display': [
                'Danish / special characters rendered incorrectly',
                'UTF-8 encoding breaks after screen navigation',
                'Text overflow / overlapping in list views',
                'No cross-browser / locale regression tests in place',
            ],
            'update': [
                'Non-Admin role bypass for sequence / job updates',
                'Insufficient permission checks on update operations',
                'CHANGESEQUENCE/CHANGEJOBS flags not respected',
            ],
            'uploaded': [
                'Blank content after file upload; job runs silently',
                'MIME type not validated on upload',
                'Uploaded file details not persisted correctly',
            ],
            'validation': [
                'Special characters accepted in restricted fields',
                'Special characters blocked in fields that allow them',
                'Incorrect job order accepted by system',
            ],
        }
        pattern_cards_html = ''
        for g in grouped[:6]:
            kw      = g['group_key'].split('_')[-1]
            pn      = pattern_name_map.get(kw, kw.capitalize()) + ' Pattern'
            bullets = pattern_bullets_map.get(kw, [
                f'Multiple defects with "{kw}" keyword detected',
                'Review related code paths for similar issues',
                'Add regression tests for this area',
            ])
            note = (f"{g['group_size']} defects  |  Largest cluster"
                    if g is grouped[0] else f"{g['group_size']} defects")
            lis = ''.join(f'<li>{esc(b)}</li>' for b in bullets)
            pattern_cards_html += (
                f'    <div class="pattern-card">'
                f'<div class="ptitle">{esc(pn)}</div>'
                f'<div class="pcount">{note}</div>'
                f'<ul>{lis}</ul>'
                f'</div>\n'
            )

        # 5 Whys blocks
        five_whys_html = ''
        seen_kws = set()
        fallback = ['error', 'display', 'update', 'uploaded']
        fb_idx = 0
        for i, g in enumerate(grouped[:4], 1):
            kw = g['group_key'].split('_')[-1]
            if kw in seen_kws or kw not in five_whys_map:
                while fb_idx < len(fallback) and fallback[fb_idx] in seen_kws:
                    fb_idx += 1
                kw = fallback[fb_idx] if fb_idx < len(fallback) else 'error'
                fb_idx += 1
            seen_kws.add(kw)
            fw = five_whys_map.get(kw, five_whys_map['error'])
            rows_html = ''.join(
                f'    <div class="why-row">'
                f'<span class="why-q">Why {j}: {esc(q)}</span>'
                f'<span class="why-a">{esc(a)}</span>'
                f'</div>\n'
                for j, (q, a) in enumerate(fw['w'], 1)
            )
            mt = ' style="margin-top:12px"' if i > 1 else ''
            five_whys_html += (
                f'  <div class="whys-block"{mt}>\n'
                f'    <div class="category-title">Pattern {i} \u2014 {esc(fw["title"])}'
                f'  <span style="font-weight:400;color:#57606a;font-size:12px">'
                f'({g["group_size"]} defects affected)</span></div>\n'
                + rows_html +
                f'    <div class="root-cause-row">'
                f'<span class="rc-label">Root Cause:</span>'
                f'<span class="rc-val">{esc(fw["root"])}</span>'
                f'</div>\n'
                f'  </div>\n'
            )

        # preventive measure lists
        immediate_items = [
            'Implement comprehensive error handling framework with standardised user-facing messages',
            'Add user-friendly, field-level error messages across all screens',
            'Implement error logging and monitoring (centralised log aggregation)',
            'Implement visual regression testing and cross-browser compatibility checks',
            'Review CSS and layout implementations for locale/character encoding correctness',
            'Fix role-based access control gaps',
            'Mask sensitive data in job logs immediately',
            'Add MIME-type and file-content validation on upload',
        ]
        longterm_items = [
            'Establish comprehensive automated test framework covering critical paths and regression',
            'Implement continuous integration with automated lint, unit, and integration tests',
            'Conduct mandatory code reviews with focus on error handling and security',
            'Define and enforce responsive design and internationalisation (i18n) standards',
            'Implement continuous monitoring and alerting for production anomalies',
            'Provide team training on best practices for error handling and access control',
            'Document lessons learned and update coding standards after each release',
            'Establish design review checkpoints and quality gates before each release',
        ]
        top_modules = ', '.join(list(module_dist.keys())[:3]) if module_dist else 'key modules'
        general_items = [
            'Conduct regular code reviews focusing on identified problem areas',
            f'Implement automated testing for high-defect modules ({top_modules})',
            'Establish coding standards and best-practices documentation',
            'Conduct knowledge-sharing sessions on common defect patterns',
            'Implement continuous integration with automated testing pipeline',
        ]

        def ol_html(items):
            return (
                '  <ol class="rec-list">\n'
                + ''.join(f'    <li>{esc(it)}</li>\n' for it in items)
                + '  </ol>\n'
            )

        gen_ts    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gen_date  = gen_ts[:10]
        short_sid = session_id[:8]
        grp_total = sum(g['group_size'] for g in grouped)

        lines = []
        lines.append('<!DOCTYPE html>')
        lines.append('<html lang="en">')
        lines.append('<head>')
        lines.append('<meta charset="UTF-8" />')
        lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0" />')
        lines.append(f'<title>RCA Summary Report \u2013 {esc(project)}</title>')
        lines.append('<style>')
        lines.append('  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }')
        lines.append('  body { font-family: -apple-system, "Segoe UI", system-ui, sans-serif;')
        lines.append('    font-size: 14px; line-height: 1.6; color: #1f2328; background: #f7f8fa; }')
        lines.append('  .page { max-width: 760px; margin: 0 auto; background: #fff; padding: 40px 48px 48px; }')
        lines.append('  .report-header { border-bottom: 2px solid #3b82d4; padding-bottom: 18px; margin-bottom: 28px; }')
        lines.append('  .report-header h1 { font-size: 22px; font-weight: 700; color: #1f2328; letter-spacing: -0.3px; }')
        lines.append('  .report-header .sub { font-size: 12px; color: #57606a; margin-top: 4px; }')
        lines.append('  .report-header .meta { display: flex; gap: 24px; margin-top: 10px; font-size: 12px; color: #57606a; }')
        lines.append('  .report-header .meta span strong { color: #1f2328; }')
        lines.append('  .print-btn { float: right; margin-top: -4px; background: #3b82d4; color: #fff; border: none;')
        lines.append('    border-radius: 4px; padding: 6px 14px; font-size: 12px; cursor: pointer; font-family: inherit; }')
        lines.append('  h2 { font-size: 15px; font-weight: 700; color: #1f2328; margin: 28px 0 12px;')
        lines.append('    padding-bottom: 5px; border-bottom: 1px solid #e5e7eb; }')
        lines.append('  h3 { font-size: 13px; font-weight: 600; color: #1f2328; margin: 16px 0 6px; }')
        lines.append('  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 8px; }')
        lines.append('  .card { background: #f7f8fa; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 12px; text-align: center; }')
        lines.append('  .card .val { font-size: 26px; font-weight: 700; color: #3b82d4; line-height: 1.2; }')
        lines.append('  .card.red .val { color: #dc2626; } .card.green .val { color: #16a34a; } .card.amber .val { color: #d97706; }')
        lines.append('  .card .lbl { font-size: 11px; color: #57606a; margin-top: 3px; }')
        lines.append('  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }')
        lines.append('  th { background: #f7f8fa; text-align: left; font-weight: 600; padding: 8px 10px;')
        lines.append('    border: 1px solid #e5e7eb; color: #1f2328; font-size: 12px; }')
        lines.append('  td { padding: 7px 10px; border: 1px solid #e5e7eb; vertical-align: top; }')
        lines.append('  tr:nth-child(even) td { background: #fafafa; }')
        lines.append('  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }')
        lines.append('  .badge-crit { background: #fee2e2; color: #991b1b; }')
        lines.append('  .badge-high { background: #fef3c7; color: #92400e; }')
        lines.append('  .pill { display: inline-block; min-width: 22px; text-align: center; padding: 1px 7px;')
        lines.append('    border-radius: 10px; font-size: 11px; font-weight: 700; background: #dbeafe; color: #1d4ed8; }')
        lines.append('  .pill-1 { background: #f3f4f6; color: #6b7280; }')
        lines.append('  .bar-wrap { margin-top: 10px; }')
        lines.append('  .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; }')
        lines.append('  .bar-label { width: 90px; text-align: right; color: #57606a; flex-shrink: 0; }')
        lines.append('  .bar-track { flex: 1; background: #f3f4f6; border-radius: 3px; height: 14px; overflow: hidden; }')
        lines.append('  .bar-fill { height: 100%; background: #3b82d4; border-radius: 3px; }')
        lines.append('  .bar-fill.sec { background: #7c5cd8; }')
        lines.append('  .bar-count { width: 22px; font-weight: 600; color: #1f2328; flex-shrink: 0; font-size: 12px; }')
        lines.append('  .pattern-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }')
        lines.append('  .pattern-card { border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px; background: #fafafa; }')
        lines.append('  .pattern-card .ptitle { font-weight: 700; font-size: 13px; color: #1f2328; margin-bottom: 6px; }')
        lines.append('  .pattern-card .pcount { font-size: 11px; color: #57606a; margin-bottom: 8px; }')
        lines.append('  .pattern-card ul { padding-left: 16px; font-size: 12px; color: #1f2328; }')
        lines.append('  .pattern-card ul li { margin-bottom: 2px; }')
        lines.append('  .whys-block { background: #f7f8fa; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 16px; margin-top: 10px; }')
        lines.append('  .whys-block .category-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; color: #1f2328; }')
        lines.append('  .why-row { display: flex; gap: 10px; margin-bottom: 8px; font-size: 12px; align-items: flex-start; }')
        lines.append('  .why-q { min-width: 160px; font-weight: 600; color: #3b82d4; flex-shrink: 0; }')
        lines.append('  .why-a { color: #1f2328; }')
        lines.append('  .root-cause-row { display: flex; gap: 10px; font-size: 12px; margin-top: 6px; padding-top: 8px;')
        lines.append('    border-top: 1px dashed #e5e7eb; align-items: flex-start; }')
        lines.append('  .root-cause-row .rc-label { min-width: 160px; font-weight: 700; color: #dc2626; flex-shrink: 0; }')
        lines.append('  .root-cause-row .rc-val { color: #1f2328; font-weight: 600; }')
        lines.append('  .rec-list { padding-left: 18px; font-size: 13px; }')
        lines.append('  .rec-list li { margin-bottom: 4px; }')
        lines.append('  .footer { margin-top: 40px; padding-top: 14px; border-top: 1px solid #e5e7eb;')
        lines.append('    text-align: center; font-size: 11px; color: #57606a; }')
        lines.append('  @media print {')
        lines.append('    body { background: #fff; } .page { padding: 20px 24px; } .print-btn { display: none; }')
        lines.append('    h2 { page-break-after: avoid; } .whys-block, .pattern-card { page-break-inside: avoid; }')
        lines.append('  }')
        lines.append('</style>')
        lines.append('<script>')
        lines.append("  document.addEventListener('DOMContentLoaded', function() {")
        lines.append("    var btn = document.querySelector('.print-btn');")
        lines.append("    if (btn) btn.addEventListener('click', function() { window.print(); });")
        lines.append('  });')
        lines.append('</script>')
        lines.append('</head>')
        lines.append('<body>')
        lines.append('<div class="page">')
        lines.append('')
        lines.append('  <div class="report-header">')
        lines.append('    <button class="print-btn">Print / Save PDF</button>')
        lines.append('    <h1>Root Cause Analysis &#8211; Summary Report</h1>')
        lines.append(f'    <div class="sub">ALM RCA Web Application &nbsp;|&nbsp; Session: {esc(session_id)}</div>')
        lines.append('    <div class="meta">')
        lines.append(f'      <span><strong>Generated:</strong> {esc(gen_ts)}</span>')
        lines.append(f'      <span><strong>Project:</strong> {esc(project)}</span>')
        lines.append(f'      <span><strong>Status:</strong> {esc(status_label)}</span>')
        lines.append('    </div>')
        lines.append('  </div>')
        lines.append('')
        lines.append('  <h2>Executive Summary</h2>')
        lines.append('  <div class="cards">')
        lines.append(f'    <div class="card"><div class="val">{total}</div><div class="lbl">Total Defects</div></div>')
        lines.append(f'    <div class="card green"><div class="val">{closed}</div><div class="lbl">Closed</div></div>')
        lines.append(f'    <div class="card"><div class="val">{open_}</div><div class="lbl">Open</div></div>')
        lines.append(f'    <div class="card red"><div class="val">{crit}</div><div class="lbl">Critical Severity</div></div>')
        lines.append('  </div>')
        lines.append('')
        lines.append('  <h2>Severity Distribution</h2>')
        lines.append('  <table>')
        lines.append('    <thead><tr><th>Severity</th><th>Count</th><th>Percentage</th><th>Visual</th></tr></thead>')
        lines.append(f'    <tbody>\n{sev_rows}    </tbody>')
        lines.append('  </table>')
        lines.append('')
        lines.append('  <h2>Module Distribution</h2>')
        lines.append('  <div class="bar-wrap">')
        lines.append(bar_rows_html(module_dist) + '  </div>')
        lines.append('')
        lines.append('  <h2>Defect Grouping &amp; Clustering</h2>')
        lines.append(f'  <p style="font-size:12px;color:#57606a;margin-bottom:10px">')
        lines.append(f'    {total} defects were clustered into <strong>{len(grouped)} groups</strong>')
        lines.append(f'    ({grp_total} defects) and <strong>{len(standalone)} standalone</strong> defects based on keyword similarity.')
        lines.append('  </p>')
        lines.append('  <table>')
        lines.append('    <thead>')
        lines.append('      <tr><th>Group</th><th>Lead Defect ID</th><th>Size</th><th>Severity</th><th>Similar Defect IDs</th><th>Summary (Lead)</th></tr>')
        lines.append('    </thead>')
        lines.append(f'    <tbody>\n{cluster_rows}    </tbody>')
        lines.append('  </table>')
        lines.append('')
        lines.append(f'  <h3 style="margin-top:20px">Standalone Defects ({len(standalone)})</h3>')
        lines.append('  <p style="font-size:12px;color:#57606a;margin-bottom:6px">Each of these defects has no close keyword-match sibling in the dataset.</p>')
        lines.append('  <table>')
        lines.append('    <thead><tr><th>ID</th><th>Severity</th><th>Summary</th></tr></thead>')
        lines.append(f'    <tbody>\n{standalone_rows}    </tbody>')
        lines.append('  </table>')
        lines.append('')
        lines.append('  <h2>Patterns Detected</h2>')
        lines.append('  <div class="pattern-grid">')
        lines.append(pattern_cards_html + '  </div>')
        lines.append('')
        lines.append('  <h2>5-Whys Root Cause Analysis</h2>')
        lines.append('')
        lines.append(five_whys_html)
        lines.append('  <h2>Preventive Measures</h2>')
        lines.append('')
        lines.append('  <h3>Immediate Actions (Next Sprint)</h3>')
        lines.append(ol_html(immediate_items))
        lines.append('  <h3 style="margin-top:16px">Long-term Prevention (3&#8211;6 Months)</h3>')
        lines.append(ol_html(longterm_items))
        lines.append('')
        lines.append('  <h2>General Best Practices</h2>')
        lines.append(ol_html(general_items))
        lines.append('')
        lines.append('  <div class="footer">')
        lines.append(f'    <p>Report generated by the ALM RCA Web Application &nbsp;&middot;&nbsp; Session {esc(short_sid)}&hellip; &nbsp;&middot;&nbsp; {esc(gen_date)}</p>')
        lines.append('    <p style="margin-top:4px">Made with IBM Bob</p>')
        lines.append('  </div>')
        lines.append('')
        lines.append('</div>')
        lines.append('</body>')
        lines.append('</html>')

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return report_file

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
            open_  = len(self.df[self.df[status_col].astype(str).str.contains('Open',   case=False, na=False)])
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

        # ── executive summary cards ───────────────────────────────────────────
        story.append(Paragraph('Executive Summary', sty['h2']))
        cards_data = [
            [
                Paragraph(f'<font size="20" color="{C_ACCENT.hexval()}"><b>{total}</b></font>', sty['body']),
                Paragraph(f'<font size="20" color="{C_GREEN.hexval()}"><b>{closed}</b></font>', sty['body']),
                Paragraph(f'<font size="20" color="{C_TEXT.hexval()}"><b>{open_}</b></font>', sty['body']),
                Paragraph(f'<font size="20" color="{C_RED.hexval()}"><b>{crit}</b></font>', sty['body']),
            ],
            [
                Paragraph('<font size="7" color="#57606a">Total Defects</font>', sty['body']),
                Paragraph('<font size="7" color="#57606a">Closed</font>', sty['body']),
                Paragraph('<font size="7" color="#57606a">Open</font>', sty['body']),
                Paragraph('<font size="7" color="#57606a">Critical Severity</font>', sty['body']),
            ],
        ]
        col_w = W / 4
        cards_tbl = Table(cards_data, colWidths=[col_w]*4, rowHeights=[18, 10])
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
        story.append(Paragraph(
            f'Report generated by the ALM RCA Web Application &nbsp;·&nbsp; '
            f'Session {short_sid}… &nbsp;·&nbsp; {gen_date}',
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
    
    def _find_column(self, possible_names):
        """Find column by trying multiple possible names"""
        if self.df is None:
            return None
        for name in possible_names:
            if name in self.df.columns:
                return name
        return None

# Made with Bob
