"""
Defect Analyzer - Adapted for web application
"""

import pandas as pd
from datetime import datetime
from collections import Counter
import warnings
warnings.filterwarnings('ignore')


class DefectAnalyzer:
    def __init__(self, data_file):
        """Initialize the analyzer with defect data file"""
        self.data_file = data_file
        self.df = None
        self.analysis_results = {}
        
    def load_data(self):
        """Load defect data from CSV or Excel file"""
        try:
            if self.data_file.endswith('.csv'):
                encodings = ['utf-16', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                delimiters = ['\t', ',', ';']
                
                for encoding in encodings:
                    for delimiter in delimiters:
                        try:
                            self.df = pd.read_csv(
                                self.data_file, 
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
            elif self.data_file.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(self.data_file)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def run_analysis(self):
        """Run complete analysis and return results"""
        if self.df is None:
            return {'error': 'No data loaded'}
        
        results = {
            'generated_at': datetime.now().isoformat(),
            'total_defects': len(self.df),
            'summary': {},
            'severity_distribution': {},
            'status_distribution': {},
            'module_distribution': {},
            'defect_types': {},
            'root_causes': {},
            'monthly_trend': {},
            'high_risk_areas': {},
            'rca_candidates': []
        }
        
        # Find columns flexibly
        status_col = self._find_column(['Status', 'status', 'State'])
        sev_col = self._find_column(['Severity', 'severity', 'Priority'])
        module_col = self._find_column(['Module', 'Component', 'module', 'Area'])
        rc_col = self._find_column(['Root_Cause', 'RootCause', 'root_cause'])
        type_col = self._find_column(['Defect_Type', 'DefectType', 'Type', 'Category'])
        date_col = self._find_column(['Detected_Date', 'DetectedDate', 'Created_Date', 'Date'])
        id_col = self._find_column(['Id', 'ID', 'Defect_ID', 'DefectID'])
        summary_col = self._find_column(['Summary', 'summary', 'Title', 'Description'])
        
        # Basic statistics
        if status_col:
            open_count = len(self.df[self.df[status_col].astype(str).str.contains('Open', case=False, na=False)])
            closed_count = len(self.df[self.df[status_col].astype(str).str.contains('Closed', case=False, na=False)])
            results['summary']['open'] = open_count
            results['summary']['closed'] = closed_count
            results['status_distribution'] = self.df[status_col].value_counts().to_dict()
        
        if sev_col:
            high_sev = len(self.df[self.df[sev_col].astype(str).str.contains(
                'Kritisk|1 -|High|Critical', case=False, na=False)])
            results['summary']['high_severity'] = high_sev
            results['severity_distribution'] = self.df[sev_col].value_counts().to_dict()
        
        # Module distribution - use actual column if available, otherwise extract from summaries
        if module_col:
            results['module_distribution'] = self.df[module_col].value_counts().head(10).to_dict()
        elif summary_col:
            # Extract modules/areas from summaries using keyword grouping (same as defect grouping)
            module_distribution = self._extract_modules_from_summaries(summary_col)
            if module_distribution:
                results['module_distribution'] = module_distribution
        
        if type_col:
            results['defect_types'] = self.df[type_col].value_counts().to_dict()
        
        if rc_col:
            df_with_rc = self.df[self.df[rc_col].notna() & (self.df[rc_col] != '')]
            if len(df_with_rc) > 0:
                results['root_causes'] = df_with_rc[rc_col].value_counts().to_dict()
        
        # Trend analysis
        if date_col:
            try:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                self.df['Month'] = self.df[date_col].dt.to_period('M')
                monthly_counts = self.df.groupby('Month').size()
                results['monthly_trend'] = {str(k): int(v) for k, v in monthly_counts.to_dict().items()}
            except:
                pass
        
        # High-risk areas
        if sev_col:
            high_risk_df = self.df[self.df[sev_col].astype(str).str.contains(
                'Kritisk|1 -|High|Critical', case=False, na=False)]
            if len(high_risk_df) > 0 and module_col:
                high_risk_modules = high_risk_df[module_col].value_counts().head(5)
                results['high_risk_areas'] = high_risk_modules.to_dict()
        
        # RCA candidates with grouping - Critical, High, and Medium severity (exclude cosmetic/low)
        if sev_col:
            # Select Critical, High, and Medium severity defects (exclude Low, Cosmetic, 4-, 5-)
            high_sev_mask = self.df[sev_col].astype(str).str.contains(
                'Kritisk|1 -|High|Critical|2 -|Medium|3 -|3', case=False, na=False)
            
            # Explicitly exclude cosmetic and low severity
            cosmetic_mask = self.df[sev_col].astype(str).str.contains(
                'Cosmetic|Low|4 -|5 -|Trivial|Minor', case=False, na=False)
            high_sev_mask = high_sev_mask & ~cosmetic_mask
            
            if rc_col:
                no_rc_mask = (self.df[rc_col].isna()) | (self.df[rc_col] == '')
                rca_df = self.df[high_sev_mask & no_rc_mask]
            else:
                rca_df = self.df[high_sev_mask]
            
            if len(rca_df) > 0 and id_col and summary_col:
                # Group defects by similarity
                all_grouped = self._group_similar_defects(rca_df, summary_col, id_col, sev_col, module_col)
                
                # Ensure all_grouped is a list
                if all_grouped is None:
                    all_grouped = []
                
                # Show all high-severity defects, but prioritize those with similar defects
                # Sort by group_size (descending) so grouped defects appear first
                all_grouped.sort(key=lambda x: (-x.get('group_size', 0), x.get('severity', '')))
                
                # Separate grouped and standalone for statistics
                grouped_defects = [g for g in all_grouped if g.get('group_size', 0) >= 2]
                standalone_defects = [g for g in all_grouped if g.get('group_size', 0) == 1]
                
                # Generate preventive measures based on grouped defects
                # If no grouped defects, still generate general measures
                if len(grouped_defects) > 0:
                    preventive_measures = self._generate_preventive_measures(grouped_defects)
                else:
                    # Generate general preventive measures even without patterns
                    preventive_measures = [{
                        'category': 'General Best Practices',
                        'icon': '📋',
                        'measures': [
                            'Conduct regular code reviews focusing on defect-prone areas',
                            'Implement comprehensive automated testing',
                            'Establish coding standards and best practices documentation',
                            'Conduct knowledge sharing sessions on common issues',
                            'Implement continuous integration with automated testing',
                            'Review and update testing strategies regularly',
                            'Implement peer review process for critical changes',
                            'Maintain detailed documentation of known issues and solutions'
                        ]
                    }]
                
                # Show all defects in RCA candidates (grouped first, then standalone)
                results['rca_candidates'] = all_grouped
                results['total_rca_defects'] = len(rca_df)
                results['grouped_count'] = len(grouped_defects)
                results['standalone_count'] = len(standalone_defects)
                results['preventive_measures'] = preventive_measures
        
        self.analysis_results = results
        return results
    
    def _find_column(self, possible_names):
        """Find column by trying multiple possible names"""
        if self.df is None:
            return None
        for name in possible_names:
            if name in self.df.columns:
                return name
        return None
    
    def _extract_modules_from_summaries(self, summary_col):
        """Extract module/area names from defect summaries using keyword matching"""
        from collections import Counter
        import re
        
        # Common module/area keywords to look for
        module_keywords = [
            'login', 'authentication', 'auth', 'password', 'user',
            'database', 'db', 'data', 'api', 'interface',
            'ui', 'frontend', 'backend', 'server', 'client',
            'payment', 'checkout', 'cart', 'order', 'invoice',
            'report', 'dashboard', 'analytics', 'search', 'filter',
            'notification', 'email', 'sms', 'message',
            'file', 'upload', 'download', 'export', 'import',
            'settings', 'configuration', 'admin', 'profile',
            'security', 'permission', 'access', 'role'
        ]
        
        module_counts = Counter()
        
        for _, row in self.df.iterrows():
            summary = str(row[summary_col]).lower()
            
            # Find matching keywords in summary
            for keyword in module_keywords:
                if keyword in summary:
                    # Capitalize first letter for display
                    module_name = keyword.capitalize()
                    module_counts[module_name] += 1
                    break  # Only count first match per defect
        
        # Return top 10 modules
        if module_counts:
            return dict(module_counts.most_common(10))
        return {}

# Made with Bob

    
    def _group_similar_defects(self, df, summary_col, id_col, sev_col, module_col):
        """Group similar defects and select representatives for RCA"""
        from collections import defaultdict
        import re
        
        # Group defects by keywords in summary
        groups = defaultdict(list)
        
        # Common keywords to group by
        keywords = [
            'login', 'password', 'authentication', 'timeout', 'connection',
            'error', 'crash', 'performance', 'slow', 'loading', 'display',
            'button', 'link', 'navigation', 'search', 'filter', 'save',
            'delete', 'update', 'create', 'validation', 'format', 'data',
            'database', 'api', 'integration', 'email', 'notification'
        ]
        
        for _, row in df.iterrows():
            summary = str(row[summary_col]).lower()
            defect_id = str(row[id_col])
            severity = str(row[sev_col]) if sev_col else 'N/A'
            module = str(row[module_col]) if module_col and module_col in df.columns else 'General'
            
            # Find matching keywords
            matched_keywords = [kw for kw in keywords if kw in summary]
            
            # Group by module + primary keyword
            if matched_keywords:
                group_key = f"{module}_{matched_keywords[0]}"
            else:
                # Extract first significant word (>4 chars)
                words = re.findall(r'\b\w{5,}\b', summary)
                group_key = f"{module}_{words[0]}" if words else f"{module}_other"
            
            groups[group_key].append({
                'id': defect_id,
                'summary': str(row[summary_col])[:100],
                'severity': severity,
                'module': module,
                'full_summary': str(row[summary_col])
            })
        
        # Select representative defects from each group
        representatives = []
        for group_key, defects in groups.items():
            # Sort by severity (Critical/High first)
            defects.sort(key=lambda x: (
                0 if 'critical' in x['severity'].lower() or 'kritisk' in x['severity'].lower() or '1' in x['severity']
                else 1 if 'high' in x['severity'].lower() or '2' in x['severity']
                else 2
            ))
            
            # Take the most severe defect as representative
            representative = defects[0].copy()
            representative['group_size'] = len(defects)
            representative['group_key'] = group_key
            
            # Add similar defect IDs
            if len(defects) > 1:
                representative['similar_defects'] = [d['id'] for d in defects[1:]]
                representative['similar_count'] = len(defects) - 1
            else:
                representative['similar_defects'] = []
                representative['similar_count'] = 0
            
            representatives.append(representative)
        
        # Sort representatives by group size (largest groups first) and severity
        representatives.sort(key=lambda x: (-x['group_size'], x['severity']))
        
        return representatives
    
    def _generate_five_whys(self, category, defect_summaries=None):
        """Generate 5 WHYs analysis for a defect category.

        When defect_summaries are provided and an LLM provider is configured
        (via WATSONX_API_KEY or OPENAI_API_KEY env vars), the analysis is
        generated by the LLM using the actual defect text.  Falls back to the
        static templates when no provider is available or the call fails.
        """
        # ── LLM path ──────────────────────────────────────────────────────────
        if defect_summaries:
            try:
                from app.utils.llm_five_whys import generate_five_whys_llm
                llm_result = generate_five_whys_llm(category, defect_summaries)
                if llm_result is not None:
                    return llm_result
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "LLM 5-Whys unavailable, using template fallback: %s", exc
                )

        # ── static template fallback ──────────────────────────────────────────
        five_whys_templates = {
            'login': {
                'why1': 'Why are login issues occurring?',
                'answer1': 'Authentication flow has multiple failure points',
                'why2': 'Why does authentication have multiple failure points?',
                'answer2': 'Insufficient validation and error handling in login process',
                'why3': 'Why is validation insufficient?',
                'answer3': 'Login requirements were not comprehensively defined',
                'why4': 'Why weren\'t requirements comprehensive?',
                'answer4': 'Edge cases and security scenarios not considered during design',
                'why5': 'Why weren\'t edge cases considered?',
                'root_cause': 'Lack of comprehensive authentication design review and security testing framework'
            },
            'password': {
                'why1': 'Why are password-related issues occurring?',
                'answer1': 'Password handling logic has security vulnerabilities',
                'why2': 'Why does password handling have vulnerabilities?',
                'answer2': 'Security best practices not consistently applied',
                'why3': 'Why aren\'t best practices applied?',
                'answer3': 'No standardized security framework for password management',
                'why4': 'Why is there no security framework?',
                'answer4': 'Security requirements not prioritized in initial design',
                'why5': 'Why weren\'t security requirements prioritized?',
                'root_cause': 'Lack of security-first design approach and password security standards'
            },
            'timeout': {
                'why1': 'Why are timeout issues occurring?',
                'answer1': 'Operations exceeding configured timeout limits',
                'why2': 'Why are operations exceeding limits?',
                'answer2': 'Performance bottlenecks in critical paths',
                'why3': 'Why are there performance bottlenecks?',
                'answer3': 'Code not optimized for performance requirements',
                'why4': 'Why wasn\'t code optimized?',
                'answer4': 'Performance requirements not clearly defined',
                'why5': 'Why weren\'t performance requirements defined?',
                'root_cause': 'Lack of performance testing and optimization strategy'
            },
            'connection': {
                'why1': 'Why are connection issues occurring?',
                'answer1': 'Network connectivity failures and timeouts',
                'why2': 'Why are there connectivity failures?',
                'answer2': 'Insufficient error handling and retry mechanisms',
                'why3': 'Why is error handling insufficient?',
                'answer3': 'Network resilience not designed into the system',
                'why4': 'Why wasn\'t resilience designed in?',
                'answer4': 'Non-functional requirements for reliability not specified',
                'why5': 'Why weren\'t reliability requirements specified?',
                'root_cause': 'Lack of resilience design patterns and network failure testing'
            },
            'database': {
                'why1': 'Why are database issues occurring?',
                'answer1': 'Database operations failing or performing poorly',
                'why2': 'Why are operations failing?',
                'answer2': 'Queries not optimized and connection management issues',
                'why3': 'Why aren\'t queries optimized?',
                'answer3': 'Database design and indexing strategy inadequate',
                'why4': 'Why is the strategy inadequate?',
                'answer4': 'Database performance requirements not analyzed',
                'why5': 'Why weren\'t requirements analyzed?',
                'root_cause': 'Lack of database performance design review and optimization framework'
            },
            'error': {
                'why1': 'Why are error handling issues occurring?',
                'answer1': 'Errors not properly caught and handled',
                'why2': 'Why aren\'t errors properly handled?',
                'answer2': 'No standardized error handling framework',
                'why3': 'Why is there no standard framework?',
                'answer3': 'Error handling patterns not established',
                'why4': 'Why weren\'t patterns established?',
                'answer4': 'Error handling requirements not documented',
                'why5': 'Why weren\'t requirements documented?',
                'root_cause': 'Lack of error handling architecture and exception management strategy'
            },
            'performance': {
                'why1': 'Why are performance issues occurring?',
                'answer1': 'System not meeting performance expectations',
                'why2': 'Why isn\'t system meeting expectations?',
                'answer2': 'Code and algorithms not optimized',
                'why3': 'Why aren\'t they optimized?',
                'answer3': 'Performance testing not conducted during development',
                'why4': 'Why wasn\'t performance testing conducted?',
                'answer4': 'Performance requirements not defined upfront',
                'why5': 'Why weren\'t requirements defined?',
                'root_cause': 'Lack of performance engineering discipline and load testing framework'
            },
            'validation': {
                'why1': 'Why are validation issues occurring?',
                'answer1': 'Input validation is inconsistent or missing',
                'why2': 'Why is validation inconsistent?',
                'answer2': 'No centralized validation framework',
                'why3': 'Why is there no centralized validation?',
                'answer3': 'Validation logic scattered across components',
                'why4': 'Why is validation logic scattered?',
                'answer4': 'No validation design pattern established',
                'why5': 'Why wasn\'t a pattern established?',
                'root_cause': 'Lack of input validation framework and data integrity strategy'
            },
            'button': {
                'why1': 'Why are UI component issues occurring?',
                'answer1': 'UI components not functioning as expected',
                'why2': 'Why aren\'t components functioning correctly?',
                'answer2': 'Event handlers and state management have bugs',
                'why3': 'Why do handlers have bugs?',
                'answer3': 'UI components not thoroughly tested',
                'why4': 'Why weren\'t components tested?',
                'answer4': 'UI testing framework not implemented',
                'why5': 'Why wasn\'t testing framework implemented?',
                'root_cause': 'Lack of UI component testing strategy and automated UI tests'
            },
            'display': {
                'why1': 'Why are display issues occurring?',
                'answer1': 'UI rendering incorrectly across different scenarios',
                'why2': 'Why is rendering incorrect?',
                'answer2': 'CSS and layout not tested across browsers/devices',
                'why3': 'Why wasn\'t it tested?',
                'answer3': 'No cross-browser testing strategy',
                'why4': 'Why is there no testing strategy?',
                'answer4': 'UI/UX requirements not comprehensively defined',
                'why5': 'Why weren\'t requirements defined?',
                'root_cause': 'Lack of responsive design guidelines and visual regression testing'
            },
            'general': {
                'why1': 'Why are defects occurring?',
                'answer1': 'Code quality and testing gaps exist',
                'why2': 'Why do quality gaps exist?',
                'answer2': 'Development processes not consistently followed',
                'why3': 'Why aren\'t processes followed?',
                'answer3': 'Processes not well-defined or enforced',
                'why4': 'Why aren\'t processes well-defined?',
                'answer4': 'Quality standards not established',
                'why5': 'Why weren\'t standards established?',
                'root_cause': 'Lack of quality assurance framework and development best practices'
            }
        }
        
        return five_whys_templates.get(category, five_whys_templates['general'])
    
    def _generate_preventive_measures(self, grouped_defects):
        """Generate preventive measures based on defect patterns"""
        measures = []
        
        # Analyze patterns in grouped defects
        categories = {}
        for group in grouped_defects:
            group_key = group.get('group_key', '')
            module = group.get('module', 'General')
            
            # Extract category from group key
            if '_' in group_key:
                category = group_key.split('_')[1]
            else:
                category = 'general'
            
            if category not in categories:
                categories[category] = {'count': 0, 'modules': set(), 'summaries': []}
            categories[category]['count'] += group['group_size']
            categories[category]['modules'].add(module)
            # Collect defect summaries so the LLM gets real context
            full_summary = group.get('full_summary') or group.get('summary', '')
            if full_summary:
                categories[category]['summaries'].append(full_summary)
            for sid in group.get('similar_defects', []):
                # similar_defects are IDs only; use the group summary as proxy
                if full_summary:
                    categories[category]['summaries'].append(full_summary)
        
        # Generate measures based on categories
        category_measures = {
            'login': {
                'title': 'Authentication & Login Issues',
                'measures': [
                    'Implement comprehensive authentication testing suite',
                    'Add session management validation',
                    'Review password reset and recovery flows',
                    'Implement multi-factor authentication testing',
                    'Add automated login flow regression tests'
                ]
            },
            'password': {
                'title': 'Password & Security',
                'measures': [
                    'Strengthen password validation rules',
                    'Implement secure password storage review',
                    'Add password complexity testing',
                    'Review encryption and hashing mechanisms',
                    'Implement security audit for authentication'
                ]
            },
            'timeout': {
                'title': 'Timeout & Performance',
                'measures': [
                    'Review and optimize timeout configurations',
                    'Implement connection pooling',
                    'Add performance monitoring and alerts',
                    'Optimize database query performance',
                    'Implement caching strategies'
                ]
            },
            'connection': {
                'title': 'Connection & Network Issues',
                'measures': [
                    'Implement connection retry mechanisms',
                    'Add network error handling',
                    'Review API endpoint reliability',
                    'Implement circuit breaker patterns',
                    'Add connection health checks'
                ]
            },
            'database': {
                'title': 'Database Issues',
                'measures': [
                    'Optimize database queries and indexes',
                    'Implement database connection pooling',
                    'Add database performance monitoring',
                    'Review transaction management',
                    'Implement database failover mechanisms'
                ]
            },
            'error': {
                'title': 'Error Handling',
                'measures': [
                    'Implement comprehensive error handling',
                    'Add user-friendly error messages',
                    'Implement error logging and monitoring',
                    'Add error recovery mechanisms',
                    'Review exception handling patterns'
                ]
            },
            'performance': {
                'title': 'Performance Optimization',
                'measures': [
                    'Implement performance testing suite',
                    'Add load testing for critical paths',
                    'Optimize resource-intensive operations',
                    'Implement performance monitoring',
                    'Review and optimize algorithms'
                ]
            },
            'validation': {
                'title': 'Data Validation',
                'measures': [
                    'Implement comprehensive input validation',
                    'Add data format validation',
                    'Review validation rules consistency',
                    'Implement server-side validation',
                    'Add validation error messaging'
                ]
            },
            'button': {
                'title': 'UI Component Issues',
                'measures': [
                    'Implement UI component testing',
                    'Add accessibility testing',
                    'Review event handler implementations',
                    'Implement cross-browser testing',
                    'Add responsive design testing'
                ]
            },
            'display': {
                'title': 'Display & Rendering',
                'measures': [
                    'Implement visual regression testing',
                    'Add cross-browser compatibility testing',
                    'Review CSS and layout implementations',
                    'Implement responsive design validation',
                    'Add device-specific testing'
                ]
            }
        }
        
        # Add general measures
        measures.append({
            'category': 'General Best Practices',
            'icon': '📋',
            'measures': [
                'Conduct regular code reviews focusing on identified problem areas',
                'Implement automated testing for high-defect modules',
                'Establish coding standards and best practices documentation',
                'Conduct knowledge sharing sessions on common defect patterns',
                'Implement continuous integration with automated testing'
            ]
        })
        
        # Add category-specific measures with 5 WHYs
        for category, data in categories.items():
            if category in category_measures:
                measure_info = category_measures[category]
                summaries = data.get('summaries', [])
                five_whys = self._generate_five_whys(category, summaries)
                measures.append({
                    'category': measure_info['title'],
                    'icon': '🛡️',
                    'affected_count': data['count'],
                    'modules': list(data['modules']),
                    'five_whys': five_whys,
                    'measures': measure_info['measures'],
                    'immediate_actions': [
                        measure_info['measures'][0],
                        measure_info['measures'][1],
                        measure_info['measures'][2]
                    ],
                    'long_term_prevention': [
                        'Establish comprehensive testing framework',
                        'Implement continuous monitoring and alerting',
                        'Conduct regular code reviews and audits',
                        'Provide team training on best practices',
                        'Document lessons learned and update standards'
                    ]
                })
        
        # Add module-specific measures if multiple modules affected
        all_modules = set()
        for group in grouped_defects:
            if group.get('module'):
                all_modules.add(group['module'])
        
        if len(all_modules) > 1:
            measures.append({
                'category': 'Module-Specific Actions',
                'icon': '📁',
                'measures': [
                    f'Conduct focused testing on {", ".join(list(all_modules)[:3])} modules',
                    'Review module dependencies and interactions',
                    'Implement module-level integration testing',
                    'Add module-specific monitoring and logging',
                    'Conduct architecture review for high-defect modules'
                ]
            })
        
        return measures
