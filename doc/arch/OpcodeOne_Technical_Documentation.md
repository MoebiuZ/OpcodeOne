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
		* [XCHG (eXCHanGe registers)](#xchg)
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
		* [SWP (SWaP bytes)](#swp)
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
* TODO: What to do when Mode is *unused*? (Raise error - do NOP - do NOP and set special flag)
* TODO: What to do when Opcode is *unused*? (Raise error - do NOP - do NOP and set special flag)


## Registers

| Register | id   | bin  | Description      |
|----------|------|------|------------------|
| A        | 0x00 | 0000 | Generic register |
| B        | 0x01 | 0001 | Generic register |
| C        | 0x02 | 0010 | Generic register |
| D        | 0x03 | 0011 | Generic register |
| unused   | 0x04 | 0100 |                  |
| unused   | 0x05 | 0101 |                  |
| unused   | 0x06 | 0110 |                  |
| unused   | 0x07 | 0111 |                  |
| unused   | 0x08 | 1000 |                  |
| unused   | 0x09 | 1001 |                  |
| unused   | 0x0a | 1010 |                  |
| unused   | 0x0b | 1011 |                  |
| FL       | 0x0c | 1100 | Flags            |
| SB       | 0x0d | 1101 | Stack Base       |
| SP       | 0x0e | 1110 | Stack Pointer    |
| PC       | 0x0f | 1111 | Program Counter  |
		



FL (Flags)  ---> Carry, Zero, Negative, Two's complement overflow, Signed (N/V), x , x,  x


## Addressing

OpcodeOne has two 24-bit address buses, Memory Bus and Video Bus. On a *standard* use case, one is intended for RAM/ROM and the other for VRAM (Video bus), but second one can be used for any other purpose.


All instruction addressing refers to Memory bus, and Video bus is only accesable with [VR](#vr), [VW](#vw) and [MTR](#mtr) instructions.

### Memory bus

### Video bus

// TODO



## Opcode table

Note: To be rearranged


| <sub>Higher Byte</sub> |  <sub>x0</sub>   |  <sub>x1</sub>   |  <sub>x2</sub>   |  <sub>x3</sub>  |  <sub>x4</sub>   |  <sub>x5</sub>   |  <sub>x6</sub>   |  <sub>x7</sub>   |  <sub>x8</sub>   |  <sub>x9</sub>   |  <sub>xA</sub>   |  <sub>xB</sub>   |  <sub>xC</sub>   |  <sub>xD</sub>   |  <sub>xE</sub>   |  <sub>xF</sub>   |
|--------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| <sub>**0x**</sub> |  <sub>[NOP](#nop)</sub>  |  <sub>[HALT](#halt)</sub> |  <sub>[MR](#mr)</sub>   |  <sub>[MW](#mw)</sub>   |  <sub>[VR](#vr)</sub>  |  <sub>[VW](#vw)</sub>   |  <sub>[PUSH](#push)</sub> |  <sub>[POP](#pop)</sub>  |  <sub>[JMP](#jmp)</sub>  |  <sub>[RET](#ret)</sub>  |  <sub>[ADD](#add)</sub>  |  <sub>[SUB](#sub)</sub>  |  <sub>[MUL](#mul)</sub>  |  <sub>[DIV](#div)</sub>  |  <sub>[AND](#and)</sub>  |  <sub>[OR](#or)</sub>   |
| <sub>**1x**</sub> |  <sub>[XOR](#xor)</sub>  |  <sub>[NAND](#nand)</sub> |  <sub>[NEG](#neg)</sub>  |  <sub>[IN](#in)</sub>   |  <sub>[OUT](#out)</sub>  |  <sub>[LD](#ld)</sub>   |  <sub>[CP](#cp)</sub>   |  <sub>[CMP](#cmp)</sub>  |  <sub>[RL](#rl)</sub>   |  <sub>[RR](#rr)</sub>   |  <sub>[SL](#sl)</sub>   |  <sub>[SR](#sr)</sub>   |  <sub>[INC](#inc)</sub>  |  <sub>[DEC](#dec)</sub>  |  <sub>[CALL](#call)</sub> |  <sub>[MTR](#mtr)</sub>  |
| <sub>**2x**</sub> | <sub>[BIT](#bit)</sub>  | <sub>[SWP](#swp)</sub>      | <sub>[XCHG](#xchg)</sub>      |       |       |       |       |       |       |       |       |       |       |       |       |       |
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




*MR* 
---
**M**emory **R**ead

**Reads a word from [*memory bus*](#memory-bus) into a [*register*](#registers).**

| Opcode | - |
|--------|---|
| 00000010 | 0x02 |



| Mode | Operation | Instruction size |
|------|-----------|------------------|
| 0000 | [Indirect](#mr_indirect_mode) | 3 bytes (1 word) |
| 0001 | [Indirect plus short offset](#mr_indirect_plus_short_offset_mode) | 3 bytes (1 words) |
| 0010 | [Indirect plus register offset](#mr_indirect_plus_register_offset_mode) | 3 bytes (1 words) |
| 0011 | [Indirect plus immediate offset](#mr_indirect_plus_immediate_offset_mode) | 6 bytes (2 words) |
| 0100 | [Indirect minus short offset](#mr_indirect_minus_short_offset_mode) | 3 bytes (1 words) |
| 0101 | [Indirect minus register offset](#mr_indirect_minus_register_offset_mode) | 3 bytes (1 words) |
| 0110 | [Indirect minus immediate offset](#mr_indirect_plus_immediate_offset_mode) | 6 bytes (2 words) |
| 0111 | [Absolute](#mr_absolute_mode) | 6 bytes (2 words) |
| 1000 | [Absolute plus short offset](#mr_absolute_plus_short_offset_mode) | 6 bytes (2 words) |
| 1001 | [Absolute plus register offset](#mr_absolute_plus_register_offset_mode) | 6 bytes (2 words) |
| 1010 | [Absolute plus immediate offset](#mr_absolute_plus_immediate_offset_mode) | 9 bytes (3 words) |
| 1011 | [Absolute minus short offset](#mr_absolute_minus_short_offset_mode) | 6 bytes (2 words) |
| 1100 | [Absolute minus register offset](#mr_absolute_minus_register_offset_mode) | 6 bytes (2 words) |
| 1101 | [Absolute minus immediate offset](#mr_absolute_minus_immediate_offset_mode) | 9 bytes (3 words) |
| 1110 | Unused | N/A |
| 1111 | Unused | N/A |


#### _(MR) Indirect mode_

	MR %dst, [%src]

Reads from the address specified by `%src` register into `%dst` register.


| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     |
|----------|------|----------|-----------|------------|
| 00000010 | 0000 | xxxx     | xxxx      | xxxx       |
Example:
><sub>Read a word from the address specified by %C into %A</sub>
>
>`MR %A, [%C]`



#### _(MR) Indirect plus short offset mode_

	MR %dst, [%src]+short_offset

Reads from the address specified by `%src` register plus a short 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0001 | xxxx     | xxxx      | xxxx       |
Example:
><sub>Read a word from the address specified by %B plus 3 into %C</sub>
>
>`MR %C, [%B]+3`

	

#### _(MR) Indirect plus register offset mode_

	MR %dst, [%src]+%offset

Reads from the address specified by `%src` register plus an offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset Reg |
|----------|------|----------|-----------|------------|
| 00000010 | 0010 | xxxx     | xxxx      | xxxx       |
Example:
><sub>Read a word from the address specified by %D plus offset specified by %B into %A</sub>
>
>`MR %A, [%D]+%B`



#### _(MR) Indirect plus immediate offset mode_

	MR %dst, [%src]+imm_offset

Reads from the address specified by `%src` register plus an immediate 24-bit offset into `%dst` register

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Immediate offset              |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |
Example:
><sub>Read a word from the address specified by %C plus 1337 into %A</sub>
>
>`MR %A, [%C]+1337`
>`MR %A, [%C]+0x539`



#### _(MR) Indirect minus short offset mode_

	MR %dst, [%src]-short_offset

Reads from the address specified by `%src` register minus a short 4-bit *offset* into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     |
|----------|------|----------|-----------|------------|
| 00000010 | 0100 | xxxx     | xxxx      | xxxx       |



#### _(MR) Indirect minus register offset mode_

	MR %dst, [%src]-%offset	

Reads from the address specified by `%src` register minus an offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset Reg |
|----------|------|----------|-----------|------------|
| 00000010 | 0101 | xxxx     | xxxx      | xxxx       |



#### _(MR) Indirect plus immediate offset mode_

	MR %dst, [%src]-imm_offset

Reads from the address specified by `%src` register minus an immediate 24-bit offset into `%dst` register

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Immediate Offset              |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0110 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |



#### _(MR) Absolute mode_

	MR %dst, addr

Reads from address into `%dst`register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 0111 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |



#### _(MR) Absolute plus short offset mode_

	MR %dst, addr+short_offset

Reads from address plus short 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1000 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |



#### _(MR) Absolute plus register offset mode_

	MR %dst, addr+%offset

Reads from address plus offset specified by `%offset` register into `%dst`register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset Reg | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1001 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |



#### _(MR) Absolute plus immediate offset mode_

	MR %dst, addr+imm_offset

Reads from address plus an immediate 24-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Immediate Offset              |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1010 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |



#### _(MR) Absolute minus short offset mode_

	MR %dst, addr-short_offset

Reads from address plus a short 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Offset     | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1011 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |




#### _(MR) Absolute minus register offset mode_

	MR %dst, addr-%offset

Reads from address minus offset specified by `%offset` register into `%dst`register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Off Reg    | Address                       |
|----------|------|----------|-----------|------------|-------------------------------|
| 00000010 | 1100 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |




#### _(MR) Absolute minus immediate offset mode_

	MR %dst, addr-imm_offset

Reads from address minus an immediate 24-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg  | Src Reg   | Unused     | Address                       | Offset                        |
|----------|------|----------|-----------|------------|-------------------------------|-------------------------------|
| 00000010 | 1101 | xxxx     | xxxx      | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |









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

// TODO: What to do when number (#) is 24-31? Should we use Mode to specify High-Medium-Lower byte and use 3 bits (0-7) for number?

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


#### SWP

// TODO: Rethink this opcode and its usefulness

Swaps 2 bytes on a register (High-Low, High-Medium, Medium-Low)

	SWP{HM} %dst
	SWP{HL} %dst
	SWP{ML} %dst

Swaps 2 nibbles on a register, where *x* and *y* are nibble number (0-5)

	SWP{Nxy} %dst




#### XCHG

	XCHG %dst, %src


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

