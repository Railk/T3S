# coding=utf8

import sublime
from .Base import Base
from ...Utils import Debug, ST3, get_prefix

class Outline(Base):

	regions = {}
	ts_view = None

	def __init__(self, t3sviews):
		super(Outline, self).__init__('Typescript : Outline View', t3sviews)


	# SET TEXT
	def set_text(self, edit_token, members, ts_view):
		"""
			This function takes the tss.js members structure instead of a string.
		"""
		# this will process the outline, even if the view is closed
		self.ts_view = ts_view
		self._tssjs_2_outline_format(members)
		super(Outline, self).set_text(edit_token, self.text)

	def is_current_ts(self, ts_view):
		if ts_view is None or self.ts_view is None:
			return
		return ts_view.id() == self.ts_view.id()

	def _tssjs_2_outline_format(self, members):
		text = []
		line = 0
		self.regions = {}

		for member in members:
			start_line = member['min']['line']
			end_line = member['lim']['line']
			left = member['min']['character']
			right = member['lim']['character']

			a = self.ts_view.text_point(start_line-1, left-1)
			b = self.ts_view.text_point(end_line-1, right-1)
			region = sublime.Region(a, b)

			kind = get_prefix(member['loc']['kind'])
			container_kind = get_prefix(member['loc']['containerKind'])
			if member['loc']['kindModifiers'] != "":
				member['loc']['kindModifiers'] = " " + member['loc']['kindModifiers']

			if member['loc']['kind'] != 'class' and member['loc']['kind'] != 'interface':
				t = "%s %s %s %s" % (kind, member['loc']['kindModifiers'], member['loc']['kind'], member['loc']['name'])
				text.append('\n\t')
				text.append(t.strip())
				line += 1
				self.regions[line] = region
			else:
				t = "%s %s %s %s {" % (container_kind, member['loc']['kindModifiers'], member['loc']['kind'], member['loc']['name'])
				if len(text) == 0:
					text.append('\n%s\n' % t.strip())
					line += 2
					self.regions[line - 1] = region
				else:
					text.append('\n\n}\n\n%s\n' % t.strip())
					lines += 5
					self.regions[line - 1] = region

		if len(members) == 0:
			text.append("\n\nno members found\n")

		self.text = ''.join(text)


	is_focusing_ts_view = False

	def on_click(self,line):
		if self.is_focusing_ts_view:
			Debug('focus', 'Outline.on_click: is just focusing other view > ignore')
			return
		if line in self.regions:
			draw = sublime.DRAW_NO_FILL if ST3 else sublime.DRAW_OUTLINED
			self.ts_view.add_regions('typescript-definition', [self.regions[line]], 'comment', 'dot', draw)
			self._focus_member_in_view(self.regions[line])

	def _focus_member_in_view(self, region):
		if self.ts_view.is_loading():
			return
		else:
			Debug('focus', "_focus_member_in_view, Region @pos %i" % (region.begin()))
			self.is_focusing_ts_view = True
			self.ts_view.show(region)
			self.ts_view.window().focus_view(self.ts_view)
			self.is_focusing_ts_view = False














