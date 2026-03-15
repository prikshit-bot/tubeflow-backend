import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)
CORS(app)

# Production Caching (5 min)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

API_KEY = "TubeFlow_786_Secure" # Kotlin app mein header mein dalna

def get_ydl_opts(extract_flat=False):
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'extract_flat': extract_flat,
        'js_runtimes': {'node': {'binary': 'node'}}, # JS Challenge solver
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36'
    }

# Security Middleware
@app.before_request
def check_auth():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/api/search', methods=['GET'])
@cache.cached(query_string=True)
def search():
    q = request.args.get('q')
    if not q: return jsonify([]), 400
    with yt_dlp.YoutubeDL(get_ydl_opts(True)) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch15:{q}", download=False)
            return jsonify([{"id": e['id'], "title": e['title'], "uploader": e.get('uploader')} for e in info.get('entries', []) if e])
        except: return jsonify([]), 500

@app.route('/api/extract', methods=['GET'])
@cache.cached(query_string=True)
def extract():
    url = request.args.get('url')
    if not url: return jsonify({"error": "URL missing"}), 400
    with yt_dlp.YoutubeDL(get_ydl_opts(False)) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return jsonify({"stream_url": info.get('url'), "title": info.get('title'), "duration": info.get('duration')})
        except: return jsonify({"error": "Failed"}), 500

@app.route('/api/similar', methods=['GET'])
def similar():
    vid = request.args.get('id')
    if not vid: return jsonify([]), 400
    with yt_dlp.YoutubeDL(get_ydl_opts(True)) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            return jsonify(info.get('related_videos', [])[:10]) # For Smart Queue
        except: return jsonify([]), 500