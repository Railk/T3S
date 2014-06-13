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
		
	def start_tss_processes_for(self, root, init_finished_callback):
		"""
			If not allready started, start tss.js (2 times) for project root.
			Displays message to user while starting and calls tss_notify_callback('init', root) afterwards
		"""
		if root in self.roots:
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
			self.get(root, SLOW).kill_tssjs_queue_and_adapter()
			self.get(root, FAST).kill_tssjs_queue_and_adapter()
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


# ----------------------------------------- PROCESS (tss and adapter starter) ------------------------ #

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
		""" send a AsyncCommand() instance to the adapter thread """
		self.tss_queue.put(async_command);

	def kill_tssjs_queue_and_adapter(self):
		"""
			Tells adapter to leave syncronized queue and to finish 
			and kills the tss.js process
		"""
		self.tss_queue.put("stop!") # setinel value to stop queue
		self.tss_process.kill()



# ----------------------------------------- ASYNC PROCESS (adapter) -------------------------- #

class TssAdapterThread(Thread):

	def __init__(self,stdin,stdout,queue):
		self.stdin = stdin
		self.stdout = stdout
		self.queue = queue
		self.middleware_queue = []
		Thread.__init__(self)

	def add_pending_items_in_queue_to_middleware_queue(self):
		try:
			while(True):
				self.append_to_middlewarequeue(self.queue.get_nowait())
		except Empty:
			pass

	def tidy_middleware_queue_and_return_newest_item_with_same_id(self, async_command):
		if(async_command.merge_behaviour == async_command.MERGE_IMMEDIATE):
			return self.merge_immediate(async_command)
		elif(async_command.merge_behaviour == async_command.MERGE_PROCRASTINATE):
			return self.merge_procrastinate(async_command)

	def merge_immediate(self, command):
		# the newest elements are at the end of the queue array, 
		# so start with the beginning
		commands_to_remove = []
		newest_command = command
		for possible_replacement in self.middleware_queue: # from old to new
			if possible_replacement.id == command.id: #command is already poped from array
				newest_command.on_replaced(possible_replacement)
				newest_command = possible_replacement
				# remove all items with the same id
				commands_to_remove.append(possible_replacement)

		if len(commands_to_remove) > 0:
			Debug('adapter+', "MERGED with %i (immediate): %s" % (len(commands_to_remove), command.id) )

		for c in commands_to_remove:
			self.middleware_queue.remove(c)

		return newest_command


	def merge_procrastinate(self, command):
		# if there is another command with same id, then do not execute it now
		# delete all same-id commands except for the last one(=newest) in the array
		commands_to_remove = []
		for possible_duplicate in self.middleware_queue: # from old to new
			if possible_duplicate.id == command.id: #command is already poped from array
				commands_to_remove.append(possible_duplicate) 

		if len(commands_to_remove) > 0:						
			commands_to_remove.pop() # don't delete newest duplicate command. 
			for c in commands_to_remove:
				self.middleware_queue.remove(c)	
			Debug('adapter+', "MERGED with %i (procr->defer): %s" % (len(commands_to_remove), command.id) )	
			return None # defer, no execution in this round
		else:
			return command # no defer, execute now, command has already been poped

	def pop_and_execute_from_middleware_queue(self):
		if not self.middleware_queue_is_finished():
			command_to_execute = self.middleware_queue.pop(0)
			Debug('adapter', "POPPED from middleware: %s" % command_to_execute.id)

			if command_to_execute.id is "trigger":
				Debug('adapter+', "FOUND OLD TRIGGER object, don't execute anything")
				# this command has only used to trigger the queue block release
				return

			command_to_execute = self.tidy_middleware_queue_and_return_newest_item_with_same_id(command_to_execute)
			if command_to_execute: # can be None if merge_procrastinate() has defered current item
				self.execute(command_to_execute)

	def execute(self, async_command):
		if not async_command.can_be_executed_now():
			Debug('adapter+', "MOVED to end of queue, debouncing")
			self.append_to_middlewarequeue(async_command, set_timer=False) # reappend to end
			return

		async_command.time_execute = time.time()
		self.stdin.write(encode(async_command.command))
		self.stdin.write(encode("\n"))
		self.stdin.flush()
		# causes result callback to be called async
		async_command.on_result(self.stdout.readline().decode('UTF-8'))

	def middleware_queue_is_finished(self):
		for cmd in self.middleware_queue:
			if cmd.can_be_executed_now():
				return False
		return True

	def trigger_queue_block_release_for(self, async_command):
		trigger_command = async_command.create_new_queue_trigger_command()
		seconds = async_command.time_until_execution()
		sublime.set_timeout(lambda: self.queue.put(trigger_command), int(seconds*1000) + 5)
		Debug('adapter+', "TRIGGER QUEUE in %fs" % seconds)

	def append_to_middlewarequeue(self, async_command, set_timer=True):
		self.middleware_queue.append(async_command)
		Debug('adapter+', "APPEND to middleware (in %fs): %s" % (async_command.time_until_execution(), async_command.id))
		if set_timer and async_command.time_until_execution() > 0:
			self.trigger_queue_block_release_for(async_command)


	def run(self):
		# use a middleware queue for implementation of the
		# behaviour described in AsyncCommand

		# block until queue is not empty anymore
		for async_command in iter(self.queue.get, "stop!"): 
			Debug('adapter', "CONTINUTE execution queue")
			self.append_to_middlewarequeue(async_command)
			self.add_pending_items_in_queue_to_middleware_queue()	

			while not self.middleware_queue_is_finished():
				self.pop_and_execute_from_middleware_queue()
				# stay up-to-date (but without entering the thread block,
				# otherwise the middleware_queue can not be worked on)
				self.add_pending_items_in_queue_to_middleware_queue()

			# queue and middleware_queue are empty
			# => enter thread block
			Debug('adapter+', "WAIT for new work")

		Debug('adapter', "QUIT async adapter to tss process and close queue")
		self.stdin.close()
		self.stdout.close()


# -------------------------------------------- INIT ------------------------------------------ #

PROCESSES = Processes()
