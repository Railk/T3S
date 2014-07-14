import uuid
import time
import sublime
import json

from ..Utils import Debug, DEFAULT_DEBOUNCE_DELAY
from .Processes import PROCESSES

# ----------------------------------------- ASYNC COMMAND ---------------------------------- #

class AsyncCommand(object):
	"""
		Represents a command wich can be executed by typescript services server tss.js
		This class provices a chainable interface for config and can add itself to the
		async execution queue via the append_to_***_queue*() commands.

		Example for use and execution:
		AsyncCommand('errors', root aka project) \
			.activate_debounce() \
			.set_callback_kwargs(bar="foo", abc="def") \
			.set_result_callback(rc) \
			.procrastinate() \
			.set_id('errors') \
			.do_json_decode_tss_answer() \
			.append_to_slow_queue()

		The id is used to identify brother commands which do the same thing (maybe on the same file).
		If an id is given, all pending commands with the same id will 
		be merged into one command. By default, the command will be executed, when
		it's first brother is on the turn. Use procastinate() to reverse this behaviour:
		Then it will be deffered until the last aka newest brother is on turn.
		Id will also be used for debouncing.
	"""

	MERGE_PROCRASTINATE = 1
	MERGE_IMMEDIATE = 2


	def __init__(self, command, root):
		self.command = command
		self.root = root

		self.id = "%s-rnd%s" % (command[:6][:-1], uuid.uuid4().hex[0:5])
		self.result_callback = None
		self.replaced_callback = None
		self.executing_callback = None
		self.callback_kwargs = {}
		self.merge_behaviour = self.MERGE_IMMEDIATE
		self.debounce_time = 0
		self.json_decode_tss_answer = False

		self.time_queue = 0
		self.time_last_bounce = 0
		self.time_execute = 0
		self.time_finish = 0
		self.is_executed = False

	# ------------------------- chainable config ---------------------------------- #

	def set_id(self, _id):
		""" set id for merging. See AsyncCommand.__doc__ for more information about merging """
		self.id = _id
		return self

	def procrastinate(self):
		""" Set merging strategy to procastinate. See AsyncCommand.__doc__ for more information about merging """
		self.merge_behaviour = self.MERGE_PROCRASTINATE
		return self

	def activate_debounce(self, delay=DEFAULT_DEBOUNCE_DELAY):
		"""
			Activates debouncing. Command will only be executed when there are no new same-id commands for <delay> seconds.
			Attention: This is only tested with MERGE_PROCRASTINATE activated.
		"""
		self.debounce_time = delay
		return self

	def do_json_decode_tss_answer(self):
		self.json_decode_tss_answer = True
		return self

	def set_callback_kwargs(self, **callback_kwargs):
		""" Set additional arguments the callbacks will be called with. """
		self.callback_kwargs = callback_kwargs
		return self

	def set_result_callback(self, result_callback=None):
		""" Will be called as result_callback(tss_answer, **callback_kwargs). """
		self.result_callback = result_callback
		return self

	def set_replaced_callback(self, replaced_callback=None):
		"""
			Will be called as replaced_callback(now_used_command, **callback_kwargs) 
			when this command has been deleted from queue without execution.
		"""
		self.replaced_callback = replaced_callback
		return self

	def set_executing_callback(self, executing_callback=None):
		""" Will be called as soon as the command is sent to tss.js """
		self.executing_callback = executing_callback
		return self



	# ------------------------- finish chain: execute ------------------------------ #

	def append_to_fast_queue(self):
		Debug('command', "CMD queued @FAST: %s" % self.id)
		return self._append_to_queue(PROCESSES.FAST)

	def append_to_slow_queue(self):
		Debug('command', "CMD queued @SLOW: %s" % self.id)
		return self._append_to_queue(PROCESSES.SLOW)

	def append_to_both_queues(self):
		return self.append_to_slow_queue() \
		   and self.append_to_fast_queue()

	def _append_to_queue(self, process_type):
		if not PROCESSES.is_initialized(self.root):
			return False
			
		self.time_queue = time.time()
		self.time_last_bounce = self.time_queue
			
		process = PROCESSES.get(self.root, process_type)
		process.send_async_command(self)
		return True

	# ------------------------- call callbacks ---------------------------------- #

	def on_replaced(self, by):
		""" calls callback by using sublime.set_timeout """
		by.time_last_bounce = max(self.time_last_bounce, by.time_last_bounce)
		if self.replaced_callback is not None:
			sublime.set_timeout(lambda:self.replaced_callback(by, **self.callback_kwargs),000)
			
		Debug('command+', "CMD replaced after %fs [ %s ]" % (time.time() - self.time_queue, self.id))
		
	def on_result(self, tss_answer):
		""" calls callback by using sublime.set_timeout """
		self.is_executed = True
		if self.result_callback is not None:
			if self.json_decode_tss_answer:
				tss_answer = json.loads(tss_answer)
			sublime.set_timeout(lambda:self.result_callback(tss_answer, **self.callback_kwargs),000)
			
		self.time_finish = time.time()
		Debug('command', "CMD %fs = %fs + %fs to execute %s" % (
			self.time_finish - self.time_queue,
			self.time_execute - self.time_queue,
			self.time_finish - self.time_execute,
			self.id))

	def on_execute(self):
		""" calls executing_callback using sublime.set_timeout """
		if self.executing_callback is not None:
			sublime.set_timeout(lambda: self.executing_callback(**self.callback_kwargs))

	# ------------------------- debouncing helpers ---------------------------------- #

	def create_new_queue_trigger_command(self):
		"""
			Creates an AsyncCommand instance which then can be added to queue without having any effect.
		"""
		return AsyncCommand("!trigger!", self.root).set_id("trigger")

	def is_only_a_queue_trigger_command(self):
		""" Returns True if this is a command without effect. """
		return self.id == "trigger"

	def can_be_executed_now(self):
		""" Returns False if debouncing is activated but timeout not finished. Otherwise True. """
		if self.debounce_time:
			return time.time() - self.time_last_bounce > self.debounce_time
		else:
			return True # debounce not activated

	def time_until_execution(self):
		""" Returns 0 or time until execution is allowed (debouncing) """
		if self.debounce_time:
			return self.debounce_time - (time.time() - self.time_last_bounce)  
		else:
			return 0 # debounce not activated


