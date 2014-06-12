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
import uuid

from .Settings import SETTINGS
from .Liste import LISTE
from ..display.Message import MESSAGE
from ..Utils import get_tss, get_kwargs, encode, ST3, Debug



# ----------------------------------------- PROCESS (tss and adapter starter) ------------------------ #

# Process class. Starts the TSS process for rootfile <root> and starts another
# thread as adapter for async communicating with the TSS process. 
# This Thread finishes afterwards and can only be used to access the Queue object
# that is used for communication with the adapter and therewith with the TSS process
class Process(Thread):

	def __init__(self,root):
		self.root = root
		self.started = False;
		Thread.__init__(self)
	
	def run(self):
		node = SETTINGS.get_node()
		tss = get_tss()
		kwargs = get_kwargs()


		self.tss_process = Popen([node, tss, self.root], stdin=PIPE, stdout=PIPE, **kwargs)
		self.tss_process.stdout.readline()

		self.tss_queue = Queue()
		self.async_tss_adapter = AsyncProcess(self.tss_process.stdin,
											  self.tss_process.stdout, 
											  self.tss_queue)
		self.async_tss_adapter.daemon = True
		self.async_tss_adapter.start()
		
		self.started = True


	def send_async_command(self, async_command):
		self.tss_queue.put(async_command);

	def kill_queue_and_adapter(self):
		self.tss_queue.put("stop!") # setinel value to stop queue
		self.tss_process.kill()


# ----------------------------------------- PROCESSES ---------------------------------------- #
 
class Processes(object):

	SLOW = 0
	FAST = 1

	liste = {} # { 'rootfilename' : (p_slow, p_fast) }

	def __init__(self):
		super(Processes, self).__init__()

	def get(self, root, type=SLOW):
		if root in self.liste:
			return self.liste[root][type]
		return None

	def is_initialized(self, root):
		return root in self.liste \
		   and self.liste[root] is not None \
		   and self.liste[root][Processes.SLOW].started \
		   and self.liste[root][Processes.FAST].started
		
	def add(self, root, tss_notify_callback):
		if root in self.liste:
			return
			
		print('Typescript initializing ' + root)

		process_slow = Process(root)
		process_slow.start()
		
		process_fast = Process(root)
		process_fast.start()
		
		self.liste[root] = ( process_slow, process_fast )
		
		self._handle(root, tss_notify_callback)

	def kill_and_remove(self, root):
		if root in self.liste:
			self.liste[root][Processes.SLOW].kill_queue_and_adapter()
			self.liste[root][Processes.FAST].kill_queue_and_adapter()
			del self.liste[root]


	# display animated Message as long as TSS is initing
	def _handle(self, root, tss_notify_callback, i=0, dir=1):
		# process does only start the TSS Process
		if not self.is_initialized(root):
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir

			if not ST3:
				MESSAGE.repeat('Typescript project is initializing')
				sublime.status_message(' Typescript project is initializing [%s=%s]' % \
					(' ' * before, ' ' * after))
			else:
				MESSAGE.repeat(' Typescript project is initializing [%s=%s]' % \
					(' ' * before, ' ' * after))

			#recursive
			sublime.set_timeout(lambda: self._handle(root, tss_notify_callback, i, dir), 100)
			
		else:
			# starting finished ->
			(head,tail) = os.path.split(root)
			MESSAGE.show('Typescript project intialized for root file : ' + tail, True)
			tss_notify_callback("init", root)

# ----------------------------------------- ASYNC COMMAND ---------------------------------- #

class AsyncCommand(object):
	MERGE_PROCRASTINATE = 1
	MERGE_IMMEDIATE = 2

	# id can be used to replace a previous command.
	# just add an async command with the same id and it will
	# be used instead of the one in the row.
	# also works if multiple commands with the same id are in
	# the queue, the newest one will be used
	# If you choose MERGE_PROCRASTINATE, it will execute the command not now,
	# but when the turn is at the last occuration of the command (id based)
	def __init__(self, command, result_callback=None, _id = "", replaced_callback=None, payload={}, merge_behaviour=MERGE_IMMEDIATE):
		self.command = command
		self.result_callback = result_callback
		self.id = _id if _id else uuid.uuid4().hex
		self.is_executed = False
		self.replaced_by = None
		self.replaced_callback = replaced_callback
		self.result = ""
		self.payload = payload
		self.merge_behaviour = merge_behaviour
		self.debounce_time = 0
		
		#debug
		self.time_queue = 0
		self.time_last_bounce = 0
		self.time_execute = 0
		self.time_finish = 0
		
	def on_replaced(self, by):
		self.replaced_by = by
		#by.time_last_bounce = time.time()
		if self.replaced_callback is not None:
			sublime.set_timeout(lambda:self.replaced_callback(self),000)
			
		if(Debug > 1): print("CMD replaced after %f s [ %s" % (time.time() - self.time_queue, self.id))
		
	def on_result(self, result):
		self.result = result
		self.is_executed = True
		if self.result_callback is not None:
			sublime.set_timeout(lambda:self.result_callback(self),000)
			
		self.time_finish = time.time()
		if(Debug): print("CMD %fs = %fs + %fs to execute %s" % (
			self.time_finish - self.time_queue,
			self.time_execute - self.time_queue,
			self.time_finish - self.time_execute,
			self.id))

	def can_be_executed_now(self):
		if self.debounce_time:
			return time.time() - self.time_last_bounce > self.debounce_time
		else:
			return True # debounce not activated
			
	def time_until_execution(self):
		if self.debounce_time:
			return self.debounce_time - (time.time() - self.time_last_bounce)  
		else:
			return 0 # debounce not activated
	

	# shortcut function (chainable)			
	# debouncing also works with the id. if there is no new command within
	# self.debounce_time, the command will be executed
	def activate_debounce(self, sec=0.8):
		self.debounce_time = sec
		return self
		
	# shortcut function (chainable)
	def procrastinate(self):
		self.merge_behaviour = AsyncCommand.MERGE_PROCRASTINATE
		return self
		
	# shortcut function (chainable)
	def add_payload(self, **payload):
		self.payload = payload
		return self
		
	# shortcut function	
	def append_to_queue(self, filename, process_type):
		root = LISTE.get_root(filename)
		if not PROCESSES.is_initialized(root):
			return False
			
		self.time_last_bounce = self.time_queue = time.time()
			
		process = PROCESSES.get(root, process_type)
		process.send_async_command(self)
		return True

	# shortcut function	
	def append_to_fast_queue(self, filename):
		if(Debug > 1): print("CMD queued @FAST: %s" % async_command.id)
		return self.append_to_queue(filename, Processes.FAST)

	# shortcut function	
	def append_to_slow_queue(self, filename):
		if(Debug > 1): print("CMD queued @FAST: %s" % async_command.id)
		return self.append_to_queue(filename, Processes.SLOW)

	# shortcut function	
	def append_to_both_queues(self, filename):
		return self.append_to_slow_queue(filename) \
		   and self.append_to_fast_queue(filename)

# ----------------------------------------- ASYNC PROCESS (adapter) -------------------------- #

class AsyncProcess(Thread):

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
		if(async_command.merge_behaviour == AsyncCommand.MERGE_IMMEDIATE):
			return self.merge_immediate(async_command)
		elif(async_command.merge_behaviour == AsyncCommand.MERGE_PROCRASTINATE):
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
			if(Debug > 1): print("MERGED with %i (immediate): %s" % (len(commands_to_remove), command.id) )
			
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
			if(Debug > 1): print("MERGED with %i (procr->defer): %s" % (len(commands_to_remove), command.id) )	
			return None # defer, no execution in this round
		else:
			return command # no defer, execute now, command has already been poped

	def pop_and_execute_from_middleware_queue(self):
		if not self.middleware_queue_is_finished():
			command_to_execute = self.middleware_queue.pop(0)
			if(Debug > 1): print("POPPED from middleware: %s" % command_to_execute.id)
			
			if command_to_execute.id is "trigger":
				if(Debug > 1): print("FOUND OLD TRIGGER object, don't execute anything")
				# this command has only used to trigger the queue block release
				return
			
			command_to_execute = self.tidy_middleware_queue_and_return_newest_item_with_same_id(command_to_execute)
			if command_to_execute: # can be None if merge_procrastinate() has defered current item
				self.execute(command_to_execute)
		
	def execute(self, async_command):
		if not async_command.can_be_executed_now():
			if(Debug > 1): print("MOVED to end of queue, debouncing")
			self.append_to_middlewarequeue(async_command, set_timer=False) # reappend to end
			return
	
		async_command.time_execute = time.time()
		self.stdin.write(encode(async_command.command))
		self.stdin.flush()
		# causes result callback to be called async
		async_command.on_result(self.stdout.readline().decode('UTF-8'))

	def middleware_queue_is_finished(self):
		for cmd in self.middleware_queue:
			if cmd.can_be_executed_now():
				return False
		return True
		

	def trigger_queue_block_release_in(self, seconds):
		if(Debug > 1): print("TRIGGER QUEUE in %fs" % seconds)
		sublime.set_timeout(lambda: self.queue.put(AsyncCommand("!trigger!", _id="trigger")), int(seconds*1000) + 5)

	def trigger_queue_block_release_for(self, async_command):
		self.trigger_queue_block_release_in(async_command.time_until_execution())

	def append_to_middlewarequeue(self, async_command, set_timer=True):
		self.middleware_queue.append(async_command)
		if(Debug > 1): print("APPEND to middleware (in %fs): %s" % (async_command.time_until_execution(), async_command.id))
		if set_timer and async_command.time_until_execution() > 0:
			self.trigger_queue_block_release_for(async_command)
			

	def run(self):
		# use a middleware queue for implementation of the
		# behaviour described in AsyncCommand
	
		# block until queue is not empty anymore
		for async_command in iter(self.queue.get, "stop!"): 
			if(Debug > 1): print("CONTINUTE execution queue")
			self.append_to_middlewarequeue(async_command)
			self.add_pending_items_in_queue_to_middleware_queue()	
			
			while not self.middleware_queue_is_finished():
				self.pop_and_execute_from_middleware_queue()
				# stay up-to-date (but without entering the thread block,
				# otherwise the middleware_queue can not be worked on)
				self.add_pending_items_in_queue_to_middleware_queue()

			# queue and middleware_queue are empty
			# => enter thread block
			if(Debug > 1): print("WAIT for new work")
			
		if(Debug): print("QUIT async adapter to tss process and close queue") # TODO Debug > 1
		self.stdin.close()
		self.stdout.close()


# -------------------------------------------- INIT ------------------------------------------ #

PROCESSES = Processes()
