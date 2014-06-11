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
from .Liste import LISTE
from ..display.Message import MESSAGE
from ..Utils import get_tss, get_kwargs, encode, ST3

Debug = True

# ----------------------------------------- THREADS ---------------------------------------- #

# Process class. Starts the TSS process for rootfile <root> and starts another
# thread as adapter for async communicating with the TSS process. 
# This Thread finishes afterwards and can only be used to access the Queue object
# that is used for communication with the adapter and therewith with the TSS process
class Process(Thread):

	def __init__(self,root):
		self.root = root
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


	def send(self,message):
		if(Debug) print("DEPRECIATED: sync: " + message[0:50])
		return ""

	def send_async_command(self, async_command):
		self.tss_queue.put(async_command);
		if(Debug) print("CMD queued (send): %s" % async_command.id)

	def kill(self):
		self.tss_queue.put("stop!") # setinel value to stop queue
		self.tss_process.kill()


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
		self.id = _id
		self.is_executed = False
		self.replaced_by = None
		self.replaced_callback = replaced_callback
		self.result = ""
		self.payload = payload
		self.merge_behaviour = merge_behaviour
		
		#debug
		self.time_queue = 0
		self.time_execute = 0
		self.time_finish = 0
		
	def on_replaced(self, by):
		self.replaced_by = by
		if self.replaced_callback is not None:
			sublime.set_timeout(lambda:self.replaced_callback(self),000)
			
		if(Debug) print("CMD replaced after %f s [ %s" % (time.time() - self.time_queue, self.id))
		
	def on_result(self, result):
		self.result = result
		self.is_executed = True
		if self.result_callback is not None:
			sublime.set_timeout(lambda:self.result_callback(self),000)
			
		self.time_finish = time.time()
		if(Debug) print("CMD %fs = %fs + %fs to execute %s" % (
			self.time_finish - self.time_queue,
			self.time_execute - self.time_queue,
			self.time_finish - self.time_execute,
			self.id))
		
	# shortcut function (chainable)
	def procrastinate(self):
		self.merge_behaviour = AsyncCommand.MERGE_PROCRASTINATE
		return self
		
	# shortcut function (chainable)
	def add_payload(self, **payload):
		self.payload = payload
		return self
		
	# shortcut function	
	def append_to_global_queue(self, filename):
		root = LISTE.get_root(filename)
		process = PROCESSES.get(root)
		if process == None:
			return False
			
		self.time_queue = time.time()
			
		process.send_async_command(self)
		return True


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
				self.middleware_queue.append(self.queue.get_nowait())
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
			if(Debug) print("MERGED with %i (immediate): %s" % (len(commands_to_remove), command.id) )
			
		for c in commands_to_remove:
			self.middleware_queue.remove(c)
		
		return newest_command
			

	def merge_procrastinate(self, command):
		# if there is another command with same id, then do not execute it now
		# delete all same-id commands except for the last one(=newest) in the array
		commands_to_remove = []
		for possible_duplicate in self.middleware_queue: # from old to new
			if possible_duplicate.id == command.id:
				commands_to_remove.append(possible_duplicate) # this also appends item itself
		
		if len(commands_to_remove) > 0:						
			commands_to_remove.pop() # don't delete newest duplicate command. 
			for c in commands_to_remove:
				self.middleware_queue.remove(c)	
			if(Debug) print("MERGED with %i (procr->defer): %s" % (len(commands_to_remove), command.id) )	
			return None # defer, no execution in this round
		else:
			return command # no defer, execute now, command has already been poped

	def pop_and_execute_from_middleware_queue(self):
		if not self.middleware_queue_is_empty():
			command_to_execute = self.middleware_queue.pop(0)
			if(Debug) print("POPED from middleware: %s" % command_to_execute.id)
			command_to_execute = self.tidy_middleware_queue_and_return_newest_item_with_same_id(command_to_execute)
			if command_to_execute: # can be None if MERGE_PROCRASTINATE has defered current item
				self.execute(command_to_execute)
		
	def execute(self, async_command):
		async_command.time_execute = time.time()
		self.stdin.write(encode(async_command.command))
		self.stdin.flush()
		# causes result callback to be called async
		async_command.on_result(self.stdout.readline().decode('UTF-8'))

	def middleware_queue_is_empty(self):
		return len(self.middleware_queue) == 0

	def run(self):
		# use a middleware queue for implementation of the
		# behaviour described in AsyncCommand
	
		# block until queue is not empty anymore
		for async_command in iter(self.queue.get, "stop!"): 
			if(Debug) print("CONTINUTE execution queue")
			self.middleware_queue.append(async_command)
			self.add_pending_items_in_queue_to_middleware_queue()	
			
			while not self.middleware_queue_is_empty():
				self.pop_and_execute_from_middleware_queue()
				# stay up-to-date (but without entering the thread block,
				# otherwise the middleware_queue can not be worked on)
				self.add_pending_items_in_queue_to_middleware_queue()

			# queue and middleware_queue are empty
			# => enter thread block
			if(Debug) print("WAIT for new work")
			
		self.stdin.close()
		self.stdout.close()


#class AsyncReader(Thread):
##
#	def __init__(self,stdout,queue):
#		self.stdout = stdout
#		self.queue = queue
#
#		Thread.__init__(self)
#
#	def run(self):
#		for line in iter(self.stdout.readline, b''):
#			line = line.decode('UTF-8')
#			if line.startswith('"updated'):
#				continue
#			if line.startswith('"added'):
#				continue
#			if line.startswith('"reloaded'):
#				if not silent: MESSAGE.show('Project reloaded',True)
#				continue
#			else:
#				self.queue.put(line)
#
#		self.stdout.close()


# ----------------------------------------- PROCESSES ---------------------------------------- #

class Processes(object):

	threads = []
	liste = {}

	def __init__(self):
		super(Processes, self).__init__()

	def get(self,root):
		if root in self.liste: return self.liste[root]
		return None

		
	def add(self, root, tss_notify_callback):
		if root in self.liste: return
		print('Typescript initializing '+root)

		process = Process(root)
		process.start()
		self.liste[root] = process
		self._handle(process, tss_notify_callback)


	def remove(self,root):
		del self.liste[root]

	# display animated Message as long as TSS is initing
	def _handle(self,process, tss_notify_callback, i=0, dir=1):
		# process does only start the TSS Process
		if process.is_alive():
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
			sublime.set_timeout(lambda: self._handle(process, tss_notify_callback, i, dir), 100)
			return

		# started ->
		(head,tail) = os.path.split(process.root)
		MESSAGE.show('Typescript project intialized for root file : ' + tail, True)
		tss_notify_callback("init", process)


# -------------------------------------------- INIT ------------------------------------------ #

PROCESSES = Processes()
