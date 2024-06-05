# Import packages
from psychopy import core, event, gui, visual, parallel, prefs
import math
import csv
import os

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
eda_trig = 1
tens_trig = {"TENS": 128, "control": 0} #Pin 8 in relay box just for the clicking sound

## within experiment parameters
experimentcode = "LI1_SM"
P_info = {"PID": ""}
info_order = ["PID"]
# iti_range = [6,8]
iti = 6 
familiarisation_iti = 3
cue_colours = ([-1,0.10588,-1],[-1,-1,1]) # 2 colours taken from Kirsten EEG
cue_colour_names = ('green','blue')
cue_positions = [(300,0),(-300,0)]
cue_width = 200

video_painratings_buffer = 5
video_stim_iti = 6

rating_scale_pos = (0,-350)
rating_text_pos = (0,-250) 
text_height = 30 

stim_colours = {
  "TENS" : cue_colours[0],
  "control": cue_colours[1] 
}

stim_colour_names = {
    "TENS" : cue_colour_names[0],
    "control": cue_colour_names[1]
}

stim_positions = {
    "TENS" : cue_positions[1],
    "control" : cue_positions[0]
}


data_filename = "responses.csv"
script_directory = os.path.dirname(os.path.abspath(__file__))  #Set the working directory to the folder the Python code is opened from

#set a path to a "data" folder to save data in
data_folder = os.path.join(script_directory, "data")

# if data folder doesn"t exist, create one
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
    
#set file name within "data" folder
data_filepath = os.path.join(data_folder,data_filename)

if os.path.exists(data_filepath):
    print(f"Data already exists. Choose a different participant ID.") ### to avoid re-writing existing data


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

if ports_live == True:
    pport = parallel.ParallelPort(address=port_address) #Get from device Manager
    pport.setData(0)
    
elif ports_live == None:
    pport = None #Get from device Manager

#create instruction trials
def instruction_trial(instructions,
                      waittime=0): 
    termination_check()
    
    visual.TextStim(win,
                    text = instructions,
                    height = text_height,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    win.flip()
    core.wait(waittime)

    
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
        core.quit()


# Define trials
trial_order = []

#### 4 x blocks (4x fixed pseudo-randomised runs of 4x TENs and 4x no-TENS)
num_blocks_conditioning = 2

conditioning_stim_blocks = [['control', 'TENS', 'control', 'control', 'TENS', 'TENS', 'TENS', 'control','control', 'TENS', 'TENS', 'control', 'control', 'TENS', 'TENS', 'control'],
                           ['TENS', 'TENS', 'TENS', 'control', 'TENS', 'control', 'TENS', 'control','control', 'TENS', 'control', 'TENS', 'control', 'control', 'TENS', 'control']]

conditioning_outcome_blocks = [['low','high','low','low','high','high','high','low','low','high','high','low','low','high','high','low'],
                              ['high','high','high','low','high','low','high','low','low','high','low','high','low','low','high','low']]

for block in range(1,num_blocks_conditioning+1):
    for stimulus,outcome in zip(conditioning_stim_blocks[block-1],conditioning_outcome_blocks[block-1]):
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
        
response_instructions = {
    "pain": "How painful was the heat?",
    "expectancy": "How painful do you expect the thermal stimulus to be?"
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
            )
}

# #Test questions
rating_stim = { "pain": visual.Slider(win,
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

rating_stim["pain"].marker.size = (30,30)
rating_stim["pain"].marker.color = "yellow"
rating_stim["pain"].validArea.size = (660,100)

rating_stim["expectancy"].marker.size = (30,30)
rating_stim["expectancy"].marker.color = "yellow"
rating_stim["expectancy"].validArea.size = (660,100)

pain_rating = rating_stim["pain"]
exp_rating = rating_stim["expectancy"]
                                
# pre-draw countdown stimuli (numbers 10-1)
countdown_text = {}
for i in range(0,41):
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
# Create functions
    # Save responses to a CSV file
def save_data(data):
    for trial in trial_order:
        trial['experimentcode'] = experimentcode
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
    

def show_trial(current_trial):
   
    if pport != None:
        pport.setData(0)

    iti = video_stim_iti
        
    win.flip()
    
    # Set the initial countdown time to 10 seconds
    countdown_timer = core.CountdownTimer(10)  

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
                pport.setData(tens_trig[current_trial["stimulus"]])
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
                pport.setData(tens_trig[current_trial["stimulus"]])
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
        pport.setData(pain_trig+eda_trig)
        core.wait(port_buffer_duration)
        pport.setData(0)

    # Get pain rating 
    pain_response_time = core.getTime() + video_painratings_buffer # amount of time for participants to adjust slider after making a response
    
    while core.getTime() < pain_response_time:
        termination_check()
        trial_text["pain"].draw()
        pain_rating.draw()
        win.flip()
        
    current_trial["pain_response"] = pain_rating.getRating()
    pain_rating.reset()

    win.flip()
    core.wait(iti)
    current_trial["iti"] = iti
    
exp_finish = None        
lastblocknum = None

# Run experiment
while not exp_finish:
    termination_check()

    if pport != None:
        pport.setData(0)
        
    instruction_trial("Experiment will start in 10 seconds",10)
    
    for trial in trial_order:
        current_blocknum = trial['blocknum']
        if lastblocknum is not None and current_blocknum != lastblocknum:
            instruction_trial("Wait for Cosette to change thermode location. Will automatically resume after brief rest",20)
        show_trial(trial)
        lastblocknum = current_blocknum
    
    instruction_trial("Wait for Cosette to come back in.",10)
    # save trial data
    save_data(trial_order)
    
    exp_finish = True
    
win.close()