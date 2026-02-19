#!/usr/bin/env python3
"""
StaphScope Web Application
Flask app for uploading genomes and running StaphScope analysis asynchronously.
"""

import os
import uuid
import zipfile
import tempfile
import shutil
from io import BytesIO
from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, send_file, url_for
)
from werkzeug.utils import secure_filename
from config import Config
from tasks import run_staphscope

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure the base jobs directory exists
os.makedirs(app.config['JOBS_DIR'], exist_ok=True)

# Allowed file extensions (FASTA formats)
ALLOWED_EXTENSIONS = {'.fasta', '.fna', '.fa', '.fn', '.faa'}

# Maximum number of FASTA files per job
MAX_FILES_PER_JOB = 10

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def extract_zip(zip_path, extract_to):
    """Extract a ZIP file and return list of extracted FASTA files."""
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if allowed_file(file):
                    extracted_files.append(os.path.join(root, file))
    return extracted_files

def get_fasta_files_from_upload(file, input_dir):
    """
    Process uploaded file(s) and save to input_dir.
    Returns list of saved file paths.
    """
    saved_files = []
    
    # Check if it's a ZIP file
    if file.filename.lower().endswith('.zip'):
        # Save ZIP temporarily
        temp_zip = os.path.join(input_dir, 'temp_upload.zip')
        file.save(temp_zip)
        
        # Extract ZIP
        extract_dir = os.path.join(input_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        extracted = extract_zip(temp_zip, extract_dir)
        
        # Move extracted files to input_dir
        for ext_file in extracted:
            filename = os.path.basename(ext_file)
            dest_path = os.path.join(input_dir, filename)
            shutil.move(ext_file, dest_path)
            saved_files.append(dest_path)
        
        # Clean up
        os.remove(temp_zip)
        shutil.rmtree(extract_dir)
    
    else:
        # Single file or multiple files from form
        filename = secure_filename(file.filename)
        filepath = os.path.join(input_dir, filename)
        file.save(filepath)
        saved_files.append(filepath)
    
    return saved_files

# ============================================================================
# TEMPLATE HELPER FUNCTIONS
# ============================================================================

def check_file_exists(job_id, filepath):
    """Check if a file exists in the job's output directory."""
    full_path = os.path.join(app.config['JOBS_DIR'], job_id, 'output', filepath)
    return os.path.exists(full_path)

def get_sample_folders(job_id, module):
    """Get list of sample folders (GCA_*, GCF_*) in a module directory."""
    module_path = os.path.join(app.config['JOBS_DIR'], job_id, 'output', module)
    if not os.path.exists(module_path):
        return []
    
    samples = []
    for item in os.listdir(module_path):
        item_path = os.path.join(module_path, item)
        if os.path.isdir(item_path) and item.startswith(('GCA_', 'GCF_')):
            samples.append(item)
    return sorted(samples)

# Make helper functions available in templates
app.jinja_env.globals.update(check_file_exists=check_file_exists)
app.jinja_env.globals.update(get_sample_folders=get_sample_folders)

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render the upload page."""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    """
    Handle file upload(s), create job directory, and launch Celery task.
    Returns JSON with job_id.
    """
    # Check if files were uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Get module skip options
    skip_modules = request.form.getlist('skip_modules')

    # Generate unique job ID
    job_id = uuid.uuid4().hex

    # Create job directory structure
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    input_dir = os.path.join(job_dir, 'input')
    os.makedirs(input_dir, exist_ok=True)

    # Process each uploaded file and collect all FASTA files
    all_saved_files = []
    for file in files:
        # Validate file extension for non-ZIP files
        if not file.filename.lower().endswith('.zip') and not allowed_file(file.filename):
            return jsonify({'error': f'File {file.filename} must be FASTA or ZIP'}), 400
        
        # Save/process file
        file_saved = get_fasta_files_from_upload(file, input_dir)
        all_saved_files.extend(file_saved)

    # Check if any FASTA files were found
    if not all_saved_files:
        return jsonify({'error': 'No valid FASTA files found'}), 400

    # ✅ ENFORCE FILE LIMIT
    if len(all_saved_files) > MAX_FILES_PER_JOB:
        # Clean up the job directory
        shutil.rmtree(job_dir)
        return jsonify({
            'error': f'Maximum {MAX_FILES_PER_JOB} FASTA files allowed per job. You uploaded {len(all_saved_files)} files.'
        }), 400

    # Launch Celery task
    run_staphscope.delay(job_id, skip_modules)

    return jsonify({
        'job_id': job_id,
        'file_count': len(all_saved_files),
        'message': f'Processing {len(all_saved_files)} FASTA files'
    }), 202

@app.route('/status/<job_id>')
def status(job_id):
    """
    Check the status of a job by looking for .done file or error.txt.
    Returns JSON with status and optional log lines.
    """
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    log_file = os.path.join(job_dir, 'staphscope.log')
    done_file = os.path.join(job_dir, '.done')
    error_file = os.path.join(job_dir, 'error.txt')

    # Read log tail (last 20 lines)
    log_lines = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_lines = f.readlines()[-20:]

    # Check for completion using .done file
    if os.path.exists(done_file):
        return jsonify({'status': 'COMPLETED', 'log': log_lines})

    # Check for failure
    if os.path.exists(error_file):
        with open(error_file, 'r') as f:
            error = f.read()
        return jsonify({'status': 'FAILED', 'error': error, 'log': log_lines})

    # Otherwise still pending/running
    return jsonify({'status': 'PENDING', 'log': log_lines})

@app.route('/progress/<job_id>')
def progress(job_id):
    """Render a progress page that polls status and shows logs."""
    return render_template('progress.html', job_id=job_id)

@app.route('/results/<job_id>')
def results(job_id):
    """
    Render the results page for a completed job.
    """
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    output_dir = os.path.join(job_dir, 'output')
    done_file = os.path.join(job_dir, '.done')

    # Check if job is complete
    if not os.path.exists(done_file):
        return "Results not found or job still processing.", 404

    # Check for new modules
    fasta_qc_exists = os.path.exists(os.path.join(output_dir, 'fasta_qc_results'))
    vis_exists = os.path.exists(os.path.join(output_dir, 'STAPHSCOPE_VISUALIZATIONS'))

    return render_template('results.html', 
                           job_id=job_id,
                           fasta_qc_exists=fasta_qc_exists,
                           vis_exists=vis_exists)

@app.route('/results/<job_id>/<path:filename>')
def result_file(job_id, filename):
    """
    Serve individual result files from the job's output directory.
    """
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    output_dir = os.path.join(job_dir, 'output')
    return send_from_directory(output_dir, filename)

@app.route('/results/<job_id>/download')
def download_results(job_id):
    """
    Zip the entire output directory and serve as a download.
    """
    job_dir = os.path.join(app.config['JOBS_DIR'], job_id)
    output_dir = os.path.join(job_dir, 'output')
    done_file = os.path.join(job_dir, '.done')

    if not os.path.exists(done_file) or not os.path.exists(output_dir):
        return "Results not found.", 404

    # Create in-memory zip file
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Store files with relative path inside zip
                arcname = os.path.relpath(file_path, output_dir)
                zf.write(file_path, arcname)

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name=f'staphscope_results_{job_id}.zip',
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
