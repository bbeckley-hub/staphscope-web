import os
import subprocess
from celery import Celery
from config import Config

celery = Celery('tasks', broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

# Map module names to staphscope skip flags
SKIP_FLAGS = {
    'fasta_qc': '--skip-fasta-qc',
    'mlst': '--skip-mlst',
    'spa': '--skip-spa',
    'sccmec': '--skip-sccmec',
    'amr': '--skip-amr',
    'abricate': '--skip-abricate',
    'lineage': '--skip-lineage',
    'comprehensive': '--skip-comprehensive',
    'visualization': '--skip-visualization'
}

@celery.task(bind=True)
def run_staphscope(self, job_id, skip_modules):
    job_dir = os.path.join(Config.JOBS_DIR, job_id)
    input_dir = os.path.join(job_dir, 'input')
    output_dir = os.path.join(job_dir, 'output')
    log_file = os.path.join(job_dir, 'staphscope.log')
    done_file = os.path.join(job_dir, '.done')
    error_file = os.path.join(job_dir, 'error.txt')
    
    os.makedirs(output_dir, exist_ok=True)

    # Build input pattern (any FASTA file)
    input_pattern = os.path.join(input_dir, '*')

    # Start building command
    cmd = [
        Config.STAPHSCOPE_SCRIPT,
        '-i', input_pattern,
        '-o', output_dir,
        '-t', '2'  # threads – could be made configurable later
    ]

    # Add skip flags for modules the user wants to skip
    for module in skip_modules:
        flag = SKIP_FLAGS.get(module)
        if flag:
            cmd.append(flag)

    # Set environment (especially TMPDIR for isolation)
    env = os.environ.copy()
    env['TMPDIR'] = os.path.join(job_dir, 'tmp')
    os.makedirs(env['TMPDIR'], exist_ok=True)

    # Run and capture output to log file
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
            # Write to log file in real time
            for line in process.stdout:
                log.write(line)
                log.flush()
            process.wait()
            
            if process.returncode != 0:
                error_msg = f"StaphScope exited with code {process.returncode}"
                with open(error_file, 'w') as f:
                    f.write(error_msg)
                raise Exception(error_msg)
            
            # ✅ SUCCESS! Create .done file to mark completion
            with open(done_file, 'w') as f:
                f.write('success')
                
        except Exception as e:
            with open(error_file, 'w') as f:
                f.write(str(e))
            raise
