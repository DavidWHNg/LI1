# Import packages
from psychopy import core, event, gui, visual, parallel, prefs
import time
import math
import random
import csv
import os


ports_live = None # Set to None if parallel ports not plugged for coding/debugging other parts of exp

### Experiment details/parameters
## misc parameters
port_buffer_duration = 1 #needs about 0.5s buffer for port signal to reset 
iti_range = [6,8]
pain_response_duration = float("inf")
response_hold_duration = 1 # How long the rating screen is left on the response (only used for Pain ratings)
TENS_pulse_int = 0.1 # interval length for TENS on/off signals (e.g. 0.1 = 0.2s per pulse)

## within experiment parameters
experimentcode = "LI1"
P_info = {"PID": ""}
info_order = ["PID"]
cue_colours = ([-1,0.10588,-1],[-1,-1,1]) # 2 colours taken from Kirsten EEG
cue_colour_names = ('green','blue')

# parallel port triggers
port_address = 0xDFD8
pain_trig = 1 #levels and order need to be organised through CHEPS system
scr_trig = 2
stim_trig = {"TENS": 128, "control": 0} #Pin 8 in relay box just for the clicking sound

#calculate iti_jitter
iti_jitter = [x * 1000 for x in iti_range]

# Participant info input
while True:
    try:
        P_info["PID"] = input("Enter participant ID: ")
        if not P_info["PID"]:
            print("Participant ID cannot be empty.")
            continue
            
        csv_filename = P_info["PID"] + "_responses.csv"
        script_directory = os.path.dirname(os.path.abspath(__file__))  #Set the working directory to the folder the Python code is opened from
        
        #set a path to a "data" folder to save data in
        data_folder = os.path.join(script_directory, "data")
        
        # if data folder doesn"t exist, create one
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        #set file name within "data" folder
        csv_filepath = os.path.join(data_folder,csv_filename)
        
        if os.path.exists(csv_filepath):
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
def instruction_trial(instructions,holdtime): 
    termination_check()
    visual.TextStim(win,
                    text = instructions,
                    height = 35,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    win.flip()
    core.wait(holdtime)
    visual.TextStim(win,
                    text = instructions,
                    height = 35,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    visual.TextStim(win,
                    text = instructions_text["continue"],
                    height = 35,
                    color = "white",
                    pos = (0,-400)
                    ).draw()
    win.flip()
    event.waitKeys(keyList=["space"])
    win.flip()
    
    core.wait(iti)
    
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
    with open(csv_filepath, mode="w", newline="") as csv_file:
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
            height = 35,
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

#pre-exposure trials
num_TENS_preexp = 16

for i in range(1, num_TENS_preexp + 1):
    trial = {
        "phase": "preexposure",
        "blocknum": 1,
        "stimulus": "TENS",
        "outcome": "none",
        "trialname": "pre-exposure",
        "exp_response": None,
        "pain_response": None
    } 
    trial_order.append(trial)


#### 4 x blocks (4x fixed pseudo-randomised runs of 4x TENs and 4x no-TENS)
num_blocks_conditioning = 2
num_blocks_extinction = 2

trial_stim_blocks = [['control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'TENS', 'control'],
               ['control', 'TENS', 'control', 'TENS', 'control', 'control', 'TENS', 'control', 'TENS', 'TENS', 'TENS', 'control', 'TENS', 'control', 'TENS', 'control'],
               ['TENS','control','control','TENS','TENS','control','control','TENS','TENS','control','TENS','TENS','control','control','control','TENS'],
               ['TENS','control','TENS','control','TENS','TENS','control','TENS','control','control','control','TENS','control','TENS','control','TENS']]

##need a different list to allocate high and low heat outcomes to TENS/control trials 
#0 = TENS high, 1 = TENS low, 2 = control high, 3 = control low
#conditioning pairs TENS with high outcome (nocebo), and control with low outcome
conditioning_outcome_blocks = [['low','high','high','low','low','high','high','low','low','high','low','low','high','high','high','low'],
                               ['low','high','low','high','low','low','high','low','high','high','high','low','high','low','high','low'],
                               ['high','low','low','high','high','low','low','high','high','low','high','high','low','low','low','high'],
                               ['high','low','high','low','high','high','low','high','low','low','low','high','low','high','low','high']]

#natural history has non-contingent pairings between high-low outcomes and stimuli
naturalhistory_outcome_blocks = [['low','high','low','high','low','low','high','low','high','high','low','high','low','high','low','high'],
                                 ['high','low','high','high','low','high','low','low','high','low','high','high','low','low','high','low'],
                                 ['high','low','high','low','high','low','high','high','low','high','low','high','low','high','low','low'],
                                 ['low','high','low','low','high','low','low','high','low','high','high','low','high','high','low','high']]

#low heat for every trial in extinction regardless of stimulus
extinction_outcome_block = ['low']*16

#print out block order for experimenter to note down before experiment starts
block_order = [0,1,2,3]

random.shuffle(block_order)
print(block_order)

### create list of trials based on trial_block order, iterating through stimulus + outcome blocks in parallel
    #create conditioning blocks, outcome dependent on natural history vs nocebo conditioning contingencies
if groupname != "naturalhistory": 
    for block in range(1,num_blocks_conditioning+1):
        for stimulus,outcome in zip(trial_stim_blocks[block_order[block-1]],conditioning_outcome_blocks[block_order[block-1]]):
            trial = {
                "phase": "conditioning",
                "blocknum": block,
                "stimulus": stimulus,
                "outcome": outcome,
                "trialname": str(stimulus) + "_" + str(outcome),
                "exp_response": None,
                "pain_response": None,
            }
            trial_order.append(trial)
            
elif groupname == "naturalhistory":
    for block in range(1,num_blocks_conditioning+1):
        for stimulus,outcome in zip(trial_stim_blocks[block_order[block-1]],naturalhistory_outcome_blocks[block_order[block-1]]):
            trial = {
                "phase": "conditioning",
                "blocknum": block,
                "stimulus": stimulus,
                "outcome": outcome,
                "trialname": str(stimulus) + "_" + str(outcome),
                "exp_response": None,
                "pain_response": None,
            }
            trial_order.append(trial)
                    
#create extinction trials, all outcomes same regardless of condition (low heat)
for block in range(num_blocks_conditioning+1,num_blocks_conditioning+num_blocks_extinction+1):
    for stimulus,outcome in zip(trial_stim_blocks[block_order[block-1]],extinction_outcome_block):
        trial = {
            "phase": "extinction",
            "blocknum": block-num_blocks_conditioning,
            "stimulus": stimulus,
            "outcome": outcome,
            "trialname": str(stimulus) + "_" + str(outcome),
            "exp_response": None,
            "pain_response": None
        }
        trial_order.append(trial)
        
# # Assign trial numbers
for trialnum, trial in enumerate(trial_order, start=1):
    trial["trialnum"] = trialnum
    
save_data(trial_order)
    
# #Test questions
rating_stim = { "Pain": visual.Slider(win,
                                    pos = (0,-200),
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
                "Expectancy": visual.Slider(win,
                                    pos = (0,-200),
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30)}

rating_stim["Pain"].marker.size = (30,30)
rating_stim["Pain"].marker.color = "yellow"
rating_stim["Pain"].validArea.size = (660,100)

rating_stim["Expectancy"].marker.size = (30,30)
rating_stim["Expectancy"].marker.color = "yellow"
rating_stim["Expectancy"].validArea.size = (660,100)

pain_rating = rating_stim["Pain"]
exp_rating = rating_stim["Expectancy"]

# # text stimuli
instructions_text = {
    "welcome": "Welcome to the experiment! Please read the following instructions carefully.", 
    "TENS_introduction": "This experiment aims to investigate the effects of Transcutaneous Electrical Nerve Stimulation (TENS) on pain sensitivity. \
        TENS may be able to increase pain sensitivity by enhancing the pain signals that travel up your arm and into your brain.\n\n\
        The TENS itself is not painful, but you will feel a small sensation when it is turned on.",
    "preexposure": "Before we begin, we will record some baseline measures. Please stay seated and stay still during this phase, as excessive movement may interfere with our readings. \n\n \
        The TENS device may be activated intermittently, although NO thermal stimuli will be delivered during this phase.",
    "baseline": "Before we begin, we will record some baseline measures. Please stay seated and stay still during this phase, as excessive movement may interfere with our readings. \n\n \
        NO thermal stimuli will be delivered during this phase.",
    "conditioning_socialmodel": "Baseline measures have been recorded, thank you for your patience. \n\n\
        Please call for the experimenter to prepare for the next stage of the experiment",
    "conditioning_naturalhistory": "Baseline measures have been recorded, thank you for your patience. \n\n\
        Please call for the experimenter to prepare for the next stage of the experiment",
    "experiment" : "We will now begin the main phase of the experiment. \n\n\
You will now receive a series of thermal stimuli and your task is to rate the intensity of each thermal stimulus on a rating scale. \
This rating scale ranges from NOT PAINFUL to VERY PAINFUL. \n\n\
All thermal stimuli will be signaled by a 10 second countdown. The heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. \
As you are waiting for the thermal stimulus during the countdown, you will also be asked to rate how painful you expect the heat to be. After each trial there will be a brief interval to allow you to rest between thermal stimuli. \n\n\
Please ask the experimenter if you have any questions now before proceeding.",
    "continue" : "\n\nPress spacebar to continue",
    "end" : "This concludes the experiment. Please ask the experimenter to help remove the devices.",
    "termination" : "The experiment has been terminated. Please ask the experimenter to help remove the devices."
}

# cue_demo_text = "When you are completely relaxed, press any key to start the next block..."

response_instructions = {
    "Pain": "How painful was the thermal stimulus?",
    "Expectancy": "How painful do you expect the next thermal stimulus to be?" #,
#     "Shock": "Press spacebar to activate the shock",
#     "Check": "Please indicate whether you would like to try the next level of shock, stay at this level, or go back to the previous level for the experiment.",
#     "Check_max": "Note that this is the maximum level of shock.\n\n\
#  Would you like to stay at this level or go down a level?"
                         }

pain_text = visual.TextStim(win,
            text=response_instructions["Pain"],
            height = 35,
            pos = (0,-100),
            )

exp_text = visual.TextStim(win,
            text=response_instructions["Expectancy"],
            height = 35,
            pos = (0,-100)
            ) 
# pre-draw countdown stimuli (numbers 10-1)
countdown_text = {}
for i in range(0,11):
    countdown_text[str(i)] = visual.TextStim(win, 
                            color="white", 
                            height = 50,
                            text=str(i))
    
# Define button_text dictionaries
#### Make trial functions
def show_trial(current_trial):
    #set ITI for trial
    iti = random.randint(iti_jitter) / 1000
    
    if pport != None:
        pport.setData(0)
        
    win.flip()
        
    # Start countdown to shock
    
    # Make a count-down screen
    countdown_timer = core.CountdownTimer(10)  # Set the initial countdown time to 10 seconds
  
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
                pport.setData(stim_trig[current_trial["stimulus"]])
            if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                pport.setData(0)
                TENS_timer = countdown_timer.getTime() 

        countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
        win.flip()

    
    TENS_timer = countdown_timer.getTime() + TENS_pulse_int

    while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
        if pport != None:
            termination_check()
                      
            # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int
            if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                pport.setData(stim_trig[current_trial["stimulus"]])
            if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                pport.setData(0)
                TENS_timer = countdown_timer.getTime() 

        countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
        
        # Ask for expectancy rating
        exp_text.draw() 
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
        termination_check()
        pain_rating.draw()
        pain_text.draw()
        win.flip()
            
            
    pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
    
    while core.getTime() < pain_response_end_time:
        termination_check()
        pain_text.draw()
        pain_rating.draw()
        win.flip()
        
    current_trial["pain_response"] = pain_rating.getRating()
    pain_rating.reset()

    win.flip()
    
    core.wait(iti)
    current_trial["iti"] = iti

exp_finish = True

# # Run experiment
# while not exp_finish:
#     termination_check()
#     #display welcome instructions
#     instruction_trial(instructions_text["welcome"],3)
#     instruction_trial(instructions_text["TENS_introduction"],3)
    
#     # #display main experiment phase
#     instruction_trial(instructions_text["experiment"],10)
#     for trial in trial_order:
#         show_trial(trial)

#     pport.setData(0) # Set all pins to 0 to shut off context, TENS, shock etc.    
#     # save trial data
#     save_data(trial_order)
#     exit_screen(instructions_text["end"])
    
#     exp_finish = True
    
# win.close()