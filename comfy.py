import json
from urllib import request, parse
import random
import time
import glob
import shutil
import os
import sys


#This is the ComfyUI api prompt format.

#If you want it for a specific workflow you can "enable dev mode options"
#in the settings of the UI (gear beside the "Queue Size: ") this will enable
#a button on the UI to save workflows in api format.

#keep in mind ComfyUI is pre alpha software so this format will change a bit.

import yaml

COMFY_HOME="D:/img/comfy2/ComfyUI_windows_portable/ComfyUI"



def find_unique_prefix(directory, prefix):
    i = 0
    while True:
        unique_prefix = f"{prefix}_{i}"
        if not any(fname.startswith(unique_prefix) for fname in os.listdir(directory)):
            return unique_prefix
        i += 1

def generate_comfy(input_prompt,seed=-1,prefix="",yaml_file="sd3_comfy.yaml",width=1024,height=1024,suffix=".png",image=None):
    
    yaml_data = yaml.safe_load(open(yaml_file).read())
    
    
    #this is the one for the default workflow
    prompt_text = open(yaml_data['workflow'],encoding="utf-8").read()
    
    
    if seed==-1:
        seed=random.randint(0,1000000)

    prompt_data=json.loads(prompt_text)

    my_prompt=prefix+input_prompt

    #print(prompt_data['43']['inputs']['Text'])

    #prompt_data['6']['inputs']['text']=my_prompt
    if 'prompt' in yaml_data:
        prompt_data[yaml_data['prompt'][0]][yaml_data['prompt'][1]][yaml_data['prompt'][2]]=my_prompt
    
    
    api_dir = os.path.join(COMFY_HOME, 'output/api')

    #make directory if it doesn't exist
    if not os.path.exists(api_dir):
        os.makedirs(api_dir)
    
    unique_prefix = find_unique_prefix(api_dir, 'img')
    prompt_data[yaml_data['output'][0]][yaml_data['output'][1]][yaml_data['output'][2]] = f"api/{unique_prefix}"
    
    #n=random.randint(0,1000000)
    #prompt_data['273']['inputs']['filename_prefix']="api/img_"+str(n)
    #prompt_data[yaml_data['output'][0]][yaml_data['output'][1]][yaml_data['output'][2]]="api/img_"+str(n)
    
    
    #if output2 is in the yaml file, set it to the same as output
    if 'output2' in yaml_data:
        prompt_data[yaml_data['output2'][0]][yaml_data['output2'][1]][yaml_data['output2'][2]]="api/img_"+str(n+1)
    
    
    #prompt_data['271']['inputs']['seed']=seed
    prompt_data[yaml_data['seed'][0]][yaml_data['seed'][1]][yaml_data['seed'][2]]=seed
    
    
    #width
    if 'width' in yaml_data:
        print('setting width',width)
        prompt_data[yaml_data['width'][0]][yaml_data['width'][1]][yaml_data['width'][2]]=width
    #height
    if 'height' in yaml_data:
        print('setting height',height)
        prompt_data[yaml_data['height'][0]][yaml_data['height'][1]][yaml_data['height'][2]]=height
        
        
    #image
    if image is not None and 'image' in yaml_data:
        #save image in {comfy_home}/input/
        image_filename = os.path.join(COMFY_HOME, 'input', 'input_image.png')
        image.save(image_filename)
        prompt_data[yaml_data['image'][0]][yaml_data['image'][1]][yaml_data['image'][2]] = 'input_image.png'
    

    prompt_text_2=json.dumps(prompt_data)

    def queue_prompt(prompt):
        p = {"prompt": prompt}
        data = json.dumps(p).encode('utf-8')
        req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
        request.urlopen(req)


    prompt = json.loads(prompt_text_2)
    

    queue_prompt(prompt)
    
    #we need to look in D:\img\comfy2\ComfyUI_windows_portable\ComfyUI\output\toon for the output
    # which will look like sd3/img_1234567890.mp4
    
    while True:
        #look for file
        #g=glob.glob(COMFY_HOME+"/output/api/img_"+str(n)+"*"+suffix)
        g=glob.glob(COMFY_HOME+"/output/api/"+unique_prefix+"*"+suffix)
        if g:
            #wait 1 second to make sure file is done writing
            time.sleep(1)
            print(g)
            #copy to static/samples
            shutil.copy(g[0],"static/samples")
            output_filename="static/samples/"+os.path.basename(g[0])
            break
        
        time.sleep(1)
        
        
    #if output2 is in the yaml file, wait for it too
    if 'output2' in yaml_data:
        while True:
            #look for file
            g=glob.glob("D:/img/comfy2/ComfyUI_windows_portable/ComfyUI/output/api/img_"+str(n+1)+"*"+suffix)
            if g:
                #wait 1 second to make sure file is done writing
                time.sleep(1)
                print(g)
                #copy to static/samples
                shutil.copy(g[0],"static/samples")
                output_filename2="static/samples/"+os.path.basename(g[0])
                break

            time.sleep(1)
    
    return output_filename


if __name__ == "__main__":
    #read prompt from command line
    prompt = sys.argv[1]
    print(prompt)
    generate_mov(prompt)