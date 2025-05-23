let elementCounter = 0;
let elementsData = {};
let timelineDuration = 140; // 5 minutes
let isResizing = false;

//load projectId from url param if it exists
const urlParams = new URLSearchParams(window.location.search);
const projectId = urlParams.get('projectId');
if (projectId) {
  document.getElementById('projectId').value = projectId;
}


let types = ['talkingHeadVideo', 'svd', 'animDiff', 'image', 'music', 'speech']

for (let type of types) {

  const thisType = type

  console.log(type + '-timeline')

  document.getElementById(type + '-timeline').addEventListener('click', function (event) {
    if (event.target === this) {
      // No specific element was clicked, show form for adding a new element
      //compute start and duration
      let start = event.offsetX / this.offsetWidth * timelineDuration
      console.log(start);
      let duration = 10;
      showForm(thisType, 'Add', null, start, duration);
    }
  });
}

function showForm(thisType, action, elementId, start, duration) {
  const form = document.getElementById('elementForm');
  form.style.display = 'block';

  console.log(action, elementId);

  if (action === 'Update' && elementId !== undefined) {
    // Prefill the form with the current element's data
    const elementData = elementsData[elementId];
    document.getElementById('prompt').value = elementData.prompt;
    document.getElementById('start').value = elementData.start;
    document.getElementById('duration').value = elementData.duration;
    document.getElementById('elementId').value = elementId;

    //set end = start+ duraation
    document.getElementById('end').value = elementData.start + elementData.duration;


    //check if elementData has priority, else 0
    if (elementData.priority) {
      document.getElementById('priority').value = elementData.priority;
    } else {
      document.getElementById('priority').value = 0;
    }





  } else {
    // Reset the form for a new element
    document.getElementById('prompt').value = 'a cat in a hat';
    document.getElementById('start').value = start;
    document.getElementById('duration').value = duration;
    document.getElementById('elementId').value = '';
    document.getElementById('elementType').value = thisType;
    elementId = addElement(thisType);
    const elementData = elementsData[elementId];

    console.log("huH?", elementData, elementId, elementsData[elementId])

    document.getElementById('prompt').value = elementData.prompt;
    document.getElementById('start').value = elementData.start;
    document.getElementById('duration').value = elementData.duration;
    document.getElementById('elementId').value = elementId;

    //check if elementData has priority, else 0
    if (elementData.priority) {
      document.getElementById('priority').value = elementData.priority;
    } else {
      document.getElementById('priority').value = 0;
    }


  }



  //change accepty type for uploadFile
  if (thisType === 'image') {
    document.getElementById('uploadFile').accept = "image/*";
  } else if (thisType === 'talkingHeadVideo' || thisType === 'svd' || thisType === 'animDiff') {
    document.getElementById('uploadFile').accept = "video/*";
  } else if (thisType === 'music') {
    document.getElementById('uploadFile').accept = "audio/*";
  } else if (thisType === 'speech') {
    document.getElementById('uploadFile').accept = "audio/*";
  }

  //custom fields
  //clear custom fields
  const customFields = document.getElementById('customFields');
  customFields.innerHTML = '';



  if (thisType === 'speech') {
    addVoicesDropdown(elementId);
  }


  // Set the button text to "Add" or "Update"
  //document.getElementById('addElementButton').textContent = action;

  displayVariants()
}

//upload file in uploadFile to /upload endpoint
function uploadFile() {

  const projectId = document.getElementById('projectId').value;
  const elementId = document.getElementById('elementId').value;
  const fileInput = document.getElementById('uploadFile');
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('elementId', elementId);
  formData.append('projectId', projectId);

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      const elementId = document.getElementById('elementId').value;

      //make sure variants is defined
      if (!elementsData[elementId].variants) {
        elementsData[elementId].variants = [];
      }

      //add uploaded file to variants
      elementsData[elementId].variants.push(data.url);

      //elementsData[elementId].chosen = data.url;
      displayVariants();
      addChosenImage(elementId);

      //save
      doSave();

    })
    .catch(error => {
      console.error('Error:', error);
    });

}


function addVoicesDropdown(elementId) {
  fetch('/getVoices')
    .then(response => response.json())
    .then(data => {
      const voices = data.voices;

      // Create the dropdown
      const select = document.createElement('select');
      select.id = 'voicesDropdown';

      // Populate the dropdown with the voices
      voices.forEach((voice, index) => {
        const option = document.createElement('option');
        option.value = voice;
        option.text = voice;
        select.appendChild(option);
      });

      // Add the dropdown to the form
      const customFields = document.getElementById('customFields');
      customFields.appendChild(select);

      // If an elementId was provided, load the selected voice from elementData
      if (elementId !== undefined) {
        const elementData = elementsData[elementId];

        console.log("huh2?", elementData, elementId, elementsData[elementId])

        if (elementData.voice) {
          select.value = elementData.voice;
        } else {
          //set voice to first option
          select.value = voices[0];
          elementData.voice = voices[0];
        }


        console.log("elementData.voice", elementsData[elementId].voice, "huh", elementData.voice)
      }



      // Add an event listener to the dropdown that updates elementData.voice
      // whenever the selected voice changes
      select.addEventListener('change', (event) => {
        const selectedVoice = event.target.value;
        const elementData = elementsData[elementId];
        elementData.voice = selectedVoice;
      });
    });
}


let dragElement = null;
let dragStartX = 0;
let timelineWidth = 0;


function copyElement() {
  let elementId = document.getElementById('elementId').value;
  let elementData = elementsData[elementId];

  // Copy the elementData
  let newElementData = { ...elementData };

  let thisType = elementsData[elementId].elementType;

  // Generate a new elementId for the copied element
  const newElementId = thisType + '-' + Math.random().toString(36).substring(7);

  // Set the new elementId in the new data
  newElementData.id = newElementId;

  // Change the start in the new data to the end of the copied
  newElementData.start = elementData.start + elementData.duration;

  // Call addElementWithData
  addElementWithData(newElementData); // Assuming this function exists and adds the element with the given data

  // Call showForm with the correct info for the new element
  showForm(thisType, 'Update', newElementId, newElementData.start, newElementData.duration);

  //save
  doSave();
}


function addElement(thisType) {
  const prompt = document.getElementById('prompt').value;
  const startTime = parseFloat(document.getElementById('start').value);
  const durationSeconds = parseFloat(document.getElementById('duration').value);
  const newElementId = thisType + '-' + Math.random().toString(36).substring(7);

  // Create the data object
  const data = {
    id: newElementId,
    elementType: thisType,
    prompt,
    start: startTime,
    duration: durationSeconds
  };

  // Call addElementWithData
  return addElementWithData(data);
}

function addElementWithData(data) {
  const elementType = data.elementType;
  const timeline = document.getElementById(elementType + '-timeline');
  const startPercent = data.start / timelineDuration * 100;
  const durationPercent = data.duration / timelineDuration * 100;

  const newElementId = data['id'];
  const timelineElement = document.createElement('div');
  timelineElement.classList.add('element');
  timelineElement.style.left = `${startPercent}%`;
  timelineElement.style.width = `${durationPercent}%`;
  timelineElement.id = newElementId;
  timelineElement.onclick = function (event) {
    event.stopPropagation();
    let thisType = elementsData[this.id].elementType;
    showForm(thisType, 'Update', this.id);
  };

  timelineElement.innerText = data.prompt;

  // Add resize handle
  const resizeHandle = document.createElement('div');
  resizeHandle.classList.add('resize-handle');
  timelineElement.appendChild(resizeHandle);

  timeline.appendChild(timelineElement);

  elementsData[newElementId] = data;

  console.log("about to die", newElementId);

  addChosenImage(newElementId);

  return newElementId;
}



window.onmousedown = function (event) {
  // Get all timeline elements
  const timelineElements = document.querySelectorAll('.element');

  // Check if the event target is a timeline element, a child of a timeline element, or a resize handle
  for (const timelineElement of timelineElements) {
    if (timelineElement.contains(event.target)) {
      console.log('start drag');
      dragElement = timelineElement;
      dragStartX = event.clientX;
      timelineWidth = timelineElement.parentElement.offsetWidth;

      // Check if the event target is a resize handle
      if (event.target.classList.contains('resize-handle')) {
        isResizing = true; // Start a resize operation
      }

      break;
    }
  }
};

document.onmousemove = function (event) {
  if (dragElement === null) return;

  const dx = event.clientX - dragStartX;

  if (isResizing) {
    const newDurationPercent = parseFloat(dragElement.style.width) + dx / timelineWidth * 100;
    dragElement.style.width = `${newDurationPercent}%`;
    elementsData[dragElement.id].duration = newDurationPercent / 100 * timelineDuration;
  } else {
    const newStartPercent = parseFloat(dragElement.style.left) + dx / timelineWidth * 100;
    dragElement.style.left = `${newStartPercent}%`;
    elementsData[dragElement.id].start = newStartPercent / 100 * timelineDuration;
  }

  dragStartX = event.clientX;
};

document.onmouseup = function (event) {
  //save if we are done dragging
  if (dragElement) {
    doSave();
  }

  dragElement = null;
  isResizing = false;


};

function addElementOrUpdate() {
  const prompt = document.getElementById('prompt').value;
  const startTime = parseFloat(document.getElementById('start').value);
  const durationSeconds = parseFloat(document.getElementById('duration').value);

  //priority
  const priority = document.getElementById('priority').value;


  //update end
  const end = parseFloat(startTime) + parseFloat(durationSeconds);
  console.log("new end", end)
  document.getElementById('end').value = end;

  const startPercent = startTime / timelineDuration * 100; // Convert start time to percent based on 2 minutes total

  const durationPercent = durationSeconds / timelineDuration * 100; // Convert duration to percent based on 2 minutes total
  const elementId = document.getElementById('elementId').value;

  if (elementId) {
    // Update existing element
    const element = document.getElementById(elementId);
    element.style.left = `${startPercent}%`;
    element.style.width = `${durationPercent}%`;
    //id
    elementsData[elementId].id = elementId;
    elementsData[elementId].prompt = prompt;
    elementsData[elementId].start = startTime;
    elementsData[elementId].duration = durationSeconds;

    //priority
    elementsData[elementId].priority = priority;

    //set inner text (prompt)
    element.innerText = prompt;

    addChosenImage(elementId)

    // Re-add resize handle
    const resizeHandle = document.createElement('div');
    resizeHandle.classList.add('resize-handle');
    element.appendChild(resizeHandle);

  } else {
    console.log("this should never happen")
  }

  console.log('priority', priority,elementsData[elementId].priority)


  // Hide the form after adding/updating
  //document.getElementById('elementForm').style.display = 'none';

  //save
  doSave();

}


//upldate the end field
const startTime = document.getElementById('start').value;
const durationSeconds = document.getElementById('duration').value;
const end = parseFloat(startTime) + parseFloat(durationSeconds);
console.log("new end", end)
document.getElementById('end').value = end;



// Get references to the form fields
const promptField = document.getElementById('prompt');
const startField = document.getElementById('start');
const durationField = document.getElementById('duration');

// Add event listeners to the form fields
promptField.addEventListener('change', updateElement);
startField.addEventListener('change', updateElement);
durationField.addEventListener('change', updateElement);
//priority
const priorityField = document.getElementById('priority');
priorityField.addEventListener('change', updateElement);


//when end is changed, we need to first calculate the new duration and then call update element
const endField = document.getElementById('end');
endField.addEventListener('change', function () {
  const start = parseFloat(document.getElementById('start').value);
  const end = parseFloat(document.getElementById('end').value);
  const newDuration = end - start;
  document.getElementById('duration').value = newDuration;
  updateElement();
});


function updateElement() {
  // Call your existing update function
  addElementOrUpdate();
}

// Functionality to handle clicking on an element to edit it would be added here

// Hide the form initially
document.getElementById('elementForm').style.display = 'none';

// Add ID field to the form (hidden from the user)
//const idInput = document.createElement('input');
//idInput.type = 'hidden';
//idInput.id = 'elementId';
//document.getElementById('elementForm').appendChild(idInput);
const idInput = document.getElementById('elementId');

async function generate() {

  let elementId = document.getElementById('elementId').value;
  let prompt = document.getElementById('prompt').value;

  let elementData = elementsData[elementId];

  const response = await fetch('/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      elementData: elementData,
      projectId: document.getElementById('projectId').value
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  const imageUrl = data.url;

  if (!elementsData[elementId].variants) {
    elementsData[elementId].variants = [];
  }

  elementsData[elementId].variants.push(imageUrl);

  displayVariants()

  //save
  doSave();

}


function getAudioDuration(src) {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    audio.onloadedmetadata = function () {
      resolve(audio.duration);
    };
    audio.onerror = function () {
      reject('Error loading audio file');
    };
    audio.src = src;
  });
}

function getVideoDuration(src) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.onloadedmetadata = function () {
      resolve(video.duration);
    };
    video.onerror = function () {
      reject('Error loading video file');
    };
    video.src = src;
  });
}

function displayVariants() {
  const elementId = document.getElementById('elementId').value;
  const variantsContainer = document.getElementById('variants');
  variantsContainer.innerHTML = ''; // Clear the container

  const elementType = elementsData[elementId].elementType;


  const variants = elementsData[elementId].variants;
  if (variants && variants.length > 0) {
    const grid = document.createElement('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))'; // Adjust as needed
    grid.style.gap = '10px'; // Adjust as needed

    variants.forEach(variant => {
      let gridItem;

      if (elementType === 'music' || elementType === 'speech') {
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = variant;
        audio.style.width = '80%'; // Reduce width to make space for the button
        audio.style.objectFit = 'cover';
        audio.preload = 'metadata'; // Add this line

        // Create a button for selecting the variant
        const selectButton = document.createElement('button');
        selectButton.textContent = 'Select';
        selectButton.style.width = '20%'; // Adjust as needed

        // Add click event listener to the button
        selectButton.addEventListener('click', async (event) => {
          elementsData[elementId].chosen = variant;

          if (elementType === 'speech') {
            try {
              // Assuming variant is the path to the audio file
              const durationSeconds = await getAudioDuration(variant);
              elementsData[elementId].duration = durationSeconds;

              // Calculate durationPercent based on the new duration
              const durationPercent = durationSeconds / timelineDuration * 100;

              // Get the element and adjust its width
              const element = document.getElementById(elementId);
              element.style.width = `${durationPercent}%`;

              //we also need to update the form field
              document.getElementById('duration').value = durationSeconds;

              //and the end field
              const start = parseFloat(document.getElementById('start').value);
              const end = start + durationSeconds;
              document.getElementById('end').value = end;



            } catch (error) {
              console.error(error);
            }
          }

          displayVariants(); // Refresh the display
          addChosenImage(elementId);
          event.stopPropagation(); // Prevent the event from bubbling up to the gridItem

          //save
          doSave();

        });

        // Wrap the audio element and the button in a div
        const audioWrapper = document.createElement('div');
        audioWrapper.appendChild(audio);
        //add br
        audioWrapper.appendChild(document.createElement('br'));
        audioWrapper.appendChild(selectButton);
        gridItem = audioWrapper;
      }
      else if (elementType === 'image') {
        const img = document.createElement('img');
        img.src = variant;
        img.style.width = '100%';
        img.style.objectFit = 'cover';
        gridItem = img;
      } else if (elementType === 'svd' || elementType === 'talkingHeadVideo' || elementType === 'animDiff') {


        console.log("showing video!" + variant);

        const video = document.createElement('video');
        video.controls = true;
        video.src = variant;
        video.style.width = '100%';
        video.style.objectFit = 'cover';


        // Create a button for selecting the variant
        const selectButton = document.createElement('button');
        selectButton.textContent = 'Select';
        selectButton.style.width = '20%'; // Adjust as needed
        // Add click event listener to the button
        selectButton.addEventListener('click', (event) => {
          elementsData[elementId].chosen = variant;


          //if talkingHeadVideo, get duration (we'll loop svd and animDiff)
          if (elementType === 'talkingHeadVideo') {
            getVideoDuration(variant).then(durationSeconds => {
              elementsData[elementId].duration = durationSeconds;

              // Calculate durationPercent based on the new duration
              const durationPercent = durationSeconds / timelineDuration * 100;

              // Get the element and adjust its width
              const element = document.getElementById(elementId);
              element.style.width = `${durationPercent}%`;

              //save
              doSave();
            }).catch(error => {
              console.error(error);
            });
          }


          displayVariants(); // Refresh the display
          addChosenImage(elementId);
          event.stopPropagation(); // Prevent the event from bubbling up to the gridItem

          //save
          doSave();

        });

        // Wrap the audio element and the button in a div
        const wrapper = document.createElement('div');
        wrapper.appendChild(video);
        //add br
        wrapper.appendChild(document.createElement('br'));
        wrapper.appendChild(selectButton);


        gridItem = wrapper;

      }

      // Add border if this variant is chosen
      if (elementsData[elementId].chosen === variant) {
        gridItem.style.border = '2px solid red'; // Adjust as needed
      }

      // Add click event listener to the div instead of the audio element
      gridItem.addEventListener('click', () => {
        elementsData[elementId].chosen = variant;
        displayVariants(); // Refresh the display
        addChosenImage(elementId);

        //save
        doSave();

      });

      grid.appendChild(gridItem);
    });


    variantsContainer.appendChild(grid);
  }
}

function addChosenImage(elementId) {
  const chosen = elementsData[elementId].chosen;
  const elementType = elementsData[elementId].elementType;

  if (chosen) {
    const element = document.getElementById(elementId);

    //clear inner text
    element.innerText = '';

    if (elementType === 'music' || elementType === 'speech') {


      const audio = document.createElement('audio');

      audio.src = chosen;
      audio.style.width = '100%'; // Adjust as needed
      audio.style.objectFit = 'cover';
      audio.preload = 'metadata'; // Add this line

      // Check the size of the element
      if (element.offsetWidth >= 100) {
        audio.controls = true;
      } else {
        // Add an event listener to play the audio when the element is clicked
        element.addEventListener('click', function () {
          if (audio.paused) {
            audio.play();
          } else {
            audio.pause();
          }
        });
        // Add a visual indicator
        let audioIndicator = document.createElement('span');
        audioIndicator.textContent = '🔊'; // You can replace this with any text or icon
        audioIndicator.style.position = 'absolute';
        audioIndicator.style.top = '50%';
        audioIndicator.style.left = '50%';
        audioIndicator.style.transform = 'translate(-50%, -50%)';
        audioIndicator.style.fontSize = '20px'; // Adjust as needed
        element.appendChild(audioIndicator);

      }

      element.appendChild(audio);




    } else if (elementType === 'image') {

      const img = document.createElement('img');
      img.src = chosen;

      element.appendChild(img);
      //add a class to img so we can do some styling
      img.classList.add('chosenImage');

    } else if (elementType === 'svd' || elementType === 'talkingHeadVideo' || elementType === 'animDiff') {
      const video = document.createElement('video');
      video.controls = false;
      video.src = chosen;
      video.style.width = '100%';
      video.style.height = '100%';
      video.style.objectFit = 'contain'; // Change 'cover' to 'contain'

      // Add click event listener to the video
      video.addEventListener('click', () => {
        if (video.paused) {
          video.play();
        } else {
          video.pause();
        }
      });

      element.appendChild(video);
    }

    //re add resize handle
    const resizeHandle = document.createElement('div');
    resizeHandle.classList.add('resize-handle');
    element.appendChild(resizeHandle);

  }
}


async function save(key) {
  const data = {
    project_name: document.getElementById('projectId').value,
    elements: elementsData,
    duration: timelineDuration,
    outputMovie: document.getElementById('outputVideo').src
  };



  const response = await fetch('/save', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ key, data: JSON.stringify(data) })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result = await response.json();
  return result;
}

async function load(key) {
  const response = await fetch(`/load?key=${encodeURIComponent(key)}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }



  const result = await response.json();
  const data = JSON.parse(result.data);

  //set final video
  document.getElementById('outputVideo').src = data.outputMovie;
  loadedElementData = data['elements']


  for (const type of types) {
    // Clear timeline and elementsData
    const timeline = document.getElementById(type + '-timeline');
    while (timeline.firstChild) {
      timeline.removeChild(timeline.firstChild);
    }
  }
  elementsData = {};

  //hide form
  document.getElementById('elementForm').style.display = 'none';

  // Assuming timeline is an array and addElement is a function that adds an element to the timeline
  for (const elementId in loadedElementData) {
    addElementWithData(loadedElementData[elementId]);
  }
}



function doSave() {
  const key = document.getElementById('projectId').value;
  save(key);
}

function doLoad() {
  const key = document.getElementById('projectId').value;
  load(key);
}


function doNew() {

  //randomize project name
  document.getElementById('projectId').value = "Project_" + Math.random().toString(36).substring(7);

  for (const type of types) {
    // Clear timeline and elementsData
    const timeline = document.getElementById(type + '-timeline');
    while (timeline.firstChild) {
      timeline.removeChild(timeline.firstChild);
    }
  }
  elementsData = {};

  //hide form
  document.getElementById('elementForm').style.display = 'none';
}



function deleteElement() {
  let elementId = document.getElementById('elementId').value;
  let element = document.getElementById(elementId);
  element.remove();
  delete elementsData[elementId];
}

async function createMovie() {
  const projectId = document.getElementById('projectId').value;
  const response = await fetch('/generateVideo', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ projectId }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  const outputVideo = document.getElementById('outputVideo'); // replace with your actual video element id
  outputVideo.src = data.url;
}

const outputVideo = document.getElementById('outputVideo');
const currentTimeLine = document.getElementById('current-time-line');

const timelineAxis = document.getElementById('timelineAxis');

outputVideo.addEventListener('timeupdate', () => {
  const progress = outputVideo.currentTime / timelineDuration;
  const timelineStart = timelineAxis.offsetLeft;
  const timelineWidth = timelineAxis.offsetWidth;
  currentTimeLine.style.left = `${timelineStart + progress * timelineWidth}px`;
});



doLoad()