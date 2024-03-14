from flask import Flask, request, jsonify
import generation_functions
import os

import dataset

from threading import Lock

from PIL import Image

import numpy as np

generate_image_lock = Lock()

# Database configuration
db = dataset.connect("sqlite:///my_database.db")

app = Flask(__name__)


import json
import datetime

def getElement(project_id, time, type):
    project_json_string = db["savedata"].find_one(key=project_id)["data"]
    project = json.loads(project_json_string)
    elements = sorted(project['elements'].values(), key=lambda e: e['start'])
    for element in elements:
        if element['elementType'] == type and element['start'] <= time and element['start'] + element['duration'] > time:
            return element
    return None




from moviepy.editor import ColorClip, AudioClip, ImageClip, VideoFileClip, CompositeVideoClip, CompositeAudioClip,concatenate_videoclips,AudioFileClip,concatenate_audioclips


def generateVideo(project_id, width=512, height=512):
    
    
    
    project_json_string = db["savedata"].find_one(key=project_id)["data"]
    project = json.loads(project_json_string)
    elements = sorted(project['elements'].values(), key=lambda e: e['start'])
    
    #compute duraton = max(start + duration for all elements)
    duration = 0
    for element in elements:
        if element['start'] + element['duration'] > duration:
            duration = element['start'] + element['duration']
    
    video = ColorClip((width, height), col=(0,0,0), duration=duration)
    audio = AudioClip(lambda t: 0, duration=duration)

    for element in elements:
        if 'chosen' in element and element['chosen']:
            start = element['start']
            end = start + element['duration']
            if start<0:
                start=0
            
            if element['elementType'] == 'image':
                img_clip = ImageClip("."+element['chosen'], duration=element['duration'])
                img_clip = img_clip.set_start(start).set_end(end)
                video = CompositeVideoClip([video, img_clip])
            elif element['elementType'] == 'svd':
                video_clip = VideoFileClip("."+element['chosen'])
                loops = int(element['duration'] // video_clip.duration) + 1
                video_clips = [video_clip for _ in range(loops)]
                video_clip = concatenate_videoclips(video_clips).subclip(0, element['duration'])
                video_clip = video_clip.set_start(start).set_end(end)
                video = CompositeVideoClip([video, video_clip])
            elif element['elementType'] in ['music', 'sound']:
                audio_clip = AudioFileClip("."+element['chosen'])
                loops = int(element['duration'] // audio_clip.duration) + 1
                audio_clips = [audio_clip for _ in range(loops)]
                audio_clip = concatenate_audioclips(audio_clips).subclip(0, element['duration'])
                audio_clip = audio_clip.set_start(start).set_end(end)
                audio = CompositeAudioClip([audio, audio_clip])
            elif element['elementType'] == 'speech':
                
                audio_clip = AudioFileClip("."+element['chosen'])
                #make sure end isn't past end of audio
                if end-start > audio_clip.duration:
                    end = start + audio_clip.duration
                audio_clip = audio_clip.set_start(start).set_end(end)
                audio = CompositeAudioClip([audio, audio_clip])
            
    video.audio = audio
    #filename = f"static/samples/{datetime}-{project_id}.mp4"
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    #replace all characters that aren't a-z or 0-9 with _
    clean_project_id = "".join([c if c.isalnum() else "_" for c in project_id])
    filename = f"static/samples/{date}{clean_project_id}.mp4"
    video.write_videofile(filename)
    
    return filename
    
@app.route("/generateVideo", methods=["POST"])
def generate_video():
    data = request.json
    project_id = data["projectId"]
    url =generateVideo(project_id)
    #prepend / to url
    url = "/" + url
    return jsonify({"url": url})
    


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    elementData=data["elementData"]
    projectId = data["projectId"]
    
    
    elementType = elementData["elementType"]
    prompt = elementData["prompt"]
    duration = elementData["duration"]
    
    if elementType == "image":
        with generate_image_lock:
            image_url = generation_functions.generate_image_url(prompt)
        return jsonify({"url": image_url})
    #music
    elif elementType == "music":
        with generate_image_lock:
            music_url = generation_functions.generate_music(prompt, duration)
        return jsonify({"url": music_url})
    #tts
    elif elementType == "speech":
        with generate_image_lock:
            tts_url = generation_functions.generate_tts(prompt)
            #add / at beginning of url
            tts_url = "/" + tts_url
        return jsonify({"url": tts_url})
    elif elementType=="svd":
        with generate_image_lock:
            time = elementData["start"]
            imageElement=getElement(projectId, time, "image")
            if not imageElement:
                return jsonify({"error": "No image found for this time"}), 400
            imageUrl = "."+imageElement['chosen']
            if imageUrl == None:
                return jsonify({"error": "No image found for this time"}), 400
            #check if file exists and is an image
            if os.path.isfile(imageUrl) and imageUrl.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                pass
            else:
                return jsonify({"error": "Invalid image file"}), 400
            #load image
            image = Image.open(imageUrl)
            #generate movie
            svd_url = generation_functions.generate_video_svd(image)
            #prepend / to url
            svd_url = "/" + svd_url
        return jsonify({"url": svd_url})
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
        need_tts=True,
        need_svd=True,
    )
    app.run(debug=True, use_reloader=False)
