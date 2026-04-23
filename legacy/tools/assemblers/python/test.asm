; asm test file

.code

main:

; Comment 1
	; Comment 2



		PAR %A, [%B] +#5 ; Comment 3
		PAR %A, [%B] +5
		PAR %A,[%B]+5
		PAR %A, [%B] +%C
		PAR %A, [%B] +0xcafeba
		PAR %A, [%B] +3000

		PAR %A, [0xde]
		PAR %A, [0xdea]
		PAR %A, [0xdead]
		PAR %A, [0xdeadbe]
		PAR %A, [0xdeadbe] +#5
		PAR %A, [0xdeadbe] +5
		PAR %A, [0xdeadbe] +%C
		PAR %A, [0xdeadbe] +0xcafeba
		PAR %A, [0xdeadbe] +3000

		PAR %A, [var1] +1	
		


.data

var1: 	.DS 'Hello world \n'
var2: 	.DW 0xcafeba
var3: 	.DW 0x123456 0x6789ab



.code

label2:

	CP %A, %PC
	LD %C, #10

label3:

	LD %C, 10
	LD %B, 0xa
	LD %D, 0xdeafda

	HALT


.data

.code