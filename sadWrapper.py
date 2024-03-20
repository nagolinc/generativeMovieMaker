import sys
sys.path.append("D:/img/SadTalker")

from inference import main

import torch


class Args:
    def __init__(self,driven_audio,source_image):
        self.driven_audio = driven_audio
        self.source_image = source_image
        self.ref_eyeblink = None
        self.ref_pose = None
        self.checkpoint_dir = 'D:/img/SadTalker/checkpoints'
        self.result_dir = 'D:/img/SadTalker/results'
        self.pose_style = 0
        self.batch_size = 2
        self.size = 256
        self.expression_scale = 1.0
        self.input_yaw = None
        self.input_pitch = None
        self.input_roll = None
        self.enhancer = None
        self.background_enhancer = None
        self.cpu = False
        self.face3dvis = False
        self.still = False
        self.preprocess = 'crop'
        self.verbose = False
        self.old_version = False
        self.net_recon = 'resnet50'
        self.init_path = None
        self.use_last_fc = False
        self.bfm_folder = 'D:/img/SadTalker/checkpoints/BFM_Fitting/'
        self.bfm_model = 'BFM_model_front.mat'
        self.focal = 1015.
        self.center = 112.
        self.camera_d = 10.
        self.z_near = 5.
        self.z_far = 15.
        # Set device based on CUDA availability
        self.device = "cuda" if torch.cuda.is_available() and not self.cpu else "cpu"

def sadTalker(
    audio_path="D:/img/movieMaker/static/samples/20240313184545_four_score_and_seven_years_ago.wav",
    img_path="D:/img/movieMaker/static/samples/2024-03-13-16-39-27_emma_watson.png"        
    ):
        
    # Create an instance of the Args class
    args = Args(audio_path,img_path)


    result = main(args,current_root_path="D:/img/SadTalker")
    return result