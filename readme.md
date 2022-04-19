# Documentation of Project Implementation for IPP 2021/2022

-   Name: **Tomáš Ondrušek**
-   Login: **xondru18**

# Interpret implementation

## How to run

`python interpret.py [--help|-h] [--source=file] [--input=file] [--stats=file] [--vars] [--insts] [--hot]`

-   `--help|-h` - print help.
-   `--source=file` - file to read XML from. If not supplied the XML is read from stdin.
-   `--input=file` - file to read input from. If not supplied the input is read from stdin.
-   `--stats=file` - file to write the statistics into.
-   `--vars` - max number of initialized variables in all frames at one point of time.
-   `--insts` - number of instructions executed.
-   `--hot` - order of the most used instruction.

At least one of `--source=file` or `--input=file` parameter must be supplied.
When using `--vars` or `--insts` or `--hot` the `--stats=file` must be supplied.

## [Interpret](interpret.py)

`interpret.py` is the main script for IPPcode22 interpret. Its job is to check XML validity, check XML syntax, execute instructions and supply runtime parameters (statistics).

## XML Parsing

For parsing XML formatted input is used `xml.etree.ElementTree`. This parses XML input into tree which is then passed into `filter_instructions()` function which finds supported XML. After that function `sort_instructions()` is called which sorts instructions based on _order_ attribute. Within instruction this function also sorts args into right order. Next in line is `check_instructions()` which checks for attributes like _opcode_, _program_, _language_. It also checks atributes for right numbering, because only range 1-3 is supported, checks for dulicities and type attribute. Next function `fill_instructions()` takes instruction from sorted tree and inserts it into list of instructions.

## Instruction checking

With instructions sorted and in list the next step is checking for correct type and correct format. This functionality is very similar to one of the `parse.php` script. Same regex-es from this script are also used. What is checked is correct value for supplied type, correct argument count for instruction.

## Classes

### Variable

Variable class is used to store variable parameters which are its data type and its value. This class is then passed as value of `key:value pair` of dictionary into frames. This class does not have class methods.

### Argument

Argument class is used to store argument data type and its value. Class is then used to fill argument array of instructions. This class does not have class methods.

### Instruction

Instruction class is used to store one single instruction. It contains information about its `Name`, `Oder`, `Number`, `Arguments`. Class is used to fill up `instructions` list. This class has class method `addArgument` which appends Argument class into args array.

### Stack

Stack is class implementing ADT Stack. Its only value is item. This class has class method to `Pop` from stack, `Push` to stack, `is_empty` to check if stack is empty and `Clear` to clear stack.

### HotInst

HotInst is class to store and manipulate one instruction. Class is used in `--hot` statistic. It holds instruction name, order and count. Class methods are used to keep class current with updating `count`, which represents how many times instruction has been interpreted. `order` is also checked to update its value to minimum for collisions. There are also methods `get_order` which is used to get order of current instuction and `print_hot` which prints out values of class.

### Hot

Hot is class that stores array of interpreted instructions. Its method `add` is used to check if instruction has been already interpreted, if yes, then HotInst class methods are used to update class and if not, HotInst is filled and appended into array. Method `print_my` prints out all instructions and its correponding values and method `get_hottest` returns instruction that has been interpreted most based on `count` variable. If there are more instructions with same `count`, `order` is compared and smallest order instruction is returned.

## Frames and variable handling

### Frames

IPP22 supports 3 data frames, which are `GF, TF, LF`. GF or `Global frame` is implemented as dictionary of name and value. TF or `Temporary frame` has the same characteristics as global frame but in needs to be created by instruction so its data type is also dictionary, but it defaults as None. LF or `Local frame` is frame that contains TFs. Its data type is _list()_

### Variable functions

#### get_variable

This function is used to find variable in frames and return it to be used in `update` function. Function returns error codes if variable does not exists or frame is not initialized.

#### find_variable

This function is used to find variable in frames.

#### update_variable

This function is used to either update variable or insert it in frame. Functions takes both variables as its input or it takes data type and value. If other variable is used function calls `get_variable` function and parses its value, then it checks for existing variable name that is to be saved in. If name is not present in frames new variable is created and appened, if name is already in frame its value or data type is updated. Function returns error codes if variable does not exists or frame is not initialized.

## [IPP_Interpret](interpret.py)

Interpreting begins by running through all instructions and saving labes for forward jumps. Next each with instruction `interpret_instruction` function is called which consists of multiple if-elif statements to call corresponding function for interpreting instruction. Instructions are interpreted and if required, errors are raised. While interpreting there can be errors like :

-   53 – wrong operand types.
-   54 – non existing variable.
-   55 – non existing frame.
-   56 – missing value in variable.
-   57 – wrong value (divisin by 0, ...).
-   58 – string handling error.

After interpreting statistics processing is called. Function `process_stats` checks if there are stats set as script arguments and if yes, checks which ones are present and writes them into file.

# Test implementation

## How to run

`php test.php [--help] [--directory=path|-d=path] [--recursive] [--parse-script=file] [--int-script=file] [--parse-only] [--int-only] [--jexampath=path] [--noclean] [--match=regexp] [--testlist=file]`

-   `--help` prints help.
-   `--directory=path|-d=path` directory containing tests. Default path is set to './'.
-   `--recursive` recursive search for tests.
-   `--parse-script=file` parse script file for analysis of IPPcode22. The default file is './parse.php'.
-   `--int-script=file` interpret script file for interpreting of XML representation of IPPcode22. The default file is './interpret.py'.
-   `--parse-only` test only parse.php. Cannot be combined with --int-only.
-   `--int-only` test only interpret.py. Cannot be combined with --parse-only.
-   `--jexampath=path` path to directory containing jexamxml.jar
-   `--match=regexp` perform test that match regex set
-   `--testlist=file` perform tests from containing names of test directories
-   `--noclean` script does not deletes temporary files

## [test.php](test.php)

Script for performing tests for IPP22, which checks the validity of parameters and their variance validity.
Script created base `HTML` docpage and while performing tests appends results into table. Each directory has its own talbe and information about tests performed, success rate and path to directory. For the files that does not exits but are required, script creates them and puts a default value in them. Then script performs tests based on its configuration (both, parser only or interpret only), creates command for the script to test and executes it using `exec()`. If return value is not 0 outputs are compared useing diff tool with `-Z --strip-trailing-cr` to ignore windows CR and ignore trailing whitespace. Temporary files created are `xxxxx_TMP_OUT.out` and `xxxxx_TMP_retCode.rc`. If both scripts are tested temporary file `xxxxx_TMP_XML.xml` is created.
