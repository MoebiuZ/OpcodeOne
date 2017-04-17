-data
.asdasd DS 's#s'
-code
MW [B], A

-code
MW [B], A
MR A, 0x0000ff   #aasd  s 

		
MW [A], B
MW [d]+16777215, A   
MW 0x0000ff, B
MW 0x0000ff+16777215, A #comment
MW 0x0000ff-16777215, A
MW 0x0000ff+0xfffff7, A
MW 0x0000ff+15, A

 # this is a comment
 		#asd
:read:


-code

MR A, [C]
MR b, [a]
MR A, [d]+16777215
MR A, 0xffffff
:narnia:
MR A, 0x0000ff+16777215
MR B, 0x0000ff+16777215

NOP

HALT


-data

.no DS '#'
.mum DS 'ññÑÑ'


.number DW 0xffffff
		DW 0x111111


