
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
	1: (0,-1),	
	2: (0,-1),
	3: (0,-1),
	4: (1,0),
	5: (1,0),
	6: (-1,0),
	7: (0,1),
	8: (0,1),
	9: (0,1)
}

MOVE_VOICE = {
	1: 'Right',
	2: 'Right',
	3: 'Right',	
	4: 'Forward',
	5: 'Forward',
	6: 'Backing up',
	7: 'Left',
	8: 'Left',
	9: 'Left'
}

TASKTYPE = ['move', 'hug', 'fingerGame']
TASKPOSE = {
	'move': 'Stand',
	'hug': 'Stand',
	'fingerGame': 'Crouch'
}
TASKPRESENTATION = {
	'fingerGame': 'Bulleri Bulleri buck, please touch my back!'
}

REACTION = ['', '', 'Thanks', 'A bit too much']

NUMBER_OF_FINGERS = ['No finger', 'One finger', 'Two fingers', 'Three fingers', 'Four fingers', 'Five fingers']

class TextileControl(object):
	def __init__(self):
		self.speech = ALProxy('ALTextToSpeech',robotIP,robotPort)
		self.posture = ALProxy('ALRobotPosture',robotIP,robotPort)
		self.motion = ALProxy('ALMotion',robotIP,robotPort)
		self.reader = PatchReader()
		self.taskType = ''

	def start(self):
		self.reader.taskType = self.taskType
		self.reader.start()
		#self.speech.say(TASKPRESENTATION[self.taskType])
		success = self.posture.goToPosture(TASKPOSE[self.taskType],0.5)
		for i in range(1000):
			command = self.reader.read() 
			print command
			if self.taskType == 'move':
				if command:
					self.speech.say(MOVE_VOICE[command])
					move = MOVE_MAP.get(command,(0,0))
					speed = 0.3
					self.motion.moveTo(move[0]*speed,0,move[1]*speed,1)
			elif self.taskType == 'hug':
				if command:
					self.speech.say(REACTION[command])
			elif self.taskType == 'fingerGame':
				self.speech.say(NUMBER_OF_FINGERS[command])

			time.sleep(1)


	def respond(self):
		self.speech.say('Hello')


def main(): 
	control = TextileControl()
	control.taskType = TASKTYPE[2]
	control.start()

if __name__ == '__main__': 
	main()