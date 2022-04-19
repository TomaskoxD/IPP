<?php

/****************************************************************************
 *   IPP                                                                    *
 *                                                                          *
 *   Implementacia testovacieho skriptu pre jazyk IPPcode22                 *
 *                                                                          *
 *	 Ondrušek Tomáš	xondru18                                                *
 *                                                                          *
 ****************************************************************************/

ini_set("display_errors", "stderr");


//----- defining variables -----
$recursive = false;
$parse_only = false;
$interpret_only = false;
$no_clean = false;
$diff_out = false;
$directories = [];
$directory = ".";
$testlist = ".";
$parse_script = "parse.php";
$interpret_script = "interpret.py";
$jexam = "/pub/courses/ipp/jexam_xml/jexam_xml.jar";
$match = "/^.*$/";
$valid = ["help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only", "jexampath:", "testlist:", "match:", "no-clean"];
$args = getopt("", $valid);
$diff = "diff";
//#################################################################################################
//----- checking args -----
if (array_key_exists("help", $args)) {
    if ($argc == 2)
        printHelp();
    else {
        fwrite(STDERR, "\e[91mWRONG SCRIPT PARAMETERS use just \"--help\"\e[0m \n");
        exit(10);
    }
}
if (array_key_exists("directory", $args)) {
    if (!is_readable($args["directory"])) {
        fwrite(STDERR, "\e[91mFILE is not readable\e[0m \n");
        exit(41);
    }
    $directory = $args["directory"];
}
array_push($directories, $directory);
if (array_key_exists("recursive", $args)) {
    $recursive = true;
    $directories = array_merge(recurse_dir($directory), $directories);
}
if (array_key_exists("parse-script", $args)) {
    if (!is_readable($args["parse-script"])) {
        fwrite(STDERR, "\e[91mFILE is not readable - parse-script\e[0m \n");
        exit(41);
    }
    $parse_script = $args["parse-script"];
}
if (array_key_exists("int-script", $args)) {
    if (!is_readable($args["int-script"])) {
        fwrite(STDERR, "\e[91mFILE is not readable - int-script\e[0m \n");
        exit(41);
    }
    $interpret_script = $args["int-script"];
}
if (array_key_exists("int-only", $args)) {
    $interpret_only = true;
}
if (array_key_exists("jexampath", $args)) {
    if (!is_readable($args["jexampath"])) {
        fwrite(STDERR, "\e[91mFILE is not readable - jexampath\e[0m \n");
        exit(41);
    }
    $jexam = $args["jexampath"];
}
if (array_key_exists("testlist", $args)) {
    $testlist = $args["testlist"];
    if (array_key_exists("directory", $args)) {
        fwrite(STDERR, "\e[91mWRONG SCRIPT PARAMETERS use just \"--help\"\e[0m \n");
        exit(10);
    }

    $directories = [];
    $new_file = fopen($testlist, "r") or exit(11);
    while (($line = fgets($new_file)) != false) {
        $line = trim($line);
        if (is_dir($line)) {
            array_push($directories, $line);
            if ($recursive)
                $directories = array_merge(recurse_dir($line), $directories);
        }
    }
    fclose($new_file);
}
if ($parse_only && (array_key_exists("int-script", $args) || $interpret_only)) {
    fwrite(STDERR, "\e[91mWRONG SCRIPT PARAMETERS use just \"--int-script\" or \"--parse-script\"\e[0m \n");
    exit(10);
}
if ($interpret_only && (array_key_exists("parse-script", $args) || $parse_only)) {
    fwrite(STDERR, "\e[91mWRONG SCRIPT PARAMETERS use just \"--int-script\" or \"--parse-script\"\e[0m \n");
    exit(10);
}
if (array_key_exists("match", $args)) {
    $match = $args["match"];
}
if (array_key_exists("no-clean", $args)) {
    $no_clean = true;
}
//#################################################################################################

$tests_all = 0;
$passed = 0;
$failed = 0;
$tests = [];

$tmp_file = $directory . "ipp_tempfile.txt";

foreach ($directories as $dir) {
    $tests[$dir]["passed"] = [];
    $tests[$dir]["failed"] = [];
    $test_in_dir = glob($dir . "/*.src");
    foreach ($test_in_dir as $test_src) {
        $test_name = basename($test_src, ".src");

        if (preg_match($match, $test_name) === false) {
            unlink($tmp_file);
            exit(11);
        }
        if (!preg_match($match, $test_name))
            continue;


        $test_input = $dir . "/" . $test_name . ".in";
        $test_output = $dir . "/" . $test_name . ".out";
        $test_ret_code = $dir . "/" . $test_name . ".rc";

        // IF FILES DOES NOT EXISTS
        if (!file_exists($test_input))
            file_write_handler($test_input, "");
        if (!file_exists($test_output))
            file_write_handler($test_output, "");
        if (!file_exists($test_ret_code))
            file_write_handler($test_ret_code, "0");
        $arrt = [];
        array_push($arrt, $test_name);


        if (run_test($test_src, $test_input, $test_output, $test_ret_code)) {
            array_push($tests[$dir]["passed"], $arrt);
            $passed++;
        } else {
            array_push($tests[$dir]["failed"], $arrt);
            $failed++;
        }
        $tests_all++;
    }
}

unlink($tmp_file);

//#################################################################################################
//----- fill table lines with data -----
$tests_results = "";
foreach ($tests as $key => $value) {
    $tests_passed = "";
    $tests_failed = "";
    foreach ($value["passed"] as $passed_test)
        $tests_passed .= '<tr class="test-row"><td class="test-name">' . $passed_test[0] . '</td><td class="test-name">' . $passed_test[1]  . '</td><td class="test-name">' . $passed_test[2]  . '</td><td class="test-result green">Passed</td></tr>';
    foreach ($value["failed"] as $failed_test)
        {
            if ($failed_test[1] == $failed_test[2])
                $fail = "Failed - different output";
            else
            $fail = "Failed - different return code";

        $tests_failed .= '<tr class="test-row"><td class="test-name">' . $failed_test[0] . '</td><td class="test-name">' . $failed_test[1] . '</td><td class="test-name">' . $failed_test[2] . '</td><td class="test-result red">'.$fail.'</td></tr>';
        }

    $failed_sub = count($value["failed"]);
    $passed_sub = count($value["passed"]);
    $count_sub = $failed_sub + $passed_sub;
    if ($failed_sub == 0) {
        $success = 100;
    } elseif ($passed_sub == 0) {
        $success = 0;
    } else {
        $success = round($passed_sub / ($passed_sub + $failed_sub) * 100, 2);
    }
    $dirname = $key;
    if ($dirname == ".") $dirname = "Current directory";
//#################################################################################################
//----- create html substructure for each test directory -----
    $curr_directory = '
        <div class="flex-item">
            <h2 class="dirname">' . $dirname . '</h2>
                <div class="report">
                    <h4>All tests count: ' . $count_sub . '</h4>
                    <h4 class="green">Passed tests count: ' . $passed_sub . '</h4>
                    <h4 class="red">Failed tests count: ' . $failed_sub . '</h4>
                    <h4>Success rate: ' . $success . '%</h4>

                </div>
                <table>
                    <tbody>
                    <tr class="test-row"><td class="test-name bold">TEST</td><td class="test-name bold">RET CODE</td><td class="test-name bold">EXPECTED RET CODE</td><td class="test-result bold">STATUS</td></tr>
                        ' . $tests_failed . '
                        ' . $tests_passed . '
                    </tbody>
            </table>
        </div>
    ';
    if ($count_sub != 0)
        $tests_results .= $curr_directory;
}
$curr_directory = '
<div class="flex-item">
    <h2 class="dirname">OUTPUT DIFFS</h2>
        <div class="report">
        </div>
        <table>
            <tbody>
            <tr class="test-row"><td class="test-name bold">TEST</td><td class="test-name bold">OUTPUT</td><td class="test-name bold">EXPECTED OUTPUT</td></tr>
                ' . $tests_diff . '
            </tbody>
    </table>
</div>
';
if($diff_out)
$tests_results = $curr_directory . $tests_results ;

//#################################################################################################
//----- create base html structure -----
if ($interpret_only) {
    $mode = "Interpret only";
} elseif ($parse_only) {
    $mode = "Parse only";
} else {
    $mode = "Both";
}
if ($failed == 0) {
    $rate = 100;
} elseif ($passed == 0) {
    $rate = 0;
} else {
    $rate = round($passed / ($passed + $failed) * 100, 2);
}
$doc =
    '
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>IPP22 test.php</title>
        <style>
            html {
				font-family: "Courier New", Courier, monospace;
                background-color: silver;
            }
            h1, .report {
				font-family: "Courier New", Courier, monospace;
            }
            h2,
            h3 {
                font-weight: bold;
            }
            .content {
                text-align: center;
            }
            .head {
                background-color: silver;
            }
            .green {
                color: green;
            }
            .red {
                color: red;
            }
            .bold {
                font-weight: bold;
            }
            .flex {
                display: flex;
                flex-wrap: wrap;
                align-items: stretch;
            }
            .flex-item {
                margin-left: auto;
                margin-right: auto;
                width: 75%;
            }
            .test-result {
                text-align: center;
                width: 50%;
            }
            .test-name {
                text-align: center;
            }
            table {
                width: 100%;
                background-color: #ccc;
            }
            td {
                border-bottom: 1px solid white;
                width: 25%;
            }
        </style>
    </head>
    <body>
        <div class="content head">
            <h1>IPP22 Test report</h1>
            <h2>Autor : Tomas Ondrusek</h2>
            <b>Mode: ' . $mode . '</b>
            <div class="report">
                <h2>All tests: ' . $tests_all . '</h2>
                <h3>
                    Passed:
                    <span class="green">' . $passed . '</span>
                </h3>
                <h3>
                    Failed: <span class="red">' . $failed . '</span>
                </h3>
                <h3>Success rate: ' . $rate . '%</h3>
            </div>
        </div>
        <div class="content main">
            <h1>Reports :</h1>
            <div class="flex">' . $tests_results . '</div>
        </div>
    </body>
</html>    
';

fwrite(STDOUT, $doc);

//#################################################################################################
//----- function to recurse and find all directories with tests -----
function recurse_dir($directory)
{
    $directories = [];
    foreach (glob($directory . "/*", GLOB_ONLYDIR) as $dir) {
        $directories = array_merge(recurse_dir($dir), $directories);
        array_push($directories, $dir);
    }
    return $directories;
}
//#################################################################################################
//----- function to write to file -----
function file_write_handler($file, $write)
{
    $new_file = fopen($file, "w") or exit(12);
    fwrite($new_file, $write);
    fclose($new_file);
}

//#################################################################################################
//----- function to compare ret val to reference one -----
function compare_ret_vals($test_ret_code, $retCode)
{
    global $arrt, $test_name, $dir, $no_clean;
    $new_file = fopen($test_ret_code, "r") or exit(11);
    $rc_ref = fgets($new_file);
    array_push($arrt, $retCode);
    array_push($arrt, $rc_ref);
    file_write_handler($dir . "/" . $test_name . "_TMP_retCode.rc", $retCode);
    if (!$no_clean) {
        unlink($dir . "/" . $test_name . "_TMP_retCode.rc");
    }
    if ($rc_ref == $retCode) {
        return true;
    } else {
        return false;
    }
}

//#################################################################################################
//----- function to run individual tests -----
function run_test($test_src, $test_input, $test_output, $test_ret_code)
{
    global $parse_script, $interpret_script, $diff, $parse_only, $interpret_only, $tmp_file, $jexam_config, $dir, $test_name, $no_clean, $tests_diff,$diff_out;
    if ($parse_only) {
        exec("timeout 10s php $parse_script < $test_src 2>/dev/null", $output, $retCode);
    } else if ($interpret_only) {
        exec("timeout 10s python3 $interpret_script --source=$test_src --input=$test_input 2>/dev/null", $output, $retCode);
    } else {
        exec("php $parse_script < $test_src 2>/dev/null", $output, $retCode);
        if ($retCode != 0) {
            if (compare_ret_vals($test_ret_code, $retCode))
                return true;
            else
                return false;
        }
        file_write_handler($tmp_file, implode("\n", $output));
        file_write_handler($dir . "/" . $test_name . "_TMP_XML.xml", implode("\n", $output));
        if (!$no_clean) {
            unlink($dir . "/" . $test_name . "_TMP_XML.xml");
        }
        $output = [];
        exec("timeout 10s python3 $interpret_script --source=$tmp_file --input=$test_input 2>/dev/null", $output, $retCode);
    }
    file_write_handler($dir . "/" . $test_name . "_TMP_OUT.out", implode("\n", $output));
    if (!$no_clean) {
        unlink($dir . "/" . $test_name . "_TMP_OUT.out");
    }
    if (compare_ret_vals($test_ret_code, $retCode)) {
        if ($retCode == 0) {
            $none = "";
            file_write_handler($tmp_file, implode("\n", $output));
            if ($parse_only) {
                exec("$diff -Z --strip-trailing-cr $test_output $tmp_file /dev/null $jexam_config 2>/dev/null", $none, $retCode);
            } else {
                exec("$diff -Z --strip-trailing-cr $test_output $tmp_file 2>/dev/null", $none, $retCode);
            }
            if ($retCode == 0)
                return true;
            else{
                $diff_out = true;
                // echo $test_output;
                $myfile = fopen($test_output, "r") or exit(12);
                $out_ref = fread($myfile,filesize($test_output));
                fclose($myfile);
                $myfile = fopen($tmp_file, "r") or exit(12);
                $out = fread($myfile,filesize($tmp_file));
                fclose($myfile);
                $tests_diff .= '<tr class="test-row"><td class="test-name">' . $test_name . '</td><td class="test-name">' . $out . '</td><td class="test-name">' . $out_ref. '</td></tr>';

                // echo $tmp_file;
                // echo "\n";
                return false;
            }
        }
        return true;
    }
    return false;
}

//#################################################################################################
//----- function to printout help -----
function printHelp()
{
    echo  "
     _____ _____  _____             _            _           _           
    |_   _|  __ \|  __ \           | |          | |         | |          
      | | | |__) | |__) |  ______  | |_ ___  ___| |_   _ __ | |__  _ __  
      | | |  ___/|  ___/  |______| | __/ _ \/ __| __| | '_ \| '_ \| '_ \ 
     _| |_| |    | |               | ||  __/\__ \ |_ _| |_) | | | | |_) |
    |_____|_|    |_|                \__\___||___/\__(_) .__/|_| |_| .__/ 
                                                      | |         | |    
                                                      |_|         |_|    
   ";
    echo "Tester for interpret.py and parse.php\n";
    echo "Usage: test.php [ --help | --directory=dir | --recursive | --parse-script=script | --int-script=script | --parse-only | --int-only | --jexam=file | --testlist=file | --match=regex ]\n";

    echo "    --directory     | Search directory for tests\n";
    echo "    --recursive     | Search directory recursively\n";
    echo "    --parse-script  | Path to parse script\n";
    echo "    --int-script    | Path to interpret script\n";
    echo "    --jexam         | Path to xml comparator\n";
    echo "    --parse-only    | Only test parse script\n";
    echo "    --int-only      | Only test interpret script\n";
    echo "    --testlist      | File containing names of test directories\n";
    echo "    --match         | Do only tests that match set regex\n";


    echo "\nExample usage: \n";
    echo "    ./parse.php --help \n";
    echo "    ./parse.php --directory=tests --int-only --int-script=./interpret.py \n";
    exit(0);
}
//#################################################################################################