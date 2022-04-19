#!/usr/bin/python3

#  ****************************************************************************
#  *   IPP                                                                    *
#  *                                                                          *
#  *   Implementacia interpreta pre jazyk IPPcode22                           *
#  *                                                                          *
#  *	 Ondrušek Tomáš	xondru18                                              *
#  *                                                                          *
#  ****************************************************************************

###################################################################################################
# ----- importing dependencies -----
import argparse
import xml.etree.ElementTree as ET
import re
from sys import stderr, stdin, exit, argv

###################################################################################################
# ----- global debug -----
DEBUG = False

###################################################################################################
# ----- function prints out debug string -----


def debug(s):
    if DEBUG:
        print(s)

###################################################################################################
# ----- argument parsing -----


parser = argparse.ArgumentParser(
    description='Interpret for IPPcode22 by - Tomas Ondrusek - xondru18 - VUT FIT - 4.2022')
parser.add_argument('--source', dest='source', type=str)
parser.add_argument('--input', dest='input', type=str)
parser.add_argument('--stats', default=None, dest='stats', type=str)
parser.add_argument('--insts', dest='insts', action='count')
parser.add_argument('--vars', dest='vars', action='count')
parser.add_argument('--hot', dest='hot', action='count')
args = parser.parse_args()
args_order = []
sourceFile = str(args.source)
inputFile = str(args.input)
statiFile = str(args.stats)
for i in range(1, len(argv)):
    if argv[i] == "--vars" or argv[i] == "--insts" or argv[i] == "--hot":
        stat_arg = argv[i]
        stat_arg = stat_arg.replace("--", '')
        args_order.append(stat_arg)

###################################################################################################
# ----- global variables -----

inputLines = []
instructions = list()
GF = dict()
orderNumbers = []
position_pointer = 0
TF = None
LF = list()
call = list()
labels = dict()
vars = 0
insts = 0

#####################################CREATING CLASSES##############################################

###################################################################################################
# ----- Class for Variables -----


class Variable:
    def __init__(self, varType, value):
        self.type = varType
        self.value = value

###################################################################################################
# ----- Class for Arguments -----


class Argument:
    def __init__(self, argType, value):
        self.type = argType
        self.value = value

###################################################################################################
# ----- Class for Instructions -----


class Instruction:
    def __init__(self, name, number, order):
        self.name = name
        self.number = number
        self.order = order
        self.args = []

    def addArgument(self, argType, value):
        self.args.append(Argument(argType, value))

###################################################################################################
# ----- Class defining adt stack -----


class Stack:
    def __init__(self):
        self.item = []

    def is_empty(self):
        return self.item == []

    def push(self, data):
        self.item.append(data)

    def pop(self):
        return self.item.pop()

    def clear(self):
        stack.item = []

###################################################################################################
# ----- Class for handling hot statistic -----


class HotInst:
    def __init__(self, name, order):
        self.name = name
        self.order = order
        self.count = 1

    def get_order(self):
        return self.order

    def inc_count(self):
        self.count = self.count + 1

    def min_ord(self, order):
        if self.order > order:
            self.order = order

    def print_hot(self):
        print("Meno: ", self.name, " order: ",
              self.order, " count: ", self.count)

###################################################################################################
# ----- Subclass for handling hot statistic -----


class Hot:
    def __init__(self):
        self.insts = []

    def add(self, name, order):
        found = False
        for instr in self.insts:
            if instr.name == name:
                found = True
        if found:
            for instr in self.insts:
                if instr.name == name:
                    instr.inc_count()
                    instr.min_ord(order)
        else:
            self.insts.append(HotInst(name, order))

    def print_my(self):
        for instr in self.insts:
            print("Name: ", instr.name, " Order: ",
                  instr.order, " Count: ", instr.count)

    def get_hottest(self):
        try:
            ins = self.insts[0]
            for instr in self.insts:
                if ins.count < instr.count:
                    ins = instr
            instrs = []
            for instr in self.insts:
                if ins.count == instr.count:
                    instrs.append(instr)
            for instr in instrs:
                if ins.order > instr.order:
                    ins = instr
            return ins
        except:
            return ""


###################################################################################################
stack = Stack()

######################################DEFINING FUNCTIONS###########################################

###################################################################################################
# ----- Functions for printing frames and stack -----


def print_gf():
    debug("----------------------------GF------------------")
    print('\033[96m' + "\nvariables in GF:" + '\033[0m')
    for var in GF:
        print(var, GF[var].type, GF[var].value)
    print("******************************")
    debug("------------------------------------------------\n")


def print_tf():
    debug("----------------------------TF------------------")
    print('\033[96m' + "\nvariables in TF:" + '\033[0m')
    try:
        for var in TF:
            print(var, TF[var].type, TF[var].value)
    except:
        pass
    print("******************************")
    debug("------------------------------------------------\n")


def print_lf():
    debug("----------------------------LF------------------")
    print('\033[96m' + "\nvariables in LF:" + '\033[0m')
    try:
        for item in LF:
            for var in item:
                print(var, item[var].type, item[var].value)
    except:
        pass
    print("******************************")
    debug("------------------------------------------------\n")


def print_stack():
    debug("----------------------------stack------------------")
    print('\033[96m' + "\nvariables in stack:" + '\033[0m')
    for var in stack.item:
        print(var.type, var.value)
    print("******************************")
    debug("------------------------------------------------\n")

###################################################################################################
# ----- Function counts all currently declared variables -----


def get_vars_count():
    counter = len(GF)
    try:
        counter += len(TF)
    except:
        pass
    try:
        for item in LF:
            counter += len(item)
    except:
        pass
    return counter

###################################################################################################
# ----- Function for processing stats -----


def process_stats():
    debug(args.stats)
    if args.stats == None:  # not initialized variable
        return
    if len(args_order) != 0 and args.stats == None:  # not initialized variable
        print_err_and_exit("Stats file option not set", 10)
    stat_file = open(args.stats, 'w')
    for stat_item in args_order:
        if stat_item == "vars":
            stat_file.write(str(vars))
        elif stat_item == "insts":
            stat_file.write(str(insts))
        elif stat_item == "hot":
            stat_file.write(str(hot.get_hottest().get_order()))
        stat_file.write('\n')
    stat_file.close()

###################################################################################################
# ----- Function for printing out errors and returning error code -----


def print_err_and_exit(string, ret_code):
    global position_pointer  # extend position pointer to function
    try:
        stderr.write('\033[91m' + string + ". Error occured on : " +
                     instructions[position_pointer].name+" with order number : "+str(instructions[position_pointer].order)+", exiting...\n" + '\033[0m')
    except:
        stderr.write('\033[91m' + string + ", exiting...\n" + '\033[0m')
    exit(ret_code)
##############################INSTRUCTION FUNCTIONS############################

# ----- Function filters instructions -----


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

# ----- Function sorts instructions based on order and arg parameters -----


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

# ----- Function checks instructions-----


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

# ----- Function fill instructions into instruction list of Instruction classes -----


def fill_instructions():
    debug("Filling instructions list--------\n")
    iCount = 1
    tab = "    "
    for elem in root:
        debug(elem.attrib['opcode'])
        if int(elem.attrib['order']) < 1:
            print_err_and_exit(
                "elements has to have order > 0", 32)
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
            if subelem.attrib['type'].lower() == "string":
                string = subelem.text
                try:
                    escaped = re.findall("\\\\\d\d\d", string)
                    for escape_sequence in escaped:
                        string = string.replace(escape_sequence, chr(
                                                int(escape_sequence.lstrip('\\'))))
                except:
                    pass
                instructions[iCount-1].addArgument(
                    subelem.attrib['type'].lower(), string)
            else:
                instructions[iCount-1].addArgument(
                    subelem.attrib['type'].lower(), subelem.text
                )
        iCount += 1
###############################################################################


############################DATA TYPE CHECK FUNCTIONS##########################
# ----- Function saves all labels -----
def save_labels():
    # save labels
    for i in instructions:
        if i.name == "LABEL":
            if i.args[0].value in labels:
                print_err_and_exit("Duplicite label found", 52)
            else:
                labels.update({i.args[0].value: i.number})

# ----- Function checks valid variable -----


def valid_var(var):
    if not(re.match(r"^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w_\-$&%*!?]*$", var.value)):
        print_err_and_exit("Argument is not valid var", 32)

# ----- Function checks valid label -----


def valid_label(var):
    if not(re.match(r"^[\w_\-$&?%*!]+$", var.value)):
        print_err_and_exit("Argument is not valid var", 32)

# ----- Function checks valid type -----


def valid_type(var):
    if not((re.match(r"^(string|int|bool)$", var.value))):
        print_err_and_exit("Argument is not valid type", 32)

# ----- Function checks valid symbol -----


def valid_symb(item):
    if item.type == "var":
        valid_var(item)
    else:
        if item.type == "int":  # if var is type int
            if re.search(r"[^\d-]", item.value):
                print_err_and_exit(
                    "Invalid value for int type", 32)
        elif item.type == "nil":  # if var is type nil
            if item.value != "nil":
                print_err_and_exit(
                    "Invalid value for nil type", 32)
        elif item.type == "string":  # if var is type string
            if item.value != None:
                if re.match(r"(\\\\[^0-9])|(\\\\[0-9][^0-9])|(\\\\[0-9][0-9][^0-9])|(\\\\$)", item.value):
                    print_err_and_exit(
                        "Invalid number of digits for escaped character", 32)
        elif item.type == "bool":  # if var is type bool
            # save false :
            if not(item.value == "true" or item.value == "false"):
                print_err_and_exit(
                    "Invalid value for bool type", 32)
###############################################################################


#######################INSTRUCTION CHECK FUNCTIONS#############################
# ----- Function compares arg count to referenced count -----
def check_arg_count(first, second):
    if first != second:
        print_err_and_exit(
            "Invalid number of arguments for given instruction", 32)

# ----- Function checks valid variable -----


def check_instruction_var(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])

# ----- Function checks valid label -----


def check_instruction_label(inst):
    if inst.args[0].type != "label":
        print_err_and_exit(
            "Invalid arg type, label expected", 32)
    valid_label(inst.args[0])

# ----- Function checks valid symb -----


def check_instruction_symb(inst):
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[0])

# ----- Function checks valid variable or symbol -----


def check_instruction_var_or_symb(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])
    if not(re.match(r"^(var|string|bool|int|nil)$", inst.args[0].type)):
        print_err_and_exit("Invalid arg type", 32)
    valid_symb(inst.args[1])

# ----- Function checks valid variable or type -----


def check_instruction_var_or_type(inst):
    if inst.args[0].type != "var":
        print_err_and_exit("Invalid arg type, var expected", 32)
    valid_var(inst.args[0])
    if not(re.match(r"^(type)$", inst.args[1].type)):
        print_err_and_exit(
            "Invalid arg type, type expected", 32)
    valid_type(inst.args[1])

# ----- Function checks valid label or symbol -----


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

# ----- Function checks valid variable or symbol -----


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

# ----- Function checks instructions and its arg count and arg type -----


def check_instruction(instruction):
    debug("\nChecking instruction")
    debug(instruction.name)
    if (
            instruction.name == "CREATEFRAME" or
            instruction.name == "PUSHFRAME" or
            instruction.name == "POPFRAME" or
            instruction.name == "RETURN" or
            instruction.name == "BREAK" or
            instruction.name == "CLEARS" or
            instruction.name == "ADDS" or
            instruction.name == "SUBS" or
            instruction.name == "MULS" or
            instruction.name == "IDIVS" or
            instruction.name == "LTS" or
            instruction.name == "GTS" or
            instruction.name == "EQS" or
            instruction.name == "ANDS" or
            instruction.name == "ORS" or
            instruction.name == "NOTS" or
            instruction.name == "INT2CHARS" or
            instruction.name == "STRI2INTS"
    ):
        check_arg_count(0, len(instruction.args))
    elif (
            instruction.name == "LABEL" or
            instruction.name == "JUMP" or
            instruction.name == "CALL" or
            instruction.name == "JUMPIFEQS" or
            instruction.name == "JUMPIFNEQS"):
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
            instruction.name == "NOTS" or
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
# ----- Function gets variable from frame -----
def get_variable(frame, var_name):
    global TF
    global LF
    if frame == "GF":
        if not var_name in GF.keys():
            print_err_and_exit("Non existing variable", 54)
        return GF[var_name]
    elif frame == "TF":
        if TF == None:  # not initialized variable
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

# ----- Function finds variable from frame -----


def find_variable(frame, var_name):
    if frame == "GF":
        if not(var_name in GF.keys()):
            print_err_and_exit("Non existing variable", 54)
    elif frame == "TF":
        if TF == None:  # not initialized variable
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

# ----- Function updates variable in frame -----


def update_variable(frame, var_name, argument):
    # if value inserted is data type
    if re.match(r"(int|bool|string|nil)", argument.type):
        if frame == "GF":
            GF[var_name] = Variable(argument.type, argument.value)
        elif frame == "TF":
            if TF == None:  # not initialized variable
                print_err_and_exit("TF not initialized", 55)
            TF[var_name] = Variable(argument.type, argument.value)
        elif frame == "LF":
            if len(LF) == 0:
                print_err_and_exit("No frame in LF stack", 55)
            LF[len(LF)-1][var_name] = Variable(argument.type, argument.value)
        else:
            print_err_and_exit("Unsupported frame passed", 55)
    # if value inserted is from another variable
    elif argument.type == "var":
        tmp = argument.value.split("@")  # split by @
        find_variable(tmp[0], tmp[1])
        hold = get_variable(tmp[0], tmp[1])
        if frame == "GF":
            GF[var_name] = Variable(hold.type, hold.value)
        elif frame == "TF":
            if TF == None:  # not initialized variable
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
    splitted = var.value.split("@")  # split by @
    tmp = Variable(None, None)
    if splitted[0] == "GF":
        if splitted[1] in GF.keys():
            print_err_and_exit("Variable already exists", 52)
        GF.update({splitted[1]: tmp})
    elif splitted[0] == "TF":
        if TF == None:  # not initialized variable
            print_err_and_exit("TF not initialized", 55)
        if splitted[1] in TF.keys():
            print_err_and_exit("Variable already exists", 52)
        TF.update({splitted[1]: tmp})
    elif splitted[0] == "LF":
        if len(LF) == 0:
            print_err_and_exit("No LF in stack", 55)
        if splitted[1] in LF[len(LF)-1].keys():
            print_err_and_exit("Variable already exists", 52)
        LF[len(LF)-1].update({splitted[1]: tmp})


def instr_call(argument, current_pos):
    global position_pointer  # extend position pointer to function
    call.append(current_pos)
    if not(argument.value in labels.keys()):
        print_err_and_exit("Label does not exist", 52)
    position_pointer = int(labels[argument.value]-1)  # jump to label


def instr_return():
    global position_pointer  # extend position pointer to function
    if len(call) == 0:
        print_err_and_exit(
            "Return without call", 56)  # uninitialized
    pos = call.pop()  # pop from call variable
    position_pointer = int(pos-1)  # jump to call instruction


def instr_aritmetic(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var2.type != "int" or var3.type != "int":
        print_err_and_exit("Arguments has to be of type int",
                           53)  # wrong type error

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

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_boolean(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    if instruction.name != "NOT":
        var3 = instruction.args[2]
        if var3.type == None:  # not initialized variable
            print_err_and_exit("Values must be initialized",
                               56)  # uninitialized
        if var3.type == "var":
            tmp = var3.value.split("@")  # split by @
            var3 = get_variable(tmp[0], tmp[1])  # get from variable
        if var3.type == None:  # not initialized variable
            print_err_and_exit("Values must be initialized",
                               56)  # uninitialized

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if instruction.name != "NOT":
        if var2.type != "bool" or var3.type != "bool":
            # wrong type error
            print_err_and_exit("Arguments has to be of type bool", 53)
    else:
        if var2.type != "bool":
            # wrong type error
            print_err_and_exit("Arguments has to be of type bool", 53)

    if instruction.name == "AND":
        if var2.value == "false" or var3.value == "false":
            new_arg = Argument("bool", "false")  # save false
        else:
            new_arg = Argument("bool", "true")  # save true
    elif instruction.name == "OR":
        if var2.value == "false" and var3.value == "false":
            new_arg = Argument("bool", "false")  # save false
        else:
            new_arg = Argument("bool", "true")  # save true
    elif instruction.name == "NOT":
        if var2.value == "false":
            new_arg = Argument("bool", "true")  # save true
        else:
            new_arg = Argument("bool", "false")  # save false

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_relational(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable
    if var2.value == None:  # not initialized variable
        var2.value = ""
    if var3.value == None:  # not initialized variable
        var3.value = ""
    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if instruction.name != "EQ":
        if var2.type == "int" and var3.type != "int":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)
        if var2.type == "bool" and var3.type != "bool":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)
        if var2.type == "string" and var3.type != "string":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)

    if instruction.name == "GT":
        if var2.type == "int":  # if var is type int
            if int(var2.value) > int(var3.value):
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "bool":  # if var is type bool
            if var2.value == "true" and var3.value == "false":
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "string":  # if var is type string
            if var2.value > var3.value:
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "nil" or var3.type == "nil":  # if var is type nil
            print_err_and_exit(
                "Argument can not be nil while performing GT", 53)  # wrong type error
    elif instruction.name == "LT":
        if var2.type == "int":  # if var is type int
            if int(var2.value) < int(var3.value):
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "bool":  # if var is type bool
            if var2.value == "false" and var3.value == "true":  # if value is true
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "string":  # if var is type string
            if var2.value < var3.value:
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "nil" or var3.type == "nil":  # if var is type nil
            print_err_and_exit(
                "Argument can not be nil while performing LT", 53)  # wrong type error

    elif instruction.name == "EQ":
        if var2.type == "int" and var3.type == "int":  # if var is type int
            if int(var2.value) == int(var3.value):
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "bool" and var3.type == "bool":  # if var is type bool
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "string" and var3.type == "string":  # if var is type string
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        elif var2.type == "nil" or var3.type == "nil":  # if var is type nil
            if var2.value == var3.value:
                new_arg = Argument("bool", "true")  # save true
            else:
                new_arg = Argument("bool", "false")  # save false
        else:
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_int_to_char(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable

    if var1.type == None:  # not initialized variable
        print_err_and_exit("Value must be initialized", 56)  # uninitialized
    if var1.type != "int":
        print_err_and_exit(
            "Argument has to be of type int to be converted to char", 53)  # wrong type error

    try:
        new_val = chr(int(var1.value))
    except:
        print_err_and_exit("Error while converting int to string", 58)
    new_arg = Argument("string", new_val)

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_string_to_int(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var2.type != "string":
        # wrong type error
        print_err_and_exit("Arguments has to be of type string", 53)
    if var3.type != "int":
        print_err_and_exit("Arguments has to be of type int",
                           53)  # wrong type error
    if var2.value == None or int(var3.value) >= len(var2.value) or int(var3.value) < 0:
        print_err_and_exit("Index out of range", 58)

    new_arg = Argument("int", ord(var2.value[int(var3.value)]))

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_strlen(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable

    if var1.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var1.type != "string":
        print_err_and_exit(
            "Argument has to be of type string to find its length", 53)  # wrong type error

    if var1.value == None:  # not initialized variable
        new_arg = Argument("int", 0)
    else:
        new_arg = Argument("int", len(var1.value))

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_concat(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var2.type != "string":
        print_err_and_exit(
            "Arguments has to be of type string to concatenate", 53)  # wrong type error
    if var3.type != "string":
        print_err_and_exit(
            "Arguments has to be of type string to concatenate", 53)  # wrong type error
    if var2.value == None and var3.value == None:  # not initialized variable
        new_arg = Argument("string", "")
    elif var2.value == None:  # not initialized variable
        new_arg = Argument("string", var3.value)
    elif var3.value == None:  # not initialized variable
        new_arg = Argument("string", var2.value)
    else:
        new_arg = Argument("string", var2.value + var3.value)

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_getchar(instruction):
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var2.type != "string":
        # wrong type error
        print_err_and_exit("Arguments has to be of type string", 53)
    if var3.type != "int":
        print_err_and_exit("Arguments has to be of type int",
                           53)  # wrong type error
    if var2.value == None or int(var3.value) >= len(var2.value) or int(var3.value) < 0:
        print_err_and_exit("Index out of range", 58)

    new_arg = Argument("string", var2.value[int(var3.value)])

    tmp = var1.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_setchar(instruction):
    var = instruction.args[0]
    var1 = instruction.args[0]  # parse instrucion argument 1
    var2 = instruction.args[1]  # parse instrucion argument 2
    var3 = instruction.args[2]  # parse instrucion argument 3

    if var1.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable
    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var1.type == None or var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var1.type != "string":
        # wrong type error
        print_err_and_exit("Arguments has to be of type strinnnng", 53)
    if var2.type != "int":
        print_err_and_exit("Arguments has to be of type int",
                           53)  # wrong type error
    if var3.type != "string":
        # wrong type error
        print_err_and_exit("Arguments has to be of type striiiing", 53)
    if var1.value == None or int(var2.value) >= len(var1.value) or int(var2.value) < 0:
        print_err_and_exit("Index out of range", 58)

    if var3.value == None:  # not initialized variable
        print_err_and_exit("Can not change string with empty character", 58)
    new_var = var1.value[:int(var2.value)] + \
        var3.value[0] + var1.value[int(var2.value)+1:]

    new_arg = Argument("string", new_var)

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_type(var, symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable

    if var1.type == None:  # not initialized variable
        new_arg = Argument("string", '')
    else:
        new_arg = Argument("string", var1.type)

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_jmpeq(instruction):
    global position_pointer  # extend position pointer to function
    var1 = instruction.args[0].value
    var2 = instruction.args[1]
    var3 = instruction.args[2]
    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if(var2.type == "nil" or var3.type == "nil"):
        if not(var1 in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifeq", 52)
        if not bool(labels):
            print_err_and_exit("Label does not exist in jumpifeq", 52)
        if (str(var2.value) == str(var3.value)):
            position_pointer = int(labels[var1]-2)
        return
    if (var3.type != var2.type):
        print_err_and_exit("Variables are of different type",
                           53)  # wrong type error
    if(var3.type == "nil" and var2.type == "nil"):
        print_err_and_exit("Variables can not be both nil",
                           53)  # wrong type error
    if not(var1 in labels.keys()):
        print_err_and_exit("Label does not exist in jumpifeq", 52)
    if not bool(labels):
        print_err_and_exit("Label does not exist in jumpifeqs", 52)
    if (str(var2.value) == str(var3.value)):
        position_pointer = int(labels[var1]-2)


def instr_jmpneq(instruction):
    global position_pointer  # extend position pointer to function
    var1 = instruction.args[0].value
    var2 = instruction.args[1]
    var3 = instruction.args[2]

    if var2.type == "var":
        tmp = var2.value.split("@")  # split by @
        var2 = get_variable(tmp[0], tmp[1])  # get from variable
    if var3.type == "var":
        tmp = var3.value.split("@")  # split by @
        var3 = get_variable(tmp[0], tmp[1])  # get from variable

    if var2.type == None or var3.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if(var2.type == "nil" or var3.type == "nil"):
        if not(var1 in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifeq", 52)
        if not bool(labels):
            print_err_and_exit("Label does not exist in jumpifeq", 52)
        if (str(var2.value) != str(var3.value)):
            position_pointer = int(labels[var1]-2)
        return
    if (var3.type != var2.type):
        print_err_and_exit("Variables are of different type",
                           53)  # wrong type error
    if(var3.type == "nil" and var2.type == "nil"):
        print_err_and_exit("Variables can not be both nil",
                           53)  # wrong type error
    if not(var1 in labels.keys()):
        print_err_and_exit("Label does not exist in jumpifneq", 52)
    if not bool(labels):
        print_err_and_exit("Label does not exist in jumpifeqs", 52)
    if (str(var2.value) != str(var3.value)):
        position_pointer = int(labels[var1]-2)


def instr_write(symb):
    var = symb
    if symb.type == "var":
        tmp = var.value.split("@")  # split by @
        var = get_variable(tmp[0], tmp[1])  # get from variable

    if var.type == "nil":  # if var is type nil
        print("", end='')
    elif var.type == None:  # not initialized variable
        print_err_and_exit("Unitialized variable", 56)  # uninitialized
    elif var.type == "bool":  # if var is type bool
        if var.value == "true":  # if value is true
            debug('\033[92m' + "true"+'\033[0m')
            if DEBUG == False:
                print("true", end='')
        else:
            debug('\033[92m' + "false"+'\033[0m')
            if DEBUG == False:
                print("false", end='')
    else:
        debug('\033[92m' + str(var.value)+'\033[0m')
        if DEBUG == False:
            print(var.value, end='')


def instr_read(var, type):
    var1 = var
    if var.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable

    type_var = type.value
    if len(inputLines) == 0:
        poped = "nil"
        type_var = "nil"
    else:
        poped = inputLines[0].strip()
        inputLines.remove(inputLines[0])
    # print(inputLines, poped)

    if type_var == "int":
        try:
            new_arg = Argument("int", int(poped))
        except:
            new_arg = Argument("nil", "nil")  # save nil
    elif type_var == "bool":
        if poped.upper() == "TRUE":
            new_arg = Argument("bool", "true")  # save true
        else:
            new_arg = Argument("bool", "false")  # save false

    elif type_var == "string":
        try:
            new_arg = Argument("string", poped)
        except:
            new_arg = Argument("nil", "nil")  # save nil
    elif type_var == "nil":
        new_arg = Argument("nil", "nil")  # save ni;

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_exit(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable

    if var1.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var1.type != "int":
        print_err_and_exit("Type of symbol is not int", 53)  # wrong type error

    if int(var1.value) < 0 or int(var1.value) > 49:
        print_err_and_exit("Invalid value for exit", 57)

    debug('\033[96m' + "\nlabels:" + '\033[0m')
    debug(labels)
    debug("******************************")
    if DEBUG:
        print_gf()
        print_tf()
        print_lf()
        print_stack()
    debug('\033[96m' + "\nstats:" + '\033[0m')

    debug("INSTS - ")
    debug(insts)
    debug("HOT   -  ")
    var = hot.get_hottest()
    # var.print_hot()
    debug(var.get_order())
    # hot.print_my()
    debug("VARS  - ")
    debug(vars)
    # print(args_order)
    debug("******************************")
    process_stats()
    # print_gf()
    # print_tf()
    # print_lf()
    # print_stack()
    exit(int(var1.value))

    # TODO vypis statistik


def instr_dprint(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable
    stderr.write(var1.value + "\n")


#################STACK INSTRUCTIONS############################################

def instr_pushs(symb):
    var1 = symb
    if symb.type == "var":
        tmp = var1.value.split("@")  # split by @
        var1 = get_variable(tmp[0], tmp[1])  # get from variable
    if var1.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized

    new_var = Variable(var1.type, var1.value)
    stack.push(new_var)


def instr_pops(var):
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized

    poped = stack.pop()
    new_arg = Argument(poped.type, poped.value)

    tmp = var.value.split("@")  # split by @
    find_variable(tmp[0], tmp[1])
    update_variable(tmp[0], tmp[1], new_arg)  # save new_arg into variable


def instr_aritmetic_s(name):
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()

    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var1 = stack.pop()

    if var1.type != "int" or var2.type != "int":
        print_err_and_exit("Arguments has to be of type int",
                           53)  # wrong type error

    if name == "ADDS":
        new_var = Variable(var1.type, int(var1.value) + int(var2.value))
    if name == "SUBS":
        new_var = Variable(var1.type, int(var1.value) - int(var2.value))
    if name == "MULS":
        new_var = Variable(var1.type, int(var1.value) * int(var2.value))
    if name == "IDIVS":
        if int(var2.value) == 0:
            print_err_and_exit("Division by 0", 57)
        new_var = Variable(var1.type, int(var1.value) // int(var2.value))

    stack.push(new_var)


def instr_relational_s(name):
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()

    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var1 = stack.pop()
    if var1.value == None:  # not initialized variable
        var1.value = ""
    if var2.value == None:  # not initialized variable
        var2.value = ""
    if var1.type == None or var2.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if name != "EQS":
        if var1.type == "int" and var2.type != "int":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)
        if var1.type == "bool" and var2.type != "bool":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)
        if var1.type == "string" and var2.type != "string":
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)

    if name == "GTS":
        if var1.type == "nil" or var2.type == "nil":  # if var is type nil
            print_err_and_exit(
                "Argument can not be nil while performing GT", 53)  # wrong type error
        elif var2.type == "int":  # if var is type int
            if int(var1.value) > int(var2.value):
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var2.type == "bool":  # if var is type bool
            if var1.value == "true" and var2.value == "false":
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var2.type == "string":  # if var is type string
            if var1.value > var2.value:
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var1.type == "nil" or var2.type == "nil":  # if var is type nil
            print_err_and_exit(
                "Argument can not be nil while performing GT", 53)  # wrong type error

    elif name == "LTS":
        if var1.type == "nil" or var2.type == "nil":  # if var is type nil
            print_err_and_exit(
                "Argument can not be nil while performing LT", 53)  # wrong type error
        elif var2.type == "int":  # if var is type int
            if int(var1.value) < int(var2.value):
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var2.type == "bool":  # if var is type bool
            if var1.value == "false" and var2.value == "true":  # if value is true
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var2.type == "string":  # if var is type string
            if var1.value < var2.value:
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false

    elif name == "EQS":
        if var1.type == "int" and var2.type == "int":  # if var is type int
            if int(var1.value) == int(var2.value):
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var1.type == "bool" and var2.type == "bool":  # if var is type bool
            if var1.value == var2.value:
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var1.type == "string" and var2.type == "string":  # if var is type string
            if var1.value == var2.value:
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        elif var1.type == "nil" or var2.type == "nil":  # if var is type nil
            if var1.value == var2.value:
                new_var = Variable("bool", "true")  # save true
            else:
                new_var = Variable("bool", "false")  # save false
        else:
            # wrong type error
            print_err_and_exit("Arguments has to be of same type", 53)

    stack.push(new_var)


def instr_boolean_s(name):
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()
    if var2.type != "bool":
        print_err_and_exit("Argument has to be of type bool",
                           53)  # wrong type error

    if name == "NOTS":
        if var2.value == "false":
            new_val = Variable("bool", "true")  # save true
        else:
            new_val = Variable("bool", "false")  # save false
    else:
        if stack.is_empty() == True:
            print_err_and_exit("Stack is empty", 56)  # uninitialized
        var1 = stack.pop()
        if var1.type != "bool":
            # wrong type error
            print_err_and_exit("Argument has to be of type bool", 53)
        if var2.type == None or var1.type == None:  # not initialized variable
            print_err_and_exit("Values must be initialized",
                               56)  # uninitialized
        if name == "ANDS":
            if var1.value == "false" or var2.value == "false":
                new_val = Variable("bool", "false")  # save false
            else:
                new_val = Variable("bool", "true")  # save true
        elif name == "ORS":
            if var1.value == "false" and var2.value == "false":
                new_val = Variable("bool", "false")  # save false
            else:
                new_val = Variable("bool", "true")  # save true

    stack.push(new_val)


def instr_int_to_char_s():
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized

    poped = stack.pop()
    if poped.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if poped.type != "int":
        print_err_and_exit(
            "Argument has to be of type int to be converted to char", 53)  # wrong type error

    try:
        new_val = chr(int(poped.value))
    except:
        print_err_and_exit("Error while converting int to string", 58)
    new_val = Variable("string", new_val)

    stack.push(new_val)


def instr_string_to_int_s():
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()

    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var1 = stack.pop()
    # print("var1 ", var1.type, " var2 ", var2.type)
    if var1.type == None or var2.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if var1.type != "string" or var2.type != "int":
        # wrong type error
        print_err_and_exit("Arguments has to be of correct type", 53)

    if var1.value == None or int(var2.value) >= len(var1.value) or int(var2.value) < 0:
        print_err_and_exit("Index out of range", 58)

    new_var = Variable("int", ord(var1.value[int(var2.value)]))

    stack.push(new_var)


def instr_jmpeq_s(label):
    global position_pointer  # extend position pointer to function
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()

    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var1 = stack.pop()

    if var1.type == None or var2.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if(var1.type == "nil" or var2.type == "nil"):
        if not(label in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifeqs", 52)
        if not bool(labels):
            print_err_and_exit("Label does not exist in jumpifeqs", 52)
        if (str(var1.value) == str(var2.value)):
            position_pointer = int(labels[label]-2)
        return
    if (var1.type != var2.type):
        print_err_and_exit("Variables are of different type",
                           53)  # wrong type error
    if(var1.type == "nil" and var2.type == "nil"):
        print_err_and_exit("Variables can not be both nil",
                           53)  # wrong type error
    if not(label in labels.keys()):
        print_err_and_exit("Label does not exist in jumpifeq", 52)
    if (str(var1.value) == str(var2.value)):
        position_pointer = int(labels[label]-2)


def instr_jmpneq_s(label):
    global position_pointer  # extend position pointer to function
    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var2 = stack.pop()

    if stack.is_empty() == True:
        print_err_and_exit("Stack is empty", 56)  # uninitialized
    var1 = stack.pop()
    if var1.type == None or var2.type == None:  # not initialized variable
        print_err_and_exit("Values must be initialized", 56)  # uninitialized
    if(var1.type == "nil" or var2.type == "nil"):
        if not(label in labels.keys()):
            print_err_and_exit("Label does not exist in jumpifeqs", 52)
        if not bool(labels):
            print_err_and_exit("Label does not exist in jumpifeqs", 52)
        if (str(var1.value) != str(var2.value)):
            position_pointer = int(labels[label]-2)
        return
    if (var1.type != var2.type):
        print_err_and_exit("Variables are of different type",
                           53)  # wrong type error
    if(var1.type == "nil" and var2.type == "nil"):
        print_err_and_exit("Variables can not be both nil",
                           53)  # wrong type error
    if not(label in labels.keys()):
        print_err_and_exit("Label does not exist in jumpifeq", 52)
    if (str(var1.value) != str(var2.value)):
        position_pointer = int(labels[label]-2)
    ###############################################################################

    ############################INTERPRET FUNCTION#################################


def interpret_instruction(instruction):

    global position_pointer  # extend position pointer to function
    global TF
    global LF
    try:
        debug(str(position_pointer) + instruction.name)
    except:
        pass
    if instruction.name == "CREATEFRAME":
        TF = dict()
    elif instruction.name == "PUSHFRAME":
        if TF == None:  # not initialized variable
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
        position_pointer = int(labels[labelName]-2)
    elif instruction.name == "DEFVAR":
        instr_defvar(instruction.args[0])
    elif instruction.name == "MOVE":
        splittedVar = instruction.args[0].value.split("@")  # split by @
        find_variable(splittedVar[0], splittedVar[1])
        var1 = instruction.args[1]
        if var1.type == "var":
            tmp = var1.value.split("@")  # split by @
            var1 = get_variable(tmp[0], tmp[1])  # get from variable
        if var1.type == None:  # not initialized variable
            print_err_and_exit("Value must be initialized",
                               56)  # uninitialized
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
    elif instruction.name == "ADDS" or instruction.name == "SUBS" or instruction.name == "MULS" or instruction.name == "IDIVS":
        instr_aritmetic_s(instruction.name)
    elif instruction.name == "LTS" or instruction.name == "GTS" or instruction.name == "EQS":
        instr_relational_s(instruction.name)
    elif instruction.name == "ANDS" or instruction.name == "ORS" or instruction.name == "NOTS":
        instr_boolean_s(instruction.name)
    elif instruction.name == "INT2CHARS":
        instr_int_to_char_s()
    elif instruction.name == "STRI2INTS":
        instr_string_to_int_s()
    elif instruction.name == "JUMPIFEQS":
        instr_jmpeq_s(instruction.args[0].value)
    elif instruction.name == "JUMPIFNEQS":
        instr_jmpneq_s(instruction.args[0].value)
    elif instruction.name == "CLEARS":
        stack.clear()

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
debug("------------------INTERPRETING---------------------------")
hot = Hot()
while position_pointer != len(instructions):
    hot.add(instructions[position_pointer].name,
            instructions[position_pointer].order)
    interpret_instruction(instructions[position_pointer])
    if get_vars_count() > vars:
        vars = get_vars_count()
    position_pointer += 1
    insts += 1
process_stats()

debug("------------------INTERPRETING FINISHED WITH SUCCESS-----")
###################################################################################################

debug('\033[96m' + "\nlabels:" + '\033[0m')
debug(labels)
debug("******************************")
if DEBUG:
    print_gf()
    print_tf()
    print_lf()
    print_stack()
debug('\033[96m' + "\nstats:" + '\033[0m')

debug("INSTS - ")
debug(insts)
debug("HOT   -  ")
var = hot.get_hottest()
# var.print_hot()
# debug(var.get_order())
# hot.print_my()
debug("VARS  - ")
debug(vars)
# print(args_order)
debug("******************************")
# 57 funkcii monkaS
