# Cloud-Based Personal Document Storage

A student-focused document storage prototype built with Flask. It supports uploading, categorizing, searching, and downloading documents. It can run in local demo mode first and can be configured to use a private Amazon S3 bucket.

## Features

- Student document dashboard
- Upload and download documents
- Categories: Certificates, Notes, Assignments, ID Documents, Other
- Search by filename and filter by category
- 10 MB upload limit and basic file-extension allowlist
- Local storage for easy testing
- Optional AWS S3 object storage
- Responsive interface

## 1. Run locally (no AWS account needed)

Requires Python 3.10 or newer.

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:STORAGE_MODE="local"
python app.py
```

### Ubuntu / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export STORAGE_MODE=local
python app.py
```

Open http://127.0.0.1:5000 in your browser. Files are stored in the local `storage/` folder while in local mode.

## 2. Optional: configure AWS S3

1. Create an S3 bucket in your chosen AWS region. Keep **Block Public Access** enabled.
2. Configure AWS credentials using an IAM identity / role and the AWS CLI credential chain. Do not put access keys in source code or commit them to GitHub.
3. Grant only the required permissions for the demo bucket/prefix (for example, `s3:ListBucket` restricted to the bucket and `s3:PutObject` / `s3:GetObject` restricted to `documents/*`).
4. Install dependencies using `pip install -r requirements.txt`.
5. Set the environment variables before running the app.

### Windows PowerShell
```powershell
$env:STORAGE_MODE="s3"
$env:S3_BUCKET="your-private-bucket-name"
$env:AWS_REGION="ap-south-1"
python app.py
```

### Ubuntu / macOS
```bash
export STORAGE_MODE=s3
export S3_BUCKET="your-private-bucket-name"
export AWS_REGION="ap-south-1"
python app.py
```

The app uses the default AWS credential chain. It does not need public bucket access. Check AWS billing and remove demo resources when finished to avoid unexpected costs.

## 3. GitHub setup

Create an empty repository on GitHub, then run these commands from this folder:

```bash
git init
git add .
git commit -m "Build student document storage demo"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/cloud-based-personal-document-storage.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Do not upload real certificates or personal documents.

## Architecture

```text
Student browser
      |
      v
Flask web application
      |
      +---- Local demo mode ---> storage/ folder
      |
      +---- AWS mode ----------> Private Amazon S3 bucket
```

GitHub hosts the source code and documentation; it is not the storage location for uploaded student documents.

## Limitations / security notes

This is an academic prototype, not a production-ready secure document service. It does not yet implement user accounts, per-student authorization, malware scanning, encryption-key management, audit logs, or production deployment hardening. Do not upload sensitive real documents. For a real multi-user deployment, add authentication and authorization before exposing documents, use HTTPS, configure appropriate encryption and lifecycle policies, and run behind a production WSGI server. The Flask development server and `debug=True` are for local development only.

## Project report demo checklist

- [ ] Start the app in local mode
- [ ] Upload one sample PDF or image
- [ ] Filter by category and search by filename
- [ ] Download the sample file
- [ ] If AWS is configured, repeat in S3 mode and show the object in the private bucket
- [ ] Capture screenshots for the report
