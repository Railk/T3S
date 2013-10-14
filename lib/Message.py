import sublime
from .Utils import debounce

class Message(object):

	messages =[]

	def show(self,message,hide=False):
		self.messages = []
		self.messages.append(message)

		window = sublime.active_window()
		window.run_command("hide_overlay")
		window.show_quick_panel(self.messages,self.hide)
		sublime.status_message(message)
		if hide:
			debounce(self.hide, 2, 'message' + str(id(MESSAGE)))


	def hide(self,index=None):
		sublime.active_window().run_command("hide_overlay")
		sublime.status_message('')

# --------------------------------------- INITIALISATION -------------------------------------- #

MESSAGE = Message()
		