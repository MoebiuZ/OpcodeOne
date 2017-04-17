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
		* [MTR (Memory TRansfer)](#mtr)
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
	* Rotate, Shift and Bit manipulation
		* [RL (Rotate Left)](#rl)
		* [RR (Rotate Right)](#rr)
		* [SL (Shift Left)](#sl)
		* [SR (Shift Right)](#sr)
		* [BIT (single BIT operations](#bit)
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
* TODO: What to do when Mode is not in table?


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


|        |  <sub>x0</sub>   |  <sub>x1</sub>   |  <sub>x2</sub>   |  <sub>x3</sub>  |  <sub>x4</sub>   |  <sub>x5</sub>   |  <sub>x6</sub>   |  <sub>x7</sub>   |  <sub>x8</sub>   |  <sub>x9</sub>   |  <sub>xA</sub>   |  <sub>xB</sub>   |  <sub>xC</sub>   |  <sub>xD</sub>   |  <sub>xE</sub>   |  <sub>xF</sub>   |
|--------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| <sub>**0x**</sub> |  <sub>[NOP](#nop)</sub>  |  <sub>[HALT](#halt)</sub> |  <sub>[MR](#mr)</sub>   |  <sub>[MW](#mw)</sub>   |  <sub>[VR](#vr)</sub>  |  <sub>[VW](#vw)</sub>   |  <sub>[PUSH](#push)</sub> |  <sub>[POP](#pop)</sub>  |  <sub>[JMP](#jmp)</sub>  |  <sub>[RET](#ret)</sub>  |  <sub>[ADD](#add)</sub>  |  <sub>[SUB](#sub)</sub>  |  <sub>[MUL](#mul)</sub>  |  <sub>[DIV](#div)</sub>  |  <sub>[AND](#and)</sub>  |  <sub>[OR](#or)</sub>   |
| <sub>**1x**</sub> |  <sub>[XOR](#xor)</sub>  |  <sub>[NAND](#nand)</sub> |  <sub>[NEG](#neg)</sub>  |  <sub>[IN](#in)</sub>   |  <sub>[OUT](#out)</sub>  |  <sub>[LD](#ld)</sub>   |  <sub>[CP](#cp)</sub>   |  <sub>[CMP](#cmp)</sub>  |  <sub>[RL](#rl)</sub>   |  <sub>[RR](#rr)</sub>   |  <sub>[SL](#sl)</sub>   |  <sub>[SR](#sr)</sub>   |  <sub>[INC](#inc)</sub>  |  <sub>[DEC](#dec)</sub>  |  <sub>[CALL](#call)</sub> |  <sub>[MTR](#mtr)</sub>  |
| <sub>**2x**</sub> | <sub>[BIT](#bit)</sub>  |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**3x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**4x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**5x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**6x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**7x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**8x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**9x**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Ax**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Bx**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Cx**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Dx**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Ex**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |
| <sub>**Fx**</sub> |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |       |



## Assembly syntax

* Arguments are comma (**,**) separated, except when different parameters *group* as a single argument (ie.: LD or PUSH)
* **%** indicates a register
* **[]** indicates an offset
* Numbers can be expressed as decimal or hexadecimal (starting with 0x)
* **{}** indicates **flags**, **conditions** or **operation type** (ie.: conditions in JMP, *with carry* in arithmetical operations or *direction" in MTR)



## O¹ instruction set

Notes: 

* All non specified instructions will default to "NOP" (ie: Non existant opcodes or existing opcodes with unused Mode)




#### MR

Reads a word from memory to a register.


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     |
|----------|------|----------|-----------|------------|
| 00000010 | 0000 | xxxx     | xxxx      | xxxx       |


	MR %dst, [%src]


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0001 | xxxx     | xxxx      | xxxx       |

	
	MR %dst, [%src]+near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000010 | 0010 | xxxx     | xxxx      | xxxx       |


	MR %dst, [%src]+%offset

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, [%src]+far_offset



| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0100 | xxxx     | xxxx      | xxxx       |


	MR %dst, [%src]-near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000010 | 0101 | xxxx     | xxxx      | xxxx       |


	MR %dst, [%src]-%offset	


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0110 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, [%src]-far_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0111 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr+near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1001 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr+%offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1010 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr+far_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr-near_offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1100 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr-%offset


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1101 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MR %dst, addr-far_offset






#### MW

Writes a word from a register into memory


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     |
|----------|------|----------|-----------|------------|
| 00000011 | 0000 | xxxx     | xxxx      | xxxx       |


	MW [%dst], %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000011 | 0001 | xxxx     | xxxx      | xxxx       |

	
	MW [%dst]+near_offset, %R


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000011 | 0010 | xxxx     | xxxx      | xxxx       |


	MW [%dst]+%offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW [%dst]+far_offset, %src



| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000011 | 0100 | xxxx     | xxxx      | xxxx       |


	MW [%dst]-near_offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    |
|----------|------|----------|-----------|------------|
| 00000011 | 0101 | xxxx     | xxxx      | xxxx       |


	MW [%dst]-%offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0110 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW [%dst]-far_offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 0111 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+near_offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1001 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+%dst, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000011 | 1010 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr+far_offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-near_offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000011 | 1100 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-%offset, %src


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000011 | 1101 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


	MW addr-far_offset, %src


#### VR

#### VW

#### MTR

Copies a word from Memory to Video memory 

| Opcode   | Mode | Dst addr reg | Src addr reg  | Unused     |
|----------|------|--------------|---------------|------------|
| 00000xxx | 0000 | xxxx         | xxxx          | xxxx       |

	MTR{V} [%dst], [%src]


Copies a word from Video Memory to Memory 

| Opcode   | Mode | Dst addr reg | Src addr reg | Unused     |
|----------|------|--------------|--------------|------------|
| 00000xxx | 0001 | xxxx         | xxxx         | xxxx       |

	MTR{M} [%dst], [%src]


Exchanges a word between Memory and Video Memory

| Opcode   | Mode | Dst addr reg | Src addr reg | Unused     |
|----------|------|--------------|--------------|------------|
| 00000xxx | 0010 | xxxx         | xxxx         | xxxx       |

	MTR{X} [%dst], [%src]



#### AND

Performs a logical AND between 2 source registers and stores the result in destination register

| Opcode   | Unused | Dst Reg  | Src Reg1  | Src Reg2     |
|----------|--------|----------|-----------|--------------|
| 00000100 | xxxx   | xxxx     | xxxx      | xxxx         |

	AND %dst, %src1, %src2


#### OR

	OR %dst, %src1, %src2

#### XOR

	XOR %dst, %src1, %src2

#### NEG

	NEG %dst, %src

#### NAND

	NAND %dst, %src1, %src2

#### INC
	
	INC %dst

#### DEC

	DEC %dst

#### ADD

	ADD %dst, %src1, %src2
	ADD{C} %dst, %src1, %src1


#### SUB

	SUB %dst, %min, %subtr
	SUB{C} %dst, %min, %subtr
    
#### MUL

	MUL %dst, %src1, %src2
 	MUL{C} %dst, %src1, %src2

#### DIV

	DIV %dst, %num, %denom

#### PUSH

	PUSH %src1 
   	PUSH %src1 %src2
   	PUSH %src1 %src2 %src3

#### POP

   	POP %dst1
   	POP %dst1 %dst2 
   	POP %dst1 %dst2 %dst3


#### RL

#### RR

#### SL

#### SR


#### BIT

// TODO: What to do when number (#) is 24-31?

Sets bit number # on register

| Opcode   | Mode    | Dst reg  | Unused  | Number  |
|----------|---------|----------|---------|---------|
| 0000xxxx | 0000    | xxxx     | xxx     | xxxxx   |

	BIT{S} %dst, #(0-24)


Resets bit number # on register

| Opcode   | Mode    | Dst reg  | Unused  | Number  |
|----------|---------|----------|---------|---------|
| 0000xxxx | 0001    | xxxx     | xxx     | xxxxx   |

	BIT{R} %dst, #(0-24)


Tests bit number # on register and sets Z flag accordingly.

| Opcode   | Mode    | Dst reg  | Src Reg | Number  |
|----------|---------|----------|---------|---------|
| 0000xxxx | 0010    | xxxx     | xxxx    | xxxxx   |

	BIT{T} %dst, #(0-24)


#### CMP


#### LD
	
	Loads an inmediate value into a register/s

| Opcode   | Mode | Dst Reg  | Unused    | Unused     | Value                         |
|----------|------|----------|-----------|------------|-------------------------------|
| 0000xxxx | 0000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

	LD %dst, 0xdeadbe


| Opcode   | Mode | Dst Reg1 | Dst reg2 | Unused     | Value                         |
|----------|------|----------|----------|------------|-------------------------------|
| 0000xxxx | 0001 | xxxx     | xxxx     | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

	LD %dst1 %dst2, 0xdeadbe


| Opcode   | Mode | Dst Reg1 | Dst reg2 | Dst reg3 | Value                         |
|----------|------|----------|----------|----------|-------------------------------|
| 0000xxxx | 0010 | xxxx     | xxxx     | xxxx     | xxxx xxxx xxxx xxxx xxxx xxxx |


	LD %dst1 %dst2 %dst3, 0xdeadbe


#### CP
	
	Copies a register into another

| Opcode   | Unused  | Dst reg  | Src Reg | Unused |
|----------|---------|----------|---------|--------|
| 0000xxxx | xxxx    | xxxx     | xxxx    | xxxx   |

	CP %dst, %src


#### IN

#### OUT

#### JMP

#### CALL

#### RET

#### NOP

Does nothing (No Operation)

| Opcode   | Unused            |
|----------|-------------------|
| 00000000 | xxxxxxxx xxxxxxxx |

	NOP


#### HALT

Halts the CPU

| Opcode   | Unused            |
|----------|-------------------|
| 0000xxxx | xxxxxxxx xxxxxxxx |
	
	HALT

