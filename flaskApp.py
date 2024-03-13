from flask import Flask, request, jsonify
import generation_functions


import dataset

from threading import Lock

generate_image_lock = Lock()

# Database configuration
db = dataset.connect("sqlite:///my_database.db")

app = Flask(__name__)


@app.route("/generate", methods=["POST"])
def generate():
    elementType = request.json["elementType"]
    prompt = request.json["prompt"]
    duration = request.json["duration"]
    
    if elementType == "image":
        with generate_image_lock:
            image_url = generation_functions.generate_image_url(prompt)
        return jsonify({"url": image_url})
    #music
    elif elementType == "music":
        with generate_image_lock:
            music_url = generation_functions.generate_music(prompt, duration)
        return jsonify({"url": music_url})
    else:
        return jsonify({"error": "Invalid type"}), 400


@app.route("/save", methods=["POST"])
def save_data():
    key = request.json["key"]
    data = request.json["data"]
    table = db["savedata"]
    table.upsert(dict(key=key, data=data), ["key"])
    return jsonify({"status": "success"}), 200


@app.route("/load", methods=["GET"])
def load_data():
    key = request.args.get("key")
    table = db["savedata"]
    row = table.find_one(key=key)
    if row:
        return jsonify({"data": row["data"]}), 200
    else:
        return jsonify({"error": "No data found for this key"}), 404


if __name__ == "__main__":
    generation_functions.setup(
        need_txt2img=True,
        need_music=True,
    )
    app.run(debug=True, use_reloader=False)
