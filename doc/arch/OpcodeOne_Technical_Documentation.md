OpcodeOne (O¹) Technical Documentation (DRAFT) v0.0.1
=====================================================



## Table of contents

* [Preliminary notes](#preliminary-notes)
* [CPU pin out](#cpu-pin-out)
* [Registers](#registers)
* [Status flags](#status-flags)
* [Addressing](#addressing)
* [Interruptions](#interruptions)
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
		* [ROT (ROTate)](#rot)
		* [SH (SHift)](#sh)
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


***

## Preliminary notes

* Word size is 24 bits, and is the minimum data unit (for the moment).
* This first draft probably "wastes" a lot of "data" being 8 bit each opcode (256 possible opcodes). This could be redesigned in the future, or using the empty opcodes to implement complex "non-standard" instructions.
* Each instruction "cycles consumed" or "instruction speed" will be determined with benchmarks once implemented, and the derived value will be used for this specification.
* Little endian architecture (for the moment)
* TODO: What to do when Mode is *unused*? (Raise error - do NOP - do NOP and set special flag)
* TODO: What to do when Opcode is *unused*? (Raise error - do NOP - do NOP and set special flag)

***

## CPU pin out

```

                        ___   +----------------------------------+
                        HLT <-|                                  |-> MB0          -+
                        ___   |                                  |-> MB1           |
                        RST ->|                                  |   ...           | Memory bus
                              |            _--------_            |-> MB22          |
                              |           +  O¹ CPU  +           |-> MB23         -+                  
               +-      IO0 <->|            ¯--------¯            |
               |       IO1 <->|                                  |
 Input/Output  |        ...   |                                  |
     bus       |      IO22 <->|                                  |
               +-     IO23 <->|                                  |
                              |                                  |
                        ___   |                                  |                  
                        IRQ ->|                                  |-> VB0          -+
                        ___   |                                  |-> VB1           |
                        NMI ->|                                  |   ...           | Video bus
                              |                          TDI [ ] |-> VB22          |
                              |                          TDO [ ] |-> VB23         -+
                              |                          TCK [ ] |
                              |                          TMS [ ] |
                        CLK ->|                         TRST [ ] |           
                              +----------------------------------+
      

      
```

***

## Registers

All O¹ registers are 24-bits wide.

The following table shows the available registers and their binary encoding withing instructions.

| Register | id   | bin  | Description      | Access     |
|----------|------|------|------------------|------------|
| A        | 0x00 | 0000 | Generic register | Read/Write |
| B        | 0x01 | 0001 | Generic register | Read/Write |
| C        | 0x02 | 0010 | Generic register | Read/Write |
| D        | 0x03 | 0011 | Generic register | Read/Write |
| unused   | 0x04 | 0100 | To be defined    | N/A        |
| unused   | 0x05 | 0101 | To be defined    | N/A        |
| unused   | 0x06 | 0110 | To be defined    | N/A        |
| unused   | 0x07 | 0111 | To be defined    | N/A        |
| unused   | 0x08 | 1000 | To be defined    | N/A        |
| unused   | 0x09 | 1001 | To be defined    | N/A        |
| unused   | 0x0a | 1010 | To be defined    | N/A        |
| unused   | 0x0b | 1011 | To be defined    | N/A        |
| FL       | 0x0c | 1100 | Flags            | Read-only  |
| SB       | 0x0d | 1101 | Stack Base       | Read/Write |
| SP       | 0x0e | 1110 | Stack Pointer    | Read/Write |
| PC       | 0x0f | 1111 | Program Counter  | Read/Write |
		
***

## Status flags

Status flags are stored in the FL register.  
Flags marked as *exposed* means there is a hardware pin that outputs its status.


| Bit | Name | Description | Exposed | 
|-----|------|-------------|---------|
| 23  | II   | [Invalid Instruction](#invalid-instruction-ii-flag) | Yes |
| 6   | Z    | [Zero](#zero-z-flag) | No |
| 4   | SB   | [Subtraction](#subtraction-sb-flag) | No |
| 3   | P    | [Parity](#parity-p-flag) | No |
| 2   | V    | [Overflow](#overflow-v-flag) | No |
| 1   | S    | [Sign](#sign-s-flag) | No |
| 0   | C    | [Carry](#carry-c-flag) | No |


**FL register**  

| <sub><sup>23</sup></sub></sub> | <sub><sup>22</sup></sub> | <sub><sup>21</sup></sub> | <sub><sup>20</sup></sub> | <sub><sup>19</sup></sub> | <sub><sup>18</sup></sub> | <sub><sup>17</sup></sub> | <sub><sup>16</sup></sub> | <sub><sup>15</sup></sub> | <sub><sup>14</sup></sub> | <sub><sup>13</sup></sub> | <sub><sup>12</sup></sub> | <sub><sup>11</sup></sub> | <sub><sup>10</sup></sub> | <sub><sup>9</sup></sub> | <sub><sup>8</sup></sub> | <sub><sup>7</sup></sub> | <sub><sup>6</sup></sub> | <sub><sup>5</sup></sub> | <sub><sup>4</sup></sub> | <sub><sup>3</sup></sub> | <sub><sup>2</sup></sub> | <sub><sup>1</sup></sub> | <sub><sup>0</sup></sub> |
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| <sub><sup>II</sup></sub>  |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    | <sub><sup>Z</sup></sub> | <sub><sup>SB</sup></sub> | <sub><sup>P</sup></sub> | <sub><sup>V<sub></sub> | <sub><sup>S</sup></sub> | <sub><sup>C</sup></sub> |


#### _Invalid Instruction (II) flag_

This flag is set if the last instruction was invalid.  
This happens when the Opcode or Mode encoded in the instruction doesn't exist.

#### _Zero (Z) flag_

This flag is set if the last operation value was zero.

#### _Subtraction (SB) flag_

This flag is set if the last operation was a subtraction.

#### _Parity (P) flag_

This flag is set if the last operation has set an even number of bits.

#### _Overflow (V) flag_

This flag is set if a 2-complement result doesn't fit a register.

#### _Sign (S) flag_

This flag is set if a 2-complement value is negative.

#### _Carry (C) flag_

This flag is set if last operation result did not fit in a register.


***

## Addressing

OpcodeOne has two 24-bit address buses, Memory bus and Video bus. For a *standard* use case, one is intended for RAM/ROM and the other for VRAM (Video bus), but second one can be used for any other purpose.  
All instructions addressing refer to [Memory bus](#memory-bus), and [Video bus](#video-bus) is only accessible with [`VR`](#vr), [`VW`](#vw) and [`MTR`](#mtr) instructions.


### Memory bus

// TODO

### Video bus

// TODO

***

## Interruptions

// TODO


***


## Opcode table

Most significative byte of an instruction indicates the code of operation (opcode).  
The following table illustrates all opcodes with their hexadecimal representation.  
<sub>Note: The opcode order and their hex value is subject to be rearranged.</sub>


| <sub>Higher Byte</sub> |  <sub>x0</sub>   |  <sub>x1</sub>   |  <sub>x2</sub>   |  <sub>x3</sub>  |  <sub>x4</sub>   |  <sub>x5</sub>   |  <sub>x6</sub>   |  <sub>x7</sub>   |  <sub>x8</sub>   |  <sub>x9</sub>   |  <sub>xA</sub>   |  <sub>xB</sub>   |  <sub>xC</sub>   |  <sub>xD</sub>   |  <sub>xE</sub>   |  <sub>xF</sub>   |
|--------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| <sub>**0x**</sub> |  <sub>[NOP](#nop)</sub>  |  <sub>[HALT](#halt)</sub> |  <sub>[MR](#mr)</sub>   |  <sub>[MW](#mw)</sub>   |  <sub>[VR](#vr)</sub>  |  <sub>[VW](#vw)</sub>   |  <sub>[PUSH](#push)</sub> |  <sub>[POP](#pop)</sub>  |  <sub>[JMP](#jmp)</sub>  |  <sub>[RET](#ret)</sub>  |  <sub>[ADD](#add)</sub>  |  <sub>[SUB](#sub)</sub>  |  <sub>[MUL](#mul)</sub>  |  <sub>[DIV](#div)</sub>  |  <sub>[AND](#and)</sub>  |  <sub>[OR](#or)</sub>   |
| <sub>**1x**</sub> |  <sub>[XOR](#xor)</sub>  |  <sub>[NAND](#nand)</sub> |  <sub>[NEG](#neg)</sub>  |  <sub>[IN](#in)</sub>   |  <sub>[OUT](#out)</sub>  |  <sub>[LD](#ld)</sub>   |  <sub>[CP](#cp)</sub>   |  <sub>[CMP](#cmp)</sub>  |  <sub>[ROT](#rot)</sub>   | <sub>[SH](#sh)</sub>  |  <sub>[INC](#inc)</sub>  |  <sub>[DEC](#dec)</sub>  |  <sub>[CALL](#call)</sub> |  <sub>[MTR](#mtr)</sub>  | <sub>[BIT](#bit)</sub>  | <sub>[SWP](#swp)</sub> | 
| <sub>**2x**</sub> | <sub>[XCHG](#xchg)</sub>  |   |  |    |       |       |       |       |       |       |       |       |       |       |       |       |
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

***

## Assembly syntax

* Arguments are comma (**,**) separated, except when different parameters *group* as a single argument (ie.: [`LD`](#ld) or [`PUSH`](#push))
* **%** indicates a register
* **[]** indicates a register is treated as an address
* **#** indicates a numerical parameter, and it will be expresed in a decimal (ie: [`ROT`](#rot)`{R} %C, #3`) 
* Numbers (as immediate values) can be expressed in decimal or hexadecimal (starting with 0x)
* Absolute addresses are expresed in hexadecimal.
* **{}** indicates **operation type** (ie.: conditions in [`JMP`](#jmp), *with carry* in arithmetical operations or *direction* in [`MTR`](#mtr))

***

## O¹ instruction set


Legend:

* **x** represents a variable parameter. It's value will indicate a different register o operation mode (it will be considered a different instruction depending on it's value).
* **\*** means the value will not affect the instruction behaviour (the instruction will be the same regardless of it's value).


*MR* 
---
**M**emory **R**ead

**Reads a word from [*Memory bus*](#memory-bus) into a [*register*](#registers).**

| Opcode | - |
|--------|---|
| 00000010 | 0x02 |



| Mode | Operation | Instruction size | Cycles |
|------|-----------|------------------|--------|
| 0000 | [Indirect](#mr-indirect-mode) | 3 bytes (1 word) | |
| 0001 | [Indirect plus immediate offset](#mr-indirect-plus-immediate-offset-mode) | 3 bytes (1 word) | |
| 0010 | [Indirect plus register offset](#mr-indirect-plus-register-offset-mode) | 3 bytes (1 word) | |
| 0011 | [Indirect plus offset](#mr-indirect-plus-offset-mode) | 6 bytes (2 words) | |
| 0100 | [Indirect minus immediate offset](#mr-indirect-minus-immediate-offset-mode) | 3 bytes (1 word) | |
| 0101 | [Indirect minus register offset](#mr-indirect-minus-register-offset-mode) | 3 bytes (1 word) | |
| 0110 | [Indirect minus offset](#mr-indirect-plus-offset-mode) | 6 bytes (2 words) | |
| 0111 | [Absolute](#mr-absolute-mode) | 6 bytes (2 words) | |
| 1000 | [Absolute plus immediate offset](#mr-absolute-plus-immediate-offset-mode) | 6 bytes (2 words) | |
| 1001 | [Absolute plus register offset](#mr-absolute-plus-register-offset-mode) | 6 bytes (2 words) | |
| 1010 | [Absolute plus offset](#mr-absolute-plus-offset-mode) | 9 bytes (3 words) | |
| 1011 | [Absolute minus immediate offset](#mr-absolute-minus-immediate-offset-mode) | 6 bytes (2 words) | |
| 1100 | [Absolute minus register offset](#mr-absolute-minus-register-offset-mode) | 6 bytes (2 words) | |
| 1101 | [Absolute minus offset](#mr-absolute-minus-offset-mode) | 9 bytes (3 words) | |
| 1110 | Unused | N/A | |
| 1111 | Unused | N/A | |

&nbsp;

#### _(MR) Indirect mode_

	MR %dst, [%src]

Reads from the address specified by `%src` register into `%dst` register.


| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00000010 | 0000 | xxxx    | xxxx    | ****   |

Example:
><sub>Read a word from the address specified by %C into %A</sub>
>
>`MR %A, [%C]`

&nbsp;

#### _(MR) Indirect plus immediate offset mode_

	MR %dst, [%src]+imm_offset

Reads from the address specified by `%src` register plus an immediate 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000010 | 0001 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %B plus 3 into %C</sub>
>
>`MR %C, [%B]+3`

&nbsp;

#### _(MR) Indirect plus register offset mode_

	MR %dst, [%src]+%offset

Reads from the address specified by `%src` register plus an offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000010 | 0010 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %D plus offset specified by %B into %A</sub>
>
>`MR %A, [%D]+%B`

&nbsp;

#### _(MR) Indirect plus offset mode_

	MR %dst, [%src]+offset

Reads from the address specified by `%src` register plus a 24-bit offset into `%dst` register

| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000010 | 0011 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

Example:
><sub>Read a word from the address specified by %C plus 1337 into %A</sub>
>
>`MR %A, [%C]+1337` <sub>h(0x023020 , 0x000539) | b(00000010 0011 0000 0010 0000, 000000000000010100111001)</sub>
>
><sub>or</sub>
>
>`MR %A, [%C]+0x539` <sub>h(0x023020 , 0x000539) | b(00000010 0011 0000 0010 0000, 000000000000010100111001)</sub>

&nbsp;

#### _(MR) Indirect minus immediate offset mode_

	MR %dst, [%src]-imm_offset

Reads from the address specified by `%src` register minus an immediate  4-bit *offset* into `%dst` register.

| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000010 | 0100 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %B minus 15 into %A</sub>
>
>`MR %A, [%B]-15` <sub>h(0x02401F) | b(00000010 0100 0000 0001 1111)</sub>
>
><sub>or</sub>
>
>`MR %A, [%B]-0xf` <sub>h(0x02401F) | b(00000010 0100 0000 0001 1111)</sub>

&nbsp;

#### _(MR) Indirect minus register offset mode_

	MR %dst, [%src]-%offset	

Reads from the address specified by `%src` register minus an offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000010 | 0101 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### _(MR) Indirect plus offset mode_

	MR %dst, [%src]-offset

Reads from the address specified by `%src` register minus a 24-bit offset into `%dst` register

| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000010 | 0110 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute mode_

	MR %dst, addr

Reads from address into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       |
|----------|------|---------|--------|--------|-------------------------------|
| 00000010 | 0111 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute plus immediate offset mode_

	MR %dst, addr+imm_offset

Reads from address plus an immediate 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Imm Offset | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1000 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute plus register offset mode_

	MR %dst, addr+%offset

Reads from address plus offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Offset Reg | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1001 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute plus offset mode_

	MR %dst, addr+offset

Reads from address plus a 24-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       | Offset                        |
|----------|------|---------|--------|--------|-------------------------------|-------------------------------|
| 00000010 | 1010 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute minus immediate offset mode_

	MR %dst, addr-imm_offset

Reads from address plus an immediate 4-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Imm Offset | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1011 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute minus register offset mode_

	MR %dst, addr-%offset

Reads from address minus offset specified by `%offset` register into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Offset Reg | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1100 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MR) Absolute minus offset mode_

	MR %dst, addr-offset

Reads from address minus a 24-bit offset into `%dst` register.

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       | Offset                        |
|----------|------|---------|--------|--------|-------------------------------|-------------------------------|
| 00000010 | 1101 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |



&nbsp;

&nbsp;



*MW*
---

**M**emory **W**rite

**Writes a wrod from a [register](#registers) into [Video bus](#video-bus) address.**

| Opcode | - |
|--------|---|
| 00000010 | 0x02 |



| Mode | Operation | Instruction size | Cycles |
|------|-----------|------------------|--------|
| 0000 | [Indirect](#mw-indirect-mode) | 3 bytes (1 word) | |
| 0001 | [Indirect plus immediate offset](#mw-indirect-plus-immediate-offset-mode) | 3 bytes (1 word) | |
| 0010 | [Indirect plus register offset](#mw-indirect-plus-register-offset-mode) | 3 bytes (1 word) | |
| 0011 | [Indirect plus offset](#mw-indirect-plus-offset-mode) | 6 bytes (2 words) | |
| 0100 | [Indirect minus immediate offset](#mw-indirect-minus-immediate-offset-mode) | 3 bytes (1 word) | |
| 0101 | [Indirect minus register offset](#mw-indirect-minus-register-offset-mode) | 3 bytes (1 word) | |
| 0110 | [Indirect minus offset](#mw-indirect-plus-offset-mode) | 6 bytes (2 words) | |
| 0111 | [Absolute](#mw-absolute-mode) | 6 bytes (2 words) | |
| 1000 | [Absolute plus immediate offset](#mw-absolute-plus-immediate-offset-mode) | 6 bytes (2 words) | |
| 1001 | [Absolute plus register offset](#mw-absolute-plus-register-offset-mode) | 6 bytes (2 words) | |
| 1010 | [Absolute plus offset](#mw-absolute-plus-offset-mode) | 9 bytes (3 words) | |
| 1011 | [Absolute minus immediate offset](#mw-absolute-minus-immediate-offset-mode) | 6 bytes (2 words) | |
| 1100 | [Absolute minus register offset](#mw-absolute-minus-register-offset-mode) | 6 bytes (2 words) | |
| 1101 | [Absolute minus offset](#mw-absolute-minus-offset-mode) | 9 bytes (3 words) | |
| 1110 | Unused | N/A | |
| 1111 | Unused | N/A | |

&nbsp;

#### _(MW) Indirect mode_

	MW [%dst], %src

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00000011 | 0000 | xxxx    | xxxx    | ****   |

&nbsp;

#### _(MW) Indirect plus immediate offset mode_

	MW [%dst]+imm_offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000011 | 0001 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### _(MW) Indirect plus register offset mode_
	
	MW [%dst]+%offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000011 | 0010 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### _(MW) Indirect plus offset mode_

	MW [%dst]+offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000011 | 0011 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Indirect minus immediate offset mode_

	MW [%dst]-imm_offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000011 | 0100 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### _(MW) Indirect minus register offset mode_

	MW [%dst]-%offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000011 | 0101 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### _(MW) Indirect plus offset mode_

	MW [%dst]-offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000011 | 0110 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute mode_

	MW addr, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       |
|----------|------|--------|---------|--------|-------------------------------|
| 00000011 | 0111 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute plus immediate offset mode_

	MW addr+imm_offset, %src


| Opcode   | Mode | Unused | Src Reg | Imm Offset | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1000 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute plus register offset mode_

	MW addr+%offset, %src


| Opcode   | Mode | Unused | Src Reg | Offset Reg | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1001 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute plus offset mode_

	MW addr+offset, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       | Offset                        |
|----------|------|--------|---------|--------|-------------------------------|-------------------------------|
| 00000011 | 1010 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute minus immediate offset mode_

	MW addr-imm_offset, %src


| Opcode   | Mode | Unused | Src Reg | Imm Offset | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1011 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute minus register offset mode_

	MW addr-%offset, %src


| Opcode   | Mode | Unused | Src Reg | Offset Reg | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1100 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### _(MW) Absolute minus offset mode_

	MW addr-offset, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       | Offset                        |
|----------|------|--------|---------|--------|-------------------------------|-------------------------------|
| 00000011 | 1101 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


&nbsp;

&nbsp;

*VR*
---

**V**ideo **R**ead

**Reads a word from [Video bus](#video-bus) into a [register](#registers).**

&nbsp;

&nbsp;

*VW*
---

**V**ideo **W**rite

**Writes a word from a [register](#registers) into [Video bus](#video-bus) address.**

&nbsp;

&nbsp;

*MTR*
---

**M**emory **TR**ansfer

**Transfers a word between [Memory](#memory-bus) and [Video](#video-bus) buses.**

| Opcode | - |
|--------|---|
| 00011111 | 0x1F |

| Mode | Operation       | Instruction size | Cycles |
|------|-----------------|------------------|--------|
| 0000 | [Memory to Video](#mtr-memory-to-video) | 3 bytes (1 word) | |
| 0001 | [Video to Memory](#mtr-video-to-memory) | 3 bytes (1 word) | |
| 0010 | [Exchange](#mtr-exchange) | 3 bytes (1 word) | |
| ...  | Unused          | N/A              | |

#### _(MTR) Memory to Video_

	MTR{V} [%dst], [%src]

Copies a word from [Memory bus](#memory-bus) to [Video bus](#video-bus)

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011111 | 0000 | xxxx    | xxxx    | ****   |

&nbsp;

#### _(MTR) Video to Memory_

	MTR{M} [%dst], [%src]

Copies a word from [Video bus](#video-bus) to [Memory bus](#memory-bus)

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011111 | 0001 | xxxx    | xxxx    | ****   |

&nbsp;

#### _(MTR) Exchange_

	MTR{X} [%dst], [%src]

Exchanges a word between [Memory bus](#memory-bus) and [Video bus](#video-bus)

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011111 | 0010 | xxxx    | xxxx    | ****   |


&nbsp;

&nbsp;

*AND*
---

Logical **AND**

Performs a logical AND between 2 source registers and stores the result in destination register.

	AND %dst, %src1, %src2

| Opcode   | Unused | Dst Reg  | Src Reg1  | Src Reg2     |
|----------|--------|----------|-----------|--------------|
| 00000100 | xxxx   | xxxx     | xxxx      | xxxx         |


&nbsp;

&nbsp;

*OR*
---

Logical **OR**

	OR %dst, %src1, %src2

&nbsp;

&nbsp;

*XOR*
---

Logical **XOR**

	XOR %dst, %src1, %src2

&nbsp;

&nbsp;

*NEG*
---

**NEG**ative - Two's complement

	NEG %dst, %src

&nbsp;

&nbsp;

*NAND*
---

Logical **N**ot **AND** (NAND)

	NAND %dst, %src1, %src2

&nbsp;

&nbsp;

*INC*
---

**INC**rement

	INC %dst

&nbsp;

&nbsp;

*DEC*
---

**DEC**rement

	DEC %dst

&nbsp;

&nbsp;

*ADD*
---

**ADD**ition

	ADD %dst, %src1, %src2
	ADD{C} %dst, %src1, %src1
	ADD{U} %dst, %src1, %src2
	ADD{UC} %dst, %src1, %src2

&nbsp;

&nbsp;

*SUB*
---

**SUB**straction

	SUB %dst, %min, %subtr
	SUB{C} %dst, %min, %subtr

&nbsp;

&nbsp;    

*MUL*
---

**MUL**tiplycation

	MUL %dst, %src1, %src2
 	MUL{C} %dst, %src1, %src2

&nbsp;

&nbsp;

*DIV*
---

**DIV**ision

	DIV %dst, %num, %denom

&nbsp;

&nbsp;

*PUSH*
---

**PUSH**

**Stores one, two or three registers into the address defined by SP register, incrementing SP after each register.**

| Opcode | - |
|--------|---|
| 00000110 | 0x1F |

| Mode | Operation       | Instruction size | Cycles |
|------|-----------------|------------------|--------|
| 0000 | [Single](#push-single) | 3 bytes (1 word) | |
| 0001 | [Double](#push-double) | 3 bytes (1 word) | |
| 0010 | [Triple](#push-triple) | 3 bytes (1 word) | |
| ...  | Unused          | N/A              | |

&nbsp;

#### _(PUSH) Single_

	PUSH %src1 

Stores `%src1` into address defined by `%SP`, then increments `%SP`.

| Opcode   | Mode    | Src1 Reg | Unused | Unused |
|----------|---------|----------|--------|--------|
| 00000110 | 0000    | xxxx     | ****   | ****   |

Example:
><sub>Push %C contents to stack.</sub>
>
>`PUSH %C`

&nbsp;

#### _(PUSH) Double_

   	PUSH %src1 %src2

Stores `%src1` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`.

| Opcode   | Mode    | Src1 Reg | Src2 Reg | Unused |
|----------|---------|----------|----------|--------|
| 00000110 | 0001    | xxxx     | xxxx     | ****   |

Example:
><sub>Push %D, then %A to stack.</sub>
>
>`PUSH %D %A`

&nbsp;

#### _(PUSH) Triple_

   	PUSH %src1 %src2 %src3

Stores `%src1` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`.

| Opcode   | Mode    | Src1 Reg | Src2 Reg | Src3 Reg |
|----------|---------|----------|----------|----------|
| 00000110 | 0010    | xxxx     | xxxx     | xxxx     |

Example:
><sub>Push %B, then %A, then %C to stack.</sub>
>
>`PUSH %B %A %C`

&nbsp;

&nbsp;

*POP*
---

**POP**

**Loads one, two or three registers from the address defined by SP register, decrementing SP after each register.**

| Opcode | - |
|--------|---|
| 00000111 | 0x1F |

| Mode | Operation       | Instruction size | Cycles |
|------|-----------------|------------------|--------|
| 0000 | [Single](#pop-single) | 3 bytes (1 word) | |
| 0001 | [Double](#pop-double) | 3 bytes (1 word) | |
| 0010 | [Triple](#pop-triple) | 3 bytes (1 word) | |
| ...  | Unused          | N/A              | |

&nbsp;

#### _(POP) Single_

   	POP %dst1

Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`,

| Opcode   | Mode    | Dst1 Reg | Unused | Unused |
|----------|---------|----------|--------|--------|
| 00000111 | 0000    | xxxx     | ****   | ****   |

Example:
><sub>Pop from stack to %C.</sub>
>
>`POP %C

&nbsp;

#### _(POP) Double_

   	POP %dst2 %dst1

Loads from address defined by `%SP` to `%dst2`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`.

| Opcode   | Mode    | Dst1 Reg | Dst2 Reg | Unused |
|----------|---------|----------|----------|--------|
| 00000111 | 0001    | xxxx     | xxxx     | ****   |

Example:
><sub>Pop from stack to %A, then %D to stack.</sub>
>
>`POP %D %A

&nbsp;

#### _(POP) Triple_

   	POP %dst3 %dst2 %dst1

Loads from address defined by `%SP` to `%dst3`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst2`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`.

| Opcode   | Mode    | Dst1 Reg | Dst2 Reg | Dst3 Reg |
|----------|---------|----------|----------|----------|
| 00000111 | 0010    | xxxx     | xxxx     | xxxx     |

Example:
><sub>Pop from stack to %C, then %A, then %B.</sub>
>
>`POP %B %A %C`

&nbsp;

&nbsp;

*ROT*
---

**ROT**ate

	ROT{L} %dst %src
	ROT{R} %dst %src

&nbsp;

&nbsp;


*SH*
---

**SH**ift

	SH{L} %dst %src
	SH{R} %dst %src

&nbsp;

&nbsp;


*BIT*
---

**BIT**

// TODO: What to do when number (#) is 24-31? Should we use Mode to specify High-Medium-Lower byte and use 3 bits (0-7) for number?



	BIT{S} %dst, #(0-24)

Sets bit number # on register

| Opcode   | Mode | Dst reg | Unused | Number |
|----------|------|---------|--------|--------|
| 0000xxxx | 0000 | xxxx    | ***    | xxxxx  |

&nbsp;

	BIT{R} %dst, #(0-24)

Resets bit number # on register

| Opcode   | Mode | Dst reg | Unused | Number |
|----------|------|---------|--------|--------|
| 0000xxxx | 0001 | xxxx    | ***    | xxxxx  |

&nbsp;

	BIT{T} %dst, #(0-24)

Tests bit number # on register and sets Z flag accordingly.

| Opcode   | Mode | Dst reg | Unused | Number |
|----------|------|---------|--------|--------|
| 0000xxxx | 0010 | xxxx    | ***    | xxxxx  |


&nbsp;

&nbsp;

*SWP*
---

**SW**a**P**

// TODO: Rethink this opcode and its usefulness


	SWP{HM} %dst
	SWP{HL} %dst
	SWP{ML} %dst

Swaps 2 bytes on a register (High-Low, High-Medium, Medium-Low)


	SWP{Nxy} %dst

Swaps 2 nibbles on a register, where *x* and *y* are nibble number (0-5)


&nbsp;

&nbsp;

*XCHG*
---

e**XCH**an**G**e

	XCHG %dst, %src

&nbsp;

&nbsp;

*CMP*
---

**C**o**MP**are

&nbsp;

&nbsp;

*LD*
---

**L**oa**D**

*Loads a value into a register/s*


Variants:

| Mnemonic | Decription |
|----------|---------------|
| LD | Loads a 24 bit value |
| LD{I} | Loads an immediate 8 bits value |





		LD %dst1, 0xdeadbe

| Opcode   | Mode | Dst Reg1 | Unused | Unused | Value                         |
|----------|------|----------|--------|--------|-------------------------------|
| 0000xxxx | 0000 | xxxx     | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

	LD %dst1 %dst2, 0xdeadbe

| Opcode   | Mode | Dst Reg1 | Dst Reg2 | Unused | Value                         |
|----------|------|----------|----------|--------|-------------------------------|
| 0000xxxx | 0001 | xxxx     | xxxx     | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

	LD %dst1 %dst2 %dst3, 0xdeadbe

| Opcode   | Mode | Dst Reg1 | Dst Reg2 | Dst Reg3 | Value                         |
|----------|------|----------|----------|----------|-------------------------------|
| 0000xxxx | 0010 | xxxx     | xxxx     | xxxx     | xxxx xxxx xxxx xxxx xxxx xxxx |


&nbsp;

	LD{I} %dst, imm_value

Loads an immediate 8 bit value into `%dst`.

| Opcode   | Mode | Dst Reg | Value    |
|----------|------|---------|----------|
| 0000xxxx | 0011 | xxxx    | xxxxxxxx |



&nbsp;

&nbsp;

*CP*
---

**C**o**P**y
	
**Copies a register into another**
	
	CP %dst, %src

Copies `%src` register into `%dst` register.

| Opcode   | Unused | Dst Reg | Src Reg | Unused |
|----------|--------|---------|---------|--------|
| 0000xxxx | ****   | xxxx    | xxxx    | ****   |


&nbsp;

&nbsp;

*IN*
---

**IN**put

&nbsp;

&nbsp;

*OUT*
---

**OUT**put

&nbsp;

&nbsp;

*JMP*
---

**J**u**MP**

&nbsp;

&nbsp;

*CALL*
---

**CALL**

&nbsp;

&nbsp;

*RET*
---

**RET**urn

&nbsp;

&nbsp;

*NOP*
---

**N**o **OP**eration

**Does nothing, only consumes cycles.**

| Opcode | - |
|--------|---|
| 00000000 | 0x00 |

| Instruction size | Cycles |
|------------------|--------|
| 3 bytes (1 word) |        |


	NOP

No operation.

| Opcode   | Unused            |
|----------|-------------------|
| 00000000 | ******** ******** |

Flag affection:

* Resets II

&nbsp;

&nbsp;

*HALT*
---

**HALT**

**Suspends the execution of the CPU until an interruption is received.**

| Opcode | - |
|--------|---|
| 00000001 | 0x01 |

| Instruction size | Cycles |
|------------------|--------|
| 3 bytes (1 word) |        |

	HALT

Halts the CPU.

| Opcode   | Unused            |
|----------|-------------------|
| 00000001 | ******** ******** |


Flag affection:

* Resets II
	
