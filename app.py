import os
import requests
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Multiple Instances for 100% Uptime
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://api-piped.mha.fi",
    "https://piped-api.lunar.icu"
]

API_KEY = "TubeFlow_786_Secure"

# Helper Function for Multi-Piped Rotation
def fetch_from_piped(endpoint):
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/{endpoint}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            continue
    return None

@app.before_request
def check_auth():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/api/search')
@cache.cached(query_string=True)
def search():
    q = request.args.get('q')
    if not q: return jsonify([]), 400
    
    data = fetch_from_piped(f"search?q={q}&filter=music_videos")
    if not data: return jsonify([]), 500
    
    results = []
    for i in data.get('items', []):
        if i.get('type') == 'stream':
            results.append({
                "id": i['url'].split('=')[-1],
                "title": i.get('title'),
                "uploader": i.get('uploaderName'),
                "duration": i.get('duration', 0),
                "thumbnail": i.get('thumbnail')
            })
    return jsonify(results)

@app.route('/api/extract')
def extract():
    vid = request.args.get('id')
    if not vid: return jsonify({"error": "ID missing"}), 400
    
    data = fetch_from_piped(f"streams/{vid}")
    if not data or not data.get('audioStreams'):
        return jsonify({"error": "No streams found"}), 500
    
    # Safe Audio Stream selection
    streams = data.get('audioStreams', [])
    stream_url = streams[0]['url'] if streams else None
    
    return jsonify({
        "stream_url": stream_url,
        "title": data.get('title'),
        "duration": data.get('duration'),
        "thumbnail": data.get('thumbnailUrl') or data.get('thumbnail')
    })

@app.route('/api/similar')
def similar():
    vid = request.args.get('id')
    if not vid: return jsonify([]), 400
    
    data = fetch_from_piped(f"streams/{vid}")
    if not data: return jsonify([]), 500
    
    rel = data.get('relatedStreams', [])
    return jsonify([{
        "id": r['url'].split('=')[-1],
        "title": r.get('title'),
        "uploader": r.get('uploaderName')
    } for r in rel[:10]])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
