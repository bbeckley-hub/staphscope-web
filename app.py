#!/usr/bin/env python3
"""
ESKAPE AMR Platform – Unified Web Application
Supports StaphScope, AcinetoScope, EcoliTyper, Kleboscope, PseudoScope, EnteroMark, EnteroScope

Author: Brown Beckley <brownbeckley94@gmail.com>
"""

import os
import uuid
import zipfile
import shutil
import json
import csv
import requests
import re
from datetime import datetime
from io import BytesIO
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, send_file, abort, Response, redirect, url_for
)
from werkzeug.utils import secure_filename
from config import Config
from tasks import run_generic_pipeline
from pipeline_registry import PIPELINE_REGISTRY, LANDING_ORDER

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['JOBS_DIR'], exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

ALLOWED_EXTENSIONS = {'.fasta', '.fna', '.fa', '.fn', '.faa'}
MAX_FILES_PER_JOB = 10
IPINFO_TOKEN = "5d6d6db497a12f"

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def get_country_from_ip(ip_address):
    try:
        url = f"https://api.ipinfo.io/lite/{ip_address}"
        headers = {"Authorization": f"Bearer {IPINFO_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('country', 'Unknown'), data.get('city', 'Unknown')
    except Exception:
        pass
    return 'Unknown', 'Unknown'

def allowed_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def extract_zip(zip_path, extract_to):
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        for root, _, files in os.walk(extract_to):
            for file in files:
                if allowed_file(file):
                    extracted_files.append(os.path.join(root, file))
    return extracted_files

def get_fasta_files_from_upload(file, input_dir):
    saved_files = []
    if file.filename.lower().endswith('.zip'):
        temp_zip = os.path.join(input_dir, 'temp_upload.zip')
        file.save(temp_zip)
        extract_dir = os.path.join(input_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        extracted = extract_zip(temp_zip, extract_dir)
        for ext_file in extracted:
            filename = os.path.basename(ext_file)
            dest_path = os.path.join(input_dir, filename)
            shutil.move(ext_file, dest_path)
            saved_files.append(dest_path)
        os.remove(temp_zip)
        shutil.rmtree(extract_dir)
    else:
        filename = secure_filename(file.filename)
        filepath = os.path.join(input_dir, filename)
        file.save(filepath)
        saved_files.append(filepath)
    return saved_files

def check_file_exists(job_id, filepath):
    full_path = os.path.join(app.config['JOBS_DIR'], job_id, 'output', filepath)
    return os.path.exists(full_path)

def get_sample_folders(job_id, module):
    module_path = os.path.join(app.config['JOBS_DIR'], job_id, 'output', module)
    if not os.path.exists(module_path):
        return []
    samples = []
    for item in os.listdir(module_path):
        item_path = os.path.join(module_path, item)
        if os.path.isdir(item_path) and item.startswith(('GCA_', 'GCF_')):
            samples.append(item)
    return sorted(samples)

app.jinja_env.globals.update(check_file_exists=check_file_exists)
app.jinja_env.globals.update(get_sample_folders=get_sample_folders)

def check_auth(username, password):
    return username == 'admin' and password == 'eskape2026'

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def landing():
    pipelines = [PIPELINE_REGISTRY[slug] for slug in LANDING_ORDER if slug in PIPELINE_REGISTRY]
    return render_template('index.html', pipelines=pipelines)

@app.route('/tools')
def tools_landing():
    pipelines = [PIPELINE_REGISTRY[slug] for slug in LANDING_ORDER if slug in PIPELINE_REGISTRY]
    return render_template('tools.html', pipelines=pipelines)

@app.route('/tools/<slug>')
def tool_page(slug):
    if slug not in PIPELINE_REGISTRY:
        abort(404)
    return render_template('pathogen_base.html', pipeline=PIPELINE_REGISTRY[slug])

@app.route('/publications')
def publications():
    return render_template('publications.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/data-policy')
def data_policy():
    return render_template('data_policy.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')

@app.route('/funding')
def funding():
    return render_template('funding.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/community')
def community():
    approved_comments = []
    approved_csv = os.path.join(os.path.dirname(__file__), 'logs', 'comments_approved.csv')
    if os.path.exists(approved_csv):
        with open(approved_csv, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                approved_comments.append({'name': row[1], 'comment': row[3]})
    return render_template('community.html', approved_comments=approved_comments)

@app.route('/submit/<slug>', methods=['POST'])
def submit(slug):
    if slug not in PIPELINE_REGISTRY:
        return jsonify({'error': 'Unknown pathogen'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400

    skip_modules = request.form.getlist('skip_modules')
    email = request.form.get('email', '').strip()

    # Collect all parameters from the form (thresholds, toggles, choices)
    # Exclude file, skip_modules, email and CSRF
    params = {}
    for key, value in request.form.items():
        if key not in ['file', 'skip_modules', 'email', 'csrf_token']:
            # Convert checkbox 'true'/'false' strings to booleans if needed
            if value.lower() in ('true', 'false'):
                params[key] = value.lower() == 'true'
            else:
                # Try to convert numeric strings to int/float
                try:
                    if '.' in value:
                        params[key] = float(value)
                    else:
                        params[key] = int(value)
                except (ValueError, TypeError):
                    params[key] = value

    job_id = uuid.uuid4().hex
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    input_dir = os.path.join(job_dir, 'input')
    os.makedirs(input_dir, exist_ok=True)

    all_saved_files = []
    for file in files:
        if not file.filename.lower().endswith('.zip') and not allowed_file(file.filename):
            return jsonify({'error': f'File {file.filename} must be FASTA or ZIP'}), 400
        all_saved_files.extend(get_fasta_files_from_upload(file, input_dir))

    if not all_saved_files:
        return jsonify({'error': 'No valid FASTA files found'}), 400

    if len(all_saved_files) > MAX_FILES_PER_JOB:
        shutil.rmtree(job_dir)
        return jsonify({'error': f'Maximum {MAX_FILES_PER_JOB} FASTA files allowed.'}), 400

    ip = get_client_ip()
    country, city = get_country_from_ip(ip)
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    geo_log = os.path.join(log_dir, 'country_log.csv')
    file_exists = os.path.isfile(geo_log)
    with open(geo_log, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'job_id', 'ip', 'country', 'city', 'slug', 'email'])
        writer.writerow([datetime.utcnow().isoformat(), job_id, ip, country, city, slug, email])

    job_info = {
        'job_id': job_id,
        'slug': slug,
        'email': email if email else None,
        'skip_modules': skip_modules,
        'created_at': datetime.utcnow().isoformat(),
        'country': country,
        'city': city,
        'params': params  # Store all parameters for the job
    }
    info_path = os.path.join(job_dir, 'job_info.json')
    with open(info_path, 'w') as f:
        json.dump(job_info, f)

    # Launch Celery task with all parameters
    run_generic_pipeline.delay(job_id, slug, skip_modules, **params)

    return jsonify({
        'job_id': job_id,
        'file_count': len(all_saved_files),
        'message': f'Processing {len(all_saved_files)} FASTA files with {PIPELINE_REGISTRY[slug]["name"]}'
    }), 202

@app.route('/status/<job_id>')
def status(job_id):
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    log_file = os.path.join(job_dir, 'pipeline.log')
    done_file = os.path.join(job_dir, '.done')
    error_file = os.path.join(job_dir, 'error.txt')
    log_lines = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            raw_lines = f.readlines()[-20:]
            log_lines = [strip_ansi_codes(line) for line in raw_lines]
    if os.path.exists(done_file):
        return jsonify({'status': 'COMPLETED', 'log': log_lines})
    if os.path.exists(error_file):
        with open(error_file, 'r') as f:
            error = f.read()
        return jsonify({'status': 'FAILED', 'error': error, 'log': log_lines})
    return jsonify({'status': 'RUNNING', 'log': log_lines})

@app.route('/progress/<job_id>')
def progress(job_id):
    return render_template('progress.html', job_id=job_id)

@app.route('/results/<job_id>')
def results(job_id):
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    info_path = os.path.join(job_dir, 'job_info.json')
    done_file = os.path.join(job_dir, '.done')
    if not os.path.exists(done_file):
        return "Results not found or job still processing.", 404
    slug = None
    if os.path.exists(info_path):
        with open(info_path, 'r') as f:
            job_info = json.load(f)
        slug = job_info.get('slug')
    if not slug:
        return "Invalid job metadata", 500
    pipeline = PIPELINE_REGISTRY.get(slug)
    return render_template('results.html', job_id=job_id, pipeline=pipeline)

@app.route('/results/<job_id>/<path:filename>')
def result_file(job_id, filename):
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    output_dir = os.path.join(job_dir, 'output')
    return send_from_directory(output_dir, filename)

@app.route('/results/<job_id>/download')
def download_results(job_id):
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    output_dir = os.path.join(job_dir, 'output')
    done_file = os.path.join(job_dir, '.done')
    if not os.path.exists(done_file) or not os.path.exists(output_dir):
        return "Results not found.", 404
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zf.write(file_path, arcname)
    memory_file.seek(0)
    return send_file(
        memory_file,
        download_name=f'eskape_results_{job_id}.zip',
        as_attachment=True
    )

@app.route('/submit-comment', methods=['POST'])
def submit_comment():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    comment = request.form.get('comment', '').strip()
    if not name or not comment:
        return jsonify({'error': 'Name and comment are required'}), 400
    ip = get_client_ip()
    timestamp = datetime.utcnow().isoformat()
    pending_csv = os.path.join(os.path.dirname(__file__), 'logs', 'comments_pending.csv')
    os.makedirs(os.path.dirname(pending_csv), exist_ok=True)
    file_exists = os.path.isfile(pending_csv)
    with open(pending_csv, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'name', 'email', 'comment', 'ip', 'approved'])
        writer.writerow([timestamp, name, email, comment, ip, '0'])
    return jsonify({'message': 'Thank you! Your comment will be reviewed before appearing.'}), 200

@app.route('/admin/comments', methods=['POST'])
@requires_auth
def admin_comments():
    action = request.form.get('action')
    row_index = request.form.get('row_index')
    comment_type = request.form.get('type')
    if not action or row_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    row_index = int(row_index)
    csv_map = {
        'pending': os.path.join(os.path.dirname(__file__), 'logs', 'comments_pending.csv'),
        'approved': os.path.join(os.path.dirname(__file__), 'logs', 'comments_approved.csv')
    }
    csv_path = csv_map.get(comment_type)
    if not csv_path or not os.path.exists(csv_path):
        return jsonify({'error': 'File not found'}), 404
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    if row_index >= len(rows):
        return jsonify({'error': 'Invalid index'}), 400
    if action == 'approve' and comment_type == 'pending':
        approved_row = rows[row_index]
        approved_row.append(datetime.utcnow().isoformat())
        approved_csv = os.path.join(os.path.dirname(__file__), 'logs', 'comments_approved.csv')
        file_exists = os.path.isfile(approved_csv)
        with open(approved_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['submitted_at', 'name', 'email', 'comment', 'ip', 'submitted_at_dup', 'approved_at'])
            writer.writerow([rows[row_index][0], rows[row_index][1], rows[row_index][2],
                             rows[row_index][3], rows[row_index][4], rows[row_index][0], approved_row[-1]])
        rows.pop(row_index)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    elif action == 'delete':
        rows.pop(row_index)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    else:
        return jsonify({'error': 'Invalid action or type'}), 400
    return redirect(url_for('admin'))

@app.route('/admin')
@requires_auth
def admin():
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'country_log.csv')
    data, headers, country_counts, total_jobs = [], [], {}, 0
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                data.append(row)
                total_jobs += 1
                if len(row) > 3:
                    country = row[3] if row[3] != 'Unknown' else 'Unknown / Private'
                    country_counts[country] = country_counts.get(country, 0) + 1
    country_stats = []
    for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        country_stats.append({'country': country, 'count': count, 'percentage': round(percentage, 1)})

    pending_comments, approved_comments = [], []
    pending_csv = os.path.join(os.path.dirname(__file__), 'logs', 'comments_pending.csv')
    if os.path.exists(pending_csv):
        with open(pending_csv, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for idx, row in enumerate(reader):
                pending_comments.append({'index': idx, 'timestamp': row[0], 'name': row[1],
                                         'email': row[2], 'comment': row[3], 'ip': row[4]})
    approved_csv = os.path.join(os.path.dirname(__file__), 'logs', 'comments_approved.csv')
    if os.path.exists(approved_csv):
        with open(approved_csv, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for idx, row in enumerate(reader):
                approved_comments.append({'index': idx, 'name': row[1], 'comment': row[3], 'approved_at': row[-1]})
    return render_template('admin.html', headers=headers, data=data, country_stats=country_stats,
                           total_jobs=total_jobs, pending_comments=pending_comments,
                           approved_comments=approved_comments)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)