<div align="center">
    
# 🔬 StaphScope Web

### A web-based interface for rapid *Staphylococcus aureus* genotyping and surveillance

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.1186%2Fs12864--026--12609--x-blue)](https://doi.org/10.1186/s12864-026-12609-x)

</div>
---

## 📋 **Table of Contents**
- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [Processing Large Datasets](#-processing-large-datasets)
- [Citation](#-citation)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 **Overview**

**StaphScope Web** is a user-friendly web interface for the [StaphScope command-line tool](https://github.com/bbeckley-hub/staphscope-typing-tool), a comprehensive bioinformatics pipeline for *Staphylococcus aureus* genomic analysis. It allows researchers and clinicians to upload bacterial genomes and receive detailed typing results without any command-line expertise.

The tool integrates **eight essential genotyping methods** into a single, cohesive workflow, making MRSA/MSSA surveillance accessible to all.

---

## ✨ **Features**

### 🔬 **Analysis Modules**
| Module | Purpose | Outputs |
|--------|---------|---------|
| **FASTA QC** | Quality control and statistics | HTML/TSV/JSON reports |
| **MLST Typing** | Multi-locus sequence typing | Sequence type, clonal complex |
| **_spa_ Typing** | Protein A gene analysis | *spa* type, repeat patterns |
| **SCC*mec* Typing** | Methicillin resistance cassette | Cassette type (I-XIII) |
| **AMR Profiling** | Antimicrobial resistance genes | 5,000+ genes, risk categories |
| **ABRicate Screening** | 9 databases (CARD, VFDB, PlasmidFinder, etc.) | Resistance, virulence, plasmids |
| **Lineage Database** | Global epidemiological context | 44 major lineages |
| **Visualization** | Interactive dashboards | PNG/SVG/PDF outputs |

### 🚀 **Web-Specific Features**
- ✅ **Drag-and-drop file upload** (single, multiple, or ZIP)
- ✅ **Module selection** – choose which analyses to run
- ✅ **Real-time progress monitoring** with live logs
- ✅ **Beautiful HTML reports** with interactive visualizations
- ✅ **Download all results as a single ZIP**
- ✅ **Responsive design** – works on desktop and tablet
- ✅ **10-file limit** for fair resource usage

### 🛡️ **MRSA-Specific Innovations**
- Automated MRSA/MSSA classification
- Clinical gene flagging (PVL, enterotoxins, *van* genes)
- Risk categorization: 'Critical Risk', 'High Risk'
- Cross-genome pattern discovery

---

## 🏗️ **Architecture**

```
staphscope-web/
├── app.py                 # Flask application with routes
├── tasks.py               # Celery worker tasks
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── jobs/                  # Job directories (created at runtime)
├── static/                # Static files (CSS, JS)
│   ├── css/
│   └── js/
└── templates/             # HTML templates
    ├── base.html
    ├── index.html
    ├── progress.html
    └── results.html
```

### **Technology Stack**
- **Backend**: Flask (Python web framework)
- **Task Queue**: Celery with Redis broker
- **Bioinformatics Engine**: StaphScope (conda environment)
- **Frontend**: Bootstrap 5, JavaScript
- **Deployment**: Gunicorn + Nginx + systemd

---

## ⚡ **Quick Start (Local Development)**

### **Prerequisites**
- Python 3.8+
- Redis server
- Conda (for StaphScope environment)

### **1. Clone the repository**
```bash
git clone https://github.com/bbeckley-hub/staphscope-web.git
cd staphscope-web
```

### **2. Set up Python virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **3. Install and start Redis**
- **Ubuntu/Debian**: `sudo apt install redis-server && sudo systemctl start redis`
- **macOS**: `brew install redis && brew services start redis`
- **Windows**: Use WSL2 or download from [redis.io](https://redis.io/download)

### **4. Configure paths**
Edit `config.py` to point to your StaphScope installation:
```python
CONDA_PYTHON = "/path/to/your/miniconda3/envs/staphscope/bin/python"
STAPHSCOPE_SCRIPT = "/path/to/your/miniconda3/envs/staphscope/bin/staphscope"
```

### **5. Start Celery worker**
```bash
celery -A tasks.celery worker --loglevel=info
```

### **6. Start Flask app**
```bash
python app.py
```

Visit `http://127.0.0.1:5000` and start analyzing!

---

## 📚 **Usage Guide**

### **Uploading Files**
1. Navigate to the home page
2. Click "Choose Files" and select one or more FASTA files (`.fasta`, `.fna`, `.fa`)
3. Alternatively, upload a ZIP archive containing multiple FASTA files
4. Select which modules to run (uncheck to skip)
5. Click "Submit" and wait for analysis to complete

### **Understanding Results**
Results are organized into tabs:
- **Comprehensive**: Unified report of all analyses
- **MLST**: Sequence typing results
- **_spa_**: *spa* typing with repeat patterns
- **SCC*mec***: Methicillin resistance cassette typing
- **AMR**: Antimicrobial resistance genes
- **ABRicate**: Multi-database screening
- **Lineage**: Phylogenetic lineage information
- **FASTA QC**: Quality control metrics
- **Visualization**: Interactive plots and dashboards

Each tab provides:
- HTML reports for interactive viewing
- TSV/JSON downloads for further analysis
- Individual sample-level reports

### **Downloading Results**
Click the **"Download All Results (ZIP)"** button to get a complete archive of all analysis outputs.

---

## 🖥️ **API Reference**

The web app provides a simple REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with upload form |
| `/submit` | POST | Submit files for analysis |
| `/status/<job_id>` | GET | Check job status (PENDING, RUNNING, COMPLETED, FAILED) |
| `/progress/<job_id>` | GET | Progress page with live logs |
| `/results/<job_id>` | GET | Results page |
| `/results/<job_id>/<path:filename>` | GET | Download specific result file |
| `/results/<job_id>/download` | GET | Download all results as ZIP |

---

## 🚀 **Production Deployment**

### **Server Requirements**
- Ubuntu 20.04/22.04 (or similar Linux)
- 4+ CPU cores, 8+ GB RAM
- 50+ GB storage
- Domain name (optional but recommended)

### **Deployment Steps**
1. **Set up the server** (see [full deployment guide](#))
2. **Install dependencies**: Conda, Redis, Nginx
3. **Clone the repository**: `git clone https://github.com/bbeckley-hub/staphscope-web.git /var/www/staphscope-web`
4. **Set up virtual environment**: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
5. **Configure services**: Create systemd units for Gunicorn and Celery
6. **Set up Nginx** as reverse proxy
7. **Enable SSL** with Let's Encrypt

### **Systemd Service Files**

**Gunicorn** (`/etc/systemd/system/staphscope-web.service`):
```ini
[Unit]
Description=Gunicorn instance for StaphScope Web
After=network.target

[Service]
User=staphscope
Group=staphscope
WorkingDirectory=/var/www/staphscope-web
Environment="PATH=/var/www/staphscope-web/venv/bin"
ExecStart=/var/www/staphscope-web/venv/bin/gunicorn --workers 3 --bind unix:/var/www/staphscope-web/staphscope.sock app:app

[Install]
WantedBy=multi-user.target
```

**Celery** (`/etc/systemd/system/staphscope-celery.service`):
```ini
[Unit]
Description=Celery worker for StaphScope Web
After=network.target redis.service

[Service]
User=staphscope
Group=staphscope
WorkingDirectory=/var/www/staphscope-web
Environment="PATH=/var/www/staphscope-web/venv/bin"
ExecStart=/var/www/staphscope-web/venv/bin/celery -A tasks.celery worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

---

## 📦 **Processing Large Datasets**

The web version limits uploads to **10 files per job** to ensure fair resource usage. For larger datasets, use the command-line version:

### **For Linux/Ubuntu users:**

```bash
# 1. Install Miniconda (if not already)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc

# 2. Create StaphScope environment
conda create -n staphscope -c conda-forge -c bioconda -c bbeckley-hub staphscope -y
conda activate staphscope

# 3. Update databases
abricate --setupdb

# 4. Navigate to your FASTA files
cd /path/to/your/fasta/files

# 5. Run StaphScope (adjust pattern to match your files)
staphscope -i "*.fna" -o Staphscope_results
```

**No need to specify threads** – StaphScope automatically allocates optimal resources based on your CPU. ☕ Relax and enjoy your coffee while it runs!

---

## 📚 **Citation**

If you use StaphScope in your research, please cite:

> Beckley, B., Amarh, V. (2026). StaphScope: a species‑optimized computational pipeline for rapid and accessible *Staphylococcus aureus* genotyping and surveillance. *BMC Genomics*, 27:123.

**DOI**: [10.1186/s12864-026-12609-x](https://doi.org/10.1186/s12864-026-12609-x)  
**PMID**: 41645058

---

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📬 **Contact**

**Author**: Brown Beckley  
**Affiliation**: University of Ghana Medical School – Department of Medical Biochemistry  
**Email**: [brownbeckley94@gmail.com](mailto:brownbeckley94@gmail.com)  
**GitHub**: [@bbeckley-hub](https://github.com/bbeckley-hub)  
**Project Link**: [https://github.com/bbeckley-hub/staphscope-web](https://github.com/bbeckley-hub/staphscope-web)

---

## 🙏 **Acknowledgements**

- StaphScope development team
- University of Ghana Medical School
- All contributors and beta testers

  </div>

---

⭐ **If you find this tool useful, please star the repository on GitHub!** ⭐
```
