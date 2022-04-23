#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <libgen.h>
#include <errno.h>
#include <string.h>
#include <getopt.h>
#include <sys/types.h>

#include "vm.h"
#include "secret_menu.h"

int MAX_HEAP_SIZE;

void print_heap(char *heap);
int run_inst(inst_t *inst);

int main(int argc, char *argv[]){
	if(argc < 2){
		printf("Gotta give me a binary!\n");
		return -1;
	}

	init_secret_menu();

	int load_offset = 100;
	MAX_HEAP_SIZE = 1024 * sizeof(char);
	FILE *f = fopen(argv[1], "rb");

	if(f){
		heap = malloc(MAX_HEAP_SIZE);	//Allocate a small heap, for now
		fread(heap + load_offset, MAX_HEAP_SIZE, 1, f); //Load binary image from file
		fseek(f, 0, SEEK_END); //Get the size of the image
		int size = ftell(f);

		//Initiate some VM state stuff
		vm_state.b = 0;	//We are running, not branching
		vm_state.ip = load_offset; //Start at the begenning of the binary image

		//for(vm_state.ip = load_offset; vm_state.ip < size + load_offset; vm_state.ip += sizeof(inst_t)){
		while(1){ //Main execution loop...
			inst_t *inst = (inst_t *) (heap + vm_state.ip); //Load inst
			printf("\tOp: %02x, A0: %04x, A1: %04x\n", inst->op, inst->a0, inst->a1);
			run_inst(inst); //Run it!

			//Give some debug outputs
			printf("\t(op: %04x, ip: %04x, b: %04x)\n", vm_state.op, vm_state.ip, vm_state.b);
			print_heap(heap);

			//Now we gotta check for a branch...
			if(vm_state.b != 0){
				vm_state.ip = vm_state.b; //Do the branch!
				vm_state.b = 0; //Clear the branch register
			}else{
				vm_state.ip += sizeof(inst_t); //Increment to next inst
			}

			if(vm_state.ip > size + load_offset){ //Kill once we get beyond code chunk(make better later)
				break;
			}
		}
	}else{
		printf("Unable to read file: %s\n", argv[1]);
		return -1;
	}

	return 0;
}

int run_inst(inst_t *inst){
	switch(inst->op){
		case WRAP_C_A:
			heap[inst->a1] = (char) inst->a0;
			break;

		case WRAP_A_A:
			heap[inst->a1] = (char) heap[inst->a0];
			break;

		case WRAP_C_O:
			vm_state.op = inst->a0;
			break;

		case WRAP_A_O:
			vm_state.op = heap[inst->a0];
			break;

		case CRUNCH:
			if(vm_state.op < 32){
				(*secret_menu[vm_state.op])();
			}
			break;
	}

	return 0;
}

void print_heap(char *heap){
	for(int i = 0; i < 16; i++){
		printf("%03i ", heap[i]);
	}
	printf("\n");
}		
