import os
import json
import uuid
from ws4py.websocket import WebSocket

from session import Session

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MemberSocket(WebSocket):

	def __init__(self, *args, **kw):
		WebSocket.__init__(self, *args, **kw)
		self._session = None
		self._uid = str(uuid.uuid4())  # TODO: The user needs to be able to set this on the site
		logging.info("Websocket created. ID: %s" % self._uid)

	def get_uid(self):
		return str(self._uid)

	def closed(self, code, reason=None):
		command = "quit"
		payload = ""
		try:
			self.crunch_message(self._session.get_uid(), command, payload)
		except:
			pass

	# A valid message looks like this:
	# message = '[	{ "command":"join",		"payload":"",		"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" },
	# 				{ "command":"ready",	"payload":"true",	"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" } ]'
	def received_message(self, data):
		rec_message = str(data)
		logging.warning("Received Message: %s." % rec_message)

		try:
			messages = json.loads(rec_message)
#			validate(messages, MemberSocket.messages_schema)
		except:
			logging.warning("Dropped Messages: %s. Messages don't comply with form or are not valid json " % rec_message)
			return

		for message in messages:
			session_id = message['regarding']
			command    = message['command']
			payload    = message['payload']

			self.crunch_message(session_id, command, payload)

	def crunch_message(self, session_id, command, payload):
		logging.warning("(Membersocket:) Crunching: regarding=%s, command=%s, payload=%s" % (session_id, command, payload))

		# If memberSocket has no session yet: Add it on first message.
		if self._session is None:
			for session in Session.all_sessions:
				if session.get_sid() == session_id:
					logging.warning("Member %s associating with session: %s" % (self.get_uid(), session_id))
					self._session = session
					self._session.crunch_message(command, payload, self)
					return
			# There is no session with that id so far. Let's create one.
			logging.warning("Creating new session: %s" % session_id)
			self._session = Session(session_id)

		# Ship message to session.
		self._session.crunch_message(command, payload, self)
# }}}