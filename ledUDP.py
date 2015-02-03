"""
 Title: LedUDP.py
 Description: This library helps users controlling the USR-WIFI232 module once
    it has been set to PWM mode. 
    This library contains a class definition that allows users setting new 
    colors without having to write specific commands for the modules.
    It also updates its internal status periodically on a different thread, so
    users don't have to request the status unless it is really required. This 
    This feature is very useful once the LEDs have been installed at home and 
    and the status must be verified periodically in case an external source 
    changed it.
""" 
__author__ = "Angel Hernandez"
__contributors__ = "Angel Hernandez"
__license__ = "GPL"
__version__ = "0.7"
__maintainer__ = "Angel Hernandez"
__email__ = "angel@tupperbot.com"
__status__ = "beta"

import socket                   # To talk to the modules
from time import sleep          # To create some delays on the communication
from threading import Thread    # To have a thread polling the modules
from datetime import datetime   # To improve reporting representation


class Led:
    """ CLASS Led:
    This class contains all the methods required to control the modules and 
    variables to help identify each module as well as pulling its status.
    """  
    # CONSTANTS DEFINITION
    DEFAULT_RED_PIN = "3"      # Red line connected to Pin 3
    DEFAULT_GREEN_PIN = "2"    # Green Line Connected to Pin 2
    DEFAULT_BLUE_PIN = "1"     # Blue Line Connected to Pin 1
    
    DEFAULT_VERBOSITY = 0           # Proportional to the amount of data shown
    DEFAULT_NAME = "NONE"           # Name of the current module. e.g. Kitchen
    DEFAULT_IP = "10.10.100.254"    # IP of the module by default    
    DEFAULT_UDP_PORT = 8899         # UDP port by default
    DEFAULT_FREQUENCY = 30000       # PWM frequency for the LED channels
    DEFAULT_MESSAGE_DELAY = 0.005   # Minimum time between messages
    DEFAULT_LAST_REQUEST = "None"   # Tracks the UDP requests
    
    # Module identification
    DEVICE_CATEGORY = "LED UDP"     # Category of the current Module. eg. strip
    id_Counter = 0                  # Module counter

    # REPORT method:
    # This method helps printing and coloring messages based on the current 
    # verbosity level. This is very useful while debugging.  
    #    Verbosity Levels:
    #    Verbosity 0: No report at all
    #    Verbosity 1: Critical errors and initialization operations
    #    Verbosity 2: Non critical errors
    #    Verbosity 3: Important regular operations
    #    Verbosity 4: All operations
    def report (self, _text, _level, _color = ''):
        _autoColor = [ColorReport.ENDC, ColorReport.RED, ColorReport.ORANGE,     
                      ColorReport.BLUE, ColorReport.GREEN, ColorReport.ENDC]    
        
        _composedMsg = (str(datetime.now()) + " " 
                        + self.name + " " 
                        + str(_text) 
                        + ColorReport.ENDC)
        
        # Check if this message is important enough
        if (self.verbosity != 0) and (_level <= self.verbosity):
            # check what color should it be printed in
            if (_color == ''):  #Color by default
                msg = _autoColor[_level] + _composedMsg
                
            else:               # Specified color 
                msg = _Color + _composedMsg 
            
            # print the message   
            print(msg)
    

    def __init__(self, _ip = DEFAULT_IP, 
                 _port = DEFAULT_UDP_PORT, 
                 _name = DEVICE_CATEGORY + " " + str(id_Counter), 
                 _verbosity = DEFAULT_VERBOSITY):
        
        self.ip = _ip           # IP of the current module
        self.port = _port       # UDP port of the current module 
        self.name = _name       # Given name of the current module
        self.verbosity = _verbosity     # How verbose will its reporting be
        self.lastRequest = self.DEFAULT_LAST_REQUEST    # Keeps last request 
        self.currentRed = 0     # Current Red PWM duty
        self.currentGreen = 0   # Current Green PWM duty
        self.currentBlue = 0    # Current Blue PWM duty
        self.autoUpdate = 10    # Polling delay of the current status in sec.
        self.redPin = self.DEFAULT_RED_PIN      # Actual Red Pin of the module
        self.greenPin = self.DEFAULT_GREEN_PIN  # Actual Green Pin of the module
        self.bluePin = self.DEFAULT_BLUE_PIN    # Actual Blue Pin of the module
        
        # Create the UDP socket
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Create the UDP listener thread
        self.thread_UDPListener = Thread(target = self.__UDP_listener)
        self.thread_UDPListener.daemon = True
        self.thread_UDPListener.start()

        # Thread to make regular updates on the LED
        self.thread_StatusPolling = Thread(target = self.__status_polling)
        self.thread_StatusPolling.daemon = True
        self.thread_StatusPolling.start()
        
        # Report the new module born
        self.report((ColorReport.GREEN + " + NEW " + self.DEVICE_CATEGORY + ": " 
                     + self.name + " @ " + self.ip + ":" + str(self.port) 
                     + " has been created" + ColorReport.ENDC), 1)

    # STATUS POLLING method:
    # This private method runs on an infinite loop with a forced delay of autoUpdate 
    # seconds after which it will poll the module and update its current values
    def __status_polling(self):
        while True:
            self.get_current_RGB()
            self.report("LED Updated automatically", 4)
            sleep(self.autoUpdate)
    
    # GET CURRENT RGB method:
    # requests the status of each RGB line in bulk and reports in case 
    # of any mismatch
    def get_current_RGB(self):
        _previousR = self.currentRed
        _previousG = self.currentGreen
        _previousB = self.currentBlue

        self.get_pin_PWM(self.redPin)
        self.get_pin_PWM(self.greenPin)
        self.get_pin_PWM(self.bluePin)

        if (_previousR != self.currentRed):
            self.report(("LED RED color mismatch: " + str(_previousR) + " -> " + str(self.currentRed)), 3)
        if (_previousG != self.currentGreen):
            self.report(("LED GREEN color mismatch: " + str(_previousG) + " -> " + str(self.currentGreen)), 3)
        if (_previousB != self.currentBlue):
            self.report(("LED BLUE color mismatch: " + str(_previousB) + " -> " + str(self.currentBlue)), 3)

    # UDP LISTENER method:
    # This private method runs on an infinite loop and simply listens for 
    # upcoming messages on the specified UDP port. It also updates internal 
    # variables based on the kind of message that has been received
    def __UDP_listener(self):
        while True:
            try:
                # Gets the new Message
                _response = self.Socket.recv(40)
                self.report(("Response: " + _response), 4)
    
                # Split the response so we can differentiate between Frequency 
                # and Duty. Responses are always as follows:
                # frequency duty 
                # for example: 30000 50 indicates a 50% duty over a 30KHz frequency
     
                _responseFrequency = int(_response.split(" ")[0])
                _responsePWM = int(_response.split(" ")[1])
                
                # Classifies the received message based on previous request
                # Requests are always like the following:
                # "PWM x GET" where x is the Pin number for each color
                # Splitting the request and looking at [1] (x), gives the previously
                # requested color  
                _lastRequestedPin = self.lastRequest.split(" ")[1]
                            
                if _lastRequestedPin == self.DEFAULT_RED_PIN:
                    self.currentRed = _responsePWM
                    self.report(("Current Red " + str(self.currentRed)), 4)
                
                if _lastRequestedPin == self.DEFAULT_GREEN_PIN:
                    self.currentGreen = _responsePWM
                    self.report(("Current Green " + str(self.currentGreen)), 4)
                
                if _lastRequestedPin == self.DEFAULT_BLUE_PIN:
                    self.currentBlue = _responsePWM
                    self.report(("Current Blue " + str(self.currentBlue)), 4)
                   
                else:
                    self.report(("Requested pin not recognized: " + self.lastRequest), 3)
                
                # Sets the request to the default one
                self.lastRequest = self.DEFAULT_LAST_REQUEST
            except:
                continue
    

    # GET COLOR LINE method:
    # This method requests the status of a single pin
    def get_pin_PWM(self, _pin):
        # sets a a timout in order to give time for the module to respond 
        _responseTimeOut = 20

        while ((self.lastRequest != self.DEFAULT_LAST_REQUEST) and (_responseTimeOut > 0)):
            _responseTimeOut = _responseTimeOut - 1
            sleep(0.01)

        # Build the request message to be sent to the module. 
        _getMessage = "PWM " + _pin + " GET"
        self.Socket.sendto(_getMessage, (self.ip, self.port))
        self.lastRequest = _getMessage


    # SET PIN PWM method:
    # This method builds and sends the message to update a specific PWM pin
    def set_pin_pwm(self, _pin, _duty = 0, _frequency = DEFAULT_FREQUENCY):
        # Build the message and send it
        _setPinMessage = "PWM " + _pin +" "+ str(_frequency) + " " + str(_duty)
        self.Socket.sendto(_setPinMessage, (self.ip, self.port))
        self.lastRequest = _setPinMessage
        
        # Offline update of the current pin PWM
        if _pin == self.redPin:
            self.currentRed = _duty
            
        elif _pin == self.greenPin:
            self.currentGreen = _duty
            
        if _pin == self.bluePin:
            self.currentBlue = _duty

        self.report(_setPinMessage, 4)

    # SET color pin methods:
    # These methods set the PWM on the color pin specified without having to 
    # write the Pin number
    def set_red(self, _duty = 0, _frequency = DEFAULT_FREQUENCY):
        self.set_pin_pwm(self.redPin, _duty, _frequency)

    def set_green(self, _duty = 0, _frequency = DEFAULT_FREQUENCY):
        self.set_pin_pwm(self.greenPin, _duty, _frequency)

    def set_blue(self, _duty = 0, _frequency = DEFAULT_FREQUENCY):
        self.set_pin_pwm(self.bluePin, _duty, _frequency)
    
    def set_black(self, _frequency = DEFAULT_FREQUENCY):
        self.set_RGB(0, 0, 0, _frequency)
        
    # SET RGB method:
    # This method sets the appropriate PWM on each pin in bulk 
    def set_RGB(self, _R=0, _G=0, _B=0, _frequency = DEFAULT_FREQUENCY):
        self.set_red(_R)
        self.set_green(_G)
        self.set_blue(_B)


class ColorReport:
    """ CLASS ColorReport:
    This class helps translating console color codes into readable constants
    """
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'