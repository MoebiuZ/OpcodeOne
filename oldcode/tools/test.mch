.code

SUB %B, %C, %D

MR %A, (var2)

.data

var1: .DW	0xdeadbe



.code 

DBG %A

.data
 var2:	.DW 0xffffff
 var3: .DS "abcd"