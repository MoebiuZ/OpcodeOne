from assembler import *
import sys
import argparse



parser = argparse.ArgumentParser(description="Machine compiler v0.0.1")

parser.add_argument("file")
parser.add_argument("-o", "--output", action="store", dest="output_file")

args = parser.parse_args()


asm = Assembler()


asm.assemble(getattr(args, "file"))

if args.output_file != None:
	asm.writefile(args.output_file)
	print "Written to " + args.output_file
'''
for item in asm.code:
	sys.stdout.write("{0:02x}".format(ord(item), "x"))
'''