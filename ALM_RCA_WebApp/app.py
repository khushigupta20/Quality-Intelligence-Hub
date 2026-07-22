"""
ALM RCA Web Application
Web-based interface for uploading defect files and generating RCA analysis
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
import time

# Load .env file if present (never required — falls back gracefully)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; set env vars manually or via shell

from app.utils.analyzer import DefectAnalyzer
from app.utils.report_generator import RCAReportGenerator

# Configure Flask to use the correct template and static folders
app = Flask(__name__,
            template_folder='app/templates',
            static_folder='app/static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main page with file upload interface"""
    # Add timestamp to force browser to reload JS/CSS files
    cache_bust = str(int(time.time()))
    return render_template('index.html', cache_bust=cache_bust)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initiate analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel file'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{session_id}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'filepath': unique_filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Perform defect analysis on uploaded file"""
    try:
        data = request.json
        session_id = data.get('session_id')
        filepath = data.get('filepath')
        
        if not session_id or not filepath:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Initialize analyzer
        analyzer = DefectAnalyzer(full_path)
        
        # Load data
        if not analyzer.load_data():
            return jsonify({'error': 'Failed to load defect data'}), 500
        
        # Run analysis
        results = analyzer.run_analysis()
        
        # Save results to JSON
        output_file = os.path.join(
            app.config['OUTPUT_FOLDER'],
            f'analysis_{session_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'results': results,
            'output_file': os.path.basename(output_file)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """Generate comprehensive RCA reports"""
    try:
        data = request.json
        session_id = data.get('session_id')
        filepath = data.get('filepath')
        
        if not session_id or not filepath:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Initialize report generator
        generator = RCAReportGenerator(full_path, app.config['OUTPUT_FOLDER'])
        
        # Load data
        if not generator.load_data():
            return jsonify({'error': 'Failed to load defect data'}), 500
        
        # Generate reports
        summary_report = generator.generate_summary_report(session_id)
        json_export = generator.export_to_json(session_id)
        
        # Store filenames in session for download
        session['summary_report'] = os.path.basename(summary_report)
        session['json_export'] = os.path.basename(json_export)
        
        return jsonify({
            'success': True,
            'summary_report': os.path.basename(summary_report),
            'json_export': os.path.basename(json_export)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-pdf-report', methods=['POST'])
def generate_pdf_report():
    """Generate a rich PDF summary report"""
    try:
        data = request.json
        session_id = data.get('session_id')
        filepath = data.get('filepath')

        if not session_id or not filepath:
            return jsonify({'error': 'Missing required parameters'}), 400

        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404

        generator = RCAReportGenerator(full_path, app.config['OUTPUT_FOLDER'])

        if not generator.load_data():
            return jsonify({'error': 'Failed to load defect data'}), 500

        pdf_report = generator.generate_pdf_report(session_id)

        return jsonify({
            'success': True,
            'pdf_report': os.path.basename(pdf_report)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated reports"""
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<session_id>')
def view_results(session_id):
    """View analysis results"""
    try:
        # Find the latest analysis file for this session
        files = [f for f in os.listdir(app.config['OUTPUT_FOLDER']) 
                if f.startswith(f'analysis_{session_id}')]
        
        if not files:
            return jsonify({'error': 'No results found for this session'}), 404
        
        # Get the most recent file
        latest_file = sorted(files)[-1]
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], latest_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return render_template('results.html', results=results, session_id=session_id)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions')
def list_sessions():
    """List all analysis sessions"""
    try:
        sessions = []
        
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            if filename.startswith('analysis_') and filename.endswith('.json'):
                filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        'filename': filename,
                        'generated_at': data.get('generated_at'),
                        'total_defects': data.get('total_defects', 0)
                    })
        
        # Sort by date, newest first
        sessions.sort(key=lambda x: x['generated_at'], reverse=True)
        
        return jsonify({'sessions': sessions})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("ALM RCA Web Application")
    print("="*60)
    print("Starting server on http://localhost:5000")
    print("Upload your defect files and get instant RCA analysis!")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made with Bob
