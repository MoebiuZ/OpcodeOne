OpcodeOne (O¹) Technical Documentation (DRAFT) v0.0.1
=====================================================



## Table of contents

* [Preliminary notes](#preliminary-notes)
* [Registers](#registers)
* Status flags
* [Addressing](#addressing)
* [Opcode table](#opcode-table)
* [Assembly syntax](#assembly-syntax)
* [O¹ Instruction set](#o-instruction-set)
	* Load and Exchange
		* [LD (LoaD)](#ld)
		* [CP (CoPy)](3cp)
		* [MR (Memory Read)](#mr)
		* [MW (Memory Write)](#mw)
		* [VR (Video memory Read)](#vr)
		* [VW (Video memory Write)](#vw)
		* [PUSH](#push)
		* [POP](#pop)
	* Arithmetic and Logical
		* [ADD (ADDition)](#add)
		* [SUB (SUBstraction)](#sub)
		* [MUL (MULtiplication)](#mul)
		* [DIV (DIVision)](#div)
		* [INC (INCrement)](#inc)
		* [DEC (DECrement)](#dec)
		* [AND (logical AND)](#and)
		* [OR (logical OR)](#or)
		* [XOR (logical XOR)](#xor)
		* [NAND (logical NAND)](#nand)
		* [NEG (NEGative - two's complement)](#neg)
		* [CMP (CoMPare)](#cmp)
	* Rotate and Shift
		* [RL (Rotate Left)](#rl)
		* [RR (Rotate Right)](#rr)
		* [SL (Shift Left)](#sl)
		* [SR (Shift Right)](#sr)
	* Bit manipulation
	* Jump
		* [JMP (JuMP)](#jmp)
		* [CALL (CALL subroutine)](#call)
		* [RET (RETurn)](#ret)
	* Input/Output
		* [IN (INput)](#in)
		* [OUT (OUTput)](#out)
	* CPU control
		* [NOP (No OPeration)](#nop)
		* [HALT (HALT machine)](#halt)





## Preliminary notes

* Word size is 24 bits, and is the minimum data unit (for the moment).
* This first draft probably wastes a lot of "data" being 8 bit each opcode (256 possible opcodes). This could be redesigned in the future, or using the empty opcodes to implement complex "non-standard" instructions.
* Each instruction "cycles consumed" or "instruction speed" will be determined with benchmarks once implemented, and the derived value will be used for this specification.
* Little endian architecture (for the moment)


## Registers

| Register | id   | Description
|----------|------|------------------|
| A        | 0x00 | Generic register |
| B        | 0x01 | Generic register |
| C        | 0x02 | Generic register |
| D        | 0x03 | Generic register |
| unused   | 0x04 |                  |
| unused   | 0x05 |                  |
| unused   | 0x06 |                  |
| unused   | 0x07 |                  |
| unused   | 0x08 |                  |
| unused   | 0x09 |                  |
| unused   | 0x0a |                  |
| unused   | 0x0b |                  |
| FL       | 0x0c | Flags            |
| SB       | 0x0d | Stack Base       |
| SP       | 0x0e | Stack Pointer    |
| PC       | 0x0f | Program Counter  |
		



FL (Flags)  ---> Carry, Zero, Negative, Two's complement overflow, Signed (N/V), x , x,  x


## Addressing

// TODO

OpcodeOne has two 24-bit address buses, one intended for RAM (manipulated with MR & MW instructions) and one intended for VRAM (manipulated with VR & VW instructions). Second one is designed to interact with video memory (for example, as a framebuffer), but it's possible to use it as a secondary RAM.


## Opcode table

Note: To be rearranged


|        |  x0   |  x1   |  x2   |  x3   |  x4   |  x5   |  x6   |  x7   |  x8   |  x9   |  xA   |  xB   |  xC   |  xD   |  xE   |  xF   |
|--------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| **0x** |  [NOP](#nop)  |  [HALT](#halt) |  [MR](#mr)   |  [MW](#mw)   |  [VR](#vr)  |  [VW](#vw)   |  [PUSH](#push) |  [POP](#pop)  |  [JMP](#jmp)  |  [RET](#ret)  |  [ADD](#add)  |  [SUB](#sub)  |  [MUL](#mul)  |  [DIV](#div)  |  [AND](#and)  |  [OR](#or)   |
| **1x** |  [XOR](#xor)  |  [NAND](#nand) |  [NEG](#neg)  |  [IN](#in)   |  [OUT](#out)  |  [LD](#ld)   |  [CP](#cp)   |  [CMP](#cmp)  |  [RL](#rl)   |  [RR](#rr)   |  [SL](#sl)   |  [SR](#sr)   |  [INC](#inc)  |  [DEC](#dec)  |  [CALL](#call) |       |
| **2x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **3x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **4x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **5x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **6x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **7x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **8x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **9x** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Ax** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Bx** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Cx** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Dx** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Ex** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| **Fx** |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |



## Assembly syntax

* Arguments are comma (**,**) separated
* **%** indicates a register
* **[]** indicates an offset
* Numbers can be expressed as decimal or hexadecimal (starting with 0x)
* **{}** indicates **flags** or **conditions** (ie.: conditions in JMP or *with carry* in arithmetical operations)



## O¹ instruction set

Notes: 

* All non specified instructions will default to "NOP" (ie: Non existant opcodes or existing opcodes with unused Mode)




#### MR

Reads a word from memory to a register.


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     |
|----------|------|----------|-----------|------------|
| 00000010 | 0000 | xxxx     | xxxx      | xxxx       |


	MR %R, [%R]


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0001 | xxxx     | xxxx      | xxxx       |

	
	MR %R, [%R]+near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000010 | 0010 | xxxx     | xxxx      | xxxx       |


	MR %R, [%R]+%R

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, [%R]+far_offset



| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0100 | xxxx     | xxxx      | xxxx       |


	MR %R, [%R]-near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000010 | 0101 | xxxx     | xxxx      | xxxx       |


	MR %R, [%R]-%R	


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0110 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, [%R]-far_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0111 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr+near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1001 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr+%R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1010 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr+far_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr-near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1100 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr-%R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1101 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %R, addr-far_offset






#### MW

Writes a word from a register into memory


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     |
|----------|------|----------|-----------|------------|
| 00000011 | 0000 | xxxx     | xxxx      | xxxx       |


	MW [%R], %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000011 | 0001 | xxxx     | xxxx      | xxxx       |

	
	MW [%R]+near_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000011 | 0010 | xxxx     | xxxx      | xxxx       |


	MW [%R]+%R, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW [%R]+far_offset, %R



| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000011 | 0100 | xxxx     | xxxx      | xxxx       |


	MW [%R]-near_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000011 | 0101 | xxxx     | xxxx      | xxxx       |


	MW [%R]-%R, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0110 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW [%R]-far_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0111 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+near_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1001 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+%R, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000011 | 1010 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+far_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-near_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1100 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-%R, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000011 | 1101 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-far_offset, %R


#### VR

#### VW


#### AND

Performs a logical AND between 2 source registers and stores the result in destination register

| Opcode   | Unused | Dst Reg  | Src Reg1  | Src Reg2     |
|----------|--------|----------|-----------|--------------|
| 00000100 | xxxx   | xxxx     | xxxx      | xxxx         |

	AND %R, %R, %R


#### OR

	OR %R, %R, %R

#### XOR

	XOR %R, %R, %R

#### NEG

	NEG %R, %R

#### NAND

	NAND %R, %R, %R

#### INC
	
	INC %R

#### DEC

	DEC %R

#### ADD

	ADD %R, %R, %R
	ADD{C} %R, %R, %R


#### SUB

	SUB %R, %R, %R
	SUB{C} %R, %R, %R
    
#### MUL

	MUL %R, %R, %R
 	MUL{C} %R, %R, %R

#### DIV

	DIV %R, %R, %R

#### PUSH

	PUSH %R 
   	PUSH %R %R
   	PUSH %R %R %R

#### POP

   	POP %R
   	POP %R %R 
   	POP %R %R %R


#### RL

#### RR

#### SL

#### SR


#### CMP


#### LD
	
	Loads a inmediate value into a register

	LD %R, 0xdeadbe

#### CP
	
	Copies a register into another

	CP %R, %R

#### IN

#### OUT

#### JMP

#### CALL

#### RET

#### NOP

| Opcode   | Unused            |
|----------|-------------------|
| 00000000 | xxxxxxxx xxxxxxxx |

	NOP


#### HALT



