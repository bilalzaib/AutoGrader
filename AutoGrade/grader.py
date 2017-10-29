import json
import zipfile
import shutil
import logging
import os
import sys
import re
import time
from datetime import datetime
from multiprocessing import Process, Manager, Queue
import tempfile

logger = logging.getLogger(__name__)

def touch(fname, times=None):
    directory = os.path.dirname(fname)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(fname, 'a'):
        os.utime(fname, times)

def get_score_from_result_line(res_line, total_points):
    # case where we have failures and passes
    match = re.match(r"=*\s(\d*)\sfailed,\s(\d*)\spassed,?\s.*", res_line)
    passed = 0
    failed = 0
    if match:
        failed = int(match.group(1))
        passed = int(match.group(2))
    else:
        match = re.match(r"=*\s(\d*)\spassed.*", res_line)
        if match:
            passed = int(match.group(1))
            failed = 0
        else:
            match = re.match(r"=*\s(\d*)\sfailed.*", res_line)
            if match:
                passed = 0
                failed = int(match.group(1))
            else:
                logger.error("Failed to parse score line: " + res_line)
                # TODO: throw exception
                raise EnvironmentError("Failed to parse score line")


    return (passed, failed)

def run_test(out_file, target_folder, timeout):
    # chdir in main process create issue for django
    logger.debug("Changing directory ... ")
    cur_directory = os.getcwd()
    os.chdir(target_folder)

    with open(out_file, 'w') as f:
        old_stdout = sys.stdout 
        old_stderr = sys.stderr 
        sys.stdout = f
        sys.stderr = f
        import pytest
        pytest.main(['--timeout=' + str(timeout)])
        sys.stdout = old_stdout  
        sys.stderr = old_stderr  

    logger.debug("Restoring working directory ...")
    os.chdir(cur_directory)

def run_student_tests(target_folder, total_points, timeout):
    # TODO: Disable networking for submission file
    # Source: https://gist.github.com/hangtwenty/9200597e3be274c79896
    # Source: https://github.com/miketheman/pytest-socket
    #import socket
    #def guard(*args, **kwargs):
    #    raise Exception("I told you not to use the Internet!")
    #socket.socket = guard
    #os.nice()
    #os.setuid()

    logger.debug("Running student tests in: " +target_folder)

    init_file = os.path.join(target_folder, "__init__.py")
    touch(init_file)

    score = (0, 0) # passed, failed

    logger.debug("Capturing stdout")

    out_file =  os.path.join(target_folder, "test-results" + ".log")
    touch(out_file)


    """
    # This code can be used to execute and compile code throught compile, In reference to PR "Languagespp - Temporary Record"

        # Compiling
        logger.debug("Checking code for compilation error")

        # We need to bring assignment variable here.
        cmd = assignment.language.compile_cmd
        cmd = process_cmd(cmd, mainfile, timeout, basename)
        cmd = cmd.split(" ")

        process = Popen(cmd, cwd=target_folder, stdout=f, stderr=f, shell=True)    
                
        (output, err) = process.communicate()
        exit_code = process.wait()

        if exit_code == 0:
            # Executing
            logger.debug("Executing code against test cases")

            cmd = assignment.language.execution_cmd
            cmd = process_cmd(cmd, mainfile, timeout, basename)
            cmd = cmd.split(" ")

            # TODO: Check against pytest, STDIN, File
            # Problem: We will need to add two files, in and out...
            process = Popen(cmd, cwd=target_folder, stdout=f, stderr=f, shell=True)    
                        
            (output, err) = process.communicate()
            p.start()
            exit_code = process.wait()
        else:
            logger.debug("Code failed compilation error")          
            
    with open(out_file) as f:
        out = f.read()

    # If it is pytest then read score from log file
    if "pytest" in assignment.language.name.lower():
        res_line = out.splitlines()[-1]
        try:
            score = get_score_from_result_line(res_line, total_points)
        except EnvironmentError:
            logger.error("===== EnvironmentError found. ======== ")
            logger.error(out)
            out = "Your assignment had critical errors. Please review. If you think this is a system issue, please send details to your admin.\n" + out
            # write back to the out file
            with open(out_file, 'w') as f:
                f.write(out)
            score = (0, 0) # error means you get a 0

        logger.debug("Read test line [" + res_line.strip("=") + "]")
        logger.debug("Calculated score: " + str(score))
    else:
        pass
    """



    p = Process(target=run_test, args=(os.path.basename(out_file), target_folder, timeout,))
    logger.debug("Starting test process for submission")
    p.start()
    p.join() # Pytest will also timeout

    with open(out_file) as f:
        out = f.read()

    # print out
    res_line = out.splitlines()[-1]
    try:
        score = get_score_from_result_line(res_line, total_points)
    except EnvironmentError:
        logger.error("===== EnvironmentError found. ======== ")
        logger.error(out)
        out = "Your assignment had critical errors. Please review. If you think this is a system issue, please send details to your admin.\n" + out
        # write back to the out file
        with open(out_file, 'w') as f:
            f.write(out)
        score = (0, 0) # error means you get a 0

    logger.debug("Read test line [" + res_line.strip("=") + "]")
    logger.debug("Calculated score: " + str(score))

    # Timeout is here because of different behavior of pytest on Linux and Windows environment
    # For complete discussion: https://github.com/BilalZaib/AutoGrader/pull/85#discussion_r144712666
    timeout = (out.find("+ Timeout +") != -1)

    return [score, timeout]