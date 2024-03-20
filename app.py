import streamlit as st
import generation_functions
from base64 import b64encode
from io import BytesIO

# Functions from your generation_functions module
#def generateImage(prompt):
#    return generation_functions.generate_image(prompt)


# Functions from your generation_functions module
def generateImage(prompt):
    # Assuming generation_functions.generate_image returns a PIL Image
    image = generation_functions.generate_image(prompt)
    # Convert PIL Image to base64 encoded string
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = b64encode(buffered.getvalue()).decode()
    return img_str

def generateDialogue(text):
    return generation_functions.tts(text)

def generateMusic(prompt):
    return generation_functions.generate_music(prompt)

def generateSoundEffect(effect):
    return generation_functions.generate_sound(effect)


def generateVideo(images,duration):
    return generation_functions.generate_video(images,duration)

def generateSpeakingVideo(dialogue,image):
    return generation_functions.generate_speaking_video(dialogue,image)

# Ensure the 'timeline' key exists in the session state
def ensure_timeline_initialized():
    if 'timeline' not in st.session_state:
        st.session_state.timeline = []

ensure_timeline_initialized()

# Function to add elements to the timeline
def add_to_timeline(element_type, content, start_time, duration):
    st.session_state.timeline.append({
        'type': element_type,
        'content': content,
        'start_time': start_time,
        'duration': duration
    })
    
    #set the next start time
    st.session_state.next_start_time = start_time + duration
    
    
# Function to get the next start time
def get_next_start_time():
    if not st.session_state.timeline:
        return 0
    return max(element['start_time'] for element in st.session_state.timeline)

# Function to calculate the total duration
def calculate_total_duration():
    if not st.session_state.timeline:
        return 0
    out = max(element['start_time'] + element['duration'] for element in st.session_state.timeline)
    return max(10, out)

# Function to display the timeline
# Function to display the timeline
def display_timeline():
    total_duration = calculate_total_duration()
    if total_duration == 0:
        st.write("No elements in the timeline yet.")
        return

    # Sort elements by start time
    sorted_timeline = sorted(st.session_state.timeline, key=lambda e: e['start_time'])

    # Container to hold the timeline visuals
    timeline_container = st.container()

    with timeline_container:
        for element in sorted_timeline:
            # Calculate the left margin as the start time percentage of the total duration
            start_percentage = (element['start_time'] / total_duration) * 100
            # Calculate the width as the duration percentage of the total duration
            width_percentage = (element['duration'] / total_duration) * 100

            # For images, we'll use custom HTML to place the image on top of a timeline block
            if element['type'] == 'Image':
                # Image block with overlay
                st.markdown(f"""
                    <div style="display: flex; align-items: center; width: 100%;">
                        <div style="margin-left: {start_percentage}%; width: {width_percentage}%; position: relative; background-color: #ddd;">
                            <img src="data:image/png;base64,{element['content']}" style="width: 100%; position: absolute; top: 0; left: 0;"/>
                            <div style="position: absolute; width: 100%; bottom: 0; background-color: rgba(0, 0, 0, 0.5); color: white; padding: 5px; text-align: center;">
                                {element['type']}: {element['start_time']}s - {element['duration']}s
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Display other types of elements as a block in the timeline
                st.markdown(f"""
                    <div style="display: flex; align-items: center; width: 100%;">
                        <div style="margin-left: {start_percentage}%; width: {width_percentage}%; background-color: #ddd; padding: 10px; text-align: center;">
                            {element['type']}: {element['content']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Add a time indicator at the bottom of the timeline
        st.markdown(f"""
            <div style="position: relative; width: 100%; border-top: 2px solid #000;">
                <span style="position: absolute; left: 0;">0:00</span>
                <span style="position: absolute; left: 50%;">{total_duration/2:0.2f}</span>
                <span style="position: absolute; right: 0;">{total_duration:0.2f}</span>
            </div>
        """, unsafe_allow_html=True)


# Main app logic
if __name__ == "__main__":
    
    generation_functions.setup(need_txt2img=True)
    
    st.title("Timeline Generation App")
    
    # Interface for adding elements
    with st.form("element_form"):
        element_type = st.selectbox("Select Element Type", ["Image", "Dialogue", "Music", "Sound Effect"])
        content = st.text_input("Enter prompt for Image/Dialogue or name for Sound Effect")
        start_time = st.number_input("Start Time (seconds)", min_value=0.0, step=0.1)
        duration = st.number_input("Duration (seconds)", min_value=0.1, step=0.1,value=2.0)
        submit = st.form_submit_button("Add to Timeline")

        if submit:
            # Depending on the type, call the appropriate generation function
            if element_type == "Image":
                generated_content = generateImage(content)
            elif element_type == "Dialogue":
                generated_content = generateDialogue(content)
            elif element_type == "Music":
                generated_content = generateMusic(content)
            elif element_type == "Sound Effect":
                generated_content = generateSoundEffect(content)
            
            # Add the generated content to the timeline
            add_to_timeline(element_type, generated_content, start_time, duration)
            # Redisplay the timeline with the new content
            display_timeline()

    #display_timeline()
