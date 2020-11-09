from enum import Enum
from random import gauss
from time import sleep, time
from typing import  final
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from random_user_agent.user_agent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread
from BotSelectors import MeetSelectors
from Recorder import Recorder
import numpy as np
import json
import os
import re

SCHEDULE_JSON = "schedule.json"
USER_DATA_JSON = "user_data.json"

class BotActions(Enum):
    CLICK = 0
    CLICK_HIDDEN = 1
    SEND_KEYS = 2
    MOVE_TO = 3
    

class ScheduleHandler:
    
    time_matrix = np.array([86400,3600, 60, 1])
    
    def __init__(self, user,  schedule_file: str=SCHEDULE_JSON):
        assert os.path.exists(SCHEDULE_JSON), f"schedule"
        self.schedule = self.__loadScheduleFile(schedule_file)
        self.student_bot = StudentBot(user)
        self.__recorder = Recorder()
        self.__is_shutdown_set = False
        
    def __loadScheduleFile(self, schedule_file: str) -> dict:
        with open(schedule_file, 'r')as f:
            return json.load(f)
    
    def parseSchedule(self, event_string: str) -> tuple:
        """
        parses a event string with format wd1,wd2,...,wdn:hh:mm
        
        wd is short for weekday, it can be a value between 0 and 6 where 0 means MONDAY and 6 means SUNDAY
        hh: is the hour where the event starts
        minute: is the minute of hh where the event starts

        Parameters
        ----------
        event_string : str
            a string decribing the time where the event most be executed    

        Returns
        -------
        tuple
            ((wdn), hh, mm)
        """
        event_time = event_string.split(":")
        assert len(event_time) == 3, f"recived an event string '{event_string}' which is invalid"
        event_time[0] = tuple(map(lambda x: int(x), event_time[0].split(",")))
        event_time[1], event_time[2] = int(event_time[1]), int(event_time[2])
        return tuple(event_time)
    
    def isEventStarted(self, current_time: datetime, event_data: tuple, event_string: str) -> bool:
        return current_time.weekday() in event_data[0] and current_time.hour == event_data[1] and (current_time.minute >= event_data[2] and abs(event_data[2] - current_time.minute) < self.schedule[event_string]['stay'])
    
    def parse24Hstring(self, time24h: str) -> datetime:
        assert re.match(r"^\d\d:\d\d$", time24h)
        time24h = tuple(map(lambda x: int(x), time24h.split(':')))
        current_time = datetime.now()

        parsed_time = datetime(current_time.year, current_time.month, current_time.day, time24h[0], time24h[1])
        if parsed_time < current_time:
            parsed_time += timedelta(days=1)
        
        return parsed_time  
    
    def shutdownAt(self, shutdown_time: str):
        """
        shutsdown the computer at a defined hour

        Parameters
        ----------
        shutdown_time : str
            a string representing the shutdown hour in 24h format 'hh:mm'
    
        """
        shutdown_time = self.parse24Hstring(shutdown_time)
        seconds = int((shutdown_time - datetime.now()).total_seconds())
        self.__setShutdown(seconds)

    def shutdownIn(self, days=0, hours=0, minutes=0, seconds=0):
        shutdown_time  = np.array([days, hours, minutes, seconds])
        return self.__setShutdown(np.dot(shutdown_time, ScheduleHandler.time_matrix))
    
    def __abortShutdown(self):
        self.__is_shutdown_set = False
        os.system("shutdown -a")

    def __setShutdown(self, seconds: int):
        if self.__is_shutdown_set:
            self.__abortShutdown()
        
        self.__is_shutdown_set = True
        os.system(f"shutdown -s -f -t {seconds}")
    
    @final    
    def awaitEvent(self,multiple=False):
        """
        awaits for an event to start and logs into the corresponding videoconference

        Parameters
        ----------
        multiple : bool, optional
            [description], by default False
        """
        while True:
            current_time = datetime.now()
            monitoring_thread = Thread(target=self.student_bot.startMonitorClass)
            for scheduled_event in self.schedule.keys():
                parsed_event = self.parseSchedule(scheduled_event) # tuple returned ((wd1,..,wdn),hh,mm)
                if self.isEventStarted(current_time, parsed_event ,scheduled_event):
                    print(f"Event {scheduled_event} started!")
                    self.__recorder.record(f'{self.schedule[scheduled_event]["class_name"]}-{current_time.strftime("%H-%M")}')
                    self.student_bot.joinMeet(self.schedule[scheduled_event]['class_name'])
                    print(f"staying in class {self.schedule[scheduled_event]['class_name']} for {self.schedule[scheduled_event]['stay']} minutes")
                    
                    monitoring_thread.start()
                    
                    minutes_elapsed = 0
                    while self.schedule[scheduled_event]['stay'] != minutes_elapsed and self.student_bot.OnClass:
                        minutes_elapsed += 1
                        sleep(60)
                    
                    print("getting out of class")
                    self.student_bot.logoutClass()
                    monitoring_thread.join(30)
                    self.__recorder.stopRecording('.')
                    if not multiple:
                        return
                    
            sleep(60)
                

class StudentBotException(Exception):
    pass

class StudentBot:
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

    bot_regexs = {
        "meetcall": re.compile(r"^https?://meet\.google\.com/([a-z]{2,}-([a-z]{2,}-?)+)\??([a-z_]+=[\da-z]+)*$")
    }
    
    def __init__(self, user: str, user_file: str=USER_DATA_JSON) -> None:
        self.user_file = user_file
        self.user_agent_rotator = UserAgent(software_names="chrome", operating_system="linux", limit=100)
        self.browser_options = Options()
        self.driver = self.__setBotOptions(user)
        self.user_name = user
        self.operational_data = self.__getUserdata()
        self.__on_class = False
        self.current_class = "N/A"
    
    def __del__(self):
        self.driver.close()
    
    def __setBotOptions(self, user) -> WebDriver:
        self.browser_options.add_argument(f"user_agent={self.user_agent_rotator.get_random_user_agent()}")
        self.browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.browser_options.add_experimental_option('useAutomationExtension', False)
        self.browser_options.add_argument("start-maximized")
        self.browser_options.add_argument(f"user-data-dir={user}")
        self.browser_options.add_experimental_option("prefs", { \
                "profile.default_content_setting_values.media_stream_camera": 2,
                "profile.default_content_setting_values.media_stream_mic": 2, 
                # "profile.default_content_setting_values.geolocation": 2, 
                "profile.default_content_setting_values.notifications": 2 
        })
        return webdriver.Chrome(os.path.join(os.getcwd(), "chromedriver.exe"), chrome_options= self.browser_options)        
    
    def __getUserdata(self):
        assert os.path.exists(self.user_file), f"the file '{os.path.join(os.getcwd(), self.user_file)}' doesnt exists!"
        with open(self.user_file,"r") as f:
            return json.load(f)

    @property
    def OnClass(self) -> bool:
        return self.__on_class


    def clickHiddenBTN(self, selector: str) -> bool:
        self.driver.execute_script("return document.querySelector(arguments[0]).click();", selector)

    def querySelector(self, selector: str) -> webdriver.remote.webdriver.WebElement:
        return self.driver.execute_script("return document.querySelector(arguments[0])", selector)
    
    def getFocusedElement(self) -> webdriver.remote.webdriver.WebElement:
        return self.driver.execute_script("return document.activeElement;")
    
    def getClassCode(self, class_name: str) -> str:
        return self.operational_data[self.user_name]["asignatures"][class_name]["code"]
    
    def getUserDataField(self, field: str) -> str or int:
        """
            returns a field from the user data

            Parameters
            ----------
            field : str
                the name of the field

            Returns
            -------
            str or int
                the value of the flied
        """
        return self.operational_data[self.user_name][field]

    def performActions(self, actions: tuple, delay: float=0.5, randomize: bool=False, panic: bool=False) -> tuple:
        """
        each action should be a tuple in which the first element will be the name of the action

        Parameters
        ----------
        actions : tuple
            set of actions of shape((action_name, ?selector if needed, ?data_to type), ... nth-action)
        delay : float, optional
            the time that the bot must wait before performing the next, by default 0.5
        randomize : bool, optional
            if true, the delay value will be randomized in a range between gauss(|delay/2|)

        Returns
        -------
        tuple
            actions responses or data collected in the order they were collected
        """
        
        
        data_collected = []
        for a in actions:
            response = False
            if a[0] == BotActions.CLICK:
                assert len(a) >= 2, f"not enought arguments for clicking actions, recevied '{a}' as arguments"
                if (web_element := self.querySelector(a[1])):
                    response = True
                    web_element.click()
            elif a[0] == BotActions.SEND_KEYS:
                assert len(a) >= 3, f"not enought arguments for typing actions, recevied '{a}' as arguments"
                if (web_element := self.querySelector(a[1])):
                    response = True
                    web_element.send_keys(a[2])
            elif a[0] == BotActions.CLICK_HIDDEN:
                # will allways return true so currently there is no way to know if an object was actually clicked
                assert len(a) >= 2, f"not enought arguments for clicken actions, recevied '{a}' as arguments"
                response = True
                if len(a) == 3:
                    wait = WebDriverWait(self.driver, a[2])
                    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, a[1])))
                self.clickHiddenBTN(a[1])
            elif a[0] == BotActions.MOVE_TO:
                assert len(a) == 2, f"Move action requires A url as second parameter, got '{a}'"
                response = True
                self.driver.get(a[1])
            else:
                raise NotImplementedError(f"No functionallity supported for action {a[0]}")
            
            if not response and panic:
                raise StudentBotException(f"Action '{a[0]}' couldnt be executed with parameters '{a[1:]}'")
            data_collected.append(response)
            sleep(delay if not randomize else abs(gauss(delay/2, delay/2)))
        assert len(actions) == len(data_collected)
        return tuple(data_collected)
    
    def getElementContent(self, selector: str):
        js_command = """
        let a = document.querySelector(arguments[0]);
        let return_value = "-1";
        if(a != undefined)
        {
            return_value = a.innerText;
        }
        return return_value;
        """
        return self.driver.execute_script(js_command,selector)
    
    @final
    def joinMeet(self, meet_class: str) -> None:
        self.driver.get(self.operational_data['meet'])
        
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, MeetSelectors.SET_CLASS_CODE_BTN)))
        self.performActions((
            (BotActions.CLICK, MeetSelectors.SET_CLASS_CODE_BTN),
            (BotActions.SEND_KEYS, MeetSelectors.CODE_INPUT, self.getClassCode(meet_class) ),
            (BotActions.CLICK, MeetSelectors.CLASS_CONTINUE_BTN),
            (BotActions.CLICK_HIDDEN, MeetSelectors.CLOSE_CAMMIC_ALERT, 6),
            (BotActions.CLICK_HIDDEN, MeetSelectors.JOIN_BTN, 3)
        ), 1, panic=True)
        
        if (self.getElementContent(MeetSelectors.PEOPLE_COUNT) == "1"):
            # closes the invite dialog in case we are the first to arrive to the call
            self.performActions(tuple([(BotActions.CLICK_HIDDEN, MeetSelectors.CLOSE_INVITE_DIALOG, 5)]),0.1)
        
        self.performActions([(BotActions.CLICK_HIDDEN, MeetSelectors.CHAT_BTN, 3)])
        
        self.__on_class = True if StudentBot.bot_regexs['meetcall'].match(self.driver.current_url) else False
        self.current_class = meet_class
        
    @final
    def logoutClass(self):
        if self.OnClass:
            response = self.performActions(tuple([(BotActions.MOVE_TO, "https://google.com/")]),2)
            self.__on_class = False
    
    def getAllComments(self) -> list:
        js_command = """
        let comments = document.querySelectorAll(arguments[0]),
            text_comments = [];
        
        comments.forEach(c => text_comments.push(c.innerText));
        return text_comments;
        """
        return self.driver.execute_script(js_command, MeetSelectors.COMMENTS_CLASS)
    
    def saveComments(self, comments: list):
        serialized_comments = ""
        for h,c in enumerate(comments):
            serialized_comments += f"{c}\n{'='*15}\n"
        
        assert os.path.exists(self.user_name)
        
        saving_path = self.user_name
        for step in [ "clases", self.current_class]:
            saving_path = os.path.join(saving_path, step)
            if not os.path.exists(saving_path):
                os.mkdir(saving_path)
        
        with open(os.path.join(saving_path, f"{self.current_class}-{datetime.now().strftime('%d-%m')}.txt"), "w",encoding="utf-8") as f:
            f.write(serialized_comments)
            
        self.current_class = "N/A"

        
    def startMonitorClass(self):
        highest_people_count = 1
        comments = None
        while self.OnClass:
            current_people_count = self.getElementContent(MeetSelectors.PEOPLE_COUNT)
            if current_people_count == "-1":
                continue
            assert current_people_count.isdigit()
            current_people_count = int(current_people_count)
            if current_people_count > highest_people_count:
                highest_people_count = current_people_count
                
            elif current_people_count <= (highest_people_count * 0.5):
                print("MORE THEN 50% OF THE PEOPLE LEFT. LOGGING OUT")
                self.logoutClass() #this will make self.OnClass == False
                continue
                
            comments = self.getAllComments()            
            
            sleep(10)
        self.saveComments(comments)
        print(comments)
    
if __name__ == "__main__":
    secretary = ScheduleHandler("lalo")
    secretary.shutdownIn(hours=1)
    exit(0)