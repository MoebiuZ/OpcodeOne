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
		* [CP (CoPy)](#cp)
		* [PAR (Primary Address bus Read)](#par)
		* [PAW (Primary Address bus Write)](#paw)
		* [SAR (Secondary Address bus Read)](#sar)
		* [SAW (Secondary Address bus Write)](#saw)
		* [ABT (Address Bus Transfer)](#abt)
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
	* [Glossary](#glossary)

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
                        HLT <-|                                  |-> PA0          -+
                        ___   |                                  |-> PA1           |
                        RST ->|                                  |   ...           | Primary Address bus
                              |            _--------_            |-> PA22          |
                              |           +  O¹ CPU  +           |-> PA23         -+                  
               +-      IO0 <->|            ¯--------¯            |
               |       IO1 <->|                                  |
 Input/Output  |        ...   |                                  |
     bus       |      IO22 <->|                                  |-> ABS 
               +-     IO23 <->|                                  |
                              |                                  |
                        ___   |                                  |                  
                        IRQ ->|                                  |-> SA0          -+
                        ___   |                                  |-> SA1           |
                        NMI ->|                                  |   ...           | Secondary Address bus
                              |                          TDI [ ] |-> SA22          |
                              |                          TDO [ ] |-> SA23         -+
                              |                          TCK [ ] |
                              |                          TMS [ ] |
                        CLK ->|                         TRST [ ] |           
                              +----------------------------------+
      

Legend:

* ABS: Address Bus Select
* CLK: Clock  
* HLT: Halt  
* IRQ: Interruption Request  
* NMI: Non-Maskable Interruption  
* RST: Reset  


      
```

***

## Registers

All O¹ registers are 24-bits wide.

The following table shows the available registers and their binary encoding within instructions.

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
| 22  | AB   | [Address Bus selection](#address-bus-selection-ab-flag) | Yes (ABS) |
| 6   | Z    | [Zero](#zero-z-flag) | No |
| 4   | SB   | [Subtraction](#subtraction-sb-flag) | No |
| 3   | P    | [Parity](#parity-p-flag) | No |
| 2   | V    | [Overflow](#overflow-v-flag) | No |
| 1   | S    | [Sign](#sign-s-flag) | No |
| 0   | C    | [Carry](#carry-c-flag) | No |


**FL register**  

| <sub><sup>23</sup></sub></sub> | <sub><sup>22</sup></sub> | <sub><sup>21</sup></sub> | <sub><sup>20</sup></sub> | <sub><sup>19</sup></sub> | <sub><sup>18</sup></sub> | <sub><sup>17</sup></sub> | <sub><sup>16</sup></sub> | <sub><sup>15</sup></sub> | <sub><sup>14</sup></sub> | <sub><sup>13</sup></sub> | <sub><sup>12</sup></sub> | <sub><sup>11</sup></sub> | <sub><sup>10</sup></sub> | <sub><sup>9</sup></sub> | <sub><sup>8</sup></sub> | <sub><sup>7</sup></sub> | <sub><sup>6</sup></sub> | <sub><sup>5</sup></sub> | <sub><sup>4</sup></sub> | <sub><sup>3</sup></sub> | <sub><sup>2</sup></sub> | <sub><sup>1</sup></sub> | <sub><sup>0</sup></sub> |
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| <sub><sup>II</sup></sub>  | <sub><sup>AB</sup></sub> |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    | <sub><sup>Z</sup></sub> | <sub><sup>SB</sup></sub> | <sub><sup>P</sup></sub> | <sub><sup>V<sub></sub> | <sub><sup>S</sup></sub> | <sub><sup>C</sup></sub> |


#### _Invalid Instruction (II) flag_

Note: To be deleted if we decide to use Interruptions for this purpose.
This flag is set if the last instruction was invalid.  
This happens when the Opcode or Mode encoded in the instruction doesn't exist.

#### _Address Bus selection (AB) flag_

This flag is set if Secondary Address bus is selected, and reset for Primary Address bus selection.

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

OpcodeOne has two 24-bit address buses, **Primary Address bus** and **Secondary Address bus**.  
For a *standard* use case, one is intended for RAM/ROM and the other for VRAM (Video), but second one can be used for any other purpose (for example, extending the addressable memory via segmentation).  
All instructions addressing refer to [Primary Address bus](#primary-address-bus), and [Secondary Address bus](#secondary-address-bus) is only accessible with [`SAR`](#sar), [`SAW`](#saw) and [`ABT`](#abt) instructions.


### Primary Address bus

// TODO

### Secondary Address bus

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
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <sub>**0x**</sub> |  <sub>[NOP](#nop)</sub>  |  <sub>[HALT](#halt)</sub> |  <sub>[PAR](#par)</sub>   |  <sub>[PAW](#paw)</sub>   |  <sub>[SAR](#sar)</sub>  |  <sub>[SAW](#saw)</sub>   |  <sub>[PUSH](#push)</sub> |  <sub>[POP](#pop)</sub>  |  <sub>[JMP](#jmp)</sub>  |  <sub>[RET](#ret)</sub>  |  <sub>[ADD](#add)</sub>  |  <sub>[SUB](#sub)</sub>  |  <sub>[MUL](#mul)</sub>  |  <sub>[DIV](#div)</sub>  |  <sub>[AND](#and)</sub>  |  <sub>[OR](#or)</sub>   |
| <sub>**1x**</sub> |  <sub>[XOR](#xor)</sub>  |  <sub>[NAND](#nand)</sub> |  <sub>[NEG](#neg)</sub>  |  <sub>[IN](#in)</sub>   |  <sub>[OUT](#out)</sub>  |  <sub>[LD](#ld)</sub>   |  <sub>[CP](#cp)</sub>   |  <sub>[CMP](#cmp)</sub>  |  <sub>[ROT](#rot)</sub>   | <sub>[SH](#sh)</sub>  |  <sub>[INC](#inc)</sub>  |  <sub>[DEC](#dec)</sub>  |  <sub>[CALL](#call)</sub> |  <sub>[ABT](#abt)</sub>  | <sub>[BIT](#bit)</sub>  | <sub>[SWP](#swp)</sub> | 
| <sub>**2x**</sub> | <sub>[XCHG](#xchg)</sub>  | | | | | | | | | | | | | | | |
| <sub>**3x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**4x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**5x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**6x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**7x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**8x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**9x**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Ax**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Bx**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Cx**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Dx**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Ex**</sub> | | | | | | | | | | | | | | | | |
| <sub>**Fx**</sub> | | | | | | | | | | | | | | | | |

***

## Assembly syntax

* Arguments are comma (**,**) separated, except when different parameters *group* as a single argument (ie.: [`LD`](#ld) or [`PUSH`](#push))
* **%** indicates a register
* **[]** indicates a register is used as an address
* **#** indicates an immediate value, and it will be expressed in decimal
* Values can be expressed in decimal or hexadecimal (starting with 0x)
* Addresses are expressed in hexadecimal
* **{}** indicates **operation type** (ie.: conditions in [`JMP`](#jmp), *with carry* in arithmetical operations or *direction* in [`ABT`](#abt))

***

## O¹ instruction set


Legend:

* **x** represents a variable parameter. Its value will indicate a different register o operation mode (it will be considered a different instruction depending on it's value).
* **\*** means the value will not affect the instruction behaviour (the instruction will be the same regardless of it's value).


*PAR* 
---

(0x02) **P**rimary **A**ddress bus **R**ead

Reads a word from [*Primary Address bus*](#primary-address-bus) into a [*register*](#registers).


_**Operations:**_

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00000010</sub> | <sub>0000</sub> | <sub>[Indirect](#1-par-indirect-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000010</sub> | <sub>0001</sub> | <sub>[Indirect plus immediate offset](#2-par-indirect-plus-immediate-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000010</sub> | <sub>0010</sub> | <sub>[Indirect plus register offset](#3-par-indirect-plus-register-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000010</sub> | <sub>0011</sub> | <sub>[Indirect plus offset](#4-par-indirect-plus-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>0100</sub> | <sub>[Indirect minus immediate offset](#5-par-indirect-minus-immediate-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000010</sub> | <sub>0101</sub> | <sub>[Indirect minus register offset](#6-par-indirect-minus-register-offset-mode) | <sub>3 bytes (1 word)</sub> | |
| <sub>00000010</sub> | <sub>0110</sub> | <sub>[Indirect minus offset](#7-par-indirect-plus-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>0111</sub> | <sub>[Absolute](#8-par-absolute-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>1000</sub> | <sub>[Absolute plus immediate offset](#9-par-absolute-plus-immediate-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>1001</sub> | <sub>[Absolute plus register offset](#10-par-absolute-plus-register-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>1010</sub> | <sub>[Absolute plus offset](#11-par-absolute-plus-offset-mode)</sub> | <sub>9 bytes (3 words)</sub> | |
| <sub>00000010</sub> | <sub>1011</sub> | <sub>[Absolute minus immediate offset](#12-par-absolute-minus-immediate-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>1100</sub> | <sub>[Absolute minus register offset](#13-par-absolute-minus-register-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000010</sub> | <sub>1101</sub> | <sub>[Absolute minus offset](#14-par-absolute-minus-offset-mode)</sub> | <sub>9 bytes (3 words)</sub> | |
| <sub>00000010</sub> | <sub>1110</sub> | <sub>Unused</sub> | <sub>N/A</sub> | |
| <sub>00000010</sub> | <sub>1111</sub> | <sub>Unused</sub> | <sub>N/A</sub> | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**


#### 1. PAR Indirect mode

Reads from the address specified by `%src` register into `%dst` register.

<sub>Syntax:</<ub>

	PAR %dst, [%src]

<sub>Bytecode:</sub>


| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00000010 | 0000 | xxxx    | xxxx    | ****   |

Example:
><sub>Read a word from the address specified by %C into %A</sub>
>
>`PAR %A, [%C]`

&nbsp;

#### 2. PAR Indirect plus immediate offset mode

Reads from the address specified by `%src` register plus an immediate 4-bit offset into `%dst` register.

<sub>Syntax:</<ub>

	PAR %dst, [%src]+#imm_offset


<sub>Bytecode:</<ub>

| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000010 | 0001 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %B plus 3 into %C</sub>
>
>`PAR %C, [%B]+#3`

&nbsp;

#### 3. PAR Indirect plus register offset mode

Reads from the address specified by `%src` register plus an offset specified by `%offset` register into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, [%src]+%offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000010 | 0010 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %D plus offset specified by %B into %A</sub>
>
>`PAR %A, [%D]+%B`

&nbsp;

#### 4. PAR Indirect plus offset mode

Reads from the address specified by `%src` register plus a 24-bit offset into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, [%src]+offset

<sub>Bytecode</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000010 | 0011 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

Example:
><sub>Read a word from the address specified by %C plus 1337 into %A</sub>
>
>`PAR %A, [%C]+1337` <sub>h(0x023020 , 0x000539) | b(00000010 0011 0000 0010 0000, 000000000000010100111001)</sub>
>
><sub>or</sub>
>
>`PAR %A, [%C]+0x539` <sub>h(0x023020 , 0x000539) | b(00000010 0011 0000 0010 0000, 000000000000010100111001)</sub>

&nbsp;

#### 5. PAR Indirect minus immediate offset mode

Reads from the address specified by `%src` register minus an immediate 4-bit *offset* into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, [%src]-#imm_offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000010 | 0100 | xxxx    | xxxx    | xxxx       |

Example:
><sub>Read a word from the address specified by %B minus 15 into %A</sub>
>
>`PAR %A, [%B]-#15` <sub>h(0x02401F) | b(00000010 0100 0000 0001 1111)</sub>


&nbsp;

#### 6. Indirect minus register offset mode

Reads from the address specified by `%src` register minus an offset specified by `%offset` register into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, [%src]-%offset	

<sub>Bytecode</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000010 | 0101 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### 7. PAR Indirect plus offset mode

Reads from the address specified by `%src` register minus a 24-bit offset into `%dst` register

<sub>Syntax:</sub>

	PAR %dst, [%src]-offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000010 | 0110 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 8. PAR Absolute mode

Reads from address into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr

<sub>Bytecode</sub>

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       |
|----------|------|---------|--------|--------|-------------------------------|
| 00000010 | 0111 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 9. PAR Absolute plus immediate offset mode

Reads from address plus an immediate 4-bit offset into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr+#imm_offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Imm Offset | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1000 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 10. PAR Absolute plus register offset mode

Reads from address plus offset specified by `%offset` register into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr+%offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Offset Reg | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1001 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 11. PAR Absolute plus offset mode

Reads from address plus a 24-bit offset into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr+offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       | Offset                        |
|----------|------|---------|--------|--------|-------------------------------|-------------------------------|
| 00000010 | 1010 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 12. PAR Absolute minus immediate offset mode

Reads from address plus an immediate 4-bit offset into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr-#imm_offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Imm Offset | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1011 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 13. PAR Absolute minus register offset mode

Reads from address minus offset specified by `%offset` register into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr-%offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Offset Reg | Address                       |
|----------|------|---------|--------|------------|-------------------------------|
| 00000010 | 1100 | xxxx    | ****   | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 14. PAR Absolute minus offset mode

Reads from address minus a 24-bit offset into `%dst` register.

<sub>Syntax:</sub>

	PAR %dst, addr-offset

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Unused | Unused | Address                       | Offset                        |
|----------|------|---------|--------|--------|-------------------------------|-------------------------------|
| 00000010 | 1101 | xxxx    | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |



&nbsp;

&nbsp;



*PAW*
---

(0x03) **P**rimary **A**ddress bus **W**rite

Writes a word from a [register](#registers) into [Primary address bus](#primary-address-bus) address.


**Operations:**

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00000011</sub> | <sub>0000</sub> | <sub>[Indirect](#1-paw-indirect-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000011</sub> | <sub>0001</sub> | <sub>[Indirect plus immediate offset](#2-paw-indirect-plus-immediate-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000011</sub> | <sub>0010</sub> | <sub>[Indirect plus register offset](#3-paw-indirect-plus-register-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000011</sub> | <sub>0011</sub> | <sub>[Indirect plus offset](#4-paw-indirect-plus-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>0100</sub> | <sub>[Indirect minus immediate offset](#5-paw-indirect-minus-immediate-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000011</sub> | <sub>0101</sub> | <sub>[Indirect minus register offset](#6-paw-indirect-minus-register-offset-mode)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000011</sub> | <sub>0110</sub> | <sub>[Indirect minus offset](#7-paw-indirect-plus-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>0111</sub> | <sub>[Absolute](#8-paw-absolute-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>1000</sub> | <sub>[Absolute plus immediate offset](#9-paw-absolute-plus-immediate-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>1001</sub> | <sub>[Absolute plus register offset](#10-paw-absolute-plus-register-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>1010</sub> | <sub>[Absolute plus offset](#11-paw-absolute-plus-offset-mode)</sub> | <sub>9 bytes (3 words)</sub> | |
| <sub>00000011</sub> | <sub>1011</sub> | <sub>[Absolute minus immediate offset](#12-paw-absolute-minus-immediate-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>1100</sub> | <sub>[Absolute minus register offset](#13-paw-absolute-minus-register-offset-mode)</sub> | <sub>6 bytes (2 words)</sub> | |
| <sub>00000011</sub> | <sub>1101</sub> | <sub>[Absolute minus offset](#14-paw-absolute-minus-offset-mode)</sub> | <sub>9 bytes (3 words)</sub> | |
| <sub>00000011</sub> | <sub>1110</sub>| <sub>Unused</sub> | <sub>N/A</sub> | |
| <sub>00000011</sub> | <sub>1111</sub> | <sub>Unused</sub> | <sub>N/A</sub> | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

#### 1. PAW Indirect mode

	PAW [%dst], %src

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00000011 | 0000 | xxxx    | xxxx    | ****   |

&nbsp;

#### 2. PAW Indirect plus immediate offset mode

	PAW [%dst]+#imm_offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000011 | 0001 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### 3. PAW Indirect plus register offset mode
	
	PAW [%dst]+%offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000011 | 0010 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### 4. PAW Indirect plus offset mode

	PAW [%dst]+offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000011 | 0011 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 5. PAW Indirect minus immediate offset mode

	PAW [%dst]-#imm_offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Imm Offset |
|----------|------|---------|---------|------------|
| 00000011 | 0100 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### 6. PAW Indirect minus register offset mode

	PAW [%dst]-%offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Offset Reg |
|----------|------|---------|---------|------------|
| 00000011 | 0101 | xxxx    | xxxx    | xxxx       |

&nbsp;

#### 7. PAW Indirect plus offset mode

	PAW [%dst]-offset, %src


| Opcode   | Mode | Dst Reg | Src Reg | Unused | Offset                        |
|----------|------|---------|---------|--------|-------------------------------|
| 00000011 | 0110 | xxxx    | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 8. PAW Absolute mode

	PAW addr, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       |
|----------|------|--------|---------|--------|-------------------------------|
| 00000011 | 0111 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 9. PAW Absolute plus immediate offset mode

	PAW addr+#imm_offset, %src


| Opcode   | Mode | Unused | Src Reg | Imm Offset | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1000 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 10. PAW Absolute plus register offset mode

	PAW addr+%offset, %src


| Opcode   | Mode | Unused | Src Reg | Offset Reg | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1001 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 11. PAW Absolute plus offset mode

	PAW addr+offset, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       | Offset                        |
|----------|------|--------|---------|--------|-------------------------------|-------------------------------|
| 00000011 | 1010 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 12. PAW Absolute minus immediate offset mode

	PAW addr-#imm_offset, %src


| Opcode   | Mode | Unused | Src Reg | Imm Offset | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1011 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 13. PAW Absolute minus register offset mode

	PAW addr-%offset, %src


| Opcode   | Mode | Unused | Src Reg | Offset Reg | Address                       |
|----------|------|--------|---------|------------|-------------------------------|
| 00000011 | 1100 | ****   | xxxx    | xxxx       | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

#### 14. PAW Absolute minus offset mode

	PAW addr-offset, %src


| Opcode   | Mode | Unused | Src Reg | Unused | Address                       | Offset                        |
|----------|------|--------|---------|--------|-------------------------------|-------------------------------|
| 00000011 | 1101 | ****   | xxxx    | ****   | xxxx xxxx xxxx xxxx xxxx xxxx | xxxx xxxx xxxx xxxx xxxx xxxx |


&nbsp;

&nbsp;

*SAR*
---

(0x04) **S**econdary **A**ddres bus **R**ead

Reads a word from [Secondary address bus](#secondary-address-bus) into a [register](#registers).

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**


&nbsp;

&nbsp;

*SAW*
---

(0x05) **S**econdary **A**ddress bus **W**rite

Writes a word from a [register](#registers) into [Secondary address bus](#secondary-address-bus) address.

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

&nbsp;

&nbsp;

*ABT*
---

(0x1D) **A**ddress **B**us **T**ransfer

Transfers a word between [Primary](#primary-address-bus) and [Secondary](#secondary-address-bus) address buses.

**Operations:**

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00011101</sub> | <sub>0000</sub> | <sub>[Primary to Secondary](#1-abt-primary-to-secondary)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00011101</sub> | <sub>0001</sub> | <sub>[Secondary to Primary](#2-abt-secondary-to-primary)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00011101</sub> | <sub>0010</sub> | <sub>[Exchange](#3-abt-exchange) | <sub>3 bytes (1 word)</sub> | |
| <sub>00011101</sub> | <sub>...</sub> | <sub>Unused</sub> | <sub>N/A</sub> | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

#### 1. ABT Primary to Secondary

Copies a word from [Primary Address bus](#primary-address-bus) to [Secondary Address bus](#secondary-address-bus)

<sub>Syntax:</sub>

	ABT{S} [%dst], [%src]

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011101 | 0000 | xxxx    | xxxx    | ****   |

&nbsp;

#### 2. ABT Secondary to Primary

Copies a word from [Secondary Address bus](#secondary-address-bus) to [Primary Address bus](#primary-address-bus)

<sub>Syntax:</sub>

	ABT{P} [%dst], [%src]

<sub><Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011101 | 0001 | xxxx    | xxxx    | ****   |

&nbsp;

#### 3. ABT Exchange

Exchanges a word between [Primary Address bus](#primary-address-bus) and [Secondary Address bus](#secondary-address-bus)

<sub>Syntax:</sub>

	ABT{X} [%dst], [%src]

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst Reg | Src Reg | Unused |
|----------|------|---------|---------|--------|
| 00011101 | 0010 | xxxx    | xxxx    | ****   |


&nbsp;

&nbsp;

*AND*
---

(0x0E) Logical **AND**

Performs a logical AND between 2 source registers and stores the result in destination register.

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

<sub>Syntax:</sub>

	AND %dst, %src1, %src2

<sub>Bytecode:</sub>

| Opcode   | Unused | Dst Reg  | Src Reg1  | Src Reg2     |
|----------|--------|----------|-----------|--------------|
| 00001110 | xxxx   | xxxx     | xxxx      | xxxx         |


&nbsp;

&nbsp;

(0x0F) *OR*
---

Logical **OR**

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

	OR %dst, %src1, %src2

&nbsp;

&nbsp;

*XOR*
---

(0x10) Logical **XOR**

	XOR %dst, %src1, %src2

&nbsp;

&nbsp;

*NEG*
---

(0x12) **NEG**ative - Two's complement

	NEG %dst, %src

&nbsp;

&nbsp;

*NAND*
---

(0x11) Logical **N**ot **AND** (NAND)

	NAND %dst, %src1, %src2

&nbsp;

&nbsp;

*INC*
---

(0x1A) **INC**rement

	INC %dst

&nbsp;

&nbsp;

*DEC*
---

(0x1B) **DEC**rement

	DEC %dst

&nbsp;

&nbsp;

*ADD*
---

(0x0A) **ADD**ition

	ADD %dst, %src1, %src2
	ADD{C} %dst, %src1, %src1
	ADD{U} %dst, %src1, %src2
	ADD{UC} %dst, %src1, %src2

&nbsp;

&nbsp;

*SUB*
---

(0x0B) **SUB**traction

	SUB %dst, %min, %subtr
	SUB{C} %dst, %min, %subtr

&nbsp;

&nbsp;    

*MUL*
---

(0x0C) **MUL**tiplication

	MUL %dst, %src1, %src2
 	MUL{C} %dst, %src1, %src2

&nbsp;

&nbsp;

*DIV*
---

(0x0D) **DIV**ision

	DIV %dst, %num, %denom

&nbsp;

&nbsp;

*PUSH*
---

(0x06) **PUSH**

Stores one, two or three registers into the address defined by SP register, incrementing SP after each register.

**Operations:**

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00000110</sub> | <sub>0000</sub> | <sub>[Single](#1-push-single)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000110</sub> | <sub>0001</sub> | <sub>[Double](#2-push-double)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000110</sub> | <sub>0010</sub> | <sub>[Triple](#3-push-triple)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000110</sub> | <sub>...</sub>  | <sub>Unused</sub> | <sub>N/A</sub> | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

#### 1. PUSH Single

Stores `%src1` into address defined by `%SP`, then increments `%SP`.

<sub>Syntax:</sub>

	PUSH %src1 

<sub>Bytecode:</sub>

| Opcode   | Mode    | Src1 Reg | Unused | Unused |
|----------|---------|----------|--------|--------|
| 00000110 | 0000    | xxxx     | ****   | ****   |

Example:
><sub>Push %C contents to stack.</sub>
>
>`PUSH %C`

&nbsp;

#### 2. PUSH Double

Stores `%src1` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`.

<sub>Syntax:</sub>

   	PUSH %src1 %src2

<sub>Bytecode:</sub>

| Opcode   | Mode    | Src1 Reg | Src2 Reg | Unused |
|----------|---------|----------|----------|--------|
| 00000110 | 0001    | xxxx     | xxxx     | ****   |

Example:
><sub>Push %D, then %A to stack.</sub>
>
>`PUSH %D %A`

&nbsp;

#### 3. PUSH Triple

Stores `%src1` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`,  
Stores `%src2` into address defined by `%SP`, then increments `%SP`.

<sub>Syntax:</sub>

   	PUSH %src1 %src2 %src3

<sub>Bytecode:</sub>

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

(0x07) **POP**

Loads one, two or three registers from the address defined by SP register, decrementing SP after each register.

**Operations:**

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00000111</sub> | <sub>0000</sub> | <sub>[Single](#1-pop-single)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000111</sub> | <sub>0001</sub> | <sub>[Double](#2-pop-double)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000111</sub> | <sub>0010</sub> | <sub>[Triple](#3-pop-triple)</sub> | <sub>3 bytes (1 word)</sub> | |
| <sub>00000111</sub> | <sub>...</sub>  | <sub>Unused</sub> | <sub>N/A</sub> | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

#### 1. POP Single

Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`.

<sub>Syntax:</sub>

   	POP %dst1

<sub>Bytecode:</sub>

| Opcode   | Mode    | Dst1 Reg | Unused | Unused |
|----------|---------|----------|--------|--------|
| 00000111 | 0000    | xxxx     | ****   | ****   |

Example:
><sub>Pop from stack to %C.</sub>
>
>`POP %C`

&nbsp;

#### 2. POP Double

Loads from address defined by `%SP` to `%dst2`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`.

<sub>Syntax:</sub>

   	POP %dst2 %dst1

<sub>Bytecode:</sub>

| Opcode   | Mode    | Dst1 Reg | Dst2 Reg | Unused |
|----------|---------|----------|----------|--------|
| 00000111 | 0001    | xxxx     | xxxx     | ****   |

Example:
><sub>Pop from stack to %A, then %D to stack.</sub>
>
>`POP %D %A`

&nbsp;

#### 3. POP Triple

Loads from address defined by `%SP` to `%dst3`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst2`, then decrements `%SP`,  
Loads from address defined by `%SP` to `%dst1`, then decrements `%SP`.

<sub>Syntax:</sub>

   	POP %dst3 %dst2 %dst1

<sub>Bytecode:</sub>

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

(0x18) **ROT**ate

	ROT{L} %dst %src
	ROT{R} %dst %src

&nbsp;

&nbsp;


*SH*
---

(0x19) **SH**ift

	SH{L} %dst %src
	SH{R} %dst %src

&nbsp;

&nbsp;


*BIT*
---

(0x1E) **BIT**

// TODO: What to do when number (#) is 24-31? Should we use Mode to specify High-Medium-Lower byte and use 3 bits (0-7) for number?

Sets bit number # on register.

<sub>Syntax:</sub>

	BIT{S} %dst, #(0-24)

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst reg | Unused | Bit number |
|----------|------|---------|--------|------------|
| 00011110 | 0000 | xxxx    | ***    | xxxxx      |

&nbsp;

Resets bit number # on register.

<sub>Syntax:</sub>

	BIT{R} %dst, #(0-24)

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst reg | Unused | Bit number |
|----------|------|---------|--------|------------|
| 00011110 | 0001 | xxxx    | ***    | xxxxx      |

&nbsp;

Tests bit number # on register and sets Z flag accordingly.

<sub>Syntax:</sub>

	BIT{T} %dst, #(0-24)

<sub>Bytecode:</sub>

| Opcode   | Mode | Dst reg | Unused | Bit number |
|----------|------|---------|--------|------------|
| 00011110 | 0010 | xxxx    | ***    | xxxxx      |


&nbsp;

&nbsp;

*SWP*
---

(0x1F) **SW**a**P**

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

(0x20) e**XCH**an**G**e

	XCHG %dst, %src

&nbsp;

&nbsp;

*CMP*
---

(0x17) **C**o**MP**are

&nbsp;

&nbsp;

*LD*
---

(0x15) **L**oa**D**

*Loads a value into a register/s*


		LD %dst1, value

| Opcode   | Mode | Dst Reg1 | Unused | Unused | Value                         |
|----------|------|----------|--------|--------|-------------------------------|
| 00010101 | 0000 | xxxx     | ****   | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

	LD %dst1 %dst2, value

| Opcode   | Mode | Dst Reg1 | Dst Reg2 | Unused | Value                         |
|----------|------|----------|----------|--------|-------------------------------|
| 00010101 | 0001 | xxxx     | xxxx     | ****   | xxxx xxxx xxxx xxxx xxxx xxxx |

&nbsp;

	LD %dst1 %dst2 %dst3, value

| Opcode   | Mode | Dst Reg1 | Dst Reg2 | Dst Reg3 | Value                         |
|----------|------|----------|----------|----------|-------------------------------|
| 00010101 | 0010 | xxxx     | xxxx     | xxxx     | xxxx xxxx xxxx xxxx xxxx xxxx |


&nbsp;

	LD %dst, #imm_value

Loads an immediate 8-bit value into `%dst`.

| Opcode   | Mode | Dst Reg | Imm Value |
|----------|------|---------|-----------|
| 00010101 | 0011 | xxxx    | xxxxxxxx  |



&nbsp;

&nbsp;

*CP*
---

(0x16) **C**o**P**y
	
**Copies a register into another**
	
	CP %dst, %src

Copies `%src` register into `%dst` register.

| Opcode   | Unused | Dst Reg | Src Reg | Unused |
|----------|--------|---------|---------|--------|
| 00010110 | ****   | xxxx    | xxxx    | ****   |


&nbsp;

&nbsp;

*IN*
---

(0x13) **IN**put

&nbsp;

&nbsp;

*OUT*
---

(0x14) **OUT**put

&nbsp;

&nbsp;

*JMP*
---

(0x08) **J**u**MP**

&nbsp;

&nbsp;

*CALL*
---

(0x1C) **CALL**

&nbsp;

&nbsp;

*RET*
---

(0x09) **RET**urn

&nbsp;

&nbsp;

*NOP*
---

(0x00) **N**o **OP**eration

Does nothing, only consumes cycles.

&nbsp;

**Operations:**

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | Instruction size | Cycles |
|---|---|---|---|---|
| <sub>00000000</sub> | <sub>N/A</sub> | <sub>[No Operation](#1-no-operation)</sub> | 3 bytes (1 word) | |

&nbsp;

**Flag affection:**

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|


&nbsp;

**Instruction details:**

#### 1. No operation

Doesn't perform any operation.

<sub>Syntax:</sub>

	NOP

<sub>Instruction bytecode:</sub>

| Opcode   | Unused            |
|----------|-------------------|
| 00000000 | ******** ******** |


&nbsp;

&nbsp;

*HALT*
---

(0x01) **HALT**

Suspends the execution of the CPU until an interruption is received.


_**Operations:**_

| <sub>Opcode</sub> | <sub>Mode</sub> | <sub>Operation</sub> | <sub>Instruction size</sub> | <sub>Cycles</sub> |
|---|---|---|---|---|
| <sub>00000001</sub> | <sub>N/A</sub> | <sub>[Halt](#1-halt)</sub> | <sub> 3 bytes (1 word)</sub> | |

&nbsp;

_**Flag affection:**_

| <sub>Flag</sub> | <sub>Effect</sub> |
|---|---|
| <sub>[II](#invalid-instruction-ii-flag)</sub> | <sub>Reset</sub> |

&nbsp;

_**Instruction details:**_

#### 1. Halt

Halts the CPU.

<sub>Syntax:</sub>

	HALT

<sub>Instruction bytecode:</sub>

| Opcode   | Unused            |
|----------|-------------------|
| 00000001 | ******** ******** |



	
***

## Glossary

**Warning**: These definitions are related to OpcodeOne architecture only. Doesn't necessary reflect generic or other architecture definitions.

| Term | Definition |
|---|---|
| Immediate value | A value that is included on the most significative word of an instruction |
| Instruction | Single operation performed by execution unit. CPU executes one instruction at a time. It is a bytecode composed by an opcode and parameters |
| Register | Internal 24-bit storage unit. O¹ has 16 registers for multiple purposes |
| Opcode | Code of operation. Most significative byte of an instruction, that indicates the operation to perform |
| Word | 24-bit data unit. Is the smallest data size in O¹ | 
