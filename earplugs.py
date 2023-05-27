from pycaw.pycaw import AudioUtilities
import keyboard
from functools import partial
import threading
import time
from win32 import win32gui

processName = "DayZ_x64.exe"
applicationTitle = "DayZ"
earplugsEnabled = threading.Event()
volume = 1.0
dayzSession = None
escape_pressed = False
allow_exit = True
volume_ctrl = None
shift_pressed = False
n_pressed = False
sessionStillExists = False
sessionEstablished = False
stop_thread = False

print("\n\nTo exit the application press ESC")

def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    window_title = win32gui.GetWindowText(hwnd)
    return window_title


def on_escape_press(event):
    global escape_pressed, allow_exit
    if dayzSession is None:
        escape_pressed = True
    elif allow_exit:
        allow_exit = False
        if(allow_exit):
            print("\nEscape key pressed.")
    else:
        print("To exit - press END.")


def on_shift_press(event):
    global shift_pressed
    shift_pressed = True

def on_shift_release(event):
    global shift_pressed
    shift_pressed = False
    
def on_n_press(event):
    global n_pressed
    n_pressed = True

def on_n_release(event):
    global n_pressed
    n_pressed = False
    
keyboard.on_press_key("esc", on_escape_press)
keyboard.on_press_key("shift", on_shift_press)
keyboard.on_release_key("shift", on_shift_release)
keyboard.on_press_key("n", on_n_press)
keyboard.on_release_key("n", on_n_release)

while dayzSession is None and not escape_pressed:
    try:
        print("\nAwaiting for DayZ to start up...")
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name() == processName:
                dayzSession = session
                sessionEstablished = True
                print("\nConnection established:\n" + str(dayzSession.Process))
                volume_ctrl = dayzSession.SimpleAudioVolume
                break
            else:
                time.sleep(0.1)
                if escape_pressed:
                    break
        if(volume_ctrl is None):
            time.sleep(3)
    

    except Exception as e:
        print("Error occurred:", str(e))
        break

if(volume_ctrl is not None):
    print("\nDayZ audio controller has been succesfully linked!\nYou can enable your earplugs by pressing 'N' button now.\n\n")

if escape_pressed:
    if(allow_exit):
        print("\nEscape key pressed.")
else:
    def enableEarplugs(event):
        if(get_active_window_title() == applicationTitle):
            if not earplugsEnabled.is_set():
                if event.name == 'n' or n_pressed and shift_pressed:
                    earplugsEnabled.set()
                    print("Earplugs enabled")
                    volume_ctrl.SetMasterVolume(volume, None)
                    print("Volume set to: " + str(volume))
            else:
                if event.name == 'n' or n_pressed and shift_pressed:
                    earplugsEnabled.clear()
                    print("Earplugs disabled")
                    volume_ctrl.SetMasterVolume(1, None)
                    print("Volume set to: " + str(1.0))
        else:
            if(event.name == 'n'):
                print("You have to be focused on DayZ to enable airplugs.")
            elif(event.name == '_' or event.name == '-' or event.name == '=' or event.name == '+'):
                print("You have to be focused on DayZ to manipulate airplugs.")
                
    def setVolume(volumeButton, volume_ctrl):
        global volume
        if(get_active_window_title() == applicationTitle):
            if earplugsEnabled.is_set():
                if volumeButton.name == '=' or volumeButton.name == '+':
                    if volume < 1:
                        volume += 0.1
                        volume = round(volume, 1)
                        volume_ctrl.SetMasterVolume(volume, None)
                        print("Volume set to: " + str(volume))
                elif volumeButton.name == '-' or volumeButton.name == '_':
                    if volume > 0:
                        volume -= 0.1
                        volume = round(volume, 1)
                        volume_ctrl.SetMasterVolume(volume, None)
                        print("Volume set to: " + str(volume))

    keyboard.on_press(partial(enableEarplugs))
    keyboard.on_press(partial(setVolume, volume_ctrl=volume_ctrl))

    def check_if_process_still_running():
        global sessionEstablished, stop_thread

        while (sessionEstablished and not stop_thread):
            if(keyboard.is_pressed('end')):
                stop_thread = True
                break
           
            sessions = AudioUtilities.GetAllSessions()
            sessionStillExists = False

            for session in sessions:
                if session.Process and session.Process.name() == processName:
                    sessionStillExists = True

            if sessionStillExists:
                sessionEstablished = True
            else:
                sessionEstablished = False
                stop_thread = True
                
                
    monitor_active_processes_Thread = threading.Thread(target=check_if_process_still_running)
    monitor_active_processes_Thread.start()
    
    while True:
        if keyboard.is_pressed('end') or escape_pressed:
            break
        if(not sessionEstablished):
            print("\n" + applicationTitle + " session has ended")
            break
        time.sleep(0.1) #literally the most important line of code - otherwise PCU would not handle this many calculations and you'd experience severe lag

if(volume_ctrl is not None):
    volume_ctrl.SetMasterVolume(1, None)
    print("Volume default value has been restored")
print("Exiting application...")
time.sleep(1.5)