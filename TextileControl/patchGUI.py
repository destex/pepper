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


# from os import listdir
# kv_path = './kv/'
# for kv in listdir(kv_path):
#     Builder.load_file(kv_path+kv)

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
        plt.imshow(MainWindow.img, cmap='gist_heat')
        #plt.draw()
        plt.pause(0.000001) 


    # def plotCallback(self, dt):
    #     plt.imshow(MainWindow.img, cmap='gist_gray')
    #     #plt.draw()
    #     plt.pause(0.000001) 


    # def plotCallback2(self, dt):
    #     plt.show()

    def pepperInAction(self, taskType):
        MainWindow.sm.current = 'plot'
        plt.ion()
        MainWindow.reader.taskType = taskType
        Clock.schedule_once(self.readerCallback)
        MainWindow.readerEvent = Clock.schedule_interval(self.readerCallback2, 1/10)

    def hugPepper(self):
        #value = int(self.display.text)
        #self.display.text = str(value+1)
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
        plt.close('all')
        print('Stopped')
        MainWindow.sm.current = 'option'



class MainWindow(BoxLayout):
    sm = ScreenManager()
    reader = PatchReader()
    readerEvent = None
    plotEvent = None

    result = 0
    img = np.zeros((20,20))


    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

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