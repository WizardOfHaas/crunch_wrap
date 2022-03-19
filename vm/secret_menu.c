#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <libgen.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>

#include "secret_menu.h"
#include "vm.h"

void _sum();
void _diff();
void _bnz();

void init_secret_menu(){
	secret_menu[0] = _sum;
	secret_menu[1] = _diff;
	secret_menu[2] = _bnz;
}

void _sum(){
	heap[0] += heap[1];
}

void _diff(){
	heap[0] -= heap[1];
}

void _bnz(){
	if(heap[0] != 0){
		vm_state.b = *((int *) (heap + 2));
	}
}
