####################################################################################################################
# IMPROVEMENTS NEEDED:
# 1. Events instead of hard-coded timeout
# 2. Regex instead of hardcoded keywords as a criteria for PASS/FAIL
####################################################################################################################

import time
import subprocess
import shlex
import sys
from threading import Timer
import os
import tkinter as tk
import tkinter.filedialog


# escapes = ''.join([chr(char) for char in range(1, 32)])
escape = ''.join(chr(27)) # character generated in the report file which should be removed

command = [";", "ping", "8.8.8.8"] # a string which should be concatenated to the Linux command since ping should be repeated x times
res = []

print("Choose the path where reports will be saved to: \n") 

root = tk.Tk() # used for creation of GUI file dialog
root.withdraw() # use to hide tkinter window

currdir = os.getcwd()
file_path = tk.filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select a directory')

# concatenate ping command 100 times to ensure it will return some bytes
# until data connection is established
def repeatCommand():
    for i in range(100):
        for x in command:
            res.append(x)
    return res


class Error(Exception):
    """Base class for other exceptions"""
    pass

class RILFailure(Error):
    pass
       

def execRIL(cmd, file, timeout):
    # the last two files should not be read, those have to be executed the other way
    if(len(cmd) == len(file[:-2])): 
        for i in range(len(cmd)):
            try:
                with open(file[i], "w") as f:
                    subprocess.run(shlex.split(cmd[i]), stdout = f, stderr = f, timeout = timeout)
            except subprocess.TimeoutExpired:
                print(os.path.basename(file[i])[:-4], ' timeout expired')  
                with open(file[i], "a+") as f:
                    f.write('\n TIMEOUT EXPIRED \n')             
    else:
        raise RILFailure("Lengths of cmd and file must be the same!")


def CHECK_LOG(files):
    try:
        for file in files:
            with open(file, "r+") as f:
                # different criterias for analysis are used for those 2 test so they are excluded in the main if
                if (file != (file_path + "/" + "request_and_test_data_connection.txt" and file_path + "/" + "ping_test.txt")):
                    a = f.read()
                    # os.stat(file).st_size == 0 means that the report file is empty
                    if ((('E_GENERIC_FAILURE' or 'moderm no response' or 'Segmentation fault') in a
                         or 'Request completed: E_SUCCESS' not in a)
                        or os.stat(file).st_size == 0):
                        # os.path.basename(file)[:-4] takes the report name from the file path and excluides .txt                    
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" FAILED \n")
                        f.write("____________________________________________________________________")
                        continue
                    # if a read file is not from the RIL functions which are running in inf loop:
                    elif (file == file[0] or file == file[1] or file == file[3] or file == file[4]): 
                        if (subprocess.TimeoutExpired):
                            f.write("\n\n")
                            f.write("____________________________________________________________________ \n")
                            f.write(os.path.basename(file)[:-4])
                            f.write(" FAILED \n")
                            f.write("____________________________________________________________________")
                            continue                         
                    else:
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" PASSED \n")
                        f.write("____________________________________________________________________")
                        continue
                elif (file == file_path + "/" + "ping_test.txt"):
                    a = f.read()
                    if(('PING' and 'bytes from' and 'icmp_seq=1') in a):
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" PASSED")
                        f.write("\n____________________________________________________________________")
                        continue
                    else:
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" FAILED \n")
                        f.write("____________________________________________________________________")
                        continue
                elif (file == file_path + "/" + "request_and_test_data_connection.txt"):
                    a = f.read()
                    if(("Request completed: E_SUCCESS" and "addresses:" and "dnses:" and "gateways:") in a):
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" PASSED")
                        f.write("\n____________________________________________________________________")
                        continue
                    else:
                        f.write("\n\n")
                        f.write("____________________________________________________________________ \n")
                        f.write(os.path.basename(file)[:-4])
                        f.write(" FAILED \n")
                        f.write("____________________________________________________________________")
                        continue
                             
    except subprocess.TimeoutExpired:          
        print("RIL function FAILED: timeout expired")
        
        
cmd = [
    "adb shell request_operator",
    "adb shell request_get_sim_status",
    "adb shell request_setup_data_call -a vipmobile",
    "adb shell request_radio_power",
    "adb shell request_send_sms 381649402195"
]
# the last 2 files should remain on those positions for successful execution
file = [
    file_path + "/" + "request_operator.txt",
    file_path + "/" + "request_get_sim_status.txt",
    file_path + "/" + "request_setup_data_call.txt",
    file_path + "/" + "request_radio_power.txt",
    file_path + "/" + "request_send_sms.txt",
    file_path + "/" + "request_and_test_data_connection.txt",
    file_path + "/" + "ping_test.txt",
]


kill = lambda process: process.kill()

with open(file_path + "/" + "request_and_test_data_connection.txt", "w") as f:
    with open(file_path + "/" + "ping_test.txt", "w") as g:
        rtdc = subprocess.Popen(["adb", "shell", "request_and_test_data_connection", "-a", "vipmobile"], stdout = f, stderr = f)
        ping = subprocess.Popen(["adb", "shell", "ping", "8.8.8.8", " ".join(repeatCommand())], stdout = g, stderr = g)

        my_timer = Timer(60, kill, [rtdc])
        my_timer2 = Timer(60, kill, [ping])

        try:
            my_timer.start()
            my_timer2.start()
            rtdc.communicate()
        finally:
            my_timer.cancel()
            my_timer2.cancel()


execRIL(cmd, file, 60)
CHECK_LOG(file)


