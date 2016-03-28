import time
import json
import logging


def initMap():
	field = []
	for idY in range(7):
		field.append(list())
		for idX in range(7):
			field[-1].append(None)

	return(field)

class Session:
	all_sessions = []

	def __init__(self, sid):
		self._sid = sid
		self._members = []
		Session.all_sessions.append(self)

		self.map = initMap()
		self.active_player = None
		self.winner = None
		self.game_over = False
		
		logging.info("Session created. ID: %s" % self._sid)


	def get_sid(self):
		return str(self._sid)

	def crunch_message(self, command, payload, member):
		logging.warning("(Session:) Crunching: regarding=%s, command=%s, payload=%s" % (member.get_uid(), command, payload))

		message_mapper = {
			'join'			: self.received_join,
			'quit'			: self.received_quit,
			'click'			: self.received_click
		}

		if command not in message_mapper:
			logging.warning("Dropped Message. %s is not a valid command.", command)
			return

		message_mapper[command](payload, member)

	def received_join(self, payload, member):
		""""Adds new members to session, tells everybody about it."""

		if member in self._members:
			logging.warning("Dropped Join. %s already joined.", member.get_uid())
			return

		if len(self._members) == 2:
			logging.warning("Dropped Join. Two players are active already.")
			return

		logging.info("Member %s joining session %s" % (member.get_uid(), self.get_sid()))
		self._members.append(member)

		# send all old members to new member
		self.send_old_members(member)

		# forward join
		messages = [self.build_message(member.get_uid(), "join", "")]
		messages = json.dumps(messages)
		self.broadcast(messages)

		# Start game
		if len(self._members) == 2:
			self.active_player = self._members[0]

			# Send map 
			messages = [(self.build_message(member.get_uid(), "map", self.map))]
			messages = json.dumps(messages)
			self.broadcast(messages)


#		if self.winner:


#		if self.game_over:


	def send_old_members(self, new_member):
		""""Sends join for all session members to the new_member."""

		messages = []

		for member in self._members:
			if member is not new_member:
				messages.append(self.build_message(member.get_uid(), "join", ""))

		messages = json.dumps(messages)
		new_member.send(messages)

	def received_quit(self, payload, member):
		if member not in self._members:
			logging.warning("Dropped Quit. Sender isn't a member of this session.")
			return

		# drop member from session
		member.close(1000, 'You quit.')  # TODO: This is probably leaking memory => release member itself too?
#		self._members.remove(member)

		# forward quit
		messages = [(self.build_message(member.get_uid(), "quit", ""))]
		messages = json.dumps(messages)
		self.broadcast(messages)

	def received_click(self, payload, member):

		xClick, yClick = payload.split('_')
		xClick, yClick = int(xClick), int(yClick)
		freeInRow = self.first_free_row(xClick)

		if member not in self._members:
			logging.warning("Dropped Click. Sender isn't a member of this session.")
			return

		if self.active_player != member:
			logging.warning("Dropped Click. It's not members turn.")
			return

		if freeInRow == None:
			logging.warning("Dropped Click. No field free in Row.")
			return
		else:		
			self.map[freeInRow][xClick] = member.get_uid()

		messages = [(self.build_message(member.get_uid(), "map", self.map))]
		messages = json.dumps(messages)
		self.broadcast(messages)

		if   self.checkWinner(member, xClick, freeInRow) != False:
			self.winner = self.active_player
			self.active_player = None
			self.game_over = True

			messages = [(self.build_message(member.get_uid(), "won", self.checkWinner(member, xClick, freeInRow)))]
			messages = json.dumps(messages)
			self.broadcast(messages)

		elif self.checkDraw():
			self.active_player = None
			self.game_over = True

			messages = [(self.build_message(member.get_uid(), "draw", ""))]
			messages = json.dumps(messages)
			self.broadcast(messages)

		else:
			if self.active_player == self._members[0]: self.active_player = self._members[1]
			else: self.active_player = self._members[0]

			messages = [(self.build_message(self.active_player.get_uid(), "turn", ""))]
			messages = json.dumps(messages)
			self.broadcast(messages)


	def first_free_row(self, xClick):
		for idY in range(len(self.map) - 1,-1,-1):		
			if self.map[idY][xClick] == None:				
				return idY
		
		return None

	def checkDraw(self):
		for row in self.map:
			for elem in row:
				if elem != None:
					return False
		return True

	def checkWinner(self, member, newX, newY):

		def checkHorizontal():
			for offsetX in range(-3, 1):
				try:
					if(	self.map[newY][newX + offsetX + 0] == member.get_uid()
					and self.map[newY][newX + offsetX + 1] == member.get_uid()
					and self.map[newY][newX + offsetX + 2] == member.get_uid()
					and self.map[newY][newX + offsetX + 3] == member.get_uid()):
						return [(newX + offsetX + 0, newY), 
								(newX + offsetX + 1, newY), 
								(newX + offsetX + 2, newY), 
								(newX + offsetX + 3, newY)]

				except Exception as e:
					pass

			return False

		def checkVertical():
			for offsetY in range(-3, 1):
				try:
					if(	self.map[newY + offsetY + 0][newX] == member.get_uid()
					and self.map[newY + offsetY + 1][newX] == member.get_uid()
					and self.map[newY + offsetY + 2][newX] == member.get_uid()
					and self.map[newY + offsetY + 3][newX] == member.get_uid()):
						return [(newX, newY + offsetY + 0), 
								(newX, newY + offsetY + 1), 
								(newX, newY + offsetY + 2), 
								(newX, newY + offsetY + 3)]

				except Exception as e:
					pass

			return False

		def checkBackslash():
			for offsetXY in range(-3, 1):
				try:
					if(	self.map[newY + offsetXY + 0][newX + offsetXY + 0] == member.get_uid()
					and self.map[newY + offsetXY + 1][newX + offsetXY + 1] == member.get_uid()
					and self.map[newY + offsetXY + 2][newX + offsetXY + 2] == member.get_uid()
					and self.map[newY + offsetXY + 3][newX + offsetXY + 3] == member.get_uid()):
						return [(newX + offsetXY + 0, newY + offsetXY + 0), 
								(newX + offsetXY + 1, newY + offsetXY + 1), 
								(newX + offsetXY + 2, newY + offsetXY + 2),
								(newX + offsetXY + 3, newY + offsetXY + 3)]

				except Exception as e:
					pass

			return False

		def checkSlash():
			for offsetXY in range(-3, 1):
				try:
					if(	self.map[newY - offsetXY - 0][newX + offsetXY + 0] == member.get_uid()
					and self.map[newY - offsetXY - 1][newX + offsetXY + 1] == member.get_uid()
					and self.map[newY - offsetXY - 2][newX + offsetXY + 2] == member.get_uid()
					and self.map[newY - offsetXY - 3][newX + offsetXY + 3] == member.get_uid()):
						return [(newX + offsetXY + 0, newY - offsetXY - 0),
								(newX + offsetXY + 1, newY - offsetXY - 1),
								(newX + offsetXY + 2, newY - offsetXY - 2),
								(newX + offsetXY + 3, newY - offsetXY - 3)]

				except Exception as e:
					pass

			return False

		if   checkHorizontal(): return checkHorizontal()
		elif checkVertical()  : return checkVertical()
		elif checkSlash()     : return checkSlash()
		elif checkBackslash() : return checkBackslash()						

		return False

	@staticmethod
	def build_message(uid, command, payload):
		# A valid message looks like this:
		# message = '[	{ "command":"join",		"payload":"",		"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" },
		# 				{ "command":"ready",	"payload":"true",	"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" } ]'
		message = {
			"command": command,
			"payload": payload,
			"regarding": uid
		}
		return message

	def broadcast(self, message):
		for member in self._members:
			try:
				logging.warning("Broadcasting Message %s to %s.", message, member.get_uid())
				member.send(message)
			except:
				logging.warning("Broadcasting Message %s to %s failed.", message, member.get_uid())
				pass  # TODO: remove member, send quit to others
