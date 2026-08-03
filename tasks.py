"""
Celery tasks for the ESKAPE AMR Platform.
Handles asynchronous execution of species‑specific genomic pipelines.

Author: Brown Beckley <brownbeckley94@gmail.com>
"""

import os
import subprocess
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
from config import Config
from pipeline_registry import PIPELINE_REGISTRY

celery = Celery('tasks', broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

def send_email(recipient, subject, body):
    """Send an email using configured SMTP settings."""
    smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('MAIL_PORT', 587))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@staphscope.dpdns.org')

    if not username or not password:
        logging.warning("Email credentials not set; skipping email notification.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        if os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true':
            server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email sent to {recipient}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {recipient}: {e}")
        return False

@celery.task(bind=True)
def run_generic_pipeline(self, job_id, slug, skip_modules, **kwargs):
    """
    Execute a species‑specific genomic pipeline for a given job.

    Parameters
    ----------
    job_id : str
        Unique identifier for the job.
    slug : str
        Pipeline identifier (e.g., 'staphscope', 'ecolityper').
    skip_modules : list of str
        Module names to skip (as defined in the registry).
    kwargs : dict
        Any additional parameters (thresholds, toggles) from the web form.
        These are mapped to command-line flags based on the pipeline's param spec.
    """
    job_dir = os.path.join(Config.JOBS_DIR, job_id)
    input_dir = os.path.join(job_dir, 'input')
    output_dir = os.path.join(job_dir, 'output')
    log_file = os.path.join(job_dir, 'pipeline.log')
    done_file = os.path.join(job_dir, '.done')
    error_file = os.path.join(job_dir, 'error.txt')

    os.makedirs(output_dir, exist_ok=True)

    pipeline_info = PIPELINE_REGISTRY.get(slug)
    if not pipeline_info:
        error_msg = f"Unknown pipeline slug: {slug}"
        with open(error_file, 'w') as f:
            f.write(error_msg)
        raise Exception(error_msg)

    executable = Config.PIPELINE_EXECUTABLES.get(slug)
    if not executable or not os.path.exists(executable):
        error_msg = f"Executable not found for {slug}: {executable}"
        with open(error_file, 'w') as f:
            f.write(error_msg)
        raise Exception(error_msg)

    # Build base command
    input_pattern = os.path.join(input_dir, '*')
    cmd = [
        executable,
        '-i', input_pattern,
        '-o', output_dir,
        '-t', '2'
    ]

    # Add skip flags
    skip_flag_map = pipeline_info.get('skip_flag_map', {})
    for module in skip_modules:
        flag = skip_flag_map.get(module)
        if flag:
            cmd.append(flag)

    # Add parameters from kwargs (mapped to flags)
    param_specs = pipeline_info.get('params', {})
    for param_name, param_spec in param_specs.items():
        # Get value from kwargs (form input) or use default
        if param_name in kwargs:
            value = kwargs[param_name]
        else:
            value = param_spec.get('default')

        if value is None:
            continue

        # -------- CLAMP amr_min_coverage to <=0.89 to avoid AMRfinder error --------
        if param_name == 'amr_min_coverage':
            original_value = value
            try:
                # Convert to float for comparison
                float_val = float(value)
                if float_val > 0.89:
                    clamped_value = 0.89
                    logging.warning(
                        f"CLAMPED amr_min_coverage for job {job_id}: {original_value} → {clamped_value} "
                        f"(AMRfinder requires coverage < 0.9 for mutation reporting)"
                    )
                    value = clamped_value
            except (ValueError, TypeError):
                # If conversion fails, keep original
                pass
        # -------------------------------------------------------------------------

        # Build the flag based on type
        if param_spec.get('type') == 'bool':
            # Boolean: only add flag if True
            if value in (True, 'true', 'True', 'on', '1', 1):
                flag_name = f'--{param_name.replace("_", "-")}'
                cmd.append(flag_name)
        else:
            # For numeric/string values: add flag and value as separate arguments
            flag_name = f'--{param_name.replace("_", "-")}'
            cmd.append(flag_name)
            # Convert value to appropriate string
            if param_spec.get('type') == 'int':
                val_str = str(int(float(value)))
            else:
                val_str = str(value)
            cmd.append(val_str)

    # Log the final command for debugging
    logging.info(f"Running command for job {job_id} (slug: {slug}): {' '.join(cmd)}")

    env = os.environ.copy()
    env['TMPDIR'] = os.path.join(job_dir, 'tmp')
    os.makedirs(env['TMPDIR'], exist_ok=True)

    with open(log_file, 'w') as log:
        try:
            process = subprocess.Popen(
                cmd,
                cwd=job_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                log.write(line)
                log.flush()
            process.wait()

            if process.returncode != 0:
                error_msg = f"Pipeline {slug} exited with code {process.returncode}"
                with open(error_file, 'w') as f:
                    f.write(error_msg)
                raise Exception(error_msg)

            with open(done_file, 'w') as f:
                f.write('success')

            info_path = os.path.join(job_dir, 'job_info.json')
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    job_info = json.load(f)
                email = job_info.get('email')
                if email:
                    name = email.split('@')[0].capitalize()
                    pipeline_name = pipeline_info['name']
                    subject = f"Your {pipeline_name} analysis job {job_id} is complete"
                    base_url = os.environ.get('BASE_URL', 'https://staphscope.dpdns.org')
                    results_url = f"{base_url}/results/{job_id}"
                    body = f"""Hi {name},

Your {pipeline_name} analysis job {job_id} has finished successfully.

You can view your results here:
{results_url}

Thank you for using the ESKAPE AMR Platform!

---
{base_url}
"""
                    send_email(email, subject, body)

        except Exception as e:
            with open(error_file, 'w') as f:
                f.write(str(e))
            raise

@celery.task(bind=True)
def run_staphscope(self, job_id, skip_modules, **kwargs):
    """
    Legacy task for backward compatibility with old StaphScope calls.
    Redirects to the generic runner with slug='staphscope'.
    """
    return run_generic_pipeline(self, job_id, 'staphscope', skip_modules, **kwargs)