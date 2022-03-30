import sys
import os
import re

#What do I need to track for a compiler?
vars = []

#Do initial parse, break each line into tokens then into trees
#Find variables, assign an address to each var
#Plug in VM opcode template for each operation
#Compose into final bin image
