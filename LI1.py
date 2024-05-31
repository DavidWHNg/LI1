# Import packages
from psychopy import core, event, gui, visual, parallel, prefs
import time
import math
import random
import csv
import os
import cv2

ports_live = None # Set to None if parallel ports not plugged for coding/debugging other parts of exp

### Experiment details/parameters
## equipment parameters
port_buffer_duration = 1 #needs about 0.5s buffer for port signal to reset 
pain_response_duration = float("inf")
response_hold_duration = 1 # How long the rating screen is left on the response (only used for Pain ratings)
TENS_pulse_int = 0.1 # interval length for TENS on/off signals (e.g. 0.1 = 0.2s per pulse)

# parallel port triggers
port_address = 0x3FF88
pain_trig = 2 #levels and order need to be organised through CHEPS system
scr_trig = 1
tens_trig = 64
audio_trig = {"TENS": 128, "control": 0} #Pin 8 in relay box just for the clicking sound

## within experiment parameters
experimentcode = "LI1"
P_info = {"PID": ""}
info_order = ["PID"]
iti_range = [6,8]
familiarisation_iti = 3
cue_colours = ([-1,0.10588,-1],[-1,-1,1]) # 2 colours taken from Kirsten EEG
cue_colour_names = ('green','blue')
cue_positions = [(300,0),(-300,0)]
cue_width = 200

rating_scale_pos = (0,-350)
rating_text_pos = (0,-250)
text_height = 35 

video_painratings_mean = {"TENS" : 81, "control": 31}
video_painratings_spread = {"TENS" : 10, "control" : 10}
video_painratings_buffer = 4
video_stim_time = 60
video_stim_iti = 6
video_stim_pos = (0,250)
video_stim_size = (400,300)

webcam_stim_pos = (0,-250)
webcam_stim_size = (400,300)

#calculate iti_jitter
iti_jitter = [x * 1000 for x in iti_range]

# Participant info input
while True:
    try:
        P_info["PID"] = input("Enter participant ID: ")
        if not P_info["PID"]:
            print("Participant ID cannot be empty.")
            continue
        
        block_order = [int(block) for block in input("Enter block order: ").split()]
        
        print(block_order)
            
        data_filename = P_info["PID"] + "_responses.csv"
        script_directory = os.path.dirname(os.path.abspath(__file__))  #Set the working directory to the folder the Python code is opened from
        
        #set a path to a "data" folder to save data in
        data_folder = os.path.join(script_directory, "data")
        
        # if data folder doesn"t exist, create one
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
            
        #set file name within "data" folder
        data_filepath = os.path.join(data_folder,data_filename)
        
        if os.path.exists(data_filepath):
            print(f"Data for participant {P_info['PID']} already exists. Choose a different participant ID.") ### to avoid re-writing existing data
        
        
        # Group == 1 == pre-exposure
        # Group == 2 == social modelling
        # Group == 3 == natural history
        # cb == 1 == TENS = GREEN, control = BLUE
        # cb == 2 == TENS = BLUE, control = GREEN
            
        else:
            if int(P_info["PID"]) % 6 == 0:
                group = 1
                cb = 1 
                groupname = "preexposure"
            elif int(P_info["PID"]) % 6 == 1:
                group = 2
                cb = 1 
                groupname = "socialmodel"
            elif int(P_info["PID"]) % 6 == 2:
                group = 3
                cb = 1 
                groupname = "naturalhistory"
            elif int(P_info["PID"]) % 6 == 3:
                group = 1
                cb = 2 
                groupname = "preexposure"
            elif int(P_info["PID"]) % 6 == 4:
                group = 2
                cb = 2 
                groupname = "socialmodel"
            elif int(P_info["PID"]) % 6 == 5:
                group = 3
                cb = 2 
                groupname = "naturalhistory"
            
            break  # Exit the loop if the participant ID is valid
        
    except KeyboardInterrupt:
        print("Participant info input canceled.")
        break  # Exit the loop if the participant info input is canceled

exp_finish = None

# get date and time of experiment start
datetime = time.strftime("%Y-%m-%d_%H.%M.%S")

#set stimulus colours according to cb 
stim_colours = {
  "TENS" : cue_colours[cb-1],
  "control": cue_colours[-cb] 
}

stim_colour_names = {
    "TENS" : cue_colour_names[cb-1],
    "control": cue_colour_names[-cb]
}

stim_positions = {
    "TENS" : cue_positions[cb-1],
    "control" : cue_positions[-cb]
}

if ports_live == True:
    pport = parallel.ParallelPort(address=port_address) #Get from device Manager
    pport.setData(0)
    
elif ports_live == None:
    pport = None #Get from device Manager

# set up screen
win = visual.Window(
    size=(1920, 1080), fullscr= True, screen=0,
    allowGUI=False, allowStencil=False,
    monitor="testMonitor", color=[0, 0, 0], colorSpace="rgb1",
    blendMode="avg", useFBO=True,
    units="pix")

# fixation stimulus
fix_stim = visual.TextStim(win,
                            text = "x",
                            color = "white",
                            height = 50,
                            font = "Roboto Mono Medium")

#create instruction trials
def instruction_trial(instructions,
                      holdtime=0,
                      key = "space",
                      buttontext = "\n\nPress spacebar to continue"): 
    termination_check()
    
    visual.TextStim(win,
                    text = instructions,
                    height = text_height,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    win.flip()
    core.wait(holdtime)
    visual.TextStim(win,
                    text = instructions,
                    height = text_height,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    
    visual.TextStim(win,
                    text = buttontext,
                    height = text_height,
                    color = "white",
                    pos = (0,-400)
                    ).draw()
    win.flip()
    event.waitKeys(keyList=key)
    win.flip()
    
    core.wait(2)
    
# Create functions
    # Save responses to a CSV file
def save_data(data):
    for trial in trial_order:
        trial['datetime'] = datetime
        trial['experimentcode'] = experimentcode
        trial["PID"] = P_info["PID"]
        trial["group"] = group
        trial["groupname"] = groupname
        trial["cb"] = cb
        trial["tens_colour"] = stim_colour_names["TENS"]
        trial["control_colour"] = stim_colour_names["control"]
        

    # Extract column names from the keys in the first trial dictionary
    colnames = list(trial_order[0].keys())

    # Open the CSV file for writing
    with open(data_filepath, mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=colnames)
        
        # Write the header row
        writer.writeheader()
        
        # Write each trial"s data to the CSV file
        for trial in data:
            writer.writerow(trial)
    
def exit_screen(instructions):
    win.flip()
    visual.TextStim(win,
            text = instructions,
            height = text_height,
            color = "white",
            pos = (0,0)).draw()
    win.flip()
    event.waitKeys()
    win.close()
    
def termination_check(): #insert throughout experiment so participants can end at any point.
    keys_pressed = event.getKeys(keyList=["escape"])  # Check for "escape" key during countdown
    if "escape" in keys_pressed:
        if ports_live:
            pport.setData(0) # Set all pins to 0 to shut off context, TENS, shock etc.
        # Save participant information

        save_data(trial_order)
        exit_screen(instructions_text["termination"])
        core.quit()


# Define trials
trial_order = []

# familiarisation trials
num_familiarisation = 10

for i in range(1, num_familiarisation + 1):
    trial = {
        "phase": "familiarisation",
        "blocknum": None,
        "stimulus": None,
        "outcome": None,
        "trialname": "familiarisation",
        "exp_response": None,
        "pain_response": None,
        "iti" : None
    } 
    trial_order.append(trial)


#pre-exposure trials
num_TENS_preexp = 16

for i in range(1, num_TENS_preexp + 1):
    trial = {
        "phase": "preexposure",
        "blocknum": None,
        "stimulus": "TENS",
        "outcome": "none",
        "trialname": "preexposure",
        "exp_response": None,
        "pain_response": None,
        "iti" : None
    } 
    trial_order.append(trial)


#### 4 x blocks (4x fixed pseudo-randomised runs of 4x TENs and 4x no-TENS)
num_blocks_conditioning = 2
num_blocks_extinction = 2

conditioning_stim_blocks = [['control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'TENS', 'control'],
                            ['control', 'TENS', 'control', 'TENS', 'control', 'control', 'TENS', 'control', 'TENS', 'TENS', 'TENS', 'control', 'TENS', 'control', 'TENS', 'control'],
                            ['TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'TENS', 'TENS', 'control', 'control', 'control', 'TENS'],
                            ['TENS', 'control', 'TENS', 'control', 'TENS', 'TENS', 'control', 'TENS', 'control', 'control', 'control', 'TENS', 'control', 'TENS', 'control', 'TENS']]

#natural history has non-contingent pairings between high-low outcomes and stimuli, so we'll change the stimuli block 
# and keep the outcome blocks the same since the outcome order is pre-programmed on the CHEPS
naturalhistory_stim_blocks = [['TENS', 'TENS', 'control', 'control', 'TENS', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control'],
                              ['TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'control'],
                              ['control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'TENS', 'control', 'control', 'TENS', 'TENS'],
                              ['control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS']]

##need a different list to allocate high and low heat outcomes to TENS/control trials 
#0 = TENS high, 1 = TENS low, 2 = control high, 3 = control low
#conditioning pairs TENS with high outcome (nocebo), and control with low outcome
conditioning_outcome_blocks = [['low','high','high','low','low','high','high','low','low','high','low','low','high','high','high','low'],
                               ['low','high','low','high','low','low','high','low','high','high','high','low','high','low','high','low'],
                               ['high','low','low','high','high','low','low','high','high','low','high','high','low','low','low','high'],
                               ['high','low','high','low','high','high','low','high','low','low','low','high','low','high','low','high']]

#low heat for every trial in extinction regardless of stimulus
extinction_outcome_block = ['low']*16

### create list of trials based on trial_block order, iterating through stimulus + outcome blocks in parallel
    #create conditioning blocks, outcome dependent on natural history vs nocebo conditioning contingencies
if groupname != "naturalhistory": 
    for block in range(1,num_blocks_conditioning+1):
        for stimulus,outcome in zip(conditioning_stim_blocks[block_order[block-1]],conditioning_outcome_blocks[block_order[block-1]]):
            trial = {
                "phase": "conditioning",
                "blocknum": block,
                "stimulus": stimulus,
                "outcome": outcome,
                "trialname": str(stimulus) + "_" + str(outcome),
                "exp_response": None,
                "pain_response": None,
                "iti" : None
            }
            trial_order.append(trial)
            
elif groupname == "naturalhistory":
    for block in range(1,num_blocks_conditioning+1):
        for stimulus,outcome in zip(naturalhistory_stim_blocks[block_order[block-1]],conditioning_outcome_blocks[block_order[block-1]]):
            trial = {
                "phase": "conditioning",
                "blocknum": block,
                "stimulus": stimulus,
                "outcome": outcome,
                "trialname": str(stimulus) + "_" + str(outcome),
                "exp_response": None,
                "pain_response": None,
                "iti": None
            }
            trial_order.append(trial)
                    
#create extinction trials, all outcomes same regardless of condition (low heat)
for block in range(num_blocks_conditioning+1,num_blocks_conditioning+num_blocks_extinction+1):
    for stimulus,outcome in zip(conditioning_stim_blocks[block_order[block-1]],extinction_outcome_block):
        trial = {
            "phase": "extinction",
            "blocknum": block,
            "stimulus": stimulus,
            "outcome": outcome,
            "trialname": str(stimulus) + "_" + str(outcome),
            "exp_response": None,
            "pain_response": None,
            "iti": None
        }
        trial_order.append(trial)
        
# # Assign trial numbers
for trialnum, trial in enumerate(trial_order, start=1):
    trial["trialnum"] = trialnum
    
save_data(trial_order)
    
# # text stimuli
instructions_text = {
    "welcome": "Welcome to the experiment! Please read the following instructions carefully.", 
    "TENS_introduction": ("This experiment aims to investigate the effects of Transcutaneous Electrical Nerve Stimulation (TENS) on heat pain sensitivity. "
    "TENS is designed to increase pain sensitivity by enhancing the conductivity of pain signals being sent to your brain. Clinically this is used to enhance pain sensitivity in medical conditions where pain sensitivity is dampened. "
    "In the absence of medical conditions, TENS significantly amplifies pain signals, meaning stimulations will be more painful when the TENS device is active. Although the TENS itself is not painful, you will feel a small sensation when it is turned on. \n\n"
    "In this study you and/or another participant will receive a series of heat pain stimulations, and some heat pain stimulations will also be accompanied with TENS stimulation."),
    
    "familiarisation_1": ("Firstly, you will be familiarised with the thermal stimuli. This familiarisation procedure is necessary to ensure that participants are able to tolerate "
    "the heat pain delivered in this experiment. The thermal stimulus is delivered through the thermode attached to your forearm, which delivers heat pain by selectively stimulating pain fibres.\n\n"
    "As the density of pain fibres can vary between individuals, the pain experienced and the efficacy of TENS can also vary. "
    "As such, this familiarisation procedure will demonstrate the range of how painful the thermal stimulus could be when TENS is active for any participant."),
    
    "familiarisation_2": ("In the familiarisation procedure, you will experience the thermal stimuli at a range of intensities. The machine will start at a low intensity, and incrementally increase each level. "
    "After receiving each thermal stimulus, you will be asked to give a pain rating for that level of heat. "
    "The familiarisation procedure will take you through 10 increasing levels of heat intensities. \n\n Although the higher levels of heat intensities may be more uncomfortable or painful, please note that "
    "the maximum level of heat is safe and unlikely to cause you any actual harm. If, however, you find the thermal stimuli intolerable at any stage, please let the experimenter know and we will terminate the experiment immediately. "
    "This procedure will proceed at your pace, so feel free to take your time to rest between heat levels."),
        
    "familiarisation_finish": "Thank you for completing the familiarisation protocol. we will now proceed to the next phase of the experiment",
    
    "preexposure_socialmodel": "We will now record some baseline measures. Please stay seated and still during this phase, as excessive movement may interfere with our readings. \n\n \
    The TENS device may be activated intermittently but NO thermal stimuli will be delivered during this phase.",
        
    "preexposure_naturalhistory": "Before we begin, we will record some baseline measures. Please stay seated and stay still during this phase, as excessive movement may interfere with our readings. \n\n \
    NO thermal stimuli will be delivered during this phase.",
    
    "preexposure_waiting": "Collecting baseline readings, please stay still",
    
    "preexposure_completed": "Baseline measures have been recorded, thank you for your patience. \n\n\
    Please call for the experimenter to prepare for the next stage of the experiment",
        
    "experiment_socialmodel_conditioning" : ("We will now begin the main phase of the experiment. You will observe another participant receive a series of thermal stimuli with and without TENS. Your task is to predict how painful the other participant finds the thermal stimulus."
    "This rating scale ranges from NOT PAINFUL to VERY PAINFUL. \n\n"
    "All thermal stimuli will be signaled by a 10 second countdown. The heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. "
    "To make clear whether the TENS is on or not, TENS will be indicated by a " + stim_colour_names["TENS"] + "square on the screen, whereas no-TENS trials will be indicated by a " + stim_colour_names["control"] + "square. "
    "As the other participant waits for the thermal stimulus during the countdown, you will be asked to rate how painful you expect their heat to be. After each trial you will find out what pain rating they actually responded with. \n\n"
    "Please call for the experimenter now to set up the stream with the other participant."),
    
    "experiment_socialmodel_webcam_waiting" : ("Waiting for connection..."),
    
    "experiment_socialmodel_webcam_ready" : ("Connection found !\n\n"
                                             "Press SPACEBAR to go live"),
    
    "experiment_socialmodel_webcam_finish" : ("Observation phase completed!\n\n"
                                              "Connection ended."),
    
    "experiment_socialmodel_extinction" : ("You will now receive a series of thermal stimuli and rate the intensity of each thermal stimulus. "
    "Similarly to the other participant, the thermal stimuli will be signaled by a 10 second countdown and the heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. "
    "To make clear whether the TENS is on or not, TENS will be indicated by a " + stim_colour_names["TENS"] + "square on the screen, whereas no-TENS trials will be indicated by a " + stim_colour_names["control"] + "square. "
    "During the countdown, you will also be asked to rate how painful you expect the heat to be. After each trial there will also be a brief interval to allow you to rest between thermal stimuli. "
    "You will also receive a brief rest between blocks of trials where the experimenter will move the thermode to another location on your arm. \n\n"
    "Please ask the experimenter now if you have any questions before proceeding."),
    
    "experiment_naturalhistory" : ("We will now begin the main phase of the experiment. \n\n"
    "You will now receive a series of thermal stimuli and your task is to rate the intensity of each thermal stimulus on a rating scale. This rating scale ranges from NOT PAINFUL to VERY PAINFUL. \n\n"
    "All thermal stimuli will be signaled by a 10 second countdown. The heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. "
    "To make clear whether the TENS is on or not, TENS activation will be indicated by a " + stim_colour_names["TENS"] + "square on the screen, whereas no-TENS trials will be indicated by a " + stim_colour_names["control"] + "square. "
    "As you are waiting for the thermal stimulus during the countdown, you will also be asked to rate how painful you expect the heat to be. After each trial there will also be a brief interval to allow you to rest between thermal stimuli. "
    "You will also receive a brief rest between blocks of trials where the experimenter will move the thermode to another location on your arm. \n\n"
    "Please ask the experimenter now if you have any questions before proceeding."),
    
    "blockrest" : "This is a rest interval. Please call for the experimenter to adjust the thermode.", 
    
    "blockresume" : "Feel free to take as much as rest as necessary before starting the next block.",
    
    "end" : "This concludes the experiment. Please ask the experimenter to help remove the devices.",
    
    "termination" : "The experiment has been terminated. Please ask the experimenter to help remove the devices."
}

# cue_demo_text = "When you are completely relaxed, press any key to start the next block..."

response_instructions = {
    "pain": "How painful was the heat?",
    "expectancy": "How painful do you expect the thermal stimulus to be?",
    "SM": "The demonstrator made the following response on this trial",
    "familiarisation": "When you are ready to receive the thermal stimulus, press the SPACEBAR to activate the thermal stimulus. "
    }

trial_text = {
     "pain": visual.TextStim(win,
            text=response_instructions["pain"],
            height = text_height,
            pos = rating_text_pos
            ),
     "expectancy": visual.TextStim(win,
            text=response_instructions["expectancy"],
            height = text_height,
            pos = rating_text_pos
            ),
     "preexposure": visual.TextStim(win,
            text=instructions_text["preexposure_waiting"],
            height=text_height,
            pos = (0,250)
            ),
     "SMrating": visual.TextStim(win, 
            color="white", 
            height = text_height,
            pos = rating_text_pos,
            text= response_instructions["SM"]
            )
}

# #Test questions
rating_stim = { "familiarisation": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,50,100],
                                    labels=(1,5,10),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
               "pain": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
                "expectancy": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30)}


rating_stim["familiarisation"].marker.size = (30,30)
rating_stim["familiarisation"].marker.color = "yellow"
rating_stim["familiarisation"].validArea.size = (660,100)

rating_stim["pain"].marker.size = (30,30)
rating_stim["pain"].marker.color = "yellow"
rating_stim["pain"].validArea.size = (660,100)

rating_stim["expectancy"].marker.size = (30,30)
rating_stim["expectancy"].marker.color = "yellow"
rating_stim["expectancy"].validArea.size = (660,100)

pain_rating = rating_stim["pain"]
exp_rating = rating_stim["expectancy"]
fam_rating = rating_stim["familiarisation"]
                                
# pre-draw countdown stimuli (numbers 10-1)
countdown_text = {}
for i in range(0,11):
    countdown_text[str(i)] = visual.TextStim(win, 
                            color="white", 
                            height = 50,
                            text=str(i))

# visual cues for TENS/control trials
cue_stims = {"TENS" : visual.Rect(win,
                        lineColor = stim_colours["TENS"],
                        fillColor = stim_colours["TENS"],
                        width = cue_width,
                        height = cue_width,
                        pos = stim_positions["TENS"],
                        autoLog = False),
             "control" : visual.Rect(win,
                        lineColor = stim_colours["control"],
                        fillColor = stim_colours["control"],
                        width = cue_width,
                        height = cue_width,
                        pos = stim_positions["control"],
                        autoLog = False)
             }

#Video stimulus (Social modelling)
video_stim = visual.MovieStim(win,
                              filename=os.path.join(script_directory, "SMconditioning.mp4"),
                              size = video_stim_size,
                              pos = video_stim_pos,
                              volume = 1.0,
                              autoStart=True,
                              loop = False)

# Define button_text dictionaries
#### Make trial functions
def show_fam_trial(current_trial):
    termination_check()
    # Wait for participant to ready up for shock
    visual.TextStim(win,
        text=response_instructions["familiarisation"],
        height = 35,
        pos = (0,0),
        wrapWidth= 800
        ).draw()
    win.flip()
    event.waitKeys(keyList = ["space"])
    
    # show fixation stimulus + deliver shock
    if pport != None:
        pport.setData(0)

    fix_stim.draw()
    win.flip()
    
    if pport != None:
        pport.setData(pain_trig)
        core.wait(port_buffer_duration)
        pport.setData(0)
    
    # Get pain rating
    while fam_rating.getRating() is None: # while mouse unclicked
        termination_check()
        trial_text["pain"].draw()
        fam_rating.draw()
        win.flip()
         
    pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
    
    while core.getTime() < pain_response_end_time:
        termination_check()
        trial_text["pain"].draw()
        fam_rating.draw()
        win.flip()

    current_trial["pain_response"] = fam_rating.getRating()
    fam_rating.reset()
    
    win.flip()
    core.wait(familiarisation_iti)
    
def show_trial(current_trial,
               trialtype,
               video = None):
   
    if pport != None:
        pport.setData(0)
        

    
    if trialtype == "socialmodel":
        iti = video_stim_iti
    else: 
        iti = random.randint(*iti_jitter) / 1000
        
    win.flip()
    
    # Set the initial countdown time to 10 seconds
    countdown_timer = core.CountdownTimer(10)  

    #if pre-exposure, only show and activate TENS
    if trialtype == "preexposure":  
        if groupname == 'preexposure':
            while countdown_timer.getTime() > 8:
                termination_check()
                trial_text["preexposure"].draw()
                win.flip()
                
            TENS_timer = countdown_timer.getTime() + TENS_pulse_int
                            
            while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 0: #turn on TENS at 8 seconds
                termination_check()
                
                if pport != None:
                # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                        pport.setData(audio_trig[current_trial["stimulus"]])
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                        pport.setData(0)
                        TENS_timer = countdown_timer.getTime() 
                cue_stims[current_trial["stimulus"]].draw()
                trial_text["preexposure"].draw()
                win.flip() 
            
            if pport != None:    
                pport.setData(0)
                
        elif groupname != 'preexposure':
            while countdown_timer.getTime() > 0:
                termination_check()
                trial_text["preexposure"].draw()
                win.flip()

        win.flip()
        core.wait(iti)   
        current_trial["iti"] = iti
        
# social modelling conditioning trials
    if trialtype == "socialmodel":
        while countdown_timer.getTime() > 8:
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            video.draw()
            win.flip()
            
        while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 7: #turn on TENS at 8 seconds
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            video.draw()
            win.flip()

        while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            video.draw()
            cue_stims[current_trial["stimulus"]].draw()
            
            # Ask for expectancy rating
            trial_text["expectancy"].draw()
            exp_rating.draw()
            video.draw()
            win.flip()    

        current_trial["exp_response"] = exp_rating.getRating() #saves the expectancy response for that trial
        exp_rating.reset() #resets the expectancy slider for subsequent trials
        
        buffer_timer = core.CountdownTimer(video_painratings_buffer)   
                       
        while buffer_timer.getTime() > 0:
            video.draw()
            win.flip() 

        # present social model's pain rating 
        pain_rating_sm = random.normalvariate(
                video_painratings_mean[current_trial["stimulus"]],
                video_painratings_spread[current_trial["stimulus"]])
        
        pain_rating.rating = pain_rating_sm
        pain_rating.readOnly = True
        
        iti_timer = core.CountdownTimer(iti)
        
        while iti_timer.getTime() > 0:
            video.draw()
            trial_text["SMrating"].draw()
            pain_rating.draw()
            win.flip()

                
        current_trial["pain_response"] = pain_rating.getRating()
        pain_rating.reset()

        win.flip()
        
        current_trial["iti"] = iti
            
    #if it's a conditioning/extinction trial, do regular 10 second countdown with stimuli + pain stimulus etc.  
      
    elif trialtype == "standard": 
        while countdown_timer.getTime() > 8:
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            win.flip()
        
            TENS_timer = countdown_timer.getTime() + TENS_pulse_int
            
        while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 7: #turn on TENS at 8 seconds
            termination_check()
            
            if pport != None:
                # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int
                if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                    pport.setData(audio_trig[current_trial["stimulus"]])
                if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                    pport.setData(0)
                    TENS_timer = countdown_timer.getTime() 

            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            win.flip()

        
        TENS_timer = countdown_timer.getTime() + TENS_pulse_int

        while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
            if pport != None:
                termination_check()
                        
                # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int
                if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                    pport.setData(audio_trig[current_trial["stimulus"]])
                if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                    pport.setData(0)
                    TENS_timer = countdown_timer.getTime() 

            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            
            # Ask for expectancy rating
            trial_text["expectancy"].draw()
            exp_rating.draw()
            win.flip()    

            current_trial["exp_response"] = exp_rating.getRating() #saves the expectancy response for that trial
            exp_rating.reset() #resets the expectancy slider for subsequent trials
                
            # deliver shock
            if pport != None:
                pport.setData(0)
            fix_stim.draw()
            win.flip()
            
            if pport != None:
                pport.setData(pain_trig)
                core.wait(port_buffer_duration)
                pport.setData(0)

            # Get pain rating
            while pain_rating.getRating() is None: # while mouse unclicked
                pain_rating.readOnly = False
                termination_check()
                pain_rating.draw()
                trial_text["pain"].draw()
                win.flip()
                    
                    
            pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
            
            while core.getTime() < pain_response_end_time:
                termination_check()
                trial_text["pain"].draw()
                pain_rating.draw()
                win.flip()
                
            current_trial["pain_response"] = pain_rating.getRating()
            pain_rating.reset()

            win.flip()
            core.wait(iti)
            current_trial["iti"] = iti
            
def webcam_waiting(waittime = 1):
    termination_check()
    global exp_finish
    # setup webcam feed
    webcam_feed = cv2.VideoCapture(0)
    
    if not webcam_feed.isOpened():
        print("Failed to open webcam.")
        exp_finish = True
        return
    

    waiting_text = visual.TextStim(win,
                        text=instructions_text['experiment_socialmodel_webcam_waiting'],
                        height = 35,
                        pos = video_stim_pos,
                        wrapWidth= 800
                        )
    ready_text = visual.TextStim(win,
                        text=instructions_text['experiment_socialmodel_webcam_ready'],
                        height = 35,
                        pos = video_stim_pos,
                        wrapWidth= 800
                        )
    waittimer = core.CountdownTimer(waittime)  
    
    while waittimer.getTime() > 0:
        termination_check()
        # capture each frame of webcam feed in RGB
        ret, webcam_frame = webcam_feed.read() 
        if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
            print("failed to capture image")
            exp_finish = True
            break
        
        webcam_frame = cv2.flip(webcam_frame,-1) 
        webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
        ## Normalize the frame to be in the range -1 to 1
        webcam_frame = webcam_frame / 255.0
        webcam_stim = visual.ImageStim(win,
                                       image = webcam_frame,
                                       pos = webcam_stim_pos,
                                       size = webcam_stim_size    
                                       )
        webcam_stim.draw()
        waiting_text.draw()     
        win.flip()
    
    space_pressed = False
        
    while not space_pressed:
        termination_check()
        # capture each frame of webcam feed in RGB
        ret, webcam_frame = webcam_feed.read() 
        if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
            print("failed to capture image")
            exp_finish = True
            break
        
        webcam_frame = cv2.flip(webcam_frame,-1) 
        webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
        ## Normalize the frame to be in the range -1 to 1
        webcam_frame = webcam_frame / 255.0
        webcam_stim = visual.ImageStim(win,
                                       image = webcam_frame,
                                       pos = webcam_stim_pos,
                                       size = webcam_stim_size    
                                       )
        webcam_stim.draw()
        ready_text.draw()     
        win.flip()
        # Check for key presses
        keys = event.getKeys()
        if 'space' in keys:
            space_pressed = True
            
def show_socialmodel(playtime = 10,socialmodel_stim = video_stim):
    termination_check() 
    webcam_feed = cv2.VideoCapture(0)
    sm_timer = core.CountdownTimer(playtime)
    while sm_timer > 0: 
        # capture each frame of webcam feed in RGB
        ret, webcam_frame = webcam_feed.read() 
        if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
            print("failed to capture image")
            exp_finish = True
            break
        
        webcam_frame = cv2.flip(webcam_frame,-1) 
        webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
        ## Normalize the frame to be in the range -1 to 1
        webcam_frame = webcam_frame / 255.0
        webcam_stim = visual.ImageStim(win,
                                       image = webcam_frame,
                                       pos = webcam_stim_pos,
                                       size = webcam_stim_size    
                                       )
        socialmodel_stim.draw()
        webcam_stim.draw()
        win.flip()
        

# Run experiment
while not exp_finish:
    termination_check()
    
    lastblocknum = None
    
    # #introduce TENS and run familiarisation procedure
    # instruction_trial(instructions_text["welcome"],3)
    # instruction_trial(instructions_text["TENS_introduction"],5)
    # instruction_trial(instructions_text["familiarisation_1"],5)
    # instruction_trial(instructions_text["familiarisation_2"],5)
    
    # for trial in list(filter(lambda trial: trial['phase'] == "familiarisation", trial_order)):
    #     show_fam_trial(trial)
    # show_fam_trial
    
    # instruction_trial(instructions_text["familiarisation_finish"],2)
    
    # #pre-exposure phase
    # if groupname == "naturalhistory":
    #     instruction_trial(instructions_text["preexposure_naturalhistory"],5)
    
    #     for trial in list(filter(lambda trial: trial['phase'] == "preexposure", trial_order)):
    #         show_trial(trial,"preexposure")
            
    #     instruction_trial(instructions_text['experiment_naturalhistory'],5)
        
        
    # # run conditioning and extinction phases normally for natural history group
    #     for blocknum in trial_order:
    #         if blocknum > 1:
    #             instruction_trial(instructions_text["blockrest"],10,"enter",None)
    #             instruction_trial(instructions_text["blockresume"],2)
                
    #         for trial in list(filter(lambda trial: trial['phase'] == "conditioning" and trial[blocknum == block], trial_order)):
    #             show_trial(trial,"standard")
        
    #         for trial in list(filter(lambda trial: trial['phase'] == "extinction" and trial[blocknum == block], trial_order)):
    #             show_trial(trial,"standard")
        
    # elif groupname != "naturalhistory":
        # instruction_trial(instructions_text["preexposure_socialmodel"],5)
        
        # for trial in list(filter(lambda trial: trial['phase'] == "preexposure", trial_order)):
        #     show_trial(trial,"preexposure")

        # instruction_trial(instructions_text["preexposure_completed"],3)
    instruction_trial(instructions_text['experiment_socialmodel_conditioning'],5)
        
    # set up 'webcam' for social model condition
    webcam_waiting(5)

    # start video 
    
    # for blocknum in trial_order:
    #     if blocknum > 1:
    #         instruction_trial(instructions_text["blockrest"],10,"enter",None)
    #         instruction_trial(instructions_text["blockresume"],2)
            
    #     for trial in list(filter(lambda trial: trial['phase'] == "conditioning", trial_order)):
    #         show_trial(trial,
    #                 trialtype="socialmodel",
    #                 video=video_stim)
    
    #     lastblocknum = None
    
    # for trial in trial_order:
    #     current_blocknum = trial['blocknum']
    #     if lastblocknum is not None and current_blocknum != lastblocknum:
    #         lastblocknum = current_blocknum
    #         instruction_trial(instructions_text["blockrest"],10,"enter",None)
    #     show_trial(trial)
    
    # #keep video going after conditioning phase and then flip at end:
    # video_stim.draw()
    # win.flip()
    
    # if video_stim.isFinished == True: 
    #     video_stim.stop()
    # win.flip()
    
    # instruction_trial(instructions_text["experiment_socialmodel_webcam_finish"],3)
    
    # instruction_trial(instructions_text["experiment_socialmodel_extinction"],10)
    # for blocknum in trial_order:
    #     if blocknum > num_blocks_conditioning:
    #         instruction_trial(instructions_text["blockrest"],10,"enter",None)
    #         instruction_trial(instructions_text["blockresume"],2)
    #     for trial in list(filter(lambda trial: trial['phase'] == "extinction", trial_order)):
    #         show_trial(trial,"standard")

    if pport != None:
        pport.setData(0)
        
    # save trial data
    save_data(trial_order)
    # exit_screen(instructions_text["end"])
    
    exp_finish = True
    
win.close()