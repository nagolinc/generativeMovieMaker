from audiocraft.models import MAGNeT
from audiocraft.data.audio import audio_write
import re
from datetime import datetime
import os



from transformers import pipeline
import scipy

synthesiser = None




def generate_filename(prompt, keyword="music",extension="wav"):
    sanitized_prompt = re.sub(r'[^a-zA-Z0-9]+', '_', prompt)[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitized_prompt}_{timestamp}_{keyword}.{extension}"


def generate_music(description,save_path="./static/samples"):
    global synthesiser
    if synthesiser is None:
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
        synthesiser = pipeline("text-to-audio", "facebook/musicgen-small")
    
    filename = os.path.join(save_path, generate_filename(description))
    
    music = synthesiser(description, forward_params={"do_sample": True})

    scipy.io.wavfile.write(filename, rate=music["sampling_rate"], data=music["audio"])#this apparently adds .wav to the filename
    return filename


def get_music(save_path="./static/samples"):
    # Search for all files ending with .wav and return them with their full paths
    wav_files = [os.path.join(save_path, f) for f in os.listdir(save_path) if f.endswith('_music.wav')]
    return wav_files
