# coding=utf8

from subprocess import Popen, PIPE
from threading import Thread
try:
	from queue import Queue
except ImportError:
	from Queue import Queue

import sublime
import os

from .Settings import SETTINGS
from ..display.Message import MESSAGE
from ..Utils import get_tss, get_kwargs, encode, ST3


# ----------------------------------------- THREADS ---------------------------------------- #

class Process(Thread):

	def __init__(self,root):
		self.root = root
		Thread.__init__(self)

	
	def run(self):
		node = SETTINGS.get_node()
		tss = get_tss()
		kwargs = get_kwargs()

		self.sync = Popen([node, tss, self.root], stdin=PIPE, stdout=PIPE, **kwargs)
		self.async = Popen([node, tss, self.root], stdin=PIPE, stdout=PIPE, **kwargs)
		self.sync.stdout.readline().decode('UTF-8')
		self.async.stdout.readline().decode('UTF-8')

		self.w_async = Queue()
		writer = AsyncWriter(self.async.stdin,self.w_async)
		writer.daemon = True
		writer.start()

		self.r_async = Queue()
		reader = AsyncReader(self.async.stdout,self.r_async)
		reader.daemon = True
		reader.start()

		# trigger compilation for completion and others
		self.init()

	def init(self):
		self.send('showErrors\n')

	def send(self,message):
		self.sync.stdin.write(encode(message))
		return self.sync.stdout.readline().decode('UTF-8')

	def send_async(self,message):
		self.w_async.put(encode(message))

	def kill(self):
		self.sync.kill()
		self.async.kill()


class AsyncWriter(Thread):

	def __init__(self,stdin,queue):
		self.stdin = stdin
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		for item in iter(self.queue.get, None):
			self.stdin.write(item)
		self.stdin.close()


class AsyncReader(Thread):

	def __init__(self,stdout,queue):
		self.stdout = stdout
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		for line in iter(self.stdout.readline, b''):
			line = line.decode('UTF-8')
			if line.startswith('"updated') or line.startswith('"added') or line.startswith('"reloaded'):
				continue
			else:
				self.queue.put(line)

		self.stdout.close()


# ----------------------------------------- PROCESSES ---------------------------------------- #

class Processes(object):

	threads = []
	liste = {}

	def __init__(self):
		super(Processes, self).__init__()

	def get(self,root):
		if root in self.liste: return self.liste[root]
		return None

		
	def add(self,root,done):
		if root in self.liste: return
		print('Typescript initializing '+root)

		process = Process(root)
		process.start()
		self.liste[root] = process
		self._handle(process,done)


	def remove(self,root):
		del self.liste[root]


	def _handle(self,process,done,i=0,dir=1):
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

			sublime.set_timeout(lambda: self._handle(process,done,i,dir), 100)
			return

		(head,tail) = os.path.split(process.root)
		MESSAGE.show('Typescript project intialized for root file : '+tail,True)
		done("init",process)


# -------------------------------------------- INIT ------------------------------------------ #

PROCESSES = Processes()