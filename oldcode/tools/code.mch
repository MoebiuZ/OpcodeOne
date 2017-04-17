.code

main: 	
		CALL (0xdeadbe)
		CALL (var)
		LD %A, 0xff
		LD %A, %B
		DBG %A
		DBG (%A)
		DBG (0xdeadbe)
		DBG (var)
#		LD B, 12
#		DBG B
#		LD C, B
#		DBG C
		MR %B, (0xffffff)
		MR %C, (%B)+12
		MR %D, (var)+%A
		MR %D, (var)-0xdeadbe
#		#DBG B
#		MR A, (var)
#		DBG A
#		MW (var), B
#		MR A, (var)
#		DBG A

		HALT


.data

var: 	.DS 'Hello world '
