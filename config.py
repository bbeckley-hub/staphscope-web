import os

class Config:
    # ============================================================
    # 1. PATHS TO EACH PIPELINE EXECUTABLE (conda environments)
    # ============================================================
    PIPELINE_EXECUTABLES = {
        'staphscope':   '/home/brown-beckley/anaconda3/envs/staphscope/bin/staphscope',
        'ecolityper':   '/home/brown-beckley/anaconda3/envs/ecolityper/bin/ecolityper',
        'acinetoscope': '/home/brown-beckley/anaconda3/envs/acinetoscope/bin/acinetoscope',
        'kleboscope':   '/home/brown-beckley/anaconda3/envs/kleboscope/bin/kleboscope',
        'pseudoscope':  '/home/brown-beckley/anaconda3/envs/pseudoscope/bin/pseudoscope',
        'enteromark':   '/home/brown-beckley/anaconda3/envs/enteromark/bin/enteromark',
        'enteroscope':  '/home/brown-beckley/anaconda3/envs/enteroscope/bin/enteroscope',
    }

    # (Legacy – kept for backward compatibility, but will not be used by new code)
    CONDA_PYTHON = "/home/brown-beckley/anaconda3/envs/klebcrispr/bin/python"
    STAPHSCOPE_SCRIPT = "/home/brown-beckley/anaconda3/envs/klebcrispr/bin/staphscope"

    # ============================================================
    # 2. JOB MANAGEMENT
    # ============================================================
    JOBS_DIR = os.path.join(os.path.dirname(__file__), 'jobs')

    # ============================================================
    # 3. CELERY & REDIS
    # ============================================================
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    # ============================================================
    # 4. FILE UPLOAD LIMITS
    # ============================================================
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024   # 50 MB
    TIMEOUT = 7200                          # 2 hours

    # ============================================================
    # 5. EMAIL NOTIFICATIONS
    # ============================================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@staphscope.dpdns.org')
    BASE_URL = os.environ.get('BASE_URL', 'https://staphscope.dpdns.org')