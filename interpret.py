#!/usr/bin/python3
import argparse
from operator import concat
from unittest import case
# from lxml import etree
import xml.etree.ElementTree as ET
import re
from sys import stderr, stdin, exit


def debug(s):
    if DEBUG:
        print(s)


DEBUG = False

parser = argparse.ArgumentParser(
    description='Interpret for IPPcode22 by - Tomas Ondrusek - xondru18 - VUT FIT - 4.2022')
parser.add_argument('--source', dest='source', type=str)
parser.add_argument('--input', dest='input', type=str)
args = parser.parse_args()
sourceFile = str(args.source)
inputFile = str(args.input)
inputLines = []
instructions = list()
GF = dict()
orderNumbers = []
stack = []
variablesStorage = {}
# output = ""
# outputErr = ""
position_pointer = 0
TF = None
LF = list()
call = list()
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
    def __init__(self, name, number, order):
        self.name = name
        self.number = number
        self.order = order
        self.args = []

    def addArgument(self, argType, value):
        self.args.append(Argument(argType, value))
###################################################################################################


######################################DEFINING FUNCTIONS###########################################

def print_gf():
    debug("----------------------------GF------------------")
    print("\nvariables in GF:")
    for var in GF:
        print(var, GF[var].type, GF[var].value)
    debug("------------------------------------------------\n")


def print_tf():
    debug("----------------------------GF------------------")
    print("\nvariables in TF:")
    try:
        for var in TF:
            print(var, TF[var].type, TF[var].value)
    except:
        pass
    debug("------------------------------------------------\n")


def print_lf():
    debug("----------------------------GF------------------")
    print("\nvariables in LF:")
    try:
        for item in LF:
            for var in item:
                print(var, item[var].type, item[var].value)
    except:
        pass
    debug("------------------------------------------------\n")


def print_stack():
    debug("----------------------------stack------------------")
    print("\nvariables in stack:")
    for var in stack:
        print(var.type, var.value)
    debug("------------------------------------------------\n")


def print_err_and_exit(string, ret_code):
    global position_pointer
    try:
        stderr.write('\033[91m' + string + ". Error occured on : " +
                     instructions[position_pointer].name+" with order number : "+str(instructions[position_pointer].order)+", exiting...\n" + '\033[0m')
    except:
        stderr.write('\033[91m' + string + ", exiting...\n" + '\033[0m')
    exit(ret_code)

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
        print_err_and_exit(
            "Error occured when sorting <instruction>", 32)
    orderNumbers.sort()


def sort_instructions():
    debug("Sorting instructions--------")
    if root.tag != 'program':
        print_err_and_exit("Root tag is not program", 32)

    # sort <instruction> tags by opcode
    try:
        root[:] = sorted(root, key=lambda child: (
            child.tag, int(child.get('order'))))
    except Exception as e:
        debug(str(e)+"\n")
        print_err_and_exit(
            "Error occured when sorting <instruction> elements", 32)

    # sort <arg#> elements
    for child in root:
        try:
            child[:] = sorted(child, key=lambda child: (child.tag))
        except Exception as e:
            debug(str(e)+"\n")
            print_err_and_exit(
                "Error occured when sorting <arg#> elements", 32)
    debug("\n")


def check_instructions():
    # XML INNER VALIDITY CHECKS
    # <program> check of correct 'language' attribute
    if not('language' in list(root.attrib.keys())):
        print_err_and_exit(
            "Unable to find 'language' attribute", 32)

    if not(re.match(r"ippcode22", root.attrib['language'], re.IGNORECASE)):
        print_err_and_exit(
            "Wrong 'language' attribute value", 32)

    # <instruction> checks of tag and correct attributes
    for child in root:
        if child.tag != 'instruction':
            print_err_and_exit(
                "First level elements has to be called 'instruction'", 32)

        # check correct attributes
        attrib = list(child.attrib.keys())
        if not('order' in attrib) or not('opcode' in attrib):
            print_err_and_exit(
                "<instruction> element has to have 'order' & 'opcode' attributes", 32)

    # iterate over <instruction> elements
    for child in root:
        # check that there are not diplicates in child elements
        dup = set()
        for children in child:
            if children.tag not in dup:
                dup.add(children.tag)
        if len(dup) != len(child):
            print_err_and_exit(
                "Found duplicate <arg#> elements", 32)

        # <arg#> checks
        for children in child:
            if not(re.match(r"arg[123]", children.tag)):
                print_err_and_exit(
                    "Only <arg#> where # ranges from 1-3 are supported", 32)

            # <arg#> attribute check
            att = list(children.attrib)
            if not('type' in att):
                print_err_and_exit(
                    "<arg#> elements has to have 'type' attribute", 32)


def fill_instructions():
    debug("Filling instructions list--------\n")
    iCount = 1
    tab = "    "
    for elem in root:
        debug(elem.attrib['opcode'])
        instructions.append(
            Instruction(elem.attrib['opcode'].upper(),
                        iCount, int(elem.attrib['order']))
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
        print_err_and_exit("Argument is not valid var", 32)


def valid_label(var):
    if not(re.match(r"^[\w_\-$&?%*!]+$", var.value)):
        print_err_and_exit("Argument is not valid var", 32)


def valid_type(var):
    if not((re.match(r"^(string|int|bool)$", var.value))):
        print_err_and_exit("Argument is not valid type", 32)


def valid_symb(item):
    if item.type == "var":
        valid_var(item)
    else:
        if item.type == "int":
            if re.search(r"[^\d-]", item.value):
                print_err_and_exit(
                    "Invalid value for int type", 32)
        elif item.type == "nil":
            if item.value != "nil":
                print_err_and_exit(
                    "Invalid value for nil type", 32)
        elif item.type == "string":
            if item.value != None:
                if re.match(r"(\\\\[^0-9])|(\\\\[0-9][^0-9])|(\\\\[0-9][0-9][^0-9])|(\\\\$)", item.value):
                    print_err_and_exit(
                        "Invalid number of digits for escaped character", 32)
        elif item.type == "bool":
            if not(item.value == "true" or item.value == "false"):
                print_err_and_exit(
                    "Invalid value for bool type", 32)
###############################################################################


#######################INSTRUCTION CHECK FUNCTIONS#############################
def check_arg_count(first, second):
    if first != second:
        print_err_and_exit(
            "Invalid number of arguments for given instruction", 32)


def check_instruction_var(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])


def check_instruction_label(inst):
    if inst.args[0].type != "label":
        print_err_and_exit(
            "Invalid arg type, label expected", 32)
    valid_label(inst.args[0])


def check_instruction_symb(inst):
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[0])


def check_instruction_var_or_symb(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[1])


def check_instruction_var_or_type(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])
    if not(re.match(r"^(string|bool|int)$", inst.args[1].type)):
        print_err_and_exit(
            "Invalid arg type, string, bool or int expected", 32)
    valid_type(inst.args[1])


def check_instruction_label_or_symb(inst):
    if inst.args[0].type != "label":
        print_err_and_exit(
            "Invalid arg type, label expected", 32)
    valid_label(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[1])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[2].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[2])


def check_instruction_var_or_symbol(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[1])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[1].type)):
        print_err_and_exit("Invalid arg type", 32)
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
        print_err_and_exit("Invalid instruction name", 32)
###############################################################################


#############################MEMORY FUNCTIONS##################################
def get_variable(frame, var_name):
    global TF
    global LF
    if frame == "GF":
        if not var_name in GF.keys():
            print_err_and_exit("Non existing variable", 54)
        return GF[var_name]
    elif frame == "TF":
        if TF == None:
            print_err_and_exit("TF not initialized", 55)
        if not var_name in TF.keys():
            print_err_and_exit("Non existing variable", 54)
        return TF[var_name]
    elif frame == "LF":
        if len(LF) == 0:
            print_err_and_exit("No frame in LFs stack", 55)
        if not var_name in LF[len(LF)-1].keys():
            print_err_and_exit("Non existing variable", 54)
        return LF[len(LF)-1][var_name]
    else:
        print_err_and_exit("Not supported frame found", 99)


def find_variable(frame, var_name):
    if frame == "GF":
        if not(var_name in GF.keys()):
            print_err_and_exit("Non existing variable", 54)
    elif frame == "TF":
        if TF == None:
            print_err_and_exit("TF not initialized", 55)
        if not(var_name in TF.keys()):
            print_err_and_exit("Non existing variable", 54)
    elif frame == "LF":
        if len(LF) == 0:
            print_err_and_exit("No frame in LF stack", 55)
        if not(var_name in LF[len(LF)-1].keys()):
            print_err_and_exit("Non existing variable", 54)
    else:
        print_err_and_exit("Not supported frame found", 99)


def update_variable(frame, var_name, argument):
    if re.match(r"(int|bool|string|nil)", argument.type):
        if frame == "GF":
            GF[var_name] = Variable(argument.type, argument.value)
        elif frame == "TF":
            if TF == None:
                print_err_and_exit("TF not initialized", 55)
            TF[var_name] = Variable(argument.type, argument.value)
        elif frame == "LF":
            if len(LF) == 0:
                print_err_and_exit("No frame in LF stack", 55)
            LF[len(LF)-1][var_name] = Variable(argument.type, argument.value)
        else:
            print_err_and_exit("Unsupported frame passed", 55)
    elif argument.type == "var":
        tmp = argument.value.split("@")
        find_variable(tmp[0], tmp[1])
        hold = get_variable(tmp[0], tmp[1])
        if frame == "GF":
            GF[var_name] = Variable(hold.type, hold.value)
        elif frame == "TF":
            if TF == None:
                print_err_and_exit("TF not initialized", 55)
            TF[var_name] = Variable(hold.type, hold.value)
        elif frame == "LF":
            if len(LF) == 0:
                print_err_and_exit("No frame in LF stack", 55)
            LF[len(LF)-1][var_name] = Variable(hold.type, hold.value)
        else:
            print_err_and_exit("Unsupported frame passed", 55)

    else:
        print_err_and_exit(
            "Unexpected error when saving to variable", 99)
###############################################################################

#####################INTERPRET INSTRUCTION FUNCTIONS###########################


def instr_defvar(var):
    splitted = var.value.split("@")
    tmp = Variable(None, None)
    if splitted[0] == "GF":
        if splitted[1] in GF.keys():
            print_err_and_exit("Variable already exists", 52)
        GF.update({splitted[1]: tmp})
    elif splitted[0] == "TF":
        if TF == None:
            print_err_and_exit("TF not initialized", 52)
        if splitted[1] in TF.keys():
            print_err_and_exit("Variable already exists", 52)
        TF.update({splitted[1]: tmp})
    elif splitted[0] == "LF":
        if len(LF) == 0:
            print_err_and_exit("No LF in stack", 52)
        if splitted[1] in LF[len(LF)-1].keys():
            print_err_and_exit("Variable already exists", 52)
        LF[len(LF)-1].update({splitted[1]: tmp})


def instr_call(argument, current_pos):
    global position_pointer
    call.append(current_pos)
    if not(argument.value in labels.keys()):
        print_err_and_exit("Label does not exist", 52)
    position_pointer = int(labels[argument.value]-1)


def instr_return():
    global position_pointer
    if len(call) == 0:
        print_err_and_exit(
            "Return without call", 56)
    pos = call.pop()
    position_pointer = int(pos-1)


def instr_aritmetic(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var2.type != "int" or var3.type != "int":
        print_err_and_exit("Arguments has to be of type int", 53)

    if instruction.name == "ADD":
        new_arg = Argument("int", int(var2.value) + int(var3.value))
    elif instruction.name == "SUB":
        new_arg = Argument("int", int(var2.value) - int(var3.value))
    elif instruction.name == "MUL":
        new_arg = Argument("int", int(var2.value) * int(var3.value))
    elif instruction.name == "IDIV":
        if int(var3.value) == 0:
            print_err_and_exit("Division by 0", 57)
        new_arg = Argument("int", int(var2.value) // int(var3.value))

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_boolean(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    try:
        var3 = instruction.args[2]
        if var3.type == "var":
            tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])
    except:
        pass

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])

    if var2.type != "bool" or var3.type != "bool":
        print_err_and_exit("Arguments has to be of type bool", 53)

    if instruction.name == "AND":
        if var2.value == "false" or var3.value == "false":
            new_arg = Argument("bool", "false")
        else:
            new_arg = Argument("bool", "true")
    elif instruction.name == "OR":
        if var2.value == "false" and var3.value == "false":
            new_arg = Argument("bool", "false")
        else:
            new_arg = Argument("bool", "true")
    elif instruction.name == "NOT":
        if var2.value == "false":
            new_arg = Argument("bool", "true")
        else:
            new_arg = Argument("bool", "false")

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_relational(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var2.type == "int" and var3.type != "int":
        print_err_and_exit("Arguments has to be of same type", 53)
    if var2.type == "bool" and var3.type != "bool":
        print_err_and_exit("Arguments has to be of same type", 53)
    if var2.type == "string" and var3.type != "string":
        print_err_and_exit("Arguments has to be of same type", 53)

    if instruction.name == "GT":
        if var2.type == "int":
            if int(var2.value) > int(var3.value):
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "bool":
            if var2.value == "true" and var3.value == "false":
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "string":
            if var2.value > var3.value:
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "nil" or var3.type == "nil":
            print_err_and_exit(
                "Argument can not be nil while performing GT", 53)
    elif instruction.name == "LT":
        if var2.type == "int":
            if int(var2.value) < int(var3.value):
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "bool":
            if var2.value == "false" and var3.value == "true":
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "string":
            if var2.value < var3.value:
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "nil" or var3.type == "nil":
            print_err_and_exit(
                "Argument can not be nil while performing LT", 53)

    elif instruction.name == "EQ":
        if var2.type == "int":
            if int(var2.value) == int(var3.value):
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "bool":
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "string":
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")
        elif var2.type == "nil" or var3.type == "nil":
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")
            else:
                new_arg = Argument("bool", "false")

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_int_to_char(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    if var1.type != "int":
        print_err_and_exit(
            "Argument has to be of type int to be converted to char", 53)

    try:
        new_val = chr(int(var1.value))
    except:
        print_err_and_exit("Error while converting int to string", 58)
    new_arg = Argument("string", new_val)

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_string_to_int(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var2.type != "string":
        print_err_and_exit("Arguments has to be of type string", 53)
    if var3.type != "int":
        print_err_and_exit("Arguments has to be of type int", 53)
    if var2.value == None or int(var3.value) >= len(var2.value) or int(var3.value) < 0:
        print_err_and_exit("Index out of range", 58)

    new_arg = Argument("int", ord(var2.value[int(var3.value)]))

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_strlen(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    if var1.type != "string":
        print_err_and_exit(
            "Argument has to be of type string to find its length", 53)

    if var1.value == None:
        new_arg = Argument("int", 0)
    else:
        new_arg = Argument("int", len(var1.value))

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_concat(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var2.type != "string":
        print_err_and_exit(
            "Arguments has to be of type string to concatenate", 53)
    if var3.type != "string":
        print_err_and_exit(
            "Arguments has to be of type string to concatenate", 53)
    if var2.value == None:
        new_arg = Argument("string", var3.value)
    elif var3.value == None:
        new_arg = Argument("string", var2.value)
    else:
        new_arg = Argument("string", var2.value + var3.value)

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_getchar(instruction):
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var2.type != "string":
        print_err_and_exit("Arguments has to be of type string", 53)
    if var3.type != "int":
        print_err_and_exit("Arguments has to be of type int", 53)
    if var2.value == None or int(var3.value) >= len(var2.value) or int(var3.value) < 0:
        print_err_and_exit("Index out of range", 58)

    new_arg = Argument("string", var2.value[int(var3.value)])

    tmp = var1.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_setchar(instruction):
    var = instruction.args[0]
    var1 = instruction.args[0]
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var1.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])
    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if var1.type != "string":
        print_err_and_exit("Arguments has to be of type strinnnng", 53)
    if var2.type != "int":
        print_err_and_exit("Arguments has to be of type int", 53)
    if var3.type != "string":
        print_err_and_exit("Arguments has to be of type striiiing", 53)
    if var1.value == None or int(var2.value) >= len(var1.value) or int(var2.value) < 0:
        print_err_and_exit("Index out of range", 58)

    if var3.value == None:
        print_err_and_exit("Can not change string with empty character", 58)
    new_var = var1.value[:int(var2.value)] + \
        var3.value[0] + var1.value[int(var2.value)+1:]

    new_arg = Argument("string", new_var)

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_type(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    new_arg = Argument("string", var1.type)

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_jmpeq(instruction):
    global position_pointer
    var1 = instruction.args[0].value
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if (var2.type != var3.type):
        if (var2.type == "nil" or var3.type == "nil"):
            return
        print_err_and_exit("Variables are of different type", 53)

    if (var2.value == var3.value):
        if not(var1 in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifeq", 52)
        position_pointer = int(labels[var1]-1)


def instr_jmpneq(instruction):
    global position_pointer
    var1 = instruction.args[0].value
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")
        var2 = get_variable(tmp[0], tmp[1])
    if var3.type == "var":
        tmp = var3.value.split("@")
        var3 = get_variable(tmp[0], tmp[1])

    if (var2.type != var3.type):
        if (var2.type == "nil" or var3.type == "nil"):
            return
        print_err_and_exit("Variables are of different type", 53)
    if (var2.value != var3.value):
        if not(var1 in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifneq", 52)
        position_pointer = int(labels[var1]-1)


def instr_write(symb):
    var = symb
    if symb.type == "var":
        tmp = var.value.split("@")
        var = get_variable(tmp[0], tmp[1])

    if var.type == "nil":
        print("", end='')
    elif var.type == "bool":
        if var.value == "true":
            print('\033[92m' + "true"+'\033[0m')
            # print("true", end='')
        else:
            print('\033[92m' + "false"+'\033[0m')
            # print("true", end='')
    else:
        print('\033[92m' + var.value+'\033[0m')
        # print(var.value, end='')


def instr_read(var, type):
    var1 = var
    if var.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    type_var = type.value
    if len(inputLines) == 0:
        poped = "nil"
        type_var = "nil"
    else:
        poped = inputLines[0].strip()
        inputLines.remove(inputLines[0])
    print(inputLines, poped)

    if type_var == "int":
        new_arg = Argument("int", int(poped))
    elif type_var == "bool":
        if poped.upper == "TRUE":
            new_arg = Argument("bool", "true")
        else:
            new_arg = Argument("bool", "false")
    elif type_var == "string":
        new_arg = Argument("string", poped)
    elif type_var == "nil":
        new_arg = Argument("nil", "nil")

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)


def instr_exit(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    if var1.type != "int":
        print_err_and_exit("Type of symbol is not int", 57)

    if int(var1.value) < 0 or int(var1.value) > 49:
        print_err_and_exit("Invalid value for exit", 57)

    exit(int(var1.value))

    # TODO vypis statistik


def instr_dprint(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])
    stderr.write(var1.value + "\n")


def instr_pushs(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")
        var1 = get_variable(tmp[0], tmp[1])

    new_arg = Variable(var1.type, var1.value)
    stack.append(new_arg)


def instr_pops(var):
    if len(stack) == 0:
        print_err_and_exit("Empty stack", 56)

    poped = stack.pop()
    new_arg = Argument(poped.type, poped.value)

    tmp = var.value.split("@")
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)

    ###############################################################################

    ############################INTERPRET FUNCTION#################################


def interpret_instruction(instruction):

    global position_pointer
    global TF
    global LF
    try:
        print(position_pointer, instruction.name)
    except:
        pass
    if instruction.name == "CREATEFRAME":
        TF = dict()
    elif instruction.name == "PUSHFRAME":
        if TF == None:
            print_err_and_exit(
                "TF not initialized for pushing to LF", 55)
        LF.append(TF)
        TF = None
    elif instruction.name == "POPFRAME":
        if len(LF) == 0:
            print_err_and_exit("Non existing frame in LF", 55)
        TF = LF.pop()
    elif instruction.name == "LABEL":
        pass
    elif instruction.name == "JUMP":
        labelName = instruction.args[0].value
        if not(labelName in labels.keys()):
            print_err_and_exit("Label does not exist", 52)
        position_pointer = int(labels[labelName]-1)
    elif instruction.name == "DEFVAR":
        instr_defvar(instruction.args[0])
    elif instruction.name == "MOVE":
        splittedVar = instruction.args[0].value.split("@")
        find_variable(splittedVar[0], splittedVar[1])
        update_variable(splittedVar[0], splittedVar[1], instruction.args[1])
    elif instruction.name == "CALL":
        instr_call(instruction.args[0], instruction.number)
    elif instruction.name == "RETURN":
        instr_return()
    elif instruction.name == "ADD" or instruction.name == "SUB" or instruction.name == "MUL" or instruction.name == "IDIV":
        instr_aritmetic(instruction)
    elif instruction.name == "AND" or instruction.name == "OR" or instruction.name == "NOT":
        instr_boolean(instruction)
    elif instruction.name == "LT" or instruction.name == "GT" or instruction.name == "EQ":
        instr_relational(instruction)
    elif instruction.name == "INT2CHAR":
        instr_int_to_char(instruction.args[0], instruction.args[1])
    elif instruction.name == "STRI2INT":
        instr_string_to_int(instruction)
    elif instruction.name == "STRLEN":
        instr_strlen(instruction.args[0], instruction.args[1])
    elif instruction.name == "CONCAT":
        instr_concat(instruction)
    elif instruction.name == "GETCHAR":
        instr_getchar(instruction)
    elif instruction.name == "SETCHAR":
        instr_setchar(instruction)
    elif instruction.name == "TYPE":
        instr_type(instruction.args[0], instruction.args[1])
    elif instruction.name == "JUMPIFEQ":
        instr_jmpeq(instruction)
    elif instruction.name == "JUMPIFNEQ":
        instr_jmpneq(instruction)
    elif instruction.name == "WRITE":
        instr_write(instruction.args[0])
    elif instruction.name == "READ":
        instr_read(instruction.args[0], instruction.args[1])
    elif instruction.name == "EXIT":
        instr_exit(instruction.args[0])
    elif instruction.name == "BREAK":
        stderr.write("BREAK on instruction order " +
                     str(instruction.order) + "\n")
    elif instruction.name == "DPRINT":
        instr_dprint(instruction.args[0])
    elif instruction.name == "PUSHS":
        instr_pushs(instruction.args[0])
    elif instruction.name == "POPS":
        instr_pops(instruction.args[0])
###############################################################################


###################################################################################################


##################################SOURCE FILES HANDLING############################################
if (sourceFile == "None" and inputFile == "None"):
    print_err_and_exit(
        "ERROR: --source or --input must be set", 10)

try:
    if (sourceFile == "None"):
        debug("reading source from stdin")
        tree = ET.parse(stdin)
    else:
        debug("source: " + sourceFile)
        tree = ET.parse(args.source)
except:
    print_err_and_exit("Wrong XML format", 31)

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
print("------------------INTERPRETING---------------------------")
while position_pointer != len(instructions):
    interpret_instruction(instructions[position_pointer])
    position_pointer += 1
print("------------------INTERPRETING FINISHED WITH SUCCESS-----")
###################################################################################################

print("LABELS : ", labels)

print_gf()
print_tf()
print_lf()
print_stack()
