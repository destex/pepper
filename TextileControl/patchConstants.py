ROBOTIP   = 'pepper.local'

ROBOTPORT = 9559

PATCHCOMPORT = 'COM5'

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
	0: '',
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
	'hug': 'Free hug, free hug',
	'move': 'Please guide me to a place',
	'fingerGame': 'Bulleri Bulleri buck, please touch my back!'
}

REACTION = ['', '', 'Thanks', 'A bit too much']

NUMBER_OF_FINGERS = ['No finger', 'One finger', 'Two fingers', 'Three fingers', 'Four fingers', 'Five fingers']