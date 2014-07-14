# coding=utf8

from subprocess import Popen, PIPE
from threading import Thread
try:
	from queue import Queue, Empty
except ImportError:
	from Queue import Queue, Empty

import sublime
import os
import time


from .Settings import SETTINGS
from ..display.Message import MESSAGE
from ..Utils import get_tss, get_kwargs, encode, ST3, Debug


#    PROCESSES = global Processes() instance
#     |
#     |_____has 2 TssJsStarterProcess
#     |     (1 for slow and 1 for fast commands)
#     |     for each project root
#     |
#    TssJsStarterThread()------->starts>         tss.js
#           |               |                      | | stdin stdout pipes
#           |               ---->starts>         TssAdapterThread (does debouncing and command reordering)
#           |                                      | |
#           --sending AsyncCommand() instances---->| |----> sublime.set_timeout(async_command.callback)
#               via synchronized Queue.Queue


# ----------------------------------------- PROCESSES ---------------------------------------- #
 
class Processes(object):
	"""
		Keeps two tss.js Processes and adapters for each project root.
		Process SLOW is for slow commands like tss>errors which can last more than 5s easily.
        Process FAST is for fast reacting commands eg. for autocompletion or type.
	"""

	SLOW = 0
	FAST = 1

	roots = {} # { 'rootfilename aka project' : (p_slow, p_fast) }

	def get(self, root, type=SLOW):
		""" Returns corresponding process for project root and type=SLOW or FAST. """
		if root in self.roots:
			return self.roots[root][type]
		return None

	def is_initialized(self, root):
		""" Returns True if both processes (SLOW and FAST) have been started. """
		return root in self.roots \
		   and self.roots[root] is not None \
		   and self.roots[root][Processes.SLOW].started \
		   and self.roots[root][Processes.FAST].started
		
	def initialisation_started(self, root):
		""" Returns True if start_tss_processes_for() has been called with root """
		return root in self.roots

	def start_tss_processes_for(self, root, init_finished_callback):
		"""
			If not allready started, start tss.js (2 times) for project root.
			Displays message to user while starting and calls tss_notify_callback('init', root) afterwards
		"""
		if self.initialisation_started(root):
			return
			
		print('Typescript initializing ' + root)

		process_slow = TssJsStarterThread(root)
		process_slow.start()
		
		process_fast = TssJsStarterThread(root)
		process_fast.start()
		
		self.roots[root] = ( process_slow, process_fast )
		
		self._wait_for_finish_and_notify_user(root, init_finished_callback)

	def kill_and_remove(self, root):
		""" Trigger killing of adapter, tss.js and queue. """
		if root in self.roots:
			Debug('tss+', "Killing tss.js process and adapter thread (for slow and fast lane) (Closing project %s)" % root)
			self.get(root, Processes.SLOW).kill_tssjs_queue_and_adapter()
			self.get(root, Processes.FAST).kill_tssjs_queue_and_adapter()
			del self.roots[root]


	def _wait_for_finish_and_notify_user(self, root, init_finished_callback, i=1, dir=-1):
		""" Displays animated Message as long as TSS is initing. Is recoursive function. """
		if not self.is_initialized(root):
			(i, dir) = self._display_animated_init_message(i, dir)
			# recoursive:
			sublime.set_timeout(lambda: self._wait_for_finish_and_notify_user(root, init_finished_callback, i, dir), 100)
		else:
			# starting finished ->
			MESSAGE.show('Typescript project intialized for root file : %s' % os.path.basename(root), True)
			init_finished_callback()

	def _display_animated_init_message(self, i, dir):
		if i in [1, 8]:
			dir *= -1
		i += dir
		anim_message = ' Typescript project is initializing [%s]' % '='.rjust(i).ljust(8)

		if not ST3:
			MESSAGE.repeat('Typescript project is initializing')
			sublime.status_message(anim_message)
		else:
			MESSAGE.repeat(anim_message)

		return (i, dir)


# ----------------------------------------- THREAD: (tss.js and adapter starter) ------------------------ #

class TssJsStarterThread(Thread):
	"""
		After starting, this class provides the methods and fields
			* send_async_command(...)
			* kill_tssjs_queue_and_adapter()
			* started
		for communication with the started Adapter and therewith the tss.js script.

		tss.js from: https://github.com/clausreinke/typescript-tools
	"""
	def __init__(self,root):
		""" init for project <root> """
		self.root = root
		self.started = False;
		Thread.__init__(self)
	
	def run(self):
		"""
			Starts the tss.js typescript services server process and the adapter thread.
		"""
		node = SETTINGS.get_node()
		tss = get_tss()
		kwargs = get_kwargs()


		self.tss_process = Popen([node, tss, self.root], stdin=PIPE, stdout=PIPE, **kwargs)
		self.tss_process.stdout.readline()

		self.tss_queue = Queue()
		self.tss_adapter = TssAdapterThread(self.tss_process.stdin,
											  self.tss_process.stdout, 
											  self.tss_queue)
		self.tss_adapter.daemon = True
		self.tss_adapter.start()
		
		self.started = True


	def send_async_command(self, async_command):
		""" Send a AsyncCommand() instance to the adapter thread. """
		self.tss_queue.put(async_command);

	def kill_tssjs_queue_and_adapter(self):
		"""
			Tells adapter to leave syncronized queue and to finish 
			and kills the tss.js process.
		"""
		self.tss_queue.put("stop!") # setinel value to stop queue
		self.tss_process.kill()



# ----------------------------------------- ADAPTER THREAD -------------------------- #

class TssAdapterThread(Thread):
	"""
		This class recieves commands from syncroized queue, merges/debounces them,
		executes them and then calls the async_command.callback in the the main_thread
		afterwards with the help of sublime.set_timeout().

		This class uses a middleware queue (simple array) to allow modification of command order.
		Every command form syncronized queue will immediatly be moved to middleware queue,
		because pythons Queue.Queue() does not allow for anything else than pop and put.

		Merging, debouncing and can then be done before poping the next command from middleware queue.

		The thread block of syncronized queue will be used to wait for new commands.
		To implement the debounce timeout, we add block release trigger commands
		to the queue via sublime.set_timeout(). This releases the queue when the command
		needs to be executed.

		If the setinel string "stop!" arrives on the syncronized queue, this thread will finish.
	"""

	def __init__(self, stdin, stdout, queue):
		"""
			stdin, stdout: Connection to tss.js, 
			queue: Synchronized queue to receive AsyncCommand instances.
		"""
		self.stdin = stdin
		self.stdout = stdout
		self.queue = queue
		self.middleware_queue = []
		Thread.__init__(self)

	def run(self):
		""" Working Loop. """
		# block until queue is not empty anymore
		# leave loop and finish thread if "stop!" arrives
		for async_command in iter(self.queue.get, "stop!"): 
			Debug('adapter', "CONTINUTE execution queue")

			self.append_to_middlewarequeue(async_command)
			self.add_pending_items_in_queue_to_middleware_queue()

			# non blocking loop: work on middleware_queue and keep up-to-date with arriving commands
			while not self.middleware_queue_is_finished():
				self.pop_and_execute_from_middleware_queue()
				self.add_pending_items_in_queue_to_middleware_queue()

			# => enter thread block
			Debug('adapter+', "WAIT for new work (%i currently debouncing)" % len(self.middleware_queue))

		Debug('adapter', "QUIT async adapter to tss process and close queue")
		self.stdin.close()
		self.stdout.close()


	def append_to_middlewarequeue(self, async_command, set_timer=True):
		""" Append async_command and set timer to release queue if told and needed. """
		self.middleware_queue.append(async_command)
		Debug('adapter+', "APPEND to middleware (in %fs): %s" % (async_command.time_until_execution(), async_command.id))
		if set_timer and not async_command.can_be_executed_now():
			self.trigger_queue_block_release_for(async_command)


	def trigger_queue_block_release_for(self, async_command):
		""" Sets timeout to trigger a block release just when async_command can be executed. """
		trigger_command = async_command.create_new_queue_trigger_command()
		seconds = async_command.time_until_execution()
		sublime.set_timeout(lambda: self.queue.put(trigger_command), int(seconds*1000) + 5)
		Debug('adapter+', "TRIGGER QUEUE in %fs" % seconds)


	def add_pending_items_in_queue_to_middleware_queue(self):
		""" Uses the non blocking version of get() to pop from syncronized queue. """
		try:
			while(True):
				self.append_to_middlewarequeue(self.queue.get_nowait())
		except Empty:
			pass


	def middleware_queue_is_finished(self):
		""" Returns True if no more commands or only debouncing commands pending on middleware queue. """
		for cmd in self.middleware_queue:
			if cmd.can_be_executed_now():
				return False
		return True


	def pop_and_execute_from_middleware_queue(self):
		""" Executes the next command, but merge it first. If merging with procrastinating enabled, do not execute it. """
		if not self.middleware_queue_is_finished():
			command_to_execute = self.middleware_queue.pop(0)
			Debug('adapter', "POPPED from middleware: %s" % command_to_execute.id)

			if command_to_execute.is_only_a_queue_trigger_command():
				Debug('adapter+', "FOUND OLD TRIGGER object, don't execute anything")
				return

			command_to_execute = self.merge_cmd_on_middleware_queue_and_return_replacement(command_to_execute)
			if command_to_execute: # can be None if merge_procrastinate() has defered current item
				self.execute(command_to_execute)


	def merge_cmd_on_middleware_queue_and_return_replacement(self, async_command):
		""" Selecting merge behaviour and merge """
		if(async_command.merge_behaviour == async_command.MERGE_IMMEDIATE):
			return self.merge_immediate(async_command)
		elif(async_command.merge_behaviour == async_command.MERGE_PROCRASTINATE):
			return self.merge_procrastinate(async_command)


	def merge_immediate(self, command):
		"""
			Removes all elements with the same id from middleware_queue.
			Remember: command is already poped from array, so there is no need to handle it
			Returns the last added aka newest same-id command
		"""
		commands_to_remove = []
		newest_command = command
		for possible_replacement in self.middleware_queue: # from old to new
			if possible_replacement.id == command.id: 
				newest_command = possible_replacement
				commands_to_remove.append(possible_replacement)

		if len(commands_to_remove) > 0:
			command.on_replaced(newest_command)
			for c in commands_to_remove:
				self.middleware_queue.remove(c)
				if c.id != newest_command.id:
					c.on_replaced(newest_command)
			Debug('adapter+', "MERGED with %i other commands (immediate): %s" % (len(commands_to_remove), command.id) )

		return newest_command


	def merge_procrastinate(self, command):
		"""
			If there is another command with same id, then do not execute it now.
			Delete all same-id commands except for the last one(=newest) in the array.
		"""
		commands_to_remove = []
		for possible_duplicate in self.middleware_queue: # from old to new
			if possible_duplicate.id == command.id:
				commands_to_remove.append(possible_duplicate) 

		if len(commands_to_remove) > 0:						
			newest_command = commands_to_remove.pop() # don't delete newest duplicate command. 
			command.on_replaced(newest_command)
			for c in commands_to_remove:
				c.on_replaced(newest_command)
				self.middleware_queue.remove(c)	
			Debug('adapter+', "MERGED with %i other commands (procrastinated): %s" % (len(commands_to_remove), command.id) )	
			return None # defer, no execution in this round
		else:
			return command # no defer, execute now, command has already been poped


	def execute(self, async_command):
		"""
			Executes Command.
			If debouncing enabled und timeout not finished, add back to the end of the queue.
			This may cause unexpected behaviour but should be unnoticed mostly.
		"""
		if not async_command.can_be_executed_now():
			self.append_to_middlewarequeue(async_command, set_timer=True) # reappend to end
			Debug('adapter+', "MOVED to end of queue, debouncing")
			return

		async_command.time_execute = time.time()
		self.stdin.write(encode(async_command.command))
		self.stdin.write(encode("\n"))
		self.stdin.flush()
		async_command.on_execute()
		# causes result callback to be called async
		async_command.on_result(self.stdout.readline().decode('UTF-8'))



# -------------------------------------------- INIT ------------------------------------------ #

PROCESSES = Processes()
