import os
import argparse
import torch
import soundfile as sf
import logging
from datetime import datetime

import sys

import glob

new_path = "D:/img/Spark-TTS"
# Add to sys.path if not already present
if new_path not in sys.path:
    sys.path.append(new_path)


from cli.SparkTTS import SparkTTS

#prompt_speech_path = "D:/img/Spark-TTS/ssstik.io_1721697730794.mp3"


save_dir="static/samples"

_device=0

#make save_dir
os.makedirs(save_dir, exist_ok=True)

model_dir="D:/img/Spark-TTS/pretrained_models/Spark-TTS-0.5B"

def tts(text,
        prompt_speech_path = "D:/img/Spark-TTS/bed3.wav",
        max_new_tokens=1000,
        ):
    """Perform TTS inference and save the generated audio."""
    logging.info(f"Using model from: {model_dir}")
    logging.info(f"Saving audio to: {save_dir}")

    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Convert device argument to torch.device
    device = torch.device(f"cuda:{_device}")

    # Initialize the model
    model = SparkTTS(model_dir, device)

    # Generate unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_path = os.path.join(save_dir, f"{timestamp}.wav")

    logging.info("Starting inference...")

    # Perform inference and save the output audio
    with torch.no_grad():
        wav = model.inference(
            text,
            prompt_speech_path,
            prompt_text=None,
            #gender="female",
            #pitch="high",
            #speed="high",
            max_new_tokens=max_new_tokens,
        )
        sf.write(save_path, wav, samplerate=16000)

    logging.info(f"Audio saved at: {save_path}")
    
    return save_path


#male voices are in static/voices/male_voices
#female voices are in static/voices/female_voices


import glob

voices_male = glob.glob("./static/voices_male/*.wav")
voices_female = glob.glob("./static/voices_female/*.wav")
print("voices", voices_male, voices_female)


def trim_words(text, max_words=50):
    words = text.split()
    return " ".join(words[:max_words])

import re

def cleanup_string(text):
    return re.sub(r"[^a-zA-Z\' .?,!]", " ", text)


def makeSpeech(caption, gender, voice_id):

    if gender == "male":
        voice = voices_male[voice_id % len(voices_male)]
    else:
        voice = voices_female[voice_id % len(voices_female)]

    speech_audio = tts(trim_words(cleanup_string(caption)), prompt_speech_path=voice)

    return speech_audio
    
if __name__=='__main__':
    tts("Hello, world!")    