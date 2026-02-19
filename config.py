import os

class Config:
    # Path to the Python interpreter from your conda environment
    CONDA_PYTHON = "/home/brown-beckley/anaconda3/envs/klebcrispr/bin/python"

    # Path to the staphscope executable script
    STAPHSCOPE_SCRIPT = "/home/brown-beckley/anaconda3/envs/klebcrispr/bin/staphscope"

    # Base directory for all jobs
    JOBS_DIR = os.path.join(os.path.dirname(__file__), 'jobs')

    # Celery broker URL
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    # Maximum allowed file size (50 MB)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    
    # Timeout for StaphScope analysis (in seconds) - 2 hours default
    TIMEOUT = 7200
