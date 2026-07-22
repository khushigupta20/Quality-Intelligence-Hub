"""
Quality Intelligence Hub
Unified web application: Defect RCA + Requirements Analyzer
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
import time

from app.utils.analyzer import DefectAnalyzer
from app.utils.report_generator import RCAReportGenerator
from app.utils.ica_agent import call_ica_agent
from app.utils.settings import get_settings, save_settings
from app.utils.auth import attempt_login, login_required, get_users, save_user, delete_user

# ── Flask app configuration ───────────────────────────────────────────────────
app = Flask(__name__,
            template_folder='app/templates',
            static_folder='app/static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if the uploaded file extension is permitted."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET'])
def login_page():
    """Serve the login page. Redirect to home if already logged in."""
    if session.get('user'):
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_submit():
    """Handle login form submission."""
    username = (request.form.get('username') or '').strip().lower()
    password = (request.form.get('password') or '')

    settings = get_settings()
    result   = attempt_login(
        username, password,
        ica_endpoint=settings.get('ica_endpoint', ''),
        ica_api_key=settings.get('ica_api_key',  ''),
    )

    if result['success']:
        session['user'] = username
        session['role'] = result.get('role', 'user')
        return redirect(url_for('index'))

    return render_template('login.html',
                           error=result['error'],
                           username=username)


@app.route('/logout', methods=['POST'])
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('login_page'))


# ── Core routes ───────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    """Serve the unified single-page application."""
    cache_bust = str(int(time.time()))
    return render_template('index.html',
                           cache_bust=cache_bust,
                           current_user=session.get('user', ''),
                           current_role=session.get('role', 'user'))


# ── Defect RCA routes ─────────────────────────────────────────────────────────

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle defect file upload and return session metadata."""
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

        # Save uploaded file with unique prefixed name
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
@login_required
def analyze():
    """Run DefectAnalyzer on the uploaded file and return analysis results."""
    try:
        data = request.json
        session_id = data.get('session_id')
        filepath = data.get('filepath')

        if not session_id or not filepath:
            return jsonify({'error': 'Missing required parameters'}), 400

        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404

        settings = get_settings()
        analyzer = DefectAnalyzer(
            full_path,
            watsonx_api_key=settings.get('watsonx_api_key', ''),
            watsonx_project_id=settings.get('watsonx_project_id', ''),
            watsonx_model_id=settings.get('watsonx_model_id', ''),
        )

        if not analyzer.load_data():
            return jsonify({'error': 'Failed to load defect data'}), 500

        results = analyzer.run_analysis()

        # Persist analysis JSON to output folder
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


@app.route('/generate-pdf-report', methods=['POST'])
@login_required
def generate_pdf_report():
    """Generate a PDF RCA report and return the filename."""
    try:
        data = request.json
        session_id = data.get('session_id')
        filepath = data.get('filepath')

        if not session_id or not filepath:
            return jsonify({'error': 'Missing required parameters'}), 400

        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404

        settings  = get_settings()
        generator = RCAReportGenerator(
            full_path,
            app.config['OUTPUT_FOLDER'],
            watsonx_api_key=settings.get('watsonx_api_key', ''),
            watsonx_project_id=settings.get('watsonx_project_id', ''),
            watsonx_model_id=settings.get('watsonx_model_id', ''),
        )

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
@login_required
def download_file(filename):
    """Stream a generated report file as a download attachment."""
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Requirements Analyzer routes ──────────────────────────────────────────────

@app.route('/api/requirements', methods=['POST'])
@login_required
def requirements():
    """Proxy a requirements task to the IBM ICA Agent."""
    try:
        data = request.json
        task_type = data.get('task_type')
        user_input = data.get('user_input')

        if not task_type or not user_input:
            return jsonify({'error': 'task_type and user_input are required.'}), 400

        settings = get_settings()
        endpoint = settings.get('ica_endpoint', '').strip()
        api_key = settings.get('ica_api_key', '').strip()

        if not endpoint or not api_key:
            return jsonify({
                'error': 'ICA Agent is not configured. Please go to Settings and enter your ICA endpoint and API key.'
            }), 400

        result = call_ica_agent(task_type, user_input, endpoint, api_key)

        if 'error' in result:
            return jsonify({'error': result['error']}), 502

        return jsonify({'reply': result['reply']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Settings routes ───────────────────────────────────────────────────────────

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings_api():
    """Return current settings — API key values are never exposed, only presence flags."""
    try:
        settings = get_settings()
        return jsonify({
            'ica_endpoint':           settings.get('ica_endpoint', ''),
            'ica_api_key_set':        bool(settings.get('ica_api_key', '').strip()),
            'watsonx_api_key_set':    bool(settings.get('watsonx_api_key', '').strip()),
            'watsonx_project_id_set': bool(settings.get('watsonx_project_id', '').strip()),
            'watsonx_model_id':       settings.get('watsonx_model_id', ''),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
@login_required
def save_settings_api():
    """Persist ICA and watsonx credentials to config.json."""
    try:
        data = request.json or {}
        save_settings({
            'ica_endpoint':      str(data.get('ica_endpoint',      '')),
            'ica_api_key':       str(data.get('ica_api_key',       '')),
            'watsonx_api_key':   str(data.get('watsonx_api_key',   '')),
            'watsonx_project_id':str(data.get('watsonx_project_id','')),
            'watsonx_model_id':  str(data.get('watsonx_model_id',  '')),
        })
        return jsonify({'success': True, 'message': 'Settings saved successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── User management routes ────────────────────────────────────────────────────

@app.route('/api/users', methods=['GET'])
@login_required
def list_users():
    """Return list of usernames and roles — no password hashes."""
    try:
        users = get_users()
        return jsonify({
            'users': [
                {'username': u, 'role': v.get('role', 'user')}
                for u, v in users.items()
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    """Create a new user (admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required.'}), 403
    try:
        data     = request.json or {}
        username = str(data.get('username', '')).strip().lower()
        password = str(data.get('password', '')).strip()
        role     = str(data.get('role', 'user')).strip()

        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters.'}), 400

        save_user(username, password, role)
        return jsonify({'success': True, 'message': f"User '{username}' created."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def remove_user(username):
    """Delete a user (admin only, cannot delete self)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required.'}), 403
    if username == session.get('user'):
        return jsonify({'error': 'You cannot delete your own account.'}), 400
    try:
        deleted = delete_user(username)
        if not deleted:
            return jsonify({'error': f"User '{username}' not found."}), 404
        return jsonify({'success': True, 'message': f"User '{username}' deleted."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<username>/password', methods=['POST'])
@login_required
def reset_password(username):
    """Reset a user's password.
    - Any logged-in user can reset their own password.
    - Admin can reset any user's password.
    """
    current_user = session.get('user')
    current_role = session.get('role')

    # Permission check: self reset OR admin reset
    if username != current_user and current_role != 'admin':
        return jsonify({'error': 'You can only reset your own password.'}), 403

    try:
        data         = request.json or {}
        new_password = str(data.get('new_password', '')).strip()

        if not new_password:
            return jsonify({'error': 'New password is required.'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters.'}), 400

        # Verify the target user exists
        users = get_users()
        if username not in users:
            return jsonify({'error': f"User '{username}' not found."}), 404

        # Preserve existing role when saving
        existing_role = users[username].get('role', 'user')
        save_user(username, new_password, existing_role)
        return jsonify({'success': True, 'message': f"Password updated for '{username}'."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Health check ──────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'Quality Intelligence Hub'})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Quality Intelligence Hub")
    print("=" * 60)
    print("  Starting server on http://localhost:5000")
    print("  Defect RCA + Requirements Analyzer")
    print("  Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
