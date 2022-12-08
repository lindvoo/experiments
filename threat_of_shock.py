#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 18:25:30 2022

@author: lindvoo
"""

# Import libraries
import expyriment
import os
import shutil

# To Do
#------------------------------------------------------------------------------

#1) Brainamp
#2) Eyelink
#3) Buttonbox


# Set before start of the experiment
#------------------------------------------------------------------------------

TESTING = 1 # 1 or 0

# Settings
REFRESH_RATE = 60  # In Hz
WINDOW_SIZE = 1280,1040
frame = 1000 / REFRESH_RATE
font_size=48


# TESTING
#------------------------------------------------------------------------------

# When testing
if TESTING == 1:
    expyriment.control.set_develop_mode() #create small screen
    expyriment.control.defaults.window_size=(500,500)
    speedup = 1 # if set at 1 it is normal duration
    portconnected = 0 #no port connected
    eyelinkconnected = 0
else:
    speedup = 1 #normal speed
    portconnected = 1 #port connected
    eyelinkconnected = 1 #eyelink
    

# EYELINK CALIBRATION
#------------------------------------------------------------------------------
# Eyelink
if eyelinkconnected == 1:
    import pygaze
    import calibrate
    tracker = calibrate.cal()
    
    
# TASK SETTINGS
#------------------------------------------------------------------------------

# Colors
l_orange=(255,85,0)
l_blue=(0,85,255)
l_grey=(127,127,127)
l_black=(0,0,0)
l_white=(255,255,255)

# Create experimental task
task = expyriment.design.Experiment(
        name= "Threat_of_Shock",         #name of exp
        background_colour = l_grey)  #background color
expyriment.control.initialize(task)
task.add_data_variable_names(['onset','threat_block','color','dur_trial','shock_blocks'])


# START [so you can give exp input]
#------------------------------------------------------------------------------
# Start
if eyelinkconnected ==1:
    expyriment.control.start(skip_ready_screen=True,subject_id=int(calibrate.log_file))
else:
    expyriment.control.start(skip_ready_screen=True)

#subject codes 101,201,301 etc are run as 001 [according to the counterbalancing sheet]
if task.subject < 10:
    SUBJ_CODE = "SPIN00" + str(task.subject)  
    edffilename=SUBJ_CODE
elif task.subject < 100:
    SUBJ_CODE = "SPIN0" + str(task.subject)
    edffilename=SUBJ_CODE
else:
    SUBJ_CODE = "SPIN0" + str(task.subject)[1:]
    edffilename="SPIN" + str(task.subject)


# Port setting: CHANGE THIS! 
port_shock = [100,200] #code and duration
port_biopack = 1 #code
if portconnected == 1:
    port = expyriment.io.ParallelPort(0xC020) # CHANGE THIS! 


# Keys, Clock
keys = expyriment.io.Keyboard()
keys.set_quit_key(expyriment.misc.constants.K_ESCAPE) #with esc you can quit
responsekey=[]

experimenterkey=[expyriment.misc.constants.K_5] #so pp cannot accidently press space bar and continue


# STIMULUS SETTINGS
#------------------------------------------------------------------------------

# Counterbalance the order of the block, we have 2 orders which have the oposite order
# and in addition the second have is a mirror of the first half [to counteract consequence
# of drift in fMRI signal] addition which color is threat and safe is counterlanced
# 1 = threat, 0 = safe
if task.subject % 4 == 1:
    block_order = [1,0,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,0,1]
    conditions = ['orange','blue'] #counterbalance across subjects
elif task.subject % 4 == 2:
    block_order = [1,0,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,0,1]
    conditions = ['blue','orange'] #counterbalance across subjects
elif task.subject % 4 == 2:
    block_order = [0,1,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,1,0]
    conditions = ['orange','blue'] #counterbalance across subjects
elif task.subject % 4 == 2:
    block_order = [0,1,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,1,0]
    conditions = ['blue','orange'] #counterbalance across subjects
    
    
# Now create the order with the color
block_color = []
for c_trials,n_trials in enumerate(block_order):
    block_color.append(conditions[n_trials])

# Create vector with duration of each block
    if TESTING:
        dur_trial = [500] * len(block_order)# .5 seconds for testing
    else:
        dur_trial = [20000] * len(block_order)# 20 second blocks

# The 1st and the 6th threat block should get a shock
shock_blocks = [0] * len(block_order)
thr_blocks = [c for c,n in enumerate(block_order) if n==1]
shock_blocks[thr_blocks[0]] = 1 # 1rst threat block
shock_blocks[thr_blocks[5]] = 1 # 6st threat block


# Make the triallist
triallistnames=['block_order','conditions','dur_trial','shock_blocks']
triallist=[block_order,block_color,dur_trial,shock_blocks]



# DESIGN [experiment/task, blocks, trials, stimuli]
#------------------------------------------------------------------------------
# Create design (blocks and trials)
# Create stimuli (and put them into trials)
# Create input/output devices (like button boxes etc.)


# One block so no loop
block = expyriment.design.Block("Block")

# Create Design, Loop over trials
for c_trials in range(len(block_order)):

    # Trial [define properties]
    trial =  expyriment.design.Trial()
    for c,name in enumerate(triallistnames):
        trial.set_factor(name,triallist[c][c_trials])   
    
    # Load fix
    if block_color[c_trials] == 'blue':
        stim = expyriment.stimuli.FixCross(colour=l_blue)   
    elif block_color[c_trials] == 'orange':
        stim = expyriment.stimuli.FixCross(colour=l_orange)   
    stim.preload()
       
    # Add stim to trial and trial to block
    trial.add_stimulus(stim)
    block.add_trial(trial)
    

# Add block to task
task.add_block(block)
    
# Other stimuli
fixcross = expyriment.stimuli.FixCross(colour=l_black)                     # default fixation cross
fixcross.preload()

# Function waits for a duration while logging key presses
def wait(dur):
    task.keyboard.clear()
    task.clock.reset_stopwatch()
    while task.clock.stopwatch_time < int(frame * int(round((dur) / frame, 5))) - 2:
        task.keyboard.check(keys=responsekey)

def waituntill(dur):
    task.keyboard.clear()
    while task.clock.time < int(frame * int(round((dur) / frame, 5))) - 2:
        task.keyboard.check(keys=responsekey)


# RUN
#------------------------------------------------------------------------------

# Start
if portconnected == 1:
    port.send(0) # to make sure it is off!

# Check subject code
expyriment.stimuli.TextLine(text="You are running: " + str(task.subject), text_colour=[0,0,0]).present()
task.keyboard.wait(experimenterkey)

# Eyelink [start recording]
if eyelinkconnected == 1:
    tracker.start_recording()
    wait(2000)
    tracker.log('start_time')

#starttime
starttime=endtime=task.clock.time
task.data.add([task.clock.time,"starttime","None","None","None"]) #LOG 



# Loop over trials/blocks
#--------------------------------------------------------------------------

#task.add_data_variable_names(['onset','threat_block','color','dur_trial','shock_blocks'])

# Start block
fixcross.present()
task.data.add([task.clock.time,"0","black",dur_trial[0],"0"]) #LOG 
wait(int(dur_trial[0]))

for count,trial in enumerate(task.blocks[0].trials):

    # Present picture 
    #--------------------------------------------------------------------------
    trial.stimuli[0].present()
    task.data.add([task.clock.time,block_order[count],block_color[count],dur_trial[count],shock_blocks[count]]) #LOG 
    
    # Send code to biopack [open] and Eyelink
    if portconnected == 1:
        port.send(port_biopack)
    if eyelinkconnected == 1:
        tracker.log('BLOCK_ONSET')
        
    # Add shock
    if shock_blocks[count] == 1:
        print("GIVE SHOCK!")

    # Wait for and show response
    wait(int(trial.get_factor("dur_trial")))

    # send code to biopack [close] and Eyelink
    if portconnected == 1:
        port.send(0)
    if eyelinkconnected == 1:
        tracker.log('BLOCK_OFFSET')   

# End block
fixcross.present()
task.data.add([task.clock.time,"0","black",dur_trial[0],"0"]) #LOG 
wait(int(dur_trial[0]))


# End
expyriment.control.end(goodbye_text="The is the end of this run.",
             goodbye_delay=2000)
task.data.add([task.clock.time,"endtime","None","None","None"]) #LOG 

# Eyelink [END RECORDING]
if eyelinkconnected == 1:
    tracker.log('end_time')
    tracker.stop_recording()
    tracker.close()


# MOVE DATA
#--------------------------------------------------------------------------
## make directory
#data_dir = os.path.join(task.data.directory, edffilename)
#event_dir = os.path.join(task.events.directory, edffilename)
#if not os.path.exists(data_dir):
#    os.makedirs(data_dir)
#if not os.path.exists(event_dir):
#    os.makedirs(event_dir)
#    
## Move folders
#shutil.move(task.data.fullpath, os.path.join(data_dir, task.data.filename))
#shutil.move(task.events.fullpath, os.path.join(event_dir, task.events.filename))
#
#if eyelinkconnected == 1:
#    os.rename(calibrate.log_file + '.EDF', os.path.join(data_dir, edffilename + WHICH_DAY + WHICH_RUN + '.EDF'))
#    
#
#
#
