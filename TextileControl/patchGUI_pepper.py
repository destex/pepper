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
import sys

from patchReader import PatchReader
import time
import patchConstants as pc

sys.path.insert(0,'C:\\pynaoqi-python2.7-2.5.5.5-win32-vs2013\\lib')
from naoqi import *

broker = ALBroker("pythonBroker","0.0.0.0",0,pc.ROBOTIP,pc.ROBOTPORT)

class Pepper(object):
    """docstring for Pepper"""
    def __init__(self):
        self.memory = ALProxy('ALMemory')
        self.speech = ALProxy('ALTextToSpeech')
        self.speechRecog = ALProxy('ALSpeechRecognition')
        self.posture = ALProxy('ALRobotPosture')
        self.anim = ALProxy('ALAnimationPlayer')
        self.motion = ALProxy('ALMotion')
        #movement = ALProxy('ALAutonomousMovement',pc.ROBOTIP,pc.ROBOTPORT)
        self.life = ALProxy('ALAutonomousLife')
        self.tracker = ALProxy("ALTracker")

        self.tracker.registerTarget('People', [])

        self.setVocabulary(['Yes','No'])
        self.speechRecog.subscribe('TextileControl')
        self.listening = False
        #self.speechRecog.pause(True)

    def say(self,text,pauseSpeechRecog=True):
        if not text: return 
        if pauseSpeechRecog: self.speechRecog.pause(True)
        def run():
            self.speech.say(text)
            if pauseSpeechRecog: self.speechRecog.pause(False)
        thread = threading.Thread(target=run)
        thread.start()

    def setVocabulary(self,words):
        self.speechRecog.pause(True)
        self.speechRecog.setVocabulary(words,False)
        self.speechRecog.pause(False)

    def listen(self,callback,threshold=0):
        self.listening = True
        value, t0, tm0 = self.memory.getTimestamp('WordRecognized')
        def run():
            while self.listening:
                value, ts, tms = self.memory.getTimestamp('WordRecognized')
                if value[1] >= threshold and ts != t0: break
                time.sleep(0.1)
            self.listening = False
            callback(*value)
        thread = threading.Thread(target=run)
        thread.start()

    def stopListening(self):
        self.listening = False

    def runAnimation(self, animation): 
        #self.life.setAutonomousAbilityEnabled('SpeakingMovement',False)
        self.anim.run(animation)

    def close(self):
        self.stopListening()
        self.speechRecog.unsubscribe('TextileControl')
        self.tracker.stopTracker()

pepper = Pepper() # Single static instance

class FingerGame(object):
    """Bulleri Bulleri Bock"""
    def __init__(self,*args):
        self.waitingForTouch = False

    def prepare(self):
        pepper.say('Bulleri Bulleri buck, please touch my back!')
        print 'prepare'
        success = pepper.posture.goToPosture('Crouch',0.5)
        self.waitingForTouch = True
        self.fingerCounts = []

    def callback(self, dt=0):
        if not self.waitingForTouch: return
        fingerCount = MainWindow.result
        if self.waitingForTouch and fingerCount and isinstance(fingerCount,int):
            self.waitingForTouch = False
            pepper.say('Oh! I think I felt %d finger%s!'%(fingerCount,fingerCount>1 and 's' or ''))
            pepper.posture.goToPosture('Stand',0.5)
            pepper.say('Am I right?',pauseSpeechRecog=False)
            pepper.listen(self.onGameComplete,0.5)

    def onGameComplete(self, word, probability):
        print word, probability
        if word == 'Yes':
            pepper.runAnimation('animations/Stand/Emotions/Positive/Winner_%d'%(probability > 0.55 and 1 or 2))
        else:
            pepper.runAnimation('animations/Stand/Emotions/Negative/Frustrated_1')
        time.sleep(4)
        pepper.say('Can we play again?',pauseSpeechRecog=False)
        pepper.listen(self.onPlayAgain,0.5)
        
    def onPlayAgain(self, word, probability):
        if word == 'Yes':
            self.prepare()
        else:
            self.stop()

    def stop(self):
        pepper.say('Another time maybe')
        pepper.runAnimation('animations/Stand/Gestures/Desperate_1')

fingerGame = FingerGame('fingerGame')

class FreeHug(object):
    def prepare(self,speak=True):
        if speak: pepper.say(pc.TASKPRESENTATION['hug'])
        success = pepper.posture.goToPosture(pc.TASKPOSE['hug'],0.5)
        pepper.anim.run('animations/Stand/Gestures/Please_1')
        self.waitingForTouch = True

    def callback(self,dt=0):
        if self.waitingForTouch and MainWindow.result > 1:
            print 'Hug', MainWindow.result
            self.waitingForTouch = False
            pepper.say(pc.REACTION[MainWindow.result])
            self.prepare(False)


freeHug = FreeHug()


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
        #print('result in GUI', MainWindow.result)

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
            #pepper.say(pc.MOVE_VOICE[MainWindow.result])
            #move = pc.MOVE_MAP.get(MainWindow.result,(0,0))
            if isinstance(MainWindow.result,tuple):
                tx,ty = MainWindow.result
                print MainWindow.result
                speed = 0.3
                #if MainWindow.result: 
                pepper.motion.move(-tx/30.0,0,ty/30.0)
                #else:
                #    pepper.motion.stopMove()
                
        elif MainWindow.reader.taskType == 'hug':
            pepper.say(pc.REACTION[MainWindow.result])
            pepper.anim.run('animations/Stand/Gestures/Please_1')
        #time.sleep(1)

    def pepperInAction(self, taskType):
        print 'Pepper in action', taskType
        MainWindow.sm.current = 'plot'
        plt.ion()
        MainWindow.reader.taskType = taskType
        Clock.schedule_once(self.readerCallback)
        MainWindow.readerEvent = Clock.schedule_interval(self.readerCallback2, 1/25.0)

        MainWindow.result = 0
        if MainWindow.reader.taskType == 'fingerGame':
            fingerGame.prepare()
            MainWindow.pepperEvent = Clock.schedule_interval(fingerGame.callback, 1)
        elif MainWindow.reader.taskType == 'move':
            #pepper.tracker.setMode('Face') 
            pepper.say(pc.TASKPRESENTATION[taskType])
            success = pepper.posture.goToPosture(pc.TASKPOSE[taskType],0.5)
            MainWindow.pepperEvent = Clock.schedule_interval(self.pepperCallback, 1)
        elif MainWindow.reader.taskType == 'hug':
            freeHug.prepare()
            MainWindow.pepperEvent = Clock.schedule_interval(freeHug.callback, 0.5)

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
        pepper.stopListening()
        MainWindow.reader.stop()
        MainWindow.readerEvent.cancel()
        MainWindow.pepperEvent.cancel()
        MainWindow.result = 0
        plt.close('all')
        print('Stopped')
        MainWindow.sm.current = 'option'
        pepper.posture.goToPosture('Stand',0.5)
        #pepper.tracker.setMode('F')
        #pepper.tracker.track('People')



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
        #pepper.life.setAutonomousAbilityEnabled('SpeakingMovement',False)
        #pepper.life.setAutonomousAbilityEnabled('ListeningMovement',False)
        #pepper.life.setAutonomousAbilityEnabled('BackgroundMovement',False)
        pepper.say('Hello everyone! I am the Pepper robot! I am very happy to be here and show off my skills!')
        self.sm.add_widget(OptionScreen(name='option'))
        self.sm.add_widget(PlotScreen(name='plot'))

        self.add_widget(self.sm)

        pepper.posture.goToPosture('Stand',0.5)
        pepper.tracker.setMode('Face')
        pepper.tracker.track('People')
        #pepper.tracker.stopTracker()
       


class MainApp(App):
    def build(self):
        self.title = 'Patch Reader'
        return MainWindow()

    def on_stop(self):
        pepper.close()
        print 'Application closed'

if __name__ == "__main__":
    app = MainApp()
    app.run()