import sublime
from ..Utils import debounce, ST3

class Message(object):

	messages =[]
	previous = ""

	def show(self,message,hide=False):
		self.messages = []
		self.messages.append(message)

		window = sublime.active_window()
		window.run_command("hide_overlay")
		window.show_quick_panel(self.messages,self.hide)
		sublime.status_message(message)

		if hide:
			debounce(self.hide, 1, 'message' + str(id(MESSAGE)))


	def repeat(self,message):
		self.messages = []
		self.messages.append(message)

		window = sublime.active_window()

		if self.previous == message:
			if ST3: 
				window.run_command("hide_overlay")
				window.show_quick_panel(self.messages,self.hide)
		else:
			if ST3: 
				window.run_command("hide_overlay")
			
			window.show_quick_panel(self.messages,self.hide)

		sublime.status_message(message)
		self.previous = message


	def hide(self,index=None):
		sublime.active_window().run_command("hide_overlay")
		sublime.status_message('')		

# --------------------------------------- INITIALISATION -------------------------------------- #

MESSAGE = Message()