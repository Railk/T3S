# coding=utf8

import sublime
import json
import hashlib

from .display.Completion import COMPLETION
from .display.Message import MESSAGE
from .system.Processes import PROCESSES
from .system.AsyncCommand import AsyncCommand
from .system.Liste import get_root
from .Utils import is_dts, encode, CancelCommand, Debug


# --------------------------------------- TSS -------------------------------------- #

class Tss(object):

	# INITIALISATION FINISHED
	def assert_initialisation_finished(self, filename):
		if not PROCESSES.is_initialized(get_root( filename )):
			sublime.status_message('You must wait for the initialisation to finish')
			raise CancelCommand()


	# INIT ROOT FILE
	def init(self, root):
		PROCESSES.start_tss_processes_for(root,
				  init_finished_callback=lambda: self.notify('init', root) )
		self.added_files = {} # added_files[filename] = hash # TODO remove to FILES
		self.executed_with_most_recent_file_contents = []
		self.is_killed = False


	# RELOAD PROCESS
	def reload(self, filename_or_root):
		AsyncCommand('reload', get_root(filename_or_root)) \
			.set_id('reload') \
			.append_to_both_queues()
		self.errors(filename_or_root)

	# GET INDEXED FILES
	def files(self, filename, callback):
		AsyncCommand('files', get_root(filename)) \
			.do_json_decode_tss_answer() \
			.set_result_callback(callback) \
			.append_to_fast_queue()

	# DUMP FILE (untested)
	def dump(self, filename, output, callback):
		dump_command = 'dump {0} {1}'.format( output, filename.replace('\\','/') )
		AsyncCommand(dump_command, get_root(filename)) \
			.set_result_callback(callback) \
			.append_to_fast_queue()

	# TYPE
	def type(self, filename, line, col, callback):
		""" callback({ tss type answer }, filename=, line=, col=) """

		type_command = 'type {0} {1} {2}'.format( str(line+1), str(col+1), filename.replace('\\','/') )

		AsyncCommand(type_command, get_root(filename)) \
			.set_id("type_command") \
			.set_callback_kwargs(filename=filename, line=line, col=col) \
			.do_json_decode_tss_answer() \
			.set_result_callback(callback) \
			.append_to_fast_queue()


	# DEFINITION
	def definition(self, filename, line, col, callback):
		""" callback({ tss type answer }, filename=, line=, col=) """

		definition_command = 'definition {0} {1} {2}'.format( str(line+1), str(col+1), filename.replace('\\','/') )

		AsyncCommand(definition_command, get_root(filename)) \
			.set_id("definition_command") \
			.set_callback_kwargs(filename=filename, line=line, col=col) \
			.do_json_decode_tss_answer() \
			.set_result_callback(callback) \
			.append_to_fast_queue()


	# REFERENCES
	def references(self, filename, line, col, callback):
		""" callback({ tss type answer }, filename=, line=, col=) """

		references_command = 'references {0} {1} {2}'.format( str(line+1), str(col+1), filename.replace('\\','/') )

		AsyncCommand(references_command, get_root(filename)) \
			.set_id("references_command") \
			.set_callback_kwargs(filename=filename, line=line, col=col) \
			.do_json_decode_tss_answer() \
			.set_result_callback(callback) \
			.append_to_fast_queue()

	# STRUCTURE
	def structure(self, filename, callback):
		""" callback({ tss type answer }, filename=) """

		structure_command = 'structure {0}'.format(filename.replace('\\','/'))

		AsyncCommand(structure_command, get_root(filename)) \
			.set_id("structure_command") \
			.set_callback_kwargs(filename=filename) \
			.do_json_decode_tss_answer() \
			.set_result_callback(callback) \
			.append_to_fast_queue()


	# ASK FOR COMPLETIONS
	def complete(self, filename, line, col, member, callback):
		""" callback("tss type answer as string") """

		completions_command = 'completions {0} {1} {2} {3}'.format(member, str(line+1), str(col+1), filename.replace('\\','/'))

		AsyncCommand(completions_command, get_root(filename)) \
			.set_id("completions_command") \
			.set_result_callback(callback) \
			.append_to_fast_queue()


	# UPDATE FILE
	def update(self, filename, lines, content):

		update_command = 'update nocheck {0} {1}\n{2}'.format(str(lines+1), filename.replace('\\','/'), content)

		AsyncCommand(update_command, get_root(filename)) \
			.set_id('update %s' % filename) \
			.append_to_both_queues()

		# Always execute tss->update because it's almost no overhead, but remember if anything has changed
		if self.need_update(filename, content):
			self.on_file_contents_have_changed()


	# ADD FILE
	def add(self, root, filename, lines, content):

		update_cmdline = 'update nocheck {0} {1}\n{2}'.format(str(lines+1),filename.replace('\\','/'),content)

		AsyncCommand(update_command, root) \
			.set_id('add %s' % filename) \
			.append_to_both_queues()

		# Always execute tss>update when adding
		self.on_file_contents_have_changed()
	

	def on_file_contents_have_changed(self):
		self.executed_with_most_recent_file_contents = []

	def need_update(self, filename, unsaved_content):
		newhash = self.make_hash(filename, unsaved_content)
		oldhash = self.added_files[filename] if filename in self.added_files else "wre"
		if newhash == oldhash:
			Debug('tss+', "NO UPDATE needed for file : %s" % filename)
			return False
		else:
			Debug('tss+', "UPDATE needed for file %s : %s" % (newhash, filename) )
			self.added_files[filename] = newhash
			return True

	def make_hash(self, filename, unsaved_content):
		return hashlib.md5(encode(unsaved_content)).hexdigest()

	# ERRORS
	# callback format: def x(result, filename=)
	def set_default_errors_callback(self, callback):
		self.default_errors_callback = callback
		
	def errors(self, filename, callback=None):
		if not callback:
			callback = self.default_errors_callback
		# only update if something in the files had changed since last execution
		if 'errors' in self.executed_with_most_recent_file_contents:
			return
		self.executed_with_most_recent_file_contents.append('errors')

		AsyncCommand('showErrors', get_root(filename)) \
			.set_id('showErrors') \
			.procrastinate() \
			.activate_debounce() \
			.set_callback_kwargs(filename=filename) \
			.set_result_callback(callback) \
			.append_to_slow_queue()
	

	# KILL PROCESS (if no more files in editor)
	def kill(self, filename):
		if not PROCESSES.is_initialized(get_root(filename)) \
			or self.is_killed:
			return

		self.is_killed = False

		def async_react_files(files):
			def kill_and_remove(_async_command=None):
				# Dont execute this twice (this fct will be called 3 times)
				if self.is_killed: 
					Debug('tss+', "ALREADY closed ts project")
					return
				self.is_killed = True
				
				root = get_root(filename)
				PROCESSES.kill_and_remove(root)
				MESSAGE.show('TypeScript project will close',True)
				self.notify('kill', root)
				
			def still_used_ts_files_open_in_window(files):
				views = sublime.active_window().views()
				for v in views:
					if v.file_name() == None:
						continue
					for f in files:
						if v.file_name().replace('\\','/').lower() == f.lower() and not is_dts(v):
							Debug('tss+', "KILL? STILL MORE TS FILES open -> do nothing")
							return True
				Debug('tss', "NO MORE TS FILES -> kill TSS process")
				return False

			if not files: # TODO: why?
				return
				
			# don't quit tss if an added *.ts file is still open in an editor view
			if still_used_ts_files_open_in_window(files):
				return


			# send quit and kill process afterwards
			AsyncCommand('quit', get_root(filename)) \
				.set_id('quit') \
				.set_result_callback(kill_and_remove) \
				.append_to_both_queues()


			# if the tss process has hang up (previous lambda will not be executed)
			# , force kill after 5 sek
			sublime.set_timeout(kill_and_remove,10000) 
			

		sublime.active_window().run_command('save_all')
		self.files(filename, async_react_files)
		

		
		
		
	listeners = {}
	# LIST OF EVENT TYPES:
	# kill

	# NOTIFY LISTENERS
	def notify(self, event_type, root):
		if root not in self.listeners: return
		for f in self.listeners[root][event_type]:
			f(root)


	# ADD EVENT LISTENER
	def addEventListener(self, event_type, root, callback):
		if root not in self.listeners:
			self.listeners[root] = {}
		if type not in self.listeners[root]:
			self.listeners[root][event_type] = []
		self.listeners[root][event_type].append(callback)


	# REMOVE EVENT LISTENER
	def removeEventListener(self, event_type, root, callback):
		if root not in self.listeners: return
		if type not in self.listeners[root]: return

		to_delete = []
		for f in self.listeners[root][event_type]:
			if f == callback:
				to_delete.append(f)

		for f in to_delete:
			self.listeners[root][event_type].remove(f)


# --------------------------------------- INITIALISATION -------------------------------------- #

TSS = Tss()
