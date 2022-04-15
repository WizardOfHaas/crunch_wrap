import sys
import os
import re
import pprint

pp = pprint.PrettyPrinter(indent=1)

#What do I need to track for a compiler?
heap_next_addr = 100
var_set = {}
labels = {}

braces = "[\[\]\{\}\(\)\<\>]"
open_braces = "[\(\{\[\<]"
close_braces =  "[\)\}\]\>]"

var_re = "[a-zA-UW-Z]+"
const_re = "[0-9]"
op_re = "[\=\~|\~\~|@|V|OUTNUM]"

token_classes = [
	{"class": "brace", "re": braces},
	{"class": "op", "re": op_re},
	{"class": "var", "re": var_re},
	{"class": "data", "re": "[a-zA-Z0-9]+"}
]

btc_templates = {
	"=": {
		#This needs to handle...
		# WRAP C -> A
		# WRAP A -> A
	}
}

exp_classes = {
	"bare_data_data": {
		"template": ["brace", "data", "op", "data", "brace"],
		"get_op": lambda ts: ts[2]['value'],
		"get_args": lambda ts: [ts[1], ts[3]]
	},
	"bare_data_var": {
		"template": ["brace", "data", "op", "var", "brace"],
		"get_op": lambda ts: ts[2]['value'],
		"get_args": lambda ts: [ts[1], ts[3]]
	},
	"bare_var_data": {
		"template": ["brace", "var", "op", "data", "brace"],
		"get_op": lambda ts: ts[2]['value'],
		"get_args": lambda ts: [ts[1], ts[3]]
	},
	"bare_var_var": {
		"template": ["brace", "var", "op", "var", "brace"],
		"get_op": lambda ts: ts[2]['value'],
		"get_args": lambda ts: [ts[1], ts[3]]
	},

	"assign": {
		"template": ["brace", "var", "brace", "data", "brace", "brace"],
		"get_op": lambda ts: "=",
		"get_args": lambda ts: [ts[1], ts[3]]
	},

	"recur_arg0": {
		"template": ["brace", "brace"],
		"get_op": lambda ts: "recur_arg0",
		"get_args": lambda ts: ["oof_0"]
	},

	"recur_arg1": {
		"template": ["brace", "var", "op", "brace"],
		"get_op": lambda ts: ts[2]['value'],
		"get_args": lambda ts: [ts[1], parse_exp(ts[3:])]
	}
}

token_re = "([\[\]\{\}\(\)\<\> ])"

#Do initial parse, break each line into tokens then into trees
def parse_exp(tokens):
	tree = {}

	#Check if this has nested children
	#if not check_for_nests(tokens):
	#	tree = {
	#		"op": exp_classes['bare']['get_op'](tokens),
	#		"children": exp_classes['bare']['get_args'](tokens)
	#	}
	#else:
	#	print("Gotta go deeper")

	for class_name in exp_classes:
		c = exp_classes[class_name]

		if "".join(list(map(lambda t: t['class'], tokens[0:len(c['template'])]))) == "".join(c['template']):
			tree = {
				"op": c['get_op'](tokens),
				"children": c['get_args'](tokens)
			}
			break

	return tree
	
#Check if exp is nested
def check_for_nests(tokens):

	if "".join(list(map(lambda t: t['class'], tokens[0:5]))) == "".join(exp_classes['bare']['template']):
		return False

	return True

def tokenize(exp):
	tokens = []

	#First, split up by braces
	for t in re.split(token_re, exp):
		#Now we categorize and add it to the token list
		for c in token_classes:
			if t != None and re.match(c["re"], t):
				tokens.append({
					"class": c["class"],
					"value": t
				})
				break

	return tokens

def scan_vars(tokens):
	global heap_next_addr
	global var_set

	for t in tokens:
		#Check if this is a variable
		if t != None and t['class'] == 'var':
			#Next, see if we have it allocated yet
			if t['value'] not in var_set:
				var_set[t['value']] = heap_next_addr
				heap_next_addr += 4
	
#Find variables, assign an address to each var
#Plug in VM opcode template for each operation
#Compose into final bin image

in_file = open(sys.argv[1], 'r')

for i, line in enumerate(in_file.readlines()):
	line = line.replace('\n', '')

	print(str(i + 1) + "\t" + line)
	
	tokens = tokenize(line)
	scan_vars(tokens)
	tree = parse_exp(tokens)

	pp.pprint(tree)

pp.pprint(var_set)
