import serial
import numpy as np
import sys, time
import cv2
import threading
import operator
from collections import deque, Counter

import patchConstants as pc

port = pc.PATCHCOMPORT
baudrate = 921600


nodeNo = 400

block_x_axis = [0,0,0,0,0,0,0,1,1,1,1,1,1,2,2,2,2,2,2,2]
block_y_axis = [0,0,0,0,0,0,0,1,1,1,1,1,1,2,2,2,2,2,2,2]

HUG_THRESHOLD_HIGH = 20000
HUG_THRESHOLD_MED = 10000
HUG_THRESHOLD_LOW = 3000


def preprocessingData(packets):
	currFrame = packets[-1]
	if len(packets) >= 2:   
		preFrame = packets[-2]

	# Not applied. done in recog()
	# remove noise
	# calculate feature points
	# reshape 400 to 20x20

	return newPacket

def calculateDiff(currIndex, preIndex, packets):
	try:
		# np.subtract(np.array(t5[-1]), np.array(t5[-2]))
		packetDiff = list(map(operator.sub, packets[currIndex], packets[preIndex]))  # in python 2, no list()
	except IndexError:
		print('Index out of range in calculateDiff.')

	return packetDiff


def calculateTotalMag(index, packets):
	# sum up all nodes
	try:
		totalMag = sum(packets[index])
	except:
		print('Index out of range in calculateDiff.')
	return totalMag

def movePepper(packets):
	# the sensor is divided into 9 parts, labeled with int 1-9 (direction)

	threshold = 5

	# calculate diff
	packetDiff = calculateDiff(-1, -2, packets)
	img = packet2img(packetDiff)
	index = [i for i, x in enumerate(packetDiff) if x>=threshold]
	t_direction = []
	if len(index) > 0:
		for ind in index:
			ix = int(ind/20)
			iy = ind - int(ind/20)*20
			t_direction.append(block_x_axis[ix] + block_y_axis[iy]*3)

		cnt = Counter()
		for  area in t_direction:
			cnt[area] += 1
		direction = cnt.most_common(1)[0][0]
	else:
		direction = -1

	return direction+1, img


def hugPepper(packets):
	# the reaction is an integer describing the intensity, an int: 1,2,3
	img = packet2img(packets[-1])

	totalMag = calculateTotalMag(-1, packets)

	#print('Total Mag =', totalMag)

	if totalMag > HUG_THRESHOLD_HIGH:
		reaction = 3
	elif HUG_THRESHOLD_MED <= totalMag <= HUG_THRESHOLD_HIGH:
		reaction = 2
	else:
		reaction = 1

	#print('reaction =', reaction)

	return reaction, img


def recog(packets):
	# use blob detection
	currFrame = np.array(packets[-1])
	#currFrame = np.multiply(currFrame, 255.0, out=currFrame, casting='unsafe') / currFrame.max()
	currFrame = np.float_(currFrame)
	currFrame *= 255.0 / currFrame.max()

	img = currFrame.reshape(20,20).astype('uint8')

	#img = cv2.medianBlur(img, 3)
	#img = cv2.blur(img,(5,5))

	#kernel = np.ones((3,3),np.float32)/9
	#img = cv2.filter2D(img,-1,kernel)

	img = cv2.GaussianBlur(img,(3,3),0)
	#img = cv2.bilateralFilter(img,5,75,75)

	#print img

	# Setup BlobDetector
	params = cv2.SimpleBlobDetector_Params()
	
	params.filterByColor = True
	params.blobColor = 255

	params.minThreshold = 5
	params.maxThreshold = 250

	# # Filter by Area.
	params.filterByArea = False
	#params.minArea = 1
	#params.maxArea = 20
		 
	# # Filter by Circularity
	params.filterByCircularity = False
	#params.minCircularity = 0.5
	 
	# # Filter by Convexity
	params.filterByConvexity = False
	#params.minConvexity = 0.87
		 
	# # Filter by Inertia
	params.filterByInertia = False
	#params.minInertiaRatio = 0.5

	# # Distance Between Blobs
	params.minDistBetweenBlobs = 1
		 
	# Create a detector with the parameters
	ver = (cv2.__version__).split('.')
	if int(ver[0]) < 3 :
		detector = cv2.SimpleBlobDetector(params)
	else : 
		detector = cv2.SimpleBlobDetector_create(params)

	keypoints = detector.detect(img)

	#print('keypoints =', keypoints)
	#print 'length = %d' % len(keypoints)
	#for kp in keypoints:
	#	print "(%d, %d) size=%.1f resp=%.1f" % (kp.pt[0], kp.pt[1], kp.size, kp.response)

	if len(keypoints) >5:
		return 0, img

	return len(keypoints), img

def packet2img(packet):
	currFrame = np.array(packet)
	currFrame.clip(0)
	currFrame = np.float_(currFrame)
	currFrame *= 255.0 / currFrame.max()

	return currFrame.reshape(20,20).astype('uint8')

def recog2(packets):
	# use finger tip contours
	# currFrame = np.array(packets[-1])
	# currFrame = np.float_(currFrame)
	# currFrame *= 255.0 / currFrame.max()
	# img = currFrame.reshape(20,20).astype('uint8')

	img = packet2img(packets[-1])

	#img = cv2.medianBlur(img, 3)
	#img = cv2.blur(img,(5,5))

	#kernel = np.ones((3,3),np.float32)/9
	#img = cv2.filter2D(img,-1,kernel)

	img = cv2.GaussianBlur(img,(3,3),0)
	#img = cv2.bilateralFilter(img,5,75,75)

	#print(img)

	flag, thresh = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)
	#contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	_, contours, _= cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	#print('length =', len(contours))

	# remove initial errors
	if len(contours) >5:
		return 0, img

	return len(contours), img


class PatchReader(object):
	def __init__(self):
		self.thread = None
		self.header = 'ff000000'

		self.useBlankImage = True # Calculate a cancelation image at the start
		self.packetMaxLen = 10
		self.resultMaxLen = 10
		self.dataLen = 604  # one frame size in a byte array
		self.bytesPerHex = 3

		self.foundHeader = False
		self.tempPacket = ''
		self.packets = deque([], self.packetMaxLen)
		self.bufResults = deque([], self.resultMaxLen)
		self.cnt = Counter()
		#self.avgDirectionResult = 0
		self.result = 0
		self.taskType = ''
		self.img = np.zeros((20,20))
		
		try:
			self.con = serial.Serial(port, baudrate)
		except Exception:
			#print e
			print('------Error: can not connect to device------')  
		if self.useBlankImage: self.blankImage()

	def blankImage(self):
		while len(self.packets) < self.packetMaxLen:
			self.readSynchronized()
		self.blank = [0 for v in self.packets[0]]
		for p in self.packets:
			for i in range(len(self.blank)):
				self.blank[i] += p[i]

		for i in range(len(self.blank)): 
			self.blank[i] = self.blank[i] / self.packetMaxLen
		print(self.blank)

	def calMostCommonResult(self, instantResult):
		result = 0
		self.bufResults.append(instantResult)

		if len(self.bufResults) == self.resultMaxLen: 
			self.cnt.clear()
			for ins in self.bufResults:
				self.cnt[ins] += 1
				if self.cnt.most_common(1)[0][1] >= 5:
					result = self.cnt.most_common(1)[0][0]
		return result

	def read(self):
		if self.thread:
			return self.result, self.img
		else:
			return self.readSynchronized()

	def readSynchronized(self):
		if not self.con.is_open:
			try:
				self.con = serial.Serial(port, baudrate)
			except Exception:
				print('------Error: can not connect to device------')  

		data = self.con.read(self.dataLen).encode('hex') #.hex() for Python3
		
		if not self.foundHeader:
			#look for header ff000000
			self.tempPacket = ''
			# print('trying to look for header...................', data)

			if self.header in data:
				index_firstbyte = data.index(self.header)
				self.tempPacket += data[(index_firstbyte+8):]

				self.foundHeader = True
		elif self.header in data:
			#print('FOUND---------------')
			index_lastbyte = data.index(self.header)
			#print('look for header in data----------------------------', data)
			#print('index is ', index_lastbyte)
			#print(data[0:index_lastbyte])
			self.tempPacket += data[0:index_lastbyte]
			#print('------------tempPacket----------', self.tempPacket)

			if len(self.tempPacket) == 1200:
				#print('Im here!!!!!')
				splitTempPacket = [self.tempPacket[i:i+self.bytesPerHex] for i in range(0, len(self.tempPacket), self.bytesPerHex)]
				#print('split data', splitTempPacket)
				self.packets.append([int(x, 16) for x in splitTempPacket])
				self.tempPacket = data[(index_lastbyte+8):]
				
				if self.taskType == 'move':
					# move pepper
					if len(self.packets) >= 2:
						direction, self.img = movePepper(self.packets)
						self.result = self.calMostCommonResult(direction)
				elif self.taskType == 'hug':
					# hug pepper
					reaction, self.img = hugPepper(self.blankedPackets(self.packets))
					self.result = self.calMostCommonResult(reaction)
				elif self.taskType == 'fingerGame':
					# the finger game
					fingerNo, self.img = recog2(self.blankedPackets(self.packets))
					self.result = self.calMostCommonResult(fingerNo)
			else:
				self.foundHeader = False

		return self.result, self.img

	def blankedPackets(self,packets):
		result = []
		for p in packets:
			result.append([max(x-y,0) for x,y in zip(p,self.blank)])
		return result

	def start(self):
		def run():
			while self.thread:
				self.readSynchronized()

		self.thread = threading.Thread(target=run)
		self.thread.start()

	def stop(self):
		self.thread = None
		if self.con.is_open:
			self.con.close()

def main():
	# receive arg from command line, port number
	
	reader = PatchReader()
	reader.taskType = 'fingerGame'
	reader.start()
	for i in range(10): 
		print('in main', reader.read()[0])
		time.sleep(1)
	reader.stop()
	


if __name__ == '__main__':
    main()