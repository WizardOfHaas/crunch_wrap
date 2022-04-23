import sys
import os
import re
import pprint
from struct import pack

pp = pprint.PrettyPrinter(indent=1)

#Some constants for the VM ISA
WRAP_C_A = 1
WRAP_A_A = 2
WRAP_C_O = 3
WRAP_A_O = 4
CRUNCH = 5

#What do I need to track for a compiler?
heap_next_addr = 6
last_tmp_var = 6
var_size = 2

tmp_var = 90
var_set = {
	'tmp': tmp_var
}
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
	"=": [ #Assign
		#This needs to handle...
		# WRAP C -> A
		# WRAP A -> A
        {
			"signature": ["var", "data"],
			"template": [WRAP_C_A, "data", "var"]
		},{
			"signature": ["var", "var"],
        	"template": [WRAP_A_A, "var", "var"]
		}
	],
	"~~": [ #Linger
		{
			"signature": ["data", "var"],
			"template": [
				WRAP_C_A, "data", tmp_var,				#Save const to temp var
				WRAP_C_O, 5, 0,							#Set OP to shift_l
				WRAP_A_A, tmp_var, 0,					#Move temp var to [0x00]
				CRUNCH, 0, 0,							#CRUNCH!
				WRAP_C_O, 0, 0,							#Set OP to add
				WRAP_A_A, "var", 1,						#Move input var to [0x01]
				CRUNCH, 0, 0,							#CRUNCH!
				WRAP_A_A, 0, tmp_var					#Save the result to temp var
			]
		},{
			"signature": ["var", "data"],
			"template": [
				WRAP_C_A, "data", tmp_var,				#Save const to temp var
				WRAP_C_O, 5, 0,							#Set OP to shift_l
				WRAP_A_A, tmp_var, 0,					#Move temp var to [0x00]
				CRUNCH, 0, 0,							#CRUNCH!
				WRAP_C_O, 0, 0,							#Set OP to add
				WRAP_A_A, "var", 1,						#Move input var to [0x01]
				CRUNCH, 0, 0,							#CRUNCH!
				WRAP_A_A, 0, tmp_var					#Save the result to temp var
			]
		}
	],
	"=~": [ #Equals-linger
		{
			"signature": ["var", "op"],
			"template": [
				WRAP_A_A, tmp_var, "var"
			]
		}
	]
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
	},
	"data_recur_arg1": {
		"template": ["brace", "data", "op", "brace"],
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
				"children": c['get_args'](tokens),
				"class": "op"
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
				heap_next_addr += var_size

def alloc_tmp_var():
	global heap_next_addr
	global var_set
	global last_tmp_var

	v = '_tmp_' + str(heap_next_addr)
	var_set[v] = heap_next_addr
	last_tmp_var = heap_next_addr
	heap_next_addr += var_size
	return var_set[v]

def convert_tree(tree):
	btc = []
	#Do we need to recur? Does the tree have a child that's an operation?
	if tree['children']:
		for i in range(0, len(tree['children'])):
			if tree['children'][i]['class'] == 'op':
				btc.extend(fill_btc_template(tree['children'][i]))

	#Otherwise, fill_btc_template
	btc.extend(fill_btc_template(tree))
	return btc

def fill_btc_template(node):
	#Find correct template to use
	templs = []

	#If a child is of class op then I need to recurr again...
	for i in range(0, len(node['children'])):
		if node['children'][i]['class'] == 'op':
			templs.extend(convert_tree(node['children'][i]))

			node['children'][i] = {
				'class': 'var',
				'value': 'tmp'
			}

	if node['op'] in btc_templates and 'children' in node:
		for t in btc_templates[node['op']]:
			if "".join(list(filter(lambda e: type(e) == str, t['signature']))) == "".join(list(map(lambda e: e['class'], node['children']))):
				#Fill in the placeholders
				templ = t['template'][:]

				for i in range(0, len(templ)):
					if type(templ[i]) == str:
						templ[i] = resolve_arg(
							list(filter(lambda c: c['class'] == templ[i], node['children']))[0]
						)
					elif callable(templ[i]):
						templ[i] = templ[i]()

				templs.extend(templ)

	#Return unpacked array
	print(templs)
	return templs

def resolve_arg(node):
	if node['class'] == 'var' and node['value'] in var_set:
		return var_set[node['value']]
	elif node['class'] == 'data':
		return int(node['value'])

def pack_btc_ins(i):
	return pack('<Bhh', i[0], i[1], i[2])

def chunks(l, n):
    return (l[i:i+n] for i in range(0, len(l), n))

#Find variables, assign an address to each var
#Plug in VM opcode template for each operation
#Compose into final bin image

in_file = open(sys.argv[1], 'r')

os.remove("test.crb")
out_file = open("test.crb", "wb+")

for i, line in enumerate(in_file.readlines()):
	if re.match("^#", line):
		continue

	line = line.replace('\n', '')

	print(str(i + 1) + "\t" + line)
	
	tokens = tokenize(line)
	scan_vars(tokens)
	tree = parse_exp(tokens)

	pp.pprint(tree)
	
	btc = convert_tree(tree)
	for ins in chunks(btc, 3):
		out_file.write(pack_btc_ins(ins))

pp.pprint(var_set)