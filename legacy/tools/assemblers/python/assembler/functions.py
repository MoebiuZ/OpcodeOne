import re
import sys
import struct
import codecs


class REMatcher(object):
    def __init__(self, matchstring):
        self.matchstring = matchstring

    def match(self,regexp):
        self.rematch = re.match(regexp, self.matchstring, re.IGNORECASE)
        return bool(self.rematch)

    def group(self,i):
        return self.rematch.group(i)

    def groups(self):
       	return self.rematch.groups()





class Assembler:

	def printerror(self, text):
		print "Error in line " + str(self.line_count) + ": " + text
		exit()


	def parse_line(self, line):
		pass



	def second_pass(self):
		pass



	def assemble(self, file):
		self.line_count = 1;


		## First pass:

		with codecs.open(file, 'r', encoding='utf-8') as source_file:
			for line in source_file:
				self.parse_line(line)
		
		source_file.close()

		## Second pass: Resolve labels and adjust mahcine code accordingly

		self.second_pass()
