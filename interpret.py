#!/usr/bin/python3
import argparse
from operator import concat
# from lxml import etree
import xml.etree.ElementTree as ET
import re
from sys import stderr, stdin, exit


def debug(s):
    if DEBUG:
        print(s)


DEBUG = False

parser = argparse.ArgumentParser(description='interpret')
parser.add_argument('--source', dest='source', type=str)
parser.add_argument('--input', dest='input', type=str)
args = parser.parse_args()
sourceFile = str(args.source)
inputFile = str(args.input)
inputLines = []
instructions = list()
GF = dict()
orderNumbers = []
# stack = []
variablesStorage = {}
# output = ""
# outputErr = ""
position_pointer = 0
TF = None
LFs = list()
# calls = list()
labels = dict()

#####################################CREATING CLASSES##############################################


class Variable:
    def __init__(self, varType, value):
        self.type = varType
        self.value = value


class Argument:
    def __init__(self, argType, value):
        self.type = argType
        self.value = value


class Instruction:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.args = []

    def addArgument(self, argType, value):
        self.args.append(Argument(argType, value))
###################################################################################################


if (sourceFile == "None" and inputFile == "None"):
    stderr.write("ERROR: --source or --input must be set, exiting...\n")
    exit(10)

try:
    if (sourceFile == "None"):
        debug("reading source from stdin")
        tree = ET.parse(stdin)
    else:
        debug("source: " + sourceFile)
        tree = ET.parse(args.source)
except:
    stderr.write("Wrong XML format, exiting...\n")
    exit(31)

if (inputFile == "None"):
    debug("reading input from stdin")
    for line in stdin:
        inputLines.append(line)
else:
    debug("input: " + inputFile)
    file = open(inputFile, 'r')
    Lines = file.readlines()
    for line in Lines:
        inputLines.append(line)
root = tree.getroot()


######################################DEFINING FUNCTIONS###########################################

def printGF():
    debug("----------------------------GF------------------")
    for key, value in GF.items():
        debug(key+" "+value.type+" "+value.value)
    debug("------------------------------------------------\n")


##############################INSTRUCTION FUNCTIONS############################
def filter_instructions():
    try:
        debug("\nFinding instructions--------")
        for element in root.findall("./instruction"):
            debug(element.attrib)
            if (int(element.attrib["order"]) not in orderNumbers and int(element.attrib["order"]) >= 0):
                orderNumbers.append(int(element.attrib["order"]))
            else:
                raise
        debug("\n")
    except:
        stderr.write("Error occured when sorting <instruction>, exiting...\n")
        exit(32)
    orderNumbers.sort()


def sort_instructions():
    debug("Sorting instructions--------")
    if root.tag != 'program':
        stderr.write("Root tag is not program, exiting...\n")
        exit(32)

    # sort <instruction> tags by opcode
    try:
        root[:] = sorted(root, key=lambda child: (
            child.tag, int(child.get('order'))))
    except Exception as e:
        debug(str(e)+"\n")
        stderr.write(
            "Error occured when sorting <instruction> elements, exiting...\n")
        exit(32)

    # sort <arg#> elements
    for child in root:
        try:
            child[:] = sorted(child, key=lambda child: (child.tag))
        except Exception as e:
            debug(str(e)+"\n")
            stderr.write(
                "Error occured when sorting <arg#> elements, exiting...\n")
            exit(32)
    debug("\n")


def check_instructions():
    # XML INNER VALIDITY CHECKS
    # <program> check of correct 'language' attribute
    if not('language' in list(root.attrib.keys())):
        stderr.write("Unable to find 'language' attribute, exiting...\n")
        exit(32)

    if not(re.match(r"ippcode22", root.attrib['language'], re.IGNORECASE)):
        stderr.write("Wrong 'language' attribute value, exiting...\n")
        exit(32)

    # <instruction> checks of tag and correct attributes
    for child in root:
        if child.tag != 'instruction':
            stderr.write(
                "First level elements has to be called 'instruction', exiting...\n")
            exit(32)

        # check correct attributes
        attrib = list(child.attrib.keys())
        if not('order' in attrib) or not('opcode' in attrib):
            stderr.write(
                "<instruction> element has to have 'order' & 'opcode' attributes, exiting...\n")
            exit(32)

    # iterate over <instruction> elements
    for child in root:
        # check that there are not diplicates in child elements
        dup = set()
        for children in child:
            if children.tag not in dup:
                dup.add(children.tag)
        if len(dup) != len(child):
            stderr.write("Found duplicate <arg#> elements, exiting...\n")
            exit(32)

        # <arg#> checks
        for children in child:
            if not(re.match(r"arg[123]", children.tag)):
                stderr.write(
                    "Only <arg#> where # ranges from 1-3 are supported, exiting...\n")
                exit(32)

            # <arg#> attribute check
            att = list(children.attrib)
            if not('type' in att):
                stderr.write(
                    "<arg#> elements has to have 'type' attribute, exiting...\n")
                exit(32)


def fill_instructions():
    debug("Filling instructions list--------\n")
    iCount = 1
    tab = "    "
    for elem in root:
        debug(elem.attrib['opcode'])
        instructions.append(
            Instruction(elem.attrib['opcode'].upper(), iCount)
        )
        for subelem in elem:
            argval = ""
            try:
                debug(tab+subelem.attrib['type']+tab+subelem.text)
            except:
                debug(tab+subelem.attrib['type'])

            instructions[iCount-1].addArgument(
                subelem.attrib['type'].lower(), subelem.text
            )
        iCount += 1
###############################################################################


############################DATA TYPE CHECK FUNCTIONS##########################
def save_labels():
    # save labels
    for i in instructions:
        if i.name == "LABEL":
            labels.update({i.args[0].value: i.number})


def valid_var(var):
    if not(re.match(r"^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w_\-$&%*!?]*$", var.value)):
        stderr.write("Argument is not valid var, exiting...\n")
        exit(32)


def valid_label(var):
    if not(re.match(r"^[\w_\-$&?%*!]+$", var.value)):
        stderr.write("Argument is not valid var, exiting...\n")
        exit(32)


def valid_type(var):
    if not((re.match(r"^(string|int|bool)$", var.value))):
        stderr.write("Argument is not valid type, exiting...\n")
        exit(32)


def valid_symb(item):
    if item.type == "var":
        valid_var(item)
    else:
        if item.type == "int":
            if re.search(r"[^\d-]", item.value):
                stderr.write("Invalid value for int type, exiting...")
                exit(32)
        elif item.type == "nil":
            if item.value != "nil":
                stderr.write("Invalid value for nil type, exiting...\n")
                exit(32)
        elif item.type == "string":
            if re.match(r"(\\\\[^0-9])|(\\\\[0-9][^0-9])|(\\\\[0-9][0-9][^0-9])|(\\\\$)", item.value):
                stderr.write(
                    "Invalid number of digits for escaped character, exiting...\n")
                exit(32)
        elif item.type == "bool":
            if not(item.value == "true" or item.value == "false"):
                stderr.write("Invalid value for bool type, exiting...\n")
                exit(32)
###############################################################################


#######################INSTRUCTION CHECK FUNCTIONS#############################
def check_arg_count(first, second):
    if first != second:
        stderr.write(
            "Invalid number of arguments for given instruction, exiting...\n")
        exit(32)


def check_instruction_var(inst):
    if inst.args[0].type != "var":
        stderr.write("Invalid arg type, var expected, exiting...\n")
        exit(32)
    valid_var(inst.args[0])


def check_instruction_label(inst):
    if inst.args[0].type != "label":
        stderr.write("Invalid arg type, label expected, exiting...\n")
        exit(32)
    valid_label(inst.args[0])


def check_instruction_symb(inst):
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[0])


def check_instruction_var_or_symb(inst):
    if inst.args[0].type != "var":
        stderr.write("Invalid arg type, var expected, exiting...\n")
        exit(32)
    valid_var(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[1])


def check_instruction_var_or_type(inst):
    if inst.args[0].type != "var":
        stderr.write("Invalid arg type, var expected, exiting...\n")
        exit(32)
    valid_var(inst.args[0])
    if not(re.match(r"^(string|bool|int)$", inst.args[1].type)):
        stderr.write(
            "Invalid arg type, string, bool or int expected, exiting...\n")
        exit(32)
    valid_type(inst.args[1])


def check_instruction_label_or_symb(inst):
    if inst.args[0].type != "label":
        stderr.write("Invalid arg type, label expected, exiting...\n")
        exit(32)
    valid_label(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[1])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[2].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[2])


def check_instruction_var_or_symbol(inst):
    if inst.args[0].type != "var":
        stderr.write("Invalid arg type, var expected, exiting...\n")
        exit(32)
    valid_var(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[1])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        stderr.write("Invalid arg type, exiting...\n")
        exit(32)
    valid_symb(inst.args[2])


def check_instruction(instruction):
    debug("\nChecking instruction")
    debug(instruction.name)
    if (
            instruction.name == "CREATEFRAME" or
            instruction.name == "PUSHFRAME" or
            instruction.name == "POPFRAME" or
            instruction.name == "RETURN" or
            instruction.name == "BREAK"):
        check_arg_count(0, len(instruction.args))
    elif (
            instruction.name == "LABEL" or
            instruction.name == "JUMP" or
            instruction.name == "CALL"):
        check_arg_count(1, len(instruction.args))
        check_instruction_label(instruction)
    elif (
            instruction.name == "DEFVAR" or
            instruction.name == "POPS"):
        check_arg_count(1, len(instruction.args))
        check_instruction_var(instruction)
    elif (
            instruction.name == "PUSHS" or
            instruction.name == "WRITE" or
            instruction.name == "EXIT" or
            instruction.name == "DPRINT"):
        check_arg_count(1, len(instruction.args))
        check_instruction_symb(instruction)
    elif (instruction.name == "READ"):
        check_arg_count(2, len(instruction.args))
        check_instruction_var_or_type(instruction)
    elif (
            instruction.name == "MOVE" or
            instruction.name == "NOT" or
            instruction.name == "INT2CHAR" or
            instruction.name == "STRLEN" or
            instruction.name == "TYPE"):
        check_arg_count(2, len(instruction.args))
        check_instruction_var_or_symb(instruction)
    elif (
            instruction.name == "JUMPIFEQ" or
            instruction.name == "JUMPIFNEQ"):
        check_arg_count(3, len(instruction.args))
        check_instruction_label_or_symb(instruction)
    elif (
            instruction.name == "ADD" or
            instruction.name == "SUB" or
            instruction.name == "MUL" or
            instruction.name == "IDIV" or
            instruction.name == "LT" or
            instruction.name == "GT" or
            instruction.name == "EQ" or
            instruction.name == "AND" or
            instruction.name == "OR" or
            instruction.name == "STRI2INT" or
            instruction.name == "CONCAT" or
            instruction.name == "GETCHAR" or
            instruction.name == "SETCHAR"):
        check_arg_count(3, len(instruction.args))
        check_instruction_var_or_symbol(instruction)
    else:
        stderr.write("Invalid instruction name, exiting...\n")
        exit(32)
###############################################################################


#############################MEMORY FUNCTIONS##################################
# TODO
###############################################################################


############################INTERPRET FUNCTION#################################
def interpret_instruction(instruction):

    global position_pointer
    global TF
    global LFs
    print(position_pointer, instruction.name, instruction.args[0].value)
    if instruction.name == "CREATEFRAME":
        TF = dict()
    elif instruction.name == "PUSHFRAME":
        LFs.append(TF)
        TF = None
    elif instruction.name == "POPFRAME":
        if LFs.count == 0:
            stderr.write("Non existing frame in LF, exiting...\n")
            exit(55)
        TF = LFs.pop()
    elif instruction.name == "LABEL":
        pass
    elif instruction.name == "JUMP":
        labelName = instruction.args[0].value
        if not(labelName in labels.keys()):
            stderr.write("Label does not exist, exiting...\n")
            exit(52)
        position_pointer = int(labels[labelName]-1)
###############################################################################


###################################################################################################

###################CALLING FUNCTIONS FOR PREPARING AND CHECKING XML################################
filter_instructions()
sort_instructions()
check_instructions()
fill_instructions()
save_labels()
###################################################################################################


########################################CHECKING INSTRUCTIONS######################################
for i in instructions:
    check_instruction(i)
###################################################################################################


########################################INTERPRETING###############################################
print("INTERPRETING--------------")
while position_pointer != len(instructions):
    interpret_instruction(instructions[position_pointer])
    position_pointer += 1
print("INTERPRETING FINISHED-----")
###################################################################################################

print("LABELS : ", labels)

printGF()
