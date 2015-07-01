# coding=utf8

import sublime

if int(sublime.version()) >= 3000:
	from .lib.Commands import *
	from .lib.Listener import TypescriptEventListener, init
	from .lib.display.T3SViews import TypescriptEventListener2

	def plugin_loaded():
		sublime.set_timeout(lambda:init(sublime.active_window().active_view()), 300)

	def plugin_unloaded():
		pass

else:
	from lib.Commands import *
	from lib.Listener import TypescriptEventListener, init
	from lib.display.T3SViews import TypescriptEventListener2

	sublime.set_timeout(lambda:init(sublime.active_window().active_view()),1000)
