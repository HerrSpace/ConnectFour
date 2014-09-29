import time
import os
import logging
import sys
import cherrypy

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('four', 'templates'))

class Four(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port

		self.four_template = env.get_template('four.html')
		self.control_channel_template = env.get_template('control_channel.js')

# Generate Page {{{
	def render(self, session):
		return self.four_template.render(sid=session)
# }}}

# AJAX {{{
	def control_channel(self, session):
		return self.control_channel_template.render(sid=session, host=self.host, port=self.port)
# }}}
