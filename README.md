# 🧬 ESKAPE AMR Platform

### A Unified, Species-Optimized Web Suite for Genomic Surveillance of ESKAPE Pathogens and *E. coli*

Welcome to the **ESKAPE AMR Platform** – a free, open-source web application that integrates seven species-specific genomic analysis pipelines into a single, user-friendly interface.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3%2B-brightgreen.svg)](https://docs.celeryproject.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/bbeckley-hub/eskape-web-platform.svg)](https://github.com/bbeckley-hub/eskape-web-platform/stargazers)

## 📌 Development Status Notice

> **This project is currently under active development.**
> The web interface and core functionality are ready for testing and collaboration. We are actively seeking institutional hosting partners to transition the platform from a personal laptop to a dedicated server, enabling 24/7 availability for the wider research community. Your feedback, contributions, and collaboration are highly welcome.

## 🌐 Live Demo

The platform is live at: **[https://eskape.bio](https://eskape.bio)**

## 📋 Table of Contents

1.  [Overview](#-overview)
2.  [Key Features](#-key-features)
    *   [Integrated Pathogen Pipelines](#integrated-pathogen-pipelines)
    *   [Web Application Features](#web-application-features)
3.  [How It Works](#-how-it-works)
    *   [Architecture Overview](#architecture-overview)
    *   [Technology Stack](#technology-stack)
4.  [Getting Started](#-getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Installation for Local Development](#installation-for-local-development)
    *   [Running the Services](#running-the-services)
5.  [Usage Guide](#-usage-guide)
    *   [Submitting a Job](#submitting-a-job)
    *   [Understanding Your Results](#understanding-your-results)
6.  [API Reference](#-api-reference)
7.  [Deployment](#-deployment)
    *   [System Requirements](#system-requirements)
    *   [Production Deployment](#production-deployment)
    *   [Institutional Hosting](#institutional-hosting)
8.  [For Power Users: Command-Line Pipelines](#-for-power-users-command-line-pipelines)
9.  [Contributing](#-contributing)
10. [Citation & Publications](#-citation--publications)
11. [License](#-license)
12. [Contact & Support](#-contact--support)
13. [Acknowledgements](#-acknowledgements)

## 🎯 Overview

The **ESKAPE AMR Platform** is a fully-featured web application designed to democratize access to advanced bacterial genomic surveillance. It addresses the fragmentation of existing bioinformatics tools by providing a single, integrated interface for analyzing the most critical drug-resistant pathogens.

This platform leverages a robust backend to asynchronously run the species-optimized command-line pipelines, delivering comprehensive, publication-ready reports without requiring command-line expertise. It is built with the needs of researchers, clinicians, and public health labs in mind, particularly in low-resource settings.

### Integrated Pathogen Pipelines

The platform integrates the following species-specific pipelines:

| Pathogen | Pipeline | Key Analyses |
| :--- | :--- | :--- |
| *S. aureus* | **StaphScope** | MLST, *spa* typing, SCC*mec*, AMR, virulence, plasmids, lineage, agr typing. |
| *A. baumannii* | **AcinetoScope** | Dual MLST, K/O capsule typing, AMR, carbapenemase tracking, plasmid typing. |
| *E. coli* | **EcoliTyper** | MLST, serotyping, CH-typing, phylogrouping, AMR, virulence. |
| *K. pneumoniae* | **Kleboscope** | MLST, K-locus typing, virulence markers (ICEKp, iuc, rmp), AMR. |
| *P. aeruginosa* | **PseudoScope** | MLST, PAST serogrouping, AMR, virulence factors (exoU/exoS). |
| *E. faecium* | **EnteroMark** | MLST, vancomycin/linezolid resistance, high-level aminoglycosides. |
| *E. cloacae* complex | **EnteroScope** | MLST, carbapenemases, efflux pumps, biofilm markers. |

## ✨ Key Features

### Web Application Features

- **Asynchronous Job Processing:** Close your browser and receive an email when your analysis is complete.
- **Intuitive File Upload:** Upload single or multiple FASTA files, or entire ZIP archives.
- **Dynamic Module Selection:** Choose exactly which analyses to run for each pathogen.
- **Real-Time Progress & Logs:** Monitor your job with live logs as they stream from the pipeline.
- **Comprehensive, Tabbed Results:** Explore results in an organized, interactive interface for each module.
- **One-Click Download:** Download all your results, images, and data as a single ZIP archive.
- **Administrative Dashboard:** Monitor platform usage and moderate community feedback.
- **Free and Open Source:** All code is released under the MIT license, ensuring full transparency and reproducibility.

### Web Platform-Specific Features

- **Country Monitoring:** Anonymized IP-based geolocation helps understand platform reach.
- **Community Feedback:** Users can submit and share testimonials (moderated).
- **Email Notifications:** Get a direct link to your results when the job finishes.
- **Automatic Job Cleanup:** Old job data is automatically deleted after 24 hours.
- **Tutorial & Documentation:** Built-in guide and video tutorial to get you started.
- **Informative Pages:** Dedicated sections for publications, team, funding, roadmap, and data policy.

## ⚙️ How It Works

### Architecture Overview

The platform uses a decoupled, asynchronous architecture to handle computational tasks efficiently.

```
User Browser
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Flask + Jinja2)               │
│  • Landing page, tool pages, progress, results.             │
│  • Bootstrap 5 for responsive design.                       │
│  • AJAX polling for live logs.                              │
└─────────────────────────────────────────────────────────────┘
      │
      ▼ (HTTP requests)
┌─────────────────────────────────────────────────────────────┐
│                 Backend (Flask routes)                      │
│  • Upload handling, job creation, status endpoint.          │
│  • Admin page for monitoring and comment moderation.        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼ (Celery task)
┌─────────────────────────────────────────────────────────────┐
│              Task Queue (Celery + Redis)                    │
│  • Asynchronous pipeline execution.                         │
│  • Each pipeline runs in its own Conda environment.         │
│  • Logs written to job-specific directories.                │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend:** Flask (Python web framework)
- **Task Queue:** Celery with Redis broker
- **Bioinformatics Engine:** Species-specific Conda environments
- **Frontend:** Bootstrap 5, JavaScript, Jinja2 templates
- **Deployment:** Gunicorn + Nginx + Cloudflare Tunnel (production)

## 🚀 Getting Started (Local Development)

### Prerequisites

- Python 3.9+
- Conda (for pipeline environments)
- Redis Server

### Installation for Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/bbeckley-hub/eskape-web-platform.git
    cd eskape-web-platform
    ```

2.  **Set up the Python environment:**
    ```bash
    conda create -n eskape-web python=3.9 -y
    conda activate eskape-web
    pip install -r requirements.txt
    ```

3.  **Install the required pipeline environments (example for StaphScope):**
    ```bash
    conda create -n staphscope_env -c conda-forge -c bioconda  staphscope -y
    # Repeat for ecolityper_env, acinetoscope_env, etc. as needed.
    ```

4.  **Configure paths in `config.py`:**
    Update the `PIPELINE_EXECUTABLES` dictionary to point to the correct Conda environment paths for each pipeline.
    ```python
    PIPELINE_EXECUTABLES = {
        'staphscope':   '/home/user/miniconda3/envs/staphscope_env/bin/staphscope',
        # ... add other pipelines
    }
    ```

5.  **Start Redis:**
    ```bash
    redis-server
    ```

### Running the Services

You need to run three services in separate terminals.

**Terminal 1 – Celery Worker:**
```bash
conda activate eskape-web
celery -A tasks worker --loglevel=info --concurrency 4
```

**Terminal 2 – Gunicorn (production WSGI server):**
```bash
conda activate eskape-web
gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
```

**Terminal 3 – (Optional) Cloudflare Tunnel for Public Access:**
```bash
cloudflared tunnel run eskape
```
*Note: For local testing, simply visit `http://localhost:5000`.*

## 📚 Usage Guide

### Submitting a Job

1.  Go to the **Tools** page and select a pathogen.
2.  **Upload your genome(s):** Click to select one or more FASTA files or a ZIP archive containing them.
3.  **(Optional) Enter your email** to receive a notification when your job is finished.
4.  **(Optional) Select modules:** Uncheck any analyses you wish to skip.
5.  **Adjust advanced parameters:** Fine-tune thresholds (e.g., AMR identity/coverage, ABRicate thresholds) using the sliders.
6.  Click **Submit Job**.

### Understanding Your Results

Once the job finishes, you will be automatically redirected to the results page, which is organized into tabs for each analysis module (e.g., MLST, AMR, ABRicate). Each tab provides:

- An interactive HTML report you can view in your browser.
- Links to download raw data (TSV, JSON, or CSV).
- The option to download all results as a single ZIP file.

## 🖥️ API Reference

The web app provides a simple REST API for programmatic access:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | GET | Home page with upload form. |
| `/submit/<slug>` | POST | Submit files for analysis. |
| `/status/<job_id>` | GET | Check job status (RUNNING, COMPLETED, FAILED). |
| `/progress/<job_id>` | GET | Progress page with live logs. |
| `/results/<job_id>` | GET | Results page. |
| `/results/<job_id>/download` | GET | Download all results as ZIP. |

## 🚀 Deployment

### System Requirements

- **OS:** Ubuntu 20.04/22.04 (recommended)
- **CPU:** 4+ cores
- **RAM:** 8+ GB (16+ GB recommended for concurrent jobs)
- **Storage:** 50+ GB for jobs, logs, and reference databases

### Production Deployment

For a production deployment, we use:

- **Gunicorn** as the WSGI server
- **Cloudflare Tunnel** for secure public access (no open ports required)
- **Systemd** services for process management
- **Redis** as the Celery broker

#### Systemd service files

**Gunicorn** (`/etc/systemd/system/eskape-web.service`):
```ini
[Unit]
Description=ESKAPE Web App (Gunicorn)
After=network.target

[Service]
User=YOUR_USER
Group=YOUR_GROUP
WorkingDirectory=/path/to/eskape-web-platform
Environment="PATH=/path/to/conda/envs/klebcrispr/bin"
ExecStart=/path/to/conda/envs/klebcrispr/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery** (`/etc/systemd/system/celery-eskape.service`):
```ini
[Unit]
Description=Celery Worker for ESKAPE AMR Platform
After=network.target redis.service

[Service]
User=YOUR_USER
Group=YOUR_GROUP
WorkingDirectory=/path/to/eskape-web-platform
Environment="PATH=/path/to/conda/envs/klebcrispr/bin"
ExecStart=/path/to/conda/envs/klebcrispr/bin/celery -A tasks worker --loglevel=info --concurrency=2
Restart=always

[Install]
WantedBy=multi-user.target
```

**Cloudflare Tunnel** (`/etc/systemd/system/cloudflared-eskape.service`):
```ini
[Unit]
Description=Cloudflare Tunnel (eskape.bio)
After=network.target

[Service]
User=YOUR_USER
Group=YOUR_GROUP
ExecStart=/usr/local/bin/cloudflared tunnel run eskape
Restart=always

[Install]
WantedBy=multi-user.target
```

### Institutional Hosting

We are actively seeking institutional hosting partners to move this platform from a personal laptop to a reliable, 24/7 server environment. If your institution is interested in collaborating, please contact us.

## 📦 For Power Users: Command-Line Pipelines

The web version is designed for ease of use and has a 10-file limit. For large batch processing (100+ genomes), use the command-line versions, which are available as Conda packages on **Bioconda**.

```bash
# Example for StaphScope
conda create -n staphscope -c conda-forge -c bioconda -c bbeckley-hub staphscope -y
conda activate staphscope
abricate --setupdb   # Setup databases first
staphscope -i "*.fna" -o results
```

## 🤝 Contributing

Contributions are welcome! We are particularly interested in:

- Bug reports and feature requests.
- Contributions to the code, documentation, or new pipelines.
- Feedback from users in low-resource settings.

Please feel free to submit a Pull Request or open an Issue on GitHub.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📚 Citation & Publications

If you use this platform or any of its component tools, please cite the relevant publications:

*   **StaphScope:** Beckley B, Amarh V. (2026). StaphScope: a species‑optimized computational pipeline for rapid and accessible *Staphylococcus aureus* genotyping and surveillance. *BMC Genomics*, 27:261. [DOI: 10.1186/s12864-026-12609-x](https://doi.org/10.1186/s12864-026-12609-x)

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 📬 Contact & Support

**Author:** Brown Beckley  
**Affiliation:** University of Ghana Medical School – Department of Medical Biochemistry  
**Email:** [brownbeckley94@gmail.com](mailto:brownbeckley94@gmail.com)  
**GitHub:** [@bbeckley-hub](https://github.com/bbeckley-hub)  
**Project Link:** [https://github.com/bbeckley-hub/eskape-web-platform](https://github.com/bbeckley-hub/eskape-web-platform)  
**Live Demo:** [https://eskape.bio](https://eskape.bio)

## 🙏 Acknowledgements

- The researchers and institutions who have provided data and feedback.
- The open-source community for the incredible tools and libraries that make this work possible.
- Dr. Vincent Amarh for guidance and support.
- All contributors, beta testers, and users.

---

⭐ **If you find this platform useful, please star the repository on GitHub!**
