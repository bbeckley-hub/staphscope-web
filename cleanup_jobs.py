#!/usr/bin/env python3
"""
Cleanup job directories older than 24 hours.
Run daily via cron.
author: Brown Beckley <brownbeckley94@gmail.com>
"""

import os
import time
import shutil
from pathlib import Path

# Configuration
JOBS_DIR = "/home/brown-beckley/eskape-web-platform/jobs"
MAX_AGE_HOURS = 24

def cleanup_old_jobs():
    now = time.time()
    max_age_seconds = MAX_AGE_HOURS * 3600
    deleted = 0
    for job_dir in Path(JOBS_DIR).iterdir():
        if job_dir.is_dir():
            # Check directory modification time
            mtime = os.path.getmtime(job_dir)
            age_seconds = now - mtime
            if age_seconds > max_age_seconds:
                shutil.rmtree(job_dir)
                print(f"Deleted old job: {job_dir.name} (age: {age_seconds/3600:.1f} hours)")
                deleted += 1
    print(f"Cleanup complete. Deleted {deleted} job(s).")

if __name__ == "__main__":
    cleanup_old_jobs()
