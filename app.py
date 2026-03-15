import os
import logging
import traceback
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)
CORS(app)

# Cache 5 min
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

API_KEY = "TubeFlow_786_Secure"


# ---------------- LOGGING ----------------

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(logging.DEBUG)


class YDLLogger:
    def debug(self, msg):
        app.logger.debug(f"[yt-dlp] {msg}")

    def warning(self, msg):
        app.logger.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        app.logger.error(f"[yt-dlp] {msg}")


# ---------------- YT-DLP OPTIONS ----------------

def get_ydl_opts(extract_flat=False):
    return {
        "quiet": False,
        "logger": YDLLogger(),
        "no_warnings": False,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "extract_flat": extract_flat,
        "noplaylist": True,
        "format": "bestaudio/best",
        "allow_unplayable_formats": True,

        # Node runtime for JS challenge
        "js_runtimes": {
            "node": {"binary": "node"}
        },

        # YouTube bypass
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "ios"]
            }
        },

        "user_agent": (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36"
        ),

        "source_address": "0.0.0.0"
    }


# ---------------- AUTH ----------------

@app.before_request
def check_auth():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401


# ---------------- SEARCH ----------------

@app.route("/api/search", methods=["GET"])
@cache.cached(query_string=True)
def search():
    q = request.args.get("q")

    if not q:
        return jsonify([]), 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(True)) as ydl:
            info = ydl.extract_info(
                f"ytsearch15:{q}",
                download=False
            )

            results = []

            for e in info.get("entries", []):
                if not e:
                    continue

                results.append({
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "uploader": e.get("uploader"),
                    "duration": e.get("duration")
                })

            return jsonify(results)

    except Exception:
        app.logger.error(traceback.format_exc())
        return jsonify([]), 500


# ---------------- EXTRACT ----------------

@app.route("/api/extract", methods=["GET"])
@cache.cached(query_string=True)
def extract():

    url = request.args.get("url")

    if not url:
        return jsonify({"error": "URL missing"}), 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(False)) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

            return jsonify({
                "stream_url": info.get("url"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail")
            })

    except Exception:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Extract failed"}), 500


# ---------------- SIMILAR ----------------

@app.route("/api/similar", methods=["GET"])
def similar():

    vid = request.args.get("id")

    if not vid:
        return jsonify([]), 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(True)) as ydl:

            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}",
                download=False
            )

            return jsonify(
                info.get("related_videos", [])[:10]
            )

    except Exception:
        app.logger.error(traceback.format_exc())
        return jsonify([]), 500


# ---------------- LOCAL RUN ----------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 3000))
    )
