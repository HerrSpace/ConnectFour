#!/usr/bin/env python3
import sys
import os

import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool

from four.fourPageHandler import Four
from four.memberSocket import MemberSocket

sys.path.append(os.path.dirname(__file__))


class Root():
	def index(self):
		raise cherrypy.HTTPRedirect("/four/example_session")

	def ws(self):
		cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


if __name__ == '__main__':
	ip = '0.0.0.0'
	port = 8080

	static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

	WebSocketPlugin(cherrypy.engine).subscribe()
	cherrypy.tools.websocket = WebSocketTool()

	cherrypy.config.update({'server.socket_host': ip})
	cherrypy.config.update({'server.socket_port': port})
	cherrypy.config.update({'error_page.404': 'static/templates/404.html'})

	index_controller = Root()
	game_controller = Four()

	d = cherrypy.dispatch.RoutesDispatcher()
	d.connect(name='root',		action='index',				controller=index_controller,	route='/')
	d.connect(name='root',		action='ws',				controller=index_controller,	route='/ws')
	d.connect(name='four',		action='render',			controller=game_controller,		route='/four/:session')
	d.connect(name='four',		action='control_channel',	controller=game_controller,		route='/four/control_channel/:session')

	config_dict = {
		'/': {
			'request.dispatch': d,
			'tools.staticdir.on': True,
			'tools.staticdir.root': static_root,
			'tools.staticdir.dir': '.'
		},
		'/ws': {
			'tools.websocket.on': True,
			'tools.websocket.handler_cls': MemberSocket
		}
	}


	cherrypy.tree.mount(None, config=config_dict)
	cherrypy.engine.start()
	cherrypy.engine.block()
