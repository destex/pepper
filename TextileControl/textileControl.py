
# NAO POSTURE EXAMPLE
#
# Using the ALRobotPosture to go to different postures
#
# Author: Erik Billing <erik.billing@his.se>


# The ALProxy is a core component of the NaoQI API
# See the Python docs for more info:
# http://doc.aldebaran.com/2-1/ref/python-api.html#naoqi-python-api
from naoqi import ALProxy
from patchReader import PatchReader
import time

# Make sure you have the right IP and port for the robot.
# Default settings should work for a Webots simulation. 
robotIP   = 'pepper.local'
robotPort = 9559

# Use ALProxy to connect to the robot and instanciate a module for the
# postures. There are no Python docs for this, use the C++ API: 
# http://doc.aldebaran.com/2-1/naoqi/motion/alrobotposture-api.html#ALRobotPostureProxy

MOVE_MAP = {
	2: (-1,0),
	4: (0,-1),
	6: (0,1),
	8: (1,0)
}

class TextileControl(object):
	def __init__(self):
		self.speech = ALProxy('ALTextToSpeech',robotIP,robotPort)
		self.posture = ALProxy('ALRobotPosture',robotIP,robotPort)
		self.motion = ALProxy('ALMotion',robotIP,robotPort)
		self.reader = PatchReader()

	def start(self):
		self.reader.start()
		success = self.posture.goToPosture('Stand',0.5)
		for i in range(1000):
			command = self.reader.read() 
			print command
			if command:
				self.speech.say('%d'%command)
				move = MOVE_MAP.get(command,(0,0))
				speed = 0.1
				self.motion.moveTo(move[0]*speed,0,move[1]*speed,1)
			time.sleep(1)

	def respond(self):
		self.speech.say('Hello')


def main(): 
	control = TextileControl()
	control.start()

if __name__ == '__main__': 
	main()