# Architecture Notes

## Components
- **Browser UI:** HTML/CSS dashboard for upload, search, category filtering, and download.
- **Flask application:** validates basic file extensions, accepts uploads, lists documents, and handles downloads.
- **Local storage:** `storage/` folder for offline development/demo.
- **Amazon S3 (optional):** private object storage for cloud mode.
- **GitHub:** version control and source-code hosting, not document storage.

## Data flow
1. A student chooses a file and category in the browser.
2. Flask checks the filename extension and the configured upload-size limit.
3. In local mode, the file is written to `storage/`.
4. In S3 mode, Flask uploads the object under `documents/<category>/` in the configured bucket.
5. The dashboard lists files and provides a download route.

## Important
This demo does not include user accounts or per-user access controls. Keep it local until proper authentication and authorization are implemented. Keep the S3 bucket private and never commit credentials.
