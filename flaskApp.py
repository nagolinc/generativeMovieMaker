from flask import Flask, request, jsonify
import generation_functions
import os

from sadWrapper import sadTalker

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


import logging
logging.basicConfig(level=logging.DEBUG)

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
            elif element['elementType'] in ['svd','talkingHeadVideo']:
                video_clip = VideoFileClip("."+element['chosen'])
                loops = int(element['duration'] // video_clip.duration) + 1
                video_clips = [video_clip for _ in range(loops)]
                video_clip = concatenate_videoclips(video_clips).subclip(0, element['duration'])
                
                # Resize the video_clip to match the size of the video
                video_clip = video_clip.resize(video.size)
                
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
    #video.write_videofile(filename)
    #video.write_videofile(filename, codec='h264_nvenc', ffmpeg_params=['-preset', 'fast'])
    print("params",['-preset', 'fast', '-v', 'verbose'])
    #video.write_videofile(filename, codec='h264_nvenc', ffmpeg_params=['-preset', 'fast', '-v', 'verbose'])
    
    video.write_videofile(
        filename,
        threads=5,
        bitrate="2000k",
        audio_codec="aac",
        codec="h264_nvenc",
    )

    
    return filename
    
@app.route("/generateVideo", methods=["POST"])
def generate_video():
    data = request.json
    project_id = data["projectId"]
    url =generateVideo(project_id)
    #prepend / to url
    url = "/" + url
    return jsonify({"url": url})
    
import shutil

def generateSadTalkerVideo(audio,image):
    result = sadTalker(audio,image)
    #copy result into static/samples/
    shutil.copy(result, "static/samples/")
    #return path to result file in static/samples/
    sample_path = "static/samples/" + os.path.basename(result)
    return sample_path

@app.route("/getVoices", methods=["GET"])
def get_voices():
    voices_dir = "static/voices"
    voices = [f for f in os.listdir(voices_dir) if os.path.isfile(os.path.join(voices_dir, f))]
    return jsonify({"voices": voices})

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
    elif elementType=="talkingHeadVideo":
        with generate_image_lock:
            time = elementData["start"]
            audioElement=getElement(projectId, time, "speech")
            if not audioElement:
                return jsonify({"error": "No sound found for this time"}), 400
            audioUrl = "."+audioElement['chosen']
            if audioUrl == None:
                return jsonify({"error": "No sound found for this time"}), 400
            #check if file exists and is an audio file
            if os.path.isfile(audioUrl) and audioUrl.endswith(('.mp3', '.wav')):
                pass
            else:
                return jsonify({"error": "Invalid audio file"}), 400
            #load audio
            audio = AudioFileClip(audioUrl)
            #get image
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
            
            #for sadtalker we need the full path
            full_image_path = os.path.abspath(imageUrl)
            full_audio_path = os.path.abspath(audioUrl)
            #generate movie
            talking_head_video_url = generateSadTalkerVideo(full_audio_path, full_image_path)
            #prepend / to url
            talking_head_video_url = "/" + talking_head_video_url
        return jsonify({"url": talking_head_video_url})
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
