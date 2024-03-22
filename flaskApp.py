from flask import Flask, request, jsonify
import generation_functions
import os

from sadWrapper import sadTalker

import dataset

from threading import Lock

from PIL import Image

import numpy as np

import shutil


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


import cv2
import numpy as np
import json
from decord import VideoReader, cpu
from moviepy.editor import AudioFileClip, CompositeAudioClip, concatenate_audioclips
import datetime
import subprocess

def generateVideo(project_id, width=512, height=512):
    project_json_string = db["savedata"].find_one(key=project_id)["data"]
    project = json.loads(project_json_string)
    elements = sorted(project['elements'].values(), key=lambda e: e['start'])
    
    duration = 0
    
    for element in elements:
        element_duration = element['start'] + element['duration']
        if element_duration > duration:
            duration = element_duration
    
    # Initialize a blank video frame array
    final_output_fps=30
    video_frames = np.zeros((int(duration * final_output_fps), height, width, 3), dtype=np.uint8)  # Assuming 30 fps
    
    audio = AudioClip(lambda t: 0, duration=duration)
    audio.fps = 44100

    for element in elements:
        start = element['start']
        end = start + element['duration']
        if 'chosen' in element and element['chosen']:
            start_frame = int(element['start'] * 30)  # Assuming 30 fps
            end_frame = start_frame + int(element['duration'] * 30)
        
            
            if element['elementType'] == 'image':
                img = cv2.imread("." + element['chosen'])
                img_resized = cv2.resize(img, (width, height))
                for f in range(start_frame, min(end_frame, len(video_frames))):
                    video_frames[f] = img_resized
            
    for element in elements:
        if 'chosen' in element and element['chosen']:
            elementType = element['elementType']
            chosen = element['chosen']
            start = element['start']
            end = start + element['duration']

            if elementType in ['svd', 'talkingHeadVideo']:
                vr = VideoReader("." + chosen, ctx=cpu(0))
                input_fps = vr.get_avg_fps()
                frame_duration = 1 / input_fps
                total_frames = len(vr)

                for output_frame_index in range(int(start * final_output_fps), int(end * final_output_fps)):
                    # Calculate the corresponding time in the video for the current frame
                    current_time = (output_frame_index - int(start * final_output_fps)) / final_output_fps
                    # Determine the source frame index, with looping for 'svd' type
                    if elementType == 'svd':
                        source_frame_index = int(current_time / frame_duration) % total_frames
                    else:
                        source_frame_index = min(int(current_time / frame_duration), total_frames - 1)

                    if 0 <= source_frame_index < total_frames:
                        frame = vr[source_frame_index].asnumpy()
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        frame_resized = cv2.resize(frame, (width, height))
                        video_frames[output_frame_index] = frame_resized

            
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


    # Save video_frames to a video file using OpenCV
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    clean_project_id = "".join([c if c.isalnum() else "_" for c in project_id])
    video_filename = f"static/samples/{date}-{clean_project_id}_video.mp4"
    out = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))
    for frame in video_frames:
        out.write(frame)
    out.release()
    
    # Save audio to file
    #audio_filename = f"static/samples/{date}-{clean_project_id}_audio.mp3"
    
    
    audio.fps = 44100
    #audio.write_audiofile(audio_filename, codec='aac')
    
    audio_filename = f"static/samples/{date}-{clean_project_id}_audio.m4a"
    audio.write_audiofile(audio_filename, codec='aac')

    # Final video filename
    final_filename = f"static/samples/{date}-{clean_project_id}.mp4"

    # Use ffmpeg to combine video and audio
    # Use ffmpeg to re-encode the video for web compatibility
    cmd = [
        'ffmpeg',
        '-i', video_filename,  # Input video file
        '-i', audio_filename,  # Input audio file
        '-c:v', 'libx264',  # Video codec: H.264
        '-preset', 'medium',  # Preset for encoding speed vs compression ratio
        '-tune', 'film',  # Tune the encoder for the type of content
        '-crf', '23',  # Constant Rate Factor (quality level, lower is better quality)
        '-profile:v', 'main',  # H.264 profile level
        '-level', '4.0',  # H.264 level
        '-movflags', '+faststart',  # Optimize MP4 for fast web start
        '-c:a', 'aac',  # Audio codec: AAC
        '-b:a', '128k',  # Audio bitrate
        '-strict', '-2',  # Allow experimental codecs, if necessary
        '-y',  # Overwrite output files without asking
        final_filename  # Output file
    ]
    subprocess.run(cmd)


    # Optionally, delete the temporary video and audio files
    # os.remove(video_filename)
    # os.remove(audio_filename)

    return final_filename



def generateVideo1(project_id, width=512, height=512):
    
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
    



import cv2
import numpy as np
import shutil
import os
import subprocess

def generateSadTalkerVideo(audio,image):
    crop_info, result = sadTalker(audio,image)
    
    print("crop info",crop_info)
    
    #x0,y0,x1,y1 = crop_info[1]
    
    # Extracting the bounding box of the cropped region in the original image
    x0_cropped, y0_cropped, x1_cropped, y1_cropped = crop_info[1]

    # Extracting the smaller box coordinates within the cropped region
    left_small, top_small, right_small, bottom_small = crop_info[2]

    # Calculating the coordinates of the smaller box in the original image's coordinate space
    x0_small_original = x0_cropped + left_small
    y0_small_original = y0_cropped + top_small
    x1_small_original = x0_cropped + right_small
    y1_small_original = y0_cropped + bottom_small
    
    x0=int(x0_small_original)
    y0=int(y0_small_original)
    x1=int(x1_small_original)
    y1=int(y1_small_original)
        
    # Load the original image
    original = cv2.imread(image)
    
    # Open the animated face video
    animated_face = cv2.VideoCapture(result)

    # Get the video's width, height, and frames per second (fps)
    fps = animated_face.get(cv2.CAP_PROP_FPS)

    # Calculate the number of frames in the animated face video
    animated_face_length = int(animated_face.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate the duration of the video in seconds
    duration = animated_face_length / fps

    # Create a VideoWriter object to write the output video
    output = cv2.VideoWriter('temp_output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (original.shape[1], original.shape[0]))

    frame_number = 0
    while frame_number < duration * fps:
        ret_anim, frame_anim = animated_face.read()

        if not ret_anim:
            break

        # Use modulo to loop over animated face frames if frame_number exceeds animated_face_length
        frame_index = frame_number % animated_face_length

        # Resize the animated face to fit the original face's location
        frame_anim_resized = cv2.resize(frame_anim, (x1-x0, y1-y0))

        # Overlay the animated face onto the original image
        original[y0:y1, x0:x1] = frame_anim_resized

        # Write the frame to the output video
        output.write(original)

        frame_number += 1

    # Release the VideoCapture and VideoWriter objects
    animated_face.release()
    output.release()

    # Re-encode the video using ffmpeg to ensure compatibility with web browsers
    subprocess.run(['ffmpeg', '-i', 'temp_output.mp4', '-i', result, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-y', 'output.mp4'])

    # Remove the temporary output file
    os.remove('temp_output.mp4')

    #copy result into static/samples/
    sample_path = "static/samples/" + os.path.basename(result)
    shutil.copy('output.mp4', sample_path)
    #return path to result file in static/samples/
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
        
        #get elementData[voice] if present
        voice = elementData.get("voice")
        
        
        with generate_image_lock:
            tts_url = generation_functions.generate_tts(prompt,speaker="static/voices/"+voice)
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


from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"url": "/static/uploads/" + filename}), 200

    return jsonify({"error": "File upload failed"}), 500



def getThumbnail(project_id):
    project_json_string = db["savedata"].find_one(key=project_id)["data"]
    project = json.loads(project_json_string)
    elements = sorted(project['elements'].values(), key=lambda e: e['start'])
    #find the first image
    for element in elements:
        if element['elementType'] == 'image':
            return element['chosen']
    return None

#list projects
@app.route("/listProjects", methods=["GET"])
def list_projects():
    projects = db["savedata"].all()
    projects = [p["key"] for p in projects]
    thumbnails = []
    
    
    for project in projects:
        thumbnail = getThumbnail(project)
        if thumbnail:
            thumbnails.append(thumbnail)
        else:
            thumbnails.append(None)
    
    
    return jsonify({"projects": projects, "thumbnails": thumbnails})


if __name__ == "__main__":
    generation_functions.setup(
        need_txt2img=True,
        need_music=True,
        need_tts=True,
        need_svd=True,
    )
    app.run(debug=True, use_reloader=False)
