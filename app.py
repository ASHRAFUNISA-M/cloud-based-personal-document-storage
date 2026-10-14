import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
LOCAL_STORAGE = BASE_DIR / "storage"
LOCAL_STORAGE.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB demo limit

CATEGORIES = ["Certificates", "Notes", "Assignments", "ID Documents", "Other"]
ALLOWED_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "txt", "doc", "docx",
    "ppt", "pptx", "xls", "xlsx", "csv"
}

STORAGE_MODE = os.environ.get("STORAGE_MODE", "local").lower()
S3_BUCKET = os.environ.get("S3_BUCKET", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


def s3_client():
    """Use standard AWS credential-chain configuration; never hard-code keys."""
    import boto3
    return boto3.client("s3", region_name=AWS_REGION)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def list_documents():
    docs = []
    if STORAGE_MODE == "s3" and S3_BUCKET:
        try:
            response = s3_client().list_objects_v2(Bucket=S3_BUCKET, Prefix="documents/")
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                name = key.rsplit("/", 1)[-1]
                # Key format: documents/category/uniqueid_originalname
                parts = key.split("/")
                category = parts[1] if len(parts) > 2 else "Other"
                original = name.split("_", 1)[1] if "_" in name else name
                docs.append({
                    "id": key,
                    "name": original,
                    "category": category,
                    "size": obj.get("Size", 0),
                    "modified": obj.get("LastModified").strftime("%Y-%m-%d %H:%M") if obj.get("LastModified") else "",
                })
        except Exception:
            app.logger.exception("Could not list S3 objects")
            flash("Could not connect to S3. Check your bucket, region, and AWS permissions.", "error")
    else:
        for path in LOCAL_STORAGE.iterdir():
            if path.is_file() and path.name != ".gitkeep":
                # Metadata is kept in the filename: category--id--originalname
                parts = path.name.split("--", 2)
                if len(parts) == 3:
                    category, doc_id, stored_name = parts
                else:
                    category, doc_id, stored_name = "Other", path.name, path.name
                docs.append({
                    "id": path.name,
                    "name": stored_name,
                    "category": category.replace("_", " "),
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
    return sorted(docs, key=lambda d: d["modified"], reverse=True)


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip().lower()
    category_filter = request.args.get("category", "").strip()
    documents = list_documents()
    if query:
        documents = [d for d in documents if query in d["name"].lower()]
    if category_filter:
        documents = [d for d in documents if d["category"] == category_filter]
    return render_template(
        "index.html",
        documents=documents,
        categories=CATEGORIES,
        query=request.args.get("q", ""),
        selected_category=category_filter,
        storage_mode=STORAGE_MODE,
        total_count=len(list_documents()),
    )


@app.route("/upload", methods=["POST"])
def upload():
    uploaded = request.files.get("document")
    category = request.form.get("category", "Other")
    if not uploaded or not uploaded.filename:
        flash("Choose a file to upload.", "error")
        return redirect(url_for("index"))
    if category not in CATEGORIES:
        category = "Other"
    original_name = secure_filename(uploaded.filename)
    if not original_name or not allowed_file(original_name):
        flash("That file type is not allowed. Try PDF, Office documents, images, or text files.", "error")
        return redirect(url_for("index"))

    unique_id = uuid.uuid4().hex[:10]
    if STORAGE_MODE == "s3":
        if not S3_BUCKET:
            flash("S3 mode is selected, but S3_BUCKET is not configured.", "error")
            return redirect(url_for("index"))
        key = f"documents/{category.replace(' ', '_')}/{unique_id}_{original_name}"
        try:
            s3_client().upload_fileobj(
                uploaded,
                S3_BUCKET,
                key,
                ExtraArgs={"ContentType": uploaded.mimetype or "application/octet-stream"},
            )
        except Exception:
            app.logger.exception("S3 upload failed")
            flash("Upload to S3 failed. Check AWS credentials, bucket region, and permissions.", "error")
            return redirect(url_for("index"))
    else:
        stored_filename = f"{category.replace(' ', '_')}--{unique_id}--{original_name}"
        uploaded.save(LOCAL_STORAGE / stored_filename)

    flash(f"{original_name} uploaded successfully.", "success")
    return redirect(url_for("index"))


@app.route("/download/<path:doc_id>")
def download(doc_id):
    if STORAGE_MODE == "s3":
        if not S3_BUCKET or not doc_id.startswith("documents/"):
            abort(404)
        try:
            obj = s3_client().get_object(Bucket=S3_BUCKET, Key=doc_id)
            filename = doc_id.rsplit("/", 1)[-1].split("_", 1)[-1]
            from flask import Response
            return Response(
                obj["Body"].read(),
                mimetype=obj.get("ContentType", "application/octet-stream"),
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            app.logger.exception("S3 download failed")
            abort(404)
    safe_id = os.path.basename(doc_id)
    path = LOCAL_STORAGE / safe_id
    if not path.is_file():
        abort(404)
    parts = safe_id.split("--", 2)
    filename = parts[2] if len(parts) == 3 else safe_id
    return send_from_directory(LOCAL_STORAGE, safe_id, as_attachment=True, download_name=filename)


@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. The demo limit is 10 MB.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Local development only. Use a production WSGI server for deployment.
    app.run(debug=True)
