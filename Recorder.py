from typing import final
from screeninfo import get_monitors
import sounddevice as sd
import subprocess
import signal
import glob
import os

class RecorderException(Exception):
    pass

class Recorder:
    
    current_monitor = None
    current_audio_output = None
    
    @classmethod
    def setScreenInfo(cls):
        cls.current_monitor = get_monitors()[0]
        cls.current_audio_output = sd.query_devices(kind='output')
    
    def __init__(self):
        Recorder.setScreenInfo()
        self.recording_cmd = ['ffmpeg', '-f', 'dshow', '-i', 'audio="virtual-audio-capturer":video="screen-capture-recorder"']
        self.__recording_process = None
        self.__recording = False
        self.__current_capture_file = None
    
    def __reset(self):
        self.__recording = False
        self.__current_capture_file = None
    
    @property
    def isRecording(self) -> bool:
        return self.__recording

    @property    
    def RP(self):
        return self.__recording_process
    
    @final
    def stopRecording(self, saveing_name: str):
        if self.__recording:
            self.__recording_process.communicate(b"q")
            self.__recording_process.wait(10)
            if os.path.exists(self.__current_capture_file) and os.path.exists(saveing_name):
                os.rename(self.__current_capture_file, os.path.join(saveing_name, self.__current_capture_file))
                self.__reset()
            else:
                raise RecorderException(f"ffmpeg error: no file named '{self.__current_capture_file}' in '{os.getcwd()}'")
    
    @final
    def record(self, file_name):
        if not self.__recording:
            file_name = f"{file_name}.mp4"
            self.__recording_process = subprocess.Popen(f'ffmpeg -f dshow -i audio="virtual-audio-capturer":video="screen-capture-recorder" {file_name}', stdin=subprocess.PIPE,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.__recording = True
            self.__current_capture_file = file_name
        else:
            raise RecorderException("Already recording!")