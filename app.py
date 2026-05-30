import logging
import mimetypes
import os
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import safe_join

SERVICE_NAME = "UltriFire Image Server"
IMAGE_DIR = Path(os.environ.get("IMAGE_DIR", "/data/images")).resolve()


def create_app() -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    app.logger.info("Using image directory: %s", IMAGE_DIR)

    @app.get("/")
    def index():
        app.logger.info("Service status requested from %s", request.remote_addr)
        return jsonify({"service": SERVICE_NAME, "status": "online"})

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    @app.get("/images")
    def list_images():
        files = []
        for path in sorted(IMAGE_DIR.iterdir(), key=lambda item: item.name.lower()):
            if path.is_file():
                files.append({"name": path.name, "size_bytes": path.stat().st_size})

        app.logger.info("Listed %s image file(s) for %s", len(files), request.remote_addr)
        return jsonify({"files": files})

    @app.get("/images/<path:filename>")
    def download_image(filename: str):
        safe_path = safe_join(str(IMAGE_DIR), filename)
        if safe_path is None:
            app.logger.warning("Rejected unsafe image path: %s", filename)
            abort(404)

        file_path = Path(safe_path)
        if not file_path.is_file():
            app.logger.warning("Image not found: %s", filename)
            abort(404)

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        file_size = file_path.stat().st_size
        app.logger.info(
            "Streaming image %s (%s bytes, %s) to %s",
            file_path.name,
            file_size,
            content_type,
            request.remote_addr,
        )

        response = send_file(
            file_path,
            mimetype=content_type,
            as_attachment=False,
            download_name=file_path.name,
            conditional=True,
            max_age=0,
        )
        response.headers["Accept-Ranges"] = "bytes"
        if "Content-Length" not in response.headers:
            response.headers["Content-Length"] = str(file_size)
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
