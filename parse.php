<?php

/****************************************************************************
 *   IPP                                                                    *
 *                                                                          *
 *   Implementacia parsera pre jazyk IPPcode22                              *
 *                                                                          *
 *	 Ondrušek Tomáš	xondru18                                                *
 *                                                                          *
 ****************************************************************************/


//----- definig variables -----
ini_set('display_errors', 'stderr');
define("ERR_OK", 0);
define("ERR_PARAM", 10);
define("ERR_HEADER", 21);
define("ERR_OPCODE", 22);
define("ERR_OTHER", 23);
define("ERR_INTERNAL", 99);
$debug = false;

$instructions = [
    //base functions
    'MOVE'        => ['var', 'symbol'],
    'CREATEFRAME' => [],
    'PUSHFRAME'   => [],
    'POPFRAME'    => [],
    'DEFVAR'      => ['var'],
    'CALL'        => ['label'],
    'RETURN'      => [],
    //stack
    'PUSHS'       => ['symbol'],
    'POPS'        => ['var'],
    'CLEARS'      => [],
    'ADDS'        => [],
    'SUBS'        => [],
    'MULS'        => [],
    'DIVS'        => [],
    'LTS'         => [],
    'GTS'         => [],
    'EQS'         => [],
    'ANDS'        => [],
    'ORS'         => [],
    'NOTS'        => [],
    'INT2FLOATS'  => [],
    'FLOAT2INTS'  => [],
    'INT2CHARS'   => [],
    'STRI2INTS'   => [],
    'JUMPIFEQS'   => ['label'],
    'JUMPIFNEQS'  => ['label'],
    //arithmetic operations
    'ADD'         => ['var', 'symbol', 'symbol'],
    'SUB'         => ['var', 'symbol', 'symbol'],
    'MUL'         => ['var', 'symbol', 'symbol'],
    'IDIV'        => ['var', 'symbol', 'symbol'],
    'LT'          => ['var', 'symbol', 'symbol'],
    'GT'          => ['var', 'symbol', 'symbol'],
    'EQ'          => ['var', 'symbol', 'symbol'],
    'AND'         => ['var', 'symbol', 'symbol'],
    'OR'          => ['var', 'symbol', 'symbol'],
    'NOT'         => ['var', 'symbol'],
    'INT2FLOAT'   => ['var', 'symbol'],
    'FLOAT2INT'   => ['var', 'symbol'],
    'INT2CHAR'    => ['var', 'symbol'],
    'STRI2INT'    => ['var', 'symbol', 'symbol'],
    //input, output 
    'READ'        => ['var', 'type'],
    'WRITE'       => ['symbol'],
    //string operations
    'CONCAT'      => ['var', 'symbol', 'symbol'],
    'STRLEN'      => ['var', 'symbol'],
    'GETCHAR'     => ['var', 'symbol', 'symbol'],
    'SETCHAR'     => ['var', 'symbol', 'symbol'],
    //type operations
    'TYPE'        => ['var', 'symbol'],
    //jumps
    'LABEL'       => ['label'],
    'JUMP'        => ['label'],
    'JUMPIFEQ'    => ['label', 'symbol', 'symbol'],
    'JUMPIFNEQ'   => ['label', 'symbol', 'symbol'],
    'EXIT'        => ['symbol'],
    //debug
    'DPRINT'      => ['symbol'],
    'BREAK'       => [],
];

$stats = [
    'comments'    => 0,                         //--comments
    'loc'         => 0,                         //--loc
    'jumps'       => 0,                         //--jumps
    'labels'      => [],                        //--labels
    'jumps_to'    => [],
    'jumps_back'  => 0,
    'jumps_front' => 0,
    'jumps_bad'   => 0,
    'order'       => []
];

$input = [];
$output = new DOMDocument("1.0", "UTF-8");
$output->formatOutput = true;
mb_internal_encoding("UTF-8");
$XMLmem = $output->createElement("program");
$XMLmem->setAttribute("language", "IPPcode22");




//----- used regex-es -----
$reg_label = "/^([\w_\-$&?%*!]+)$/"; //a-z A-Z _ -$&?%*!
$reg_variable = "/^([a-zA-Z_\-$&%*!?][\w_\-$&%*!?]*)$/"; // sekvence libovolných alfanumerických a speciálních znaků bez bílých znaků začínající písmenem nebo speciálním znakem, kde speciální znaky jsou: _, -, $, &, %, *, !, ?
$reg_integer = "/^[-+]?\d+$/"; //-+cislo
$reg_float = "/^[0-9\.abcdefABCDEF\+\-px]*$/"; // float
$reg_first_word = "/^([\S]+)/"; // checks for first word 
//----- used functions -----

/**
 * Prints debugging informations
 * @param str is string to be printed
 */
function debug_print($str)
{
    global $debug;
    if ($debug) echo $str;
}

/**
 * Checks if variable is correct
 * @param str name of variable to be checked
 * @return true if variable exists, false otherwise
 */
function check_correct_variable($str)
{ // upravene
    global $reg_variable;
    if (strpos($str, "@")) {
        $frame = substr($str, 0, 2);
        $name = substr($str, 3);
        $correct = preg_match($reg_variable, $name); // sekvence libovolných alfanumerických a speciálních znaků bez bílých znaků začínající písmenem nebo speciálním znakem, kde speciální znaky jsou: _, -, $, &, %, *, !, ?
        if ($correct && ($frame == "GF" || $frame == "LF" || $frame == "TF")) {
            debug_print("\e[92mvarCheck GOOD\e[0m\n");
            return true;
        }
    }
    debug_print("\e[91mvarCheck FAILED\e[0m\n");
    return false;
}

/**
 * Checks if string is a number
 * @param str name of variable to be checked
 * @return true if variable is between 0 and 9, false otherwise
 */
function is_number($number)
{
    if ($number >= '0' && $number <= '9') {
        return true;
    }
    return false;
}

/**
 * Checks if symbol is ok
 * @param str symbol to be checked
 * @return type if (int, bool, string, nil, var), false otherwise
 */
function check_correct_symbol($str) // upravene cca
{
    global $reg_integer;
    global $reg_float;

    if (($to_cut = strpos($str, "@")) !== false) {
        $prefix = substr($str, 0, $to_cut);
        $name = substr($str, $to_cut + 1);

        if ($prefix == "GF" || $prefix == "LF" || $prefix == "TF") {
            debug_print(" check_correct_symbol -> varCheck\n");
            if (!check_correct_variable($str)) {
                return false;
            }
            return "var";
        } elseif ($prefix == "int" || $prefix == "bool" || $prefix == "string" || $prefix == "nil" || $prefix == "float") {
            switch ($prefix) {

                case "string":
                    for ($i = 0; $i < strlen($name); $i++) {
                        if ($name[$i] == "\\") {
                            if (!((isset($name[$i + 1]) && is_number($name[$i + 1]))
                                && (isset($name[$i + 2]) && is_number($name[$i + 2]))
                                && (isset($name[$i + 3]) && is_number($name[$i + 3])))) {
                                debug_print("\e[91mcheck_correct_symbol FAIL bad escape sequence\e[0m\n");
                                return false;
                            }
                            $i += 3;
                        }
                    }
                    debug_print("\e[92mcheck_correct_symbol IS symbol [ $str ]\e[0m\n");
                    return "string";
                    break;

                case "int":
                    if (preg_match($reg_integer, $name)) {
                        debug_print("\e[92mcheck_correct_symbol IS symbol [ $str ]\e[0m\n");
                        return "int";
                    }
                    break;


                case "bool":
                    if ($name == "true" || $name == "false") {
                        debug_print("\e[92mcheck_correct_symbol IS symbol [ $str ]\e[0m\n");
                        return "bool";
                    }
                    break;


                case "nil":
                    if ($name == "nil") {
                        debug_print("\e[92mcheck_correct_symbol IS symbol [ $str ]\e[0m\n");
                        return "nil";
                        break;
                    }
                    break;


                case "float":
                    if (preg_match($reg_float, $name)) {
                        debug_print("\e[92mcheck_correct_symbol IS symbol [ $str ]\e[0m\n");
                        return "float";
                    }
            }
        }
    }
    debug_print(" check_correct_symbol FAIL [ $str ]\n");
    return false;
}

/**
 * Checks if given string is label
 * @param str string to be checked
 * @return true if str is label, false otherwise
 */
function check_correct_label($str)
{
    global $reg_label;
    if (preg_match($reg_label, $str)) {
        debug_print("\e[92mcheck_correct_label OK [ $str ]\e[0m\n");
        return true;
    }
    debug_print("\e[91mcheck_correct_label FAIL[ $str ]\e[0m\n");
    return false;
}

/**
 * Function transforms strings into XML friendly strings
 * @param str variable to be stransformed
 * @return str that is transformed
 */
function special_chars($str)
{
    $str = str_replace("&", "&amp;", $str);
    $str = str_replace("'", "&apos;", $str);
    $str = str_replace("\"", "&quot;", $str);
    $str = str_replace("<", "&lt;", $str);
    $str = str_replace(">", "&gt;", $str);
    debug_print("\n.........................\n");
    debug_print($str);
    debug_print("\n.........................\n");
    // $str = htmlspecialchars($str);
    return $str;
}

//---------------------------------MAIN----------------------------------------
//arg check
if (count($argv) > 2) {
    foreach ($argv as $value) {
        if ($value == "--help" || $value == "-h") {
            fwrite(STDERR, "\e[91mWRONG SCRIPT PARAMETERS use just \"--help\"\e[0m \n");
            exit(ERR_PARAM);
        }
    }
} else if (count($argv) == 2) {
    if ($argv[1] == "-h" || $argv[1] == "--help") {
        echo" 
         _____ _____  _____                                               _           
        |_   _|  __ \|  __ \                                             | |          
          | | | |__) | |__) |  ______   _ __   __ _ _ __ ___  ___   _ __ | |__  _ __  
          | | |  ___/|  ___/  |______| | '_ \ / _` | '__/ __|/ _ \ | '_ \| '_ \| '_ \ 
         _| |_| |    | |               | |_) | (_| | |  \__ \  __/_| |_) | | | | |_) |
        |_____|_|    |_|               | .__/ \__,_|_|  |___/\___(_) .__/|_| |_| .__/ 
                                       | |                         | |         | |    
                                       |_|                         |_|         |_|    

        Script expects input in language IPPcode22 on standard input, then checks if its syntax is correct and generates
        XML representation of program. If set can output statistics.
   Options :
   \"--help\" or \"-h\"  print help 
   \"--stats=[file]\" to set on the output stat file and give location
   \"--loc\"           number of lines
   \"--comments\"      number of comments
   \"--labels\"        number of labels
   \"--jumps\"         number of jumps
   if used, you must set source file, otherwise script will fail\n\n";
        exit(ERR_OK);
    }
}

//--------------------------------LOAD FROM STDIN------------------------------
$curr_line = fgets(STDIN);
while ($curr_line !== FALSE) {
    $line = str_replace("\n", '', trim($curr_line));
    array_push($input, $line);
    $curr_line = fgets(STDIN);
}

//--------------------------------TRIM COMMENTS--------------------------------
debug_print("\e[96m----- LOADED INPUT -----\e[0m\n");
if ($debug) print_r($input);
for ($i = 0; $i < count($input); $i++) {
    if (($to_cut = strpos($input[$i], "#")) !== false) {
        //line has a comment
        $stats['comments']++;
        $input[$i] = substr($input[$i], 0, $to_cut);
        trim($input[$i]);
    }
}

//--------------------------------HEADER CHECK---------------------------------
$i = 0;
$found = true;
while ($found) {
    $input[$i] = trim($input[$i]);
    if ($input[$i] == "") {
        $i++;
    } elseif (strtolower($input[$i]) == ".ippcode22") {
        $i++;
        $found = false;
    } else {
        //missing header
        fwrite(STDERR, "\e[31mMISSING HEADER .IPPcode22... returning\e[0m\n");
        exit(ERR_HEADER);
    }
}
debug_print("\e[96m---- WITHOUT COMMENTS ----\e[0m\n");
if ($debug) print_r($input);


//--------------------------------INDIVIDUAL LINE CHECK------------------------
debug_print("\e[96m---- MAIN CHECKER ----\e[0m\n");
$count = 0;
for ($i; $i < count($input); $i++) {
    debug_print("\e[93mCHECKING LINE  - $i --> | $input[$i] |\e[0m\n");
    if (preg_match($reg_first_word, $input[$i], $reg_cut)) {
        $count++;
        $opcode = strtoupper($reg_cut[0]);
        // v $opcode je nazov instrukcie
        if (isset($instructions[$opcode])) {
            //opcode found in instruction set
            $stats['loc']++;


            $num = count($instructions[$opcode]);
            // echo $num;
            // echo "-------------------\n";

            $regexinstr = "/^(\w+)"; // a-z A-Z _

            for ($y = 0; $y < $num; $y++) {
                $regexinstr = $regexinstr . "\s+([^\s]+)"; // ' ' hocico ' ' 
            }
            $regexinstr = $regexinstr . "\s*$/"; // ' ' terminacia

            //   echo $regexp;
            //   echo "-------------------\n";

            if (preg_match("$regexinstr", $input[$i], $reg_cut)) {
                debug_print("\e[32mPARAMETER CHECK GOOD\e[0m\n");
            } else {
                //bad num of args
                fwrite(STDERR, "\e[91mPARAMETER CHECK FAIL\e[0m\n");
                exit(ERR_OTHER);
            }
            $XMLinstr = $output->createElement("instruction");
            $XMLinstr->setAttribute("order", $count);
            $XMLinstr->setAttribute("opcode", $opcode);

            //print_r( $reg_cut);

            $index = 2;
            foreach ($instructions[$opcode] as $value) {
                // echo ">>>>>>value check>>>>>>>\n";
                // echo $value;
                // echo "\n<<<<<<<<<<<<<\n";

                // $name = "";
                // $type = "";
                if ($value == "var") {
                    if (!check_correct_variable($reg_cut[$index])) {
                        fwrite(STDERR, "\e[91mOPCODE $opcode FAIL VARIABLE CHECK at [$reg_cut[$index]]\e[0m\n");
                        exit(ERR_OTHER);
                    }
                    $type = "var";
                    $name = special_chars($reg_cut[$index]);
                } elseif ($value == "symbol") {
                    if (($type = check_correct_symbol($reg_cut[$index])) === false) {
                        fwrite(STDERR, "\e[91mOPCODE $opcode FAIL check_correct_symbol at [$reg_cut[$index]]\e[0m\n");
                        exit(ERR_OTHER);
                    }
                    if ($type == "var") {
                        $name = special_chars($reg_cut[$index]);
                    } else {
                        $to_cut = strpos($reg_cut[$index], "@");
                        if ($type == "string") {
                            $name = special_chars(substr($reg_cut[$index], $to_cut + 1));
                        } else {
                            $name = substr($reg_cut[$index], $to_cut + 1);
                        }
                    }
                } elseif ($value == "label") {
                    if (!check_correct_label($reg_cut[$index])) {
                        fwrite(STDERR, "\e[91mOPCODE $opcode FAIL check_correct_label at [$reg_cut[$index]]\e[0m");
                        exit(ERR_OTHER);
                    }
                    $type = "label";
                    $name = $reg_cut[$index];
                } elseif ($value == "type") {
                    $name = $reg_cut[$index];
                    $type = "type";
                    if ($reg_cut[$index] != "int" && $reg_cut[$index] != "string" && $reg_cut[$index] != "bool" && $reg_cut[$index] != "float") {
                        fwrite(STDERR, "\e[91mOPCODE $opcode FAIL by check_correct_type at [$reg_cut[$index]]\e[0m\n");
                        exit(ERR_OTHER);
                    }
                }
                $XMLarg = $output->createElement("arg" . ($index - 1));
                $XMLarg->setAttribute("type", $type);
                $XMLarg->nodeValue = $name;
                $XMLinstr->appendChild($XMLarg);
                $index++;
            }
            $XMLmem->appendChild($XMLinstr);
            if (
                $opcode == "JUMP" || $opcode == "JUMPIFEQ" || $opcode == "JUMPIFNEQ" || $opcode == "CALL" ||
                $opcode == "JUMPIFEQS" || $opcode == "JUMPIFNEQS"
            ) {
                $stats['jumps']++;

                //#########################################################################################################################################
                // print("#################\n");
                // print($reg_cut[2]);
                // print("\n");

                // print($input[$i]);
                //potrebujem porovnat ci sa aktualne to co je v reg cut nachadza v labels, ak ano je to skok spat
                $found_label = in_array($reg_cut[2], $stats['labels']);
                //print("\n");
                if ($found_label) {
                    //print("mam");
                    $stats['jumps_back']++;
                } else {
                    //print("nemam");
                    $stats['jumps_front']++;
                    array_push($stats['jumps_to'], $reg_cut[2]);
                }
                // print($found_label);
                // print("\n");
                // print_r($stats['labels']);
                // print("#################\n");
                //ak nie tak si to potrebujem niekde ulozit a na konci za main end si to potrebujem rozdelit na forward a back jump
            }
            if ($opcode == "LABEL") {
                $addL = true;
                foreach ($stats['labels'] as $value) {
                    if ($value == $reg_cut[2]) {
                        $addL = false;
                    }
                }
                if ($addL) {
                    array_push($stats['labels'], $reg_cut[2]);
                }
            }
        } else {
            //opcode not found in rules
            fwrite(STDERR, "\e[91mBAD OPCODE... returning\e[0m\n");
            exit(ERR_OPCODE);
        }
    } else {
        //no opcode on line
    }
}
debug_print("---- MAIN END ----\n");

foreach ($stats['jumps_to'] as $jump_label) {

    $jump_front = in_array($jump_label, $stats['labels']);
    if (!$jump_front) {
        $stats['jumps_bad']++;
        $stats['jumps_front']--;

        debug_print("nenasiel som vec\n");
    }

}
// print_r($stats['labels']);
// print("\n");
// print_r($stats['jumps_back']);
// print("\n");

// print_r($stats['jumps_front']);
// print("\n");

// print_r($stats['jumps_bad']);
// print("\n");
// print_r($stats['jumps_to']);
// print("\n");


// printf("%s \n", $jump_label);





//--------------------------------STATS FILE HANDLING--------------------------
$file = false;
if (count($argv) > 1) {
    $counter = 0;
    foreach ($argv as $value) {
        if ($value == "parse.php") {
        } elseif ($value == "--loc" || $value == "--comments" || $value == "--labels" || $value == "--jumps" || $value == "--fwjumps" || $value == "--backjumps" || $value == "--badjumps") {
            array_push($stats['order'], $value);
        } elseif (
            preg_match("/^--stats=(\w*.*)$/", $value, $reg_cut) !== false || preg_match("/^--stats=\"(\w*.*)\"$/", $value, $reg_cut) !== false
        ) {
            // if( $counter != 1){
            //     fwrite(STDERR,"BAD STATFILE POSITION... returning \n");
            //     exit(ERR_PARAM); 
            // }
            if ($file) {
                fwrite(STDERR, "\e[91mMULTIPLE STATFILE PLACES... returning\e[0m\n");
                exit(ERR_PARAM);
            } else {
                $stats_file = $reg_cut[1];
                $file = true;
            }
        } else {
            fwrite(STDERR, "\e[91mUNKNOWN OPTION SET... returning\e[0m\n");
        }
        $counter++;
    }
    if (!$file) {
        fwrite(STDERR, "\e[91mNO FILE SET... returning\e[0m\n");
        exit(ERR_PARAM);
    }
    if (($fp = fopen($stats_file, "w")) === false) {
        exit(ERR_INTERNAL);
    }

    foreach ($stats['order'] as $value) {
        switch ($value) {
            case "--loc":
                fprintf($fp, "%d\n", $stats['loc']);
                break;
            case "--comments":
                fprintf($fp, "%d\n", $stats['comments']);
                break;
            case "--labels":
                fprintf($fp, "%d\n", count($stats['labels']));
                break;
            case "--jumps":
                fprintf($fp, "%d\n", $stats['jumps']);
                break;
            case "--fwjumps":
                fprintf($fp, "%d\n", $stats['jumps_front']);
                break;
            case "--backjumps":
                fprintf($fp, "%d\n", $stats['jumps_back']);
                break;
            case "--badjumps":
                fprintf($fp, "%d\n", $stats['jumps_bad']);
                break;
            default:
                exit(ERR_INTERNAL);
        }
    }
    fclose($fp);
}
if ($debug){
    print_r($stats);
} 
$output->appendChild($XMLmem);
print ($output->saveXML());
exit(ERR_OK);
