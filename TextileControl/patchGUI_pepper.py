from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

#import matplotlib
#matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')

from matplotlib import pyplot as plt
import numpy as np
import threading

from patchReader import PatchReader
from naoqi import ALProxy, ALModule, ALBroker
import time
import patchConstants as pc

broker = ALBroker("pythonBroker","0.0.0.0",0,pc.ROBOTIP,pc.ROBOTPORT)

class Pepper(object):
    """docstring for Pepper"""
    def __init__(self):
        self.memory = ALProxy('ALMemory')
        self.speech = ALProxy('ALTextToSpeech')
        self.speechRecog = ALProxy('ALSpeechRecognition')
        self.posture = ALProxy('ALRobotPosture')
        self.motion = ALProxy('ALMotion')
        #movement = ALProxy('ALAutonomousMovement',pc.ROBOTIP,pc.ROBOTPORT)
        self.life = ALProxy('ALAutonomousLife')

    def say(self,text):
        thread = threading.Thread(target=lambda: self.speech.say(text))
        thread.start()

    def setVocabulary(self,words,enabled):
        self.speechRecog.pause(True)
        self.speechRecog.setVocabulary(words,enabled)
        self.speechRecog.pause(False)

    def subscribe(self,event,obj,method):
        self.memory.subscribeToEvent(event,obj,method)

pepper = Pepper() # Single static instance

class FingerGame(ALModule):
    """Bulleri Bulleri Bock"""
    #def __init__(self,*args):
        #self.waitingForTouch = True


    def callback(self, dt):
        if not self.waitingForTouch: return
        fingerCount = MainWindow.result
        if fingerCount:
            self.waitingForTouch = False
            pepper.say('Oh! I think I felt %d fingers!'%fingerCount)
            pepper.posture.goToPosture('Stand',0.5)
            pepper.say('Am I right?')

    def onWordRecognized(self, key, value):
        print key,  value
fingerGame = FingerGame('fingerGame')
pepper.setVocabulary(['Yes','No'],True)
pepper.speechRecog.subscribe('my_subsriber')
print pepper.subscribe("WordRecognized", 'fingerGame', "onWordRecognized")

class OptionScreen(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)
        box = TaskBox()
        self.add_widget(box)


class TaskBox(GridLayout):
    #display = ObjectProperty()

    def readerCallback(self, dt):
        MainWindow.reader.start()


    def readerCallback2(self, dt):
        MainWindow.result, MainWindow.img = MainWindow.reader.read()
        print('result in GUI', MainWindow.result)

        if hasattr(self,'img'):
            self.img.set_data(MainWindow.img)
        else:
            self.img = plt.imshow(MainWindow.img, cmap='gist_heat', vmin=0, vmax=255)
        #plt.draw()
        plt.pause(0.000001) 

    def pepperCallback(self, dt):
        if MainWindow.reader.taskType == 'fingerGame':
            pepper.say(pc.NUMBER_OF_FINGERS[MainWindow.result])
        elif MainWindow.reader.taskType == 'move':
            pepper.say(pc.MOVE_VOICE[MainWindow.result])
            move = pc.MOVE_MAP.get(MainWindow.result,(0,0))
            speed = 0.3
            pepper.motion.moveTo(move[0]*speed,0,move[1]*speed,1)
        elif MainWindow.reader.taskType == 'hug':
            pepper.say(pc.REACTION[MainWindow.result])
        #time.sleep(1)

    def pepperInAction(self, taskType):
        pepper.say(pc.TASKPRESENTATION[taskType])
        success = pepper.posture.goToPosture(pc.TASKPOSE[taskType],0.5)

        MainWindow.sm.current = 'plot'
        plt.ion()
        MainWindow.reader.taskType = taskType
        Clock.schedule_once(self.readerCallback)
        MainWindow.readerEvent = Clock.schedule_interval(self.readerCallback2, 1/25)

        if MainWindow.reader.taskType == 'fingerGame':
            MainWindow.pepperEvent = Clock.schedule_interval(fingerGame.callback, 1/10)
        elif MainWindow.reader.taskType == 'move':
            MainWindow.pepperEvent = Clock.schedule_interval(self.pepperCallback, 1/10)
        elif MainWindow.reader.taskType == 'hug':
            MainWindow.pepperEvent = Clock.schedule_interval(self.pepperCallback, 1/10)

    def hugPepper(self):
        self.pepperInAction('hug')


    def movePepper(self):
        self.pepperInAction('move')


    def fingerGame(self):
        self.pepperInAction('fingerGame')
        #Clock.schedule_interval(self.plotCallback, 1/10)


class PlotScreen(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)
        box = PlotBox()
        self.add_widget(box)


class PlotBox(GridLayout):
    def stopPlotting(self):  
        MainWindow.reader.stop()
        MainWindow.readerEvent.cancel()
        MainWindow.pepperEvent.cancel()
        plt.close('all')
        print('Stopped')
        MainWindow.sm.current = 'option'



class MainWindow(BoxLayout):
    sm = ScreenManager()
    reader = PatchReader()
    readerEvent = None
    pepperEvent = None
    #plotEvent = None

    result = 0
    img = np.zeros((20,20))

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        #MainWindow.life.setState('disabled')
        pepper.life.setAutonomousAbilityEnabled('BackgroundMovement',False)
        pepper.say('Hello everyone! I am the Pepper robot! I am very happy to be here and show off my skills!')
        pepper.posture.goToPosture('Stand',0.5)
        self.sm.add_widget(OptionScreen(name='option'))
        self.sm.add_widget(PlotScreen(name='plot'))

        self.add_widget(self.sm)

       


class MainApp(App):
    def build(self):
        self.title = 'Patch Reader'
        return MainWindow()


if __name__ == "__main__":
    app = MainApp()
    app.run()