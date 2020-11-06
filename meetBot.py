from enum import Enum
import json
from random import gauss
from time import sleep
from typing import final
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from random_user_agent.user_agent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread 
from BotSelectors import MeetSelectors
import os
import re

class BotActions(Enum):
    CLICK = 0
    CLICK_HIDDEN = 1
    SEND_KEYS = 2
    


class Bot:
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

    def __init__(self, user: str) -> None:
        self.user_agent_rotator = user_agent = UserAgent(software_names="chrome", operating_system="linux", limit=100)
        self.browser_options = Options()
        self.driver = self.__setBotOptions(user)
        self.user_name = user
        self.operational_data = self.__getUserdata()
    
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
        assert os.path.exists("./user_data.json"), f"the file '{os.path.join(os.getcwd(), 'user_data.json')}' doesnt exists!"
        with open("./user_data.json","r") as f:
            return json.load(f)

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

    def performActions(self, actions: tuple, delay: float=0.5, randomize: bool=False) -> tuple:
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
                data_collected.append(response)
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
            else:
                raise NotImplementedError(f"No functionallity supported for action {a[0]}")
            
            sleep(delay if not randomize else abs(gauss(delay/2, delay/2)))
        return tuple(data_collected)
    
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
        ), 1)
            