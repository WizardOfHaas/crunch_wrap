#ifndef VM_H
#define VM_H

#include <stddef.h>

//Overall VM register state
typedef struct vm_state_tag{
	int ip;		//Instruction pointer
	short op;	//Operation reg
	int b;		//Branch address, set to 0 if not branching, or new ip value if branching		
} vm_state_t;

enum op{
	WRAP_C_A = 1,	//Load const -> addr
	WRAP_A_A = 2,	//Load addr -> addr
	WRAP_C_O = 3,	//Load const -> op
	WRAP_A_O = 4,	//Load addr -> op
	CRUNCH = 5		//JUST DO IT!, operate OP on ADR0 and ADR1
};

typedef struct __attribute__((__packed__)) inst_tag{
	char op;

	short a0;
	short a1;
} inst_t;

vm_state_t vm_state;
char *heap;

#endif
