#!/usr/bin/python

import filecmp # Compare *_lifted.ob with *_lifted_lifted.ob
import glob # Find *.ob files within assorted file structures
import os # Path methods
import re # Regex
import subprocess # Popen for running tests
import sys # Command line arguments and exit

COMMAND = ""
TESTS = None
LEVEL = None
CODEGEN = False
REFERENCE_COMPILER = False

#######################################################################
# Runs all tests for Silver's implementation of Oberon0
#
# Written by: Kevin Williams
#######################################################################

def printTest(test_type, passed, error, path):
  ## Unified method to show results to user
  text = test_type + "\t" + "- "
  
  if passed:
    text += "PASS:"
  else: # not passed
    text += "FAIL: " + error

  text += "\t"

  text += path

  print text.expandtabs(20)


def runPositiveTest(testpath, results):
  success = False

  ## Remember where we started
  cur_dir = os.path.abspath('.') + "/"

  ## cd into testname's location
  os.chdir(os.path.dirname(os.path.abspath(testpath)))

  ## Remove directory portion of testname
  testname = os.path.basename(testpath)

  outputs = subprocess.Popen(COMMAND + ' ' + testname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  stdout_output = outputs.stdout.readlines()
  stderr_output = outputs.stderr.readlines()

  if REFERENCE_COMPILER:
    if len(stdout_output) > 0:
      if 'line' in stdout_output[0]:
        ## Error found
        printTest("Positive test", False, "ERROR", testpath)
        results['positive'][1] = results['positive'][1] + 1
        results['fail']['ERROR'].append(testpath)
      else: # 'line' not in stdout_output[0]
        ## Output found, but no line -> just output
        printTest("Positive test", True, "", testpath)
        results['positive'][0] = results['positive'][0] + 1
        success = True
    elif len(stderr_output) > 0:
      ## Stderr found
      printTest("Positive test", False, "STDERR", testpath)
      results['positive'][1] = results['positive'][1] + 1
      results['fail']["STDERR"].append(testpath)
    else: # len(stdout_output) <= 0
      ## No output -> no error
      printTest("Positive test", True, "", testpath)
      results['positive'][0] = results['positive'][0] + 1
      success = True

  elif len(stdout_output) > 0:
    printTest("Positive test", False, "ERROR", testpath)
    results['positive'][1] = results['positive'][1] + 1
    results['fail']['ERROR'].append(testpath)

  elif len(stderr_output) > 0:
    printTest("Positive test", False, "STDERR", testpath)
    results['positive'][1] = results['positive'][1] + 1
    results['fail']["STDERR"].append(testpath)

  else:
    printTest("Positive test", True, "", testpath)
    results['positive'][0] = results['positive'][0] + 1
    success = True
  
  ## cd back to where we started
  os.chdir(os.path.dirname(cur_dir))
  
  return success

 
def runParseTest(testpath, results):
  success = False

  ## Remember where we started
  cur_dir = os.path.abspath('.') + "/"

  ## cd into testname's location
  os.chdir(os.path.dirname(os.path.abspath(testpath)))

  ## Remove directory portion of testname
  testname = os.path.basename(testpath)

  outputs = subprocess.Popen(COMMAND + ' ' + testname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  
  stdout_output = outputs.stdout.readlines()
  stderr_output = outputs.stderr.readlines()

  if REFERENCE_COMPILER:
    if len(stdout_output) > 0:
      ## Error found
      printTest("Parse test", True, "", testpath)
      results['parse'][0] = results['parse'][0] + 1
      success = True

    elif len(stderr_output) > 0:
      ## Stderr found
      printTest("Parse test", False, "STDERR", testpath)
      results['parse'][1] = results['parse'][1] + 1
      results['fail']["STDERR"].append(testpath)

    else: # len(stdout_output) <= 0 and len(stderr_output) <= 0
      ## No output -> no error
      printTest("Parse test", False, "NO ERROR", testpath)
      results['parse'][1] = results['parse'][1] + 1
      results['fail']["NO ERROR"].append(testpath)

  elif len(stdout_output) == 0 and len(stderr_output) == 0:
    printTest("Parse test", False, "NO ERROR", testpath)
    ## Fail - Must have errors to pass
    results['parse'][1] = results['parse'][1] + 1
    results['fail']["NO ERROR"].append(testpath)

  elif len(stderr_output) > 0:
    printTest("Parse test", False, "STDERR", testpath)
    ## Fail - Errors sent to stderr -> incorrect error.
    results['parse'][1] = results['parse'][1] + 1
    results['fail']["STDERR"].append(testpath)

  else: # len(returned_lines) != 0:
    printTest("Parse test", True, "", testpath)
    results['parse'][0] = results['parse'][0] + 1
    success = True
  
  ## cd back to where we started
  os.chdir(os.path.dirname(cur_dir))

  return success


def runNameTypeTest(testpath, results):
  success = False

  ## Remember where we started
  cur_dir = os.path.abspath('.') + "/"

  ## cd into testname's location
  os.chdir(os.path.dirname(os.path.abspath(testpath)))

  ## Remove directory portion of testname
  testname = os.path.basename(testpath)

  outputs = subprocess.Popen(COMMAND + ' ' + testname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  stdout_output = outputs.stdout.readlines()
  stderr_output = outputs.stderr.readlines()

  if REFERENCE_COMPILER:
    if len(stdout_output) > 0:
      if 'line' in stdout_output[0]:
        ## Error found
        success = checkErrorInNameOrTypeTest(stdout_output, results, testpath, testname)

      else: # 'line' not in stdout_output[0]
        ## No line -> no error
        printTest("Name or Type Test", False, "NO ERROR", testpath)
        results['name_type'][1] = results['name_type'][1] + 1
        results['fail']["NO ERROR"].append(testpath)

    elif len(stderr_output) > 0:
      ## Stderr found
      printTest("Name or Type Test", False, "STDERR", testpath)
      results['name_type'][1] = results['name_type'][1] + 1
      results['fail']["STDERR"].append(testpath)

    else: # len(stdout_output) <= 0 and len(stderr_output) <= 0
      ## No output -> no error
      printTest("Name or Type Test", False, "NO ERROR", testpath)
      results['name_type'][1] = results['name_type'][1] + 1
      results['fail']["NO ERROR"].append(testpath)

  elif len(stdout_output) == 0 and len(stderr_output) == 0:
    printTest("Name or Type Test", False, "NO ERROR", testpath)
    ## Fail - Must have errors to pass
    results['name_type'][1] = results['name_type'][1] + 1
    results['fail']["NO ERROR"].append(testpath)

  elif len(stderr_output) > 0:
    printTest("Name or Type Test", False, "STDERR", testpath)
    ## Fail - Errors sent to stderr -> incorrect error.
    results['name_type'][1] = results['name_type'][1] + 1
    results['fail']["STDERR"].append(testpath)

  else: # len(returned_lines) != 0:
    success = checkErrorInNameOrTypeTest(stdout_output, results, testpath, testname)

  ## cd back to where we started
  os.chdir(os.path.dirname(cur_dir))

  return success


def checkErrorInNameOrTypeTest(stdout_output, results, testpath, testname):
  """ Subroutine to compare a returned error with the name of the test """
  success = False

  match = None # Flag to hold match object
  i = 0 # Current index of returned_lines

  # Regex to find line number in returned error
  line_pattern = r'(?:.*[Ll]ine[:]?\s+)?(\d+)'

  match = re.match(line_pattern, stdout_output[0])

  if not match:
    printTest("Name or Type Test", False, "NO LINE", testpath)
    results['name_type'][1] = results['name_type'][1] + 1
    results['fail']["NO LINE"].append(testpath)
  else: # match
    # Found a match in the error!
    found_line = match.group(1)
    
    # Regex to find a match in the filename...
    file_pattern = '(' + found_line + r')_.*\.ob'

    if not re.match(file_pattern, testname):
      # Line found in error doesn't match line found in filename
      printTest("Name or Type Test", False, "LINE "+found_line, testpath)
      results['name_type'][1] = results['name_type'][1] + 1
      results['fail']["WRONG LINE"].append(testpath)

    else: #re.match(file_pattern, testname)
      # Line found in error matches line found in filename!
      printTest("Name or Type Test", True, "", testpath)
      results['name_type'][0] = results['name_type'][0] + 1
      success = True
  
  return success


def compareLifted(lifted, lifted_lifted, results):
  success = False
  
  if not os.path.exists(lifted):
    printTest("Compare Lifted", False, "NO FILE 1", lifted)
    results['lifted_cmp'][1] = results['lifted_cmp'][1] + 1
    results['fail']["LIFTED ERR"].append(testpath)

  else: #os.path.exists(lifted)
    if not os.path.exists(lifted_lifted):
      printTest("Compare Lifted", False, "NO FILE 2", lifted_lifted)
      results['lifted_cmp'][1] = results['lifted_cmp'][1] + 1
      results['fail']["LIFTED ERR"].append(testpath)

    else: #os.path.exists(lifted_lifted):
      comparison = filecmp.cmp(lifted, lifted_lifted)
      
      if not comparison:
        printTest("Compare Lifted", False, "DIFFERENT", lifted_lifted)
        results['lifted_cmp'][1] = results['lifted_cmp'][1] + 1
        results['fail']["LIFTED ERR"].append(testpath)

      else: # comparison == True
        printTest("Compare Lifted", True, "", lifted_lifted)
        results['lifted_cmp'][0] = results['lifted_cmp'][0] + 1
        success = True
  
  return success


def runCCode(testpath, results):
  success = False

  ## Check for existence
  if not os.path.exists(testpath):
    printTest("Positive Run C", False, "NO C FILE", testpath)
    results['compile_c'][1] = results['compile_c'][1] + 1
    results['fail']['NO C FILE'].append(testpath)
  else: #os.path.exists(testpath):

    ## Remember where we started
    cur_dir = os.path.abspath('.') + "/"

    ## cd into testname's location
    os.chdir(os.path.dirname(os.path.abspath(testpath)))

    ## Remove directory portion of testname
    testname = os.path.basename(testpath)
    executable = os.path.splitext(testname)[0] + '.a'

    exit_code = os.system('gcc ' + testname + ' -o ' + executable)

    if exit_code != 0:
      printTest("Positive GCC", False, "GCC ERR: " + str(exit_code), testpath)
      results['compile_c'][1] = results['compile_c'][1] + 1
      results['fail']['GCC ERR'].append(testpath)
    else: #exit_code == 0
      printTest("Positive GCC", True, "", testpath)
      results['compile_c'][0] = results['compile_c'][0] + 1

      ## Configure stdin
      stdin_file = os.path.splitext(testname)[0] + '.stdin'
      #print "STDIN FILE:", stdin_file

      stdin_text = ""
      if os.path.exists(stdin_file):
        stdin_text = "< " + stdin_file + " "
      #print "STDIN TEXT:", stdin_text

      ## Configure stdout
      stdout_file = os.path.splitext(testname)[0] + '.stdout'

      if os.path.exists(stdout_file):
        os.remove(stdout_file)

      ## Run the compiled executable
      outputs = subprocess.Popen('./' + executable + ' ' + stdin_text + ' > ' + stdout_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      ## Not needed; redirected to stdout_file
      #stdout_output = outputs.stdout.readlines()

      stderr_output = outputs.stderr.readlines()

      if len(stderr_output) > 0:
        printTest("Positive Run", False, "STDERR", executable)
        results['run_c'][1] = results['run_c'][1] + 1
        results['fail']['STDERR'].append(testpath)
      else:
        printTest("Positive Run", True, "", testpath)
        results['run_c'][0] = results['run_c'][0] + 1

        expected = os.path.splitext(testname)[0] + '.expected'

        ## Compare stdout_file to .expected
        if not os.path.exists(expected):
          ## stdout file doesn't exist
          if os.path.getsize(stdout_file) == 0:
            ## .expected doesn't exist and no stdout -> Pass
            printTest("Compare Empty", True, "", expected)
            results['expected_cmp'][0] = results['expected_cmp'][0] + 1
          else: #os.path.getsize(stdout_file) != 0
            printTest("Compare Empty", False, "NO .expected FILE", expected)
            results['expected_cmp'][1] = results['expected_cmp'][1] + 1
            results['fail']['NO EXP FILE'].append(testpath)
        else: #os.path.exists(expected)
          if not os.path.exists(stdout_file):
            printTest("Compare Expected", False, "NO STDOUT FILE", stdout_file)
            results['expected_cmp'][1] = results['expected_cmp'][1] + 1
            results['fail']['NO STDOUT FILE'].append(testpath)
          else: #os.path.exists(stdout_file)
            comparison = filecmp.cmp(expected, stdout_file)

            if not comparison:
              printTest("Compare Expected", False, "EXP CMP", stdout_file)
              results['expected_cmp'][1] = results['expected_cmp'][1] + 1
              results['fail']["EXP CMP"].append(testpath)
            else: #comparison == True
              printTest("Compare Expected", True, "", stdout_file)
              results['expected_cmp'][0] = results['expected_cmp'][0] + 1
              success = True

    os.chdir(os.path.dirname(cur_dir))


  return success


def printResults(results):
  text = ""
  if len(results['fail']) > 0:
    text += '\n'
    text += 'Failures:' + '\n' 
    for fail_group in results['fail']:
      if len(results['fail'][fail_group]) > 0:
        text += '\t' + fail_group + '\n' 
        for f in results['fail'][fail_group]:
          text += '\t\t' + f + '\n' 
  text += '\n' 
  text += 'Positive tests:\tLifted compare:' + '\tCompare Expected:' + '\n' 
  text += 'Pass: ' + str(results['positive'][0]) + '\t\tPass: ' + str(results['lifted_cmp'][0]) + '\t\tPass: ' + str(results['expected_cmp'][0]) + '\n' 
  text += 'Fail: ' + str(results['positive'][1]) + '\t\tFail: ' + str(results['lifted_cmp'][1]) + '\t\tFail: ' + str(results['expected_cmp'][1]) + '\n' 
  text += '\n'
  text += 'Name or type tests:\tCompile C:' + '\n' 
  text += 'Pass: ' + str(results['name_type'][0]) + '\t\tPass: ' + str(results['compile_c'][0]) + '\n' 
  text += 'Fail: ' + str(results['name_type'][1]) + '\t\tFail: ' + str(results['compile_c'][1]) + '\n' 
  text += '\n'
  text += 'Parse tests:\tRun C:' + '\n' 
  text += 'Pass: ' + str(results['parse'][0]) + '\t\tPass: ' + str(results['run_c'][0])  + '\n' 
  text += 'Fail: ' + str(results['parse'][1]) + '\t\tPass: ' + str(results['run_c'][1])  + '\n' 
  text += '\n'
  text += 'Summary:' + '\n' 
  text += 'Pass: ' + str(results['positive'][0] + 
                         results['name_type'][0] +
                         results['parse'][0] +
                         results['lifted_cmp'][0] +
                         results['compile_c'][0] +
                         results['run_c'][0] +
                         results['expected_cmp'][0]) + '\n' 
  text += 'Fail: ' + str(results['positive'][1] + 
                         results['name_type'][1] +
                         results['parse'][1] +
                         results['lifted_cmp'][1] +
                         results['compile_c'][1] +
                         results['run_c'][1] +
                         results['expected_cmp'][1]) + '\n' 

  print text.expandtabs(12)

def main():
  global COMMAND
  global TESTS
  global LEVEL
  global CODEGEN
  global REFERENCE_COMPILER

  if len(sys.argv) > 1:
    ## Is the level specified?
    artifact_pattern = r'-?(A(?:[1345]|2[ab]))'
    for i in sys.argv[1:]:
      m = re.match(artifact_pattern, i)
      if m and not LEVEL:
        artifact = m.group(1)
        sys.argv.remove(m.group(0))
        if artifact == 'A1':
          LEVEL = ['L1', 'L2']
          TESTS = ['T1', 'T2']
        elif artifact == 'A2a':
          LEVEL = ['L1', 'L2', 'L3']
          TESTS = ['T1', 'T2']
        elif artifact == 'A2b':
          LEVEL = ['L1', 'L2']
          TESTS = ['T1', 'T2', 'T3']
        elif artifact == 'A3':
          LEVEL = ['L1', 'L2', 'L3']
          TESTS = ['T1', 'T2', 'T3']
        elif artifact == 'A4':
          LEVEL = ['L1', 'L2', 'L3', 'L4']
          TESTS = ['T1', 'T2', 'T3', 'T5a']
        elif artifact == 'A5':
          LEVEL = ['L1', 'L2', 'L3', 'L4', 'L5']
          TESTS = ['T1', 'T2', 'T3', 'T5a']
        else:
          print "Error: Unrecognized artifact:", artifact
          sys.exit(0)

    if not LEVEL or not TESTS:
      print 'LEVEL: ALL'
      LEVEL = ['L1', 'L2', 'L3', 'L4']
      TESTS = ['T1', 'T2', 'T3', 'T5a']

    ## Is codegen specified?
    if '-codegen' in sys.argv:
      CODEGEN = True
      sys.argv.remove('-codegen')

    if '-ref' in sys.argv:
      REFERENCE_COMPILER = True
      sys.argv.remove('-ref')

    ## What's left is the running command
    COMMAND = " ".join(sys.argv[1:])
  else:
    print "Please supply commands to run compiler"
    sys.exit(0)

  PATH_TO_TEST = '../tests/'
  all_tests = []
  ## results[test_type] = [num_pass, num_fail]
  ## results['fail'][fail_type] = [fail_path0, fail_path1, ...]
  results = {'positive':[0,0], 'name_type':[0,0], 'parse':[0,0], 'lifted_cmp':[0,0], 'compile_c':[0,0], 'run_c':[0,0], 'expected_cmp':[0,0],
             'fail':{"ERROR":[], "NO ERROR":[], "WRONG LINE":[], "STDERR":[], "WRONG ERR":[], "LIFTED CMP":[], "GCC ERR":[], "NO C FILE":[], "NO EXP FILE":[], "NO STDOUT FILE":[], "EXP CMP":[], "NO LINE":[], "LIFTED ERR":[]} }


  #####################################################################
  # Find all Oberon0 files within PATH_TO_TEST
  #
  # Files are located in tests/positive/L*/*.ob and tests/negative/L*/*_errors/*.ob
  #
  # Within the path, the following items are found:
  #  * Location of the test
  #  * Whether the test is positive or negative
  #  * The level of the test (L1, L2, etc)
  #####################################################################
  for test_dir in glob.glob(os.path.join(PATH_TO_TEST, "*/positive/L*/*.ob*")):
    if not '_pp' in test_dir and not '_lifted' in test_dir:
      all_tests.append(test_dir)


  for test_dir in glob.glob(os.path.join(PATH_TO_TEST, "*/negative/*_errors/L*/*.ob*")):
    if not '_pp' in test_dir and not '_lifted' in test_dir:
      all_tests.append(test_dir)

  all_tests.sort()

  #####################################################################
  # Run each test
  #####################################################################
  print LEVEL
  print TESTS
  for test in all_tests:
    dirname = os.path.dirname(test)

    for l in LEVEL:
      if l in dirname:
        ## Correct level number, need to check test number
        if 'negative' in dirname:
          ## Skip negative L3 tests if A5
          if not ('L3' in dirname and 'L5' in LEVEL):
            ## T1 -> run tests in parse_errors
            if 'T1' in TESTS and 'parse_errors' in dirname:
              runParseTest(test, results)
  
            ## T2 -> run tests in name_errors
            elif 'T2' in TESTS and 'name_errors' in dirname:
              runNameTypeTest(test, results)
            
            ## T3 -> run tests in type_errors
            elif 'T3' in TESTS and 'type_errors' in dirname:
              runNameTypeTest(test, results)

        elif 'positive' in dirname:
          i = 0
          done = False
          while i < len(LEVEL) and not done:
            if LEVEL[i] in dirname:
              done = True
              success = runPositiveTest(test, results)

              ## if base test succeeds and -codegen in args
              if success and (not REFERENCE_COMPILER) and (CODEGEN or 'T5a' in TESTS):
                splitext = os.path.splitext(test)
                test_lifted = splitext[0] + '_lifted' + splitext[1]
                test_lifted_lifted = splitext[0] + '_lifted_lifted' + splitext[1]

                ## run the compiler on file_lifted.ob(0?), check for no errors
                lifted_success = runPositiveTest(test_lifted, results)
                if lifted_success:
                  compareLifted(test_lifted, test_lifted_lifted, results)

                ## run gcc on file.c, check for zero value return code
                test_c = splitext[0] + '.c'
                runCCode(test_c, results)
            i += 1

        else: # 'negative' not in test and 'positive' not in test
          print "Supertest error, Unknown test:", test

  printResults(results)


if __name__ == "__main__":
  main()
