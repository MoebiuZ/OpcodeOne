import re

class Assembler:


	def inst_CALL(self, m):
		self.checkInCode()
		opcode = self.OPCODES['CALL']
		r_src = 'A'
		r_dest = 'A'
		r_op = 'A'
		
		if re.match(self.HEX, m.group(2)):
			addr = m.group(2)
		elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(2)):
			self.enqueuelabel(m.group(2).strip("()"), self.inst_addr+1)
			addr = "0xdeadbe"
		
		self.instructions.append(self.inst_addr)
		self.push24(opcode << 16)
		self.push24(addr)
		self.inst_addr += 2
		


	def inst_LD(self, m):
		self.checkInCode()
		opcode = self.OPCODES['LD']
		mode = ''
		r_dest = 'A'
		r_src = 'A'
		r_op = 'A'
		value = ''
		
		r_dest = m.group(2).upper()
		if re.match(self.REG, m.group(3)):
			mode = "REGISTER"
			r_src = m.group(3).upper()
		elif re.match(self.HEX + "|" + self.INT, m.group(3)):
			mode = "VALUE"
			value = m.group(3)
		elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(3)):
			mode = "VALUE"
			self.enqueuelabel(m.group(3).strip("()"), self.inst_addr+1)
			value = "0xdeadbe"
		else:
			self.printerror("Syntax error")

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8(self.MODES[mode] << 4)
		self.push8((self.REGISTERS[r_src] << 4) | self.REGISTERS[r_dest])
		self.inst_addr += 1
		if value != '':
			self.push24(int(value, 0))
			self.inst_addr += 1
		

	def inst_DBG(self, m):
		self.checkInCode()
		opcode = self.OPCODES['DBG']
		r_src = 'A'
		r_dest = 'A'
		r_op = 'A'

		r_op = m.group(2)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8(self.REGISTERS[r_op])
		self.push8(0x00)
		self.inst_addr += 1


	def inst_HALT(self, m):
		self.checkInCode()
		opcode = self.OPCODES['HALT']
		self.instructions.append(self.inst_addr)
		self.push24(opcode << 16)
		self.inst_addr += 1


	def inst_MR(self, m):
		self.checkInCode()
		opcode = self.OPCODES['MR']
		mode = ''
		r_dest = 'A'
		r_src = 'A'
		r_op = 'A'
		addr = ''
		offset = ''
		near = False
		relative = False
						
		r_dest = m.group(2).upper()
		if re.match("\[" + self.REG + "\]", m.group(3), re.IGNORECASE):
			mode += "INDIRECT"
			r_dest = re.sub('[\[\]]', '',m.group(3).upper())
		elif re.match(self.HEX, m.group(3), re.IGNORECASE):
			mode += "ABSOLUTE"
			addr = m.group(3)
		elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(3)):
			mode = "ABSOLUTE"
			self.enqueuelabel(m.group(3).strip("()"), self.inst_addr+1)
			offset = "0xdeadbe"
		else:
			self.printerror("Syntax error")

			
		if (m.group(4) != None): # There is offset

			mode += m.group(4)
			if re.match(self.REG, m.group(4), re.IGNORECASE):
				mode += "REG"
				r_op = m.group(4).upper()
			elif re.match(self.INT, m.group(5), re.IGNORECASE):
				if int(m.group(5), 0) <= 15:
					mode += "NEAR"
					near = True
					r_op = m.group(5)
				elif int(m.group(5), 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
					
				else:
					mode += "FAR"
					offset = m.group(5)
			else:
				mode += "FAR"
				offset = m.group(5)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8((self.MODES[mode] << 4) | (int(r_op) if near else self.REGISTERS[r_op]))
		self.push8((self.REGISTERS[r_src] << 4) | self.REGISTERS[r_dest])
		self.inst_addr += 1
		if addr != '':
			self.push24(int(addr, 0))
			self.inst_addr += 1
		if offset != '':
			self.push24(int(offset, 0))
			self.inst_addr += 1



	def inst_MW(self, m):
			self.checkInCode()
			opcode = self.OPCODES['MW']
			mode = ''
			r_dest = 'A'
			r_src = 'A'
			r_op = 'A'
			addr = ''
			offset = ''
			near = False
			relative = False
					
			r_src = m.group(5).upper()
			if re.match("\[" + self.REG + "\]", m.group(2), re.IGNORECASE):
				mode += "INDIRECT"
				r_dest = re.sub('[\[\]]', '', m.group(2).upper())
			elif re.match(self.HEX, m.group(2), re.IGNORECASE):
				mode += "ABSOLUTE"
				addr = m.group(2)
			elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(2)):
				mode = "ABSOLUTE"
				self.enqueuelabel(m.group(2).strip("()"), self.inst_addr+1)
				addr = "0xdeadbe"
			
			else:
				self.printerror("Syntax error")
			

			if m.group(3) != None: # There is offset
				mode += m.group(3)
				if re.match(self.REG, m.group(4), re.IGNORECASE):
					mode += "REG"
					r_op = m.group(4).upper()
				elif re.match(self.INT, m.group(4), re.IGNORECASE):
					if int(m.group(4), 0) <= 15:
						mode += "NEAR"
						near = True
						r_op = m.group(4)
					elif int(m.group(4), 0) > self.MAX_INT:
						self.printerror("Max. offset 16777215")
					else:
						mode += "FAR"
						offset = m.group(4)
				else:
					mode += "FAR"
					offset = m.group(4)

			self.instructions.append(self.inst_addr)
			self.push8(opcode)
			self.push8((self.MODES[mode] << 4) | (int(r_op) if near else self.REGISTERS[r_op]))
			self.push8((self.REGISTERS[r_src] << 4) | self.REGISTERS[r_dest])
			self.inst_addr += 1
			if addr != '':
				self.push24(int(addr, 0))
				self.inst_addr += 1
			if offset != '':
				self.push24(int(offset, 0))
				self.inst_addr += 1



	def inst_NOP(self, m):
		self.checkInCode()
		opcode = self.OPCODES['NOP']
		self.instructions.append(self.inst_addr)
		self.push24(opcode << 16)
		self.inst_addr += 1


	def inst_POP(self, m):
		self.checkInCode()
		opcode = self.OPCODES['POP']
		r_src = 'A'
		r_dest = 'A'
		r_op = 'A'

		r_dest = m.group(2)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8(0x00)
		self.push8(self.REGISTERS[r_dest])
		self.inst_addr += 1
		
		


	def inst_PUSH(self, m):
		self.checkInCode()
		opcode = self.OPCODES['PUSH']
		r_src = 'A'
		r_dest = 'A'
		r_op = 'A'

		r_src = m.group(2)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8(0x00)
		self.push8(self.REGISTERS[r_src] << 8)
		self.inst_addr += 1
		


	def inst_RET(self, m):
		self.checkInCode()
		opcode = self.OPCODES['RET']
		self.instructions.append(self.inst_addr)
		self.push24(opcode << 16)
		self.inst_addr += 1


	def inst_VR(self, m):
		self.checkInCode()
		opcode = self.OPCODES['VR']
		mode = ''
		r_dest = 'A'
		r_src = 'A'
		r_op = 'A'
		addr = ''
		offset = ''
		near = False
		relative = False
						
		r_dest = m.group(2).upper()
		if re.match("\[" + self.REG + "\]", m.group(3), re.IGNORECASE):
			mode += "INDIRECT"
			r_dest = re.sub('[\[\]]', '',m.group(3).upper())
		elif re.match(self.HEX, m.group(3), re.IGNORECASE):
			mode += "ABSOLUTE"
			addr = m.group(3)
		elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(3)):
			mode = "ABSOLUTE"
			self.enqueuelabel(m.group(3).strip("()"), self.inst_addr+1)
			offset = "0xdeadbe"
		else:
			self.printerror("Syntax error")

			
		if (m.group(4) != None): # There is offset

			mode += m.group(4)
			if re.match(self.REG, m.group(4), re.IGNORECASE):
				mode += "REG"
				r_op = m.group(4).upper()
			elif re.match(self.INT, m.group(5), re.IGNORECASE):
				if int(m.group(5), 0) <= 15:
					mode += "NEAR"
					near = True
					r_op = m.group(5)
				elif int(m.group(5), 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
					
				else:
					mode += "FAR"
					offset = m.group(5)
			else:
				mode += "FAR"
				offset = m.group(5)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8((self.MODES[mode] << 4) | (int(r_op) if near else self.REGISTERS[r_op]))
		self.push8((self.REGISTERS[r_src] << 4) | self.REGISTERS[r_dest])
		self.inst_addr += 1
		if addr != '':
			self.push24(int(addr, 0))
			self.inst_addr += 1
		if offset != '':
			self.push24(int(offset, 0))
			self.inst_addr += 1


	def inst_VW(self, m):
		self.checkInCode()
		opcode = self.OPCODES['VW']
		mode = ''
		r_dest = 'A'
		r_src = 'A'
		r_op = 'A'
		addr = ''
		offset = ''
		near = False
		relative = False
					
		r_src = m.group(5).upper()
		if re.match("\[" + self.REG + "\]", m.group(2), re.IGNORECASE):
			mode += "INDIRECT"
			r_dest = re.sub('[\[\]]', '', m.group(2).upper())
		elif re.match(self.HEX, m.group(2), re.IGNORECASE):
			mode += "ABSOLUTE"
			addr = m.group(2)
		elif re.match("\(" + self.ALPHANUMERIC + "\)", m.group(2)):
			mode = "ABSOLUTE"
			self.enqueuelabel(m.group(2).strip("()"), self.inst_addr+1)
			addr = "0xdeadbe"
			
		else:
			self.printerror("Syntax error")
			

		if m.group(3) != None: # There is offset
			mode += m.group(3)
			if re.match(self.REG, m.group(4), re.IGNORECASE):
				mode += "REG"
				r_op = m.group(4).upper()
			elif re.match(self.INT, m.group(4), re.IGNORECASE):
				if int(m.group(4), 0) <= 15:
					mode += "NEAR"
					near = True
					r_op = m.group(4)
				elif int(m.group(4), 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
				else:
					mode += "FAR"
					offset = m.group(4)
			else:
				mode += "FAR"
				offset = m.group(4)

		self.instructions.append(self.inst_addr)
		self.push8(opcode)
		self.push8((self.MODES[mode] << 4) | (int(r_op) if near else self.REGISTERS[r_op]))
		self.push8((self.REGISTERS[r_src] << 4) | self.REGISTERS[r_dest])
		self.inst_addr += 1
		if addr != '':
			self.push24(int(addr, 0))
			self.inst_addr += 1
		if offset != '':
			self.push24(int(offset, 0))
			self.inst_addr += 1
