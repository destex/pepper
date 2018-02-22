"""
* Commit to svn
* Look for Aaaa sound (Jiong)
* Response from pepper (Buleri Bock)
"""

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

from patchReader import PatchReader
from naoqi import ALProxy
import time
import patchConstants as pc


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

        # if MainWindow.reader.taskType == 'fingerGame':
        #     MainWindow.speech.say(pc.NUMBER_OF_FINGERS[MainWindow.result])
        # elif MainWindow.reader.taskType == 'move':
        #     MainWindow.speech.say(pc.MOVE_VOICE[MainWindow.result])
        #     move = pc.MOVE_MAP.get(MainWindow.result,(0,0))
        #     speed = 0.3
        #     MainWindow.motion.moveTo(move[0]*speed,0,move[1]*speed,1)
        # elif MainWindow.reader.taskType == 'hug':
        #     MainWindow.speech.say(pc.REACTION[MainWindow.result])
        if hasattr(self,'img'):
            self.img.set_data(MainWindow.img)
        else:
            self.img = plt.imshow(MainWindow.img, cmap='gist_heat', vmin=0, vmax=255)
        #plt.draw()
        plt.pause(0.000001) 

    def pepperCallback(self, dt):
        if MainWindow.reader.taskType == 'fingerGame':
            MainWindow.speech.say(pc.NUMBER_OF_FINGERS[MainWindow.result])
        elif MainWindow.reader.taskType == 'move':
            MainWindow.speech.say(pc.MOVE_VOICE[MainWindow.result])
            move = pc.MOVE_MAP.get(MainWindow.result,(0,0))
            speed = 0.3
            MainWindow.motion.moveTo(move[0]*speed,0,move[1]*speed,1)
        elif MainWindow.reader.taskType == 'hug':
            MainWindow.speech.say(pc.REACTION[MainWindow.result])
        #time.sleep(1)

    def pepperInAction(self, taskType):
        MainWindow.speech.say(pc.TASKPRESENTATION[taskType])
        success = MainWindow.posture.goToPosture(pc.TASKPOSE[taskType],0.5)

        MainWindow.sm.current = 'plot'
        plt.ion()
        MainWindow.reader.taskType = taskType
        Clock.schedule_once(self.readerCallback)
        MainWindow.readerEvent = Clock.schedule_interval(self.readerCallback2, 1/25)
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

    speech = ALProxy('ALTextToSpeech',pc.ROBOTIP,pc.ROBOTPORT)
    posture = ALProxy('ALRobotPosture',pc.ROBOTIP,pc.ROBOTPORT)
    motion = ALProxy('ALMotion',pc.ROBOTIP,pc.ROBOTPORT)

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        MainWindow.posture.goToPosture('Stand',0.5)
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