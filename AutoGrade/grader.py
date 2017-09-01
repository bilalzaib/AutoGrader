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


    percent = ((float(passed) * total_points / (passed+failed)) / total_points) * 100
    return (passed, failed, percent)

def run_test(out_file, target_folder, timeout):
    # chdir in main process create issue for django
    logger.debug("Changing directory ... ")
    cur_directory = os.getcwd()
    os.chdir(target_folder)

    with open(out_file, 'w') as f:
        sys.stdout = f
        import pytest
        pytest.main(['--timeout=' + str(timeout)])
        sys.stdout = sys.__stdout__

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

    score = (0, 0, 0) # passed, failed, percent

    logger.debug("Capturing stdout")

    out_file =  os.path.join(target_folder, "test-results" + ".log")
    touch(out_file)

    p = Process(target=run_test, args=(os.path.basename(out_file), target_folder, timeout,))
    logger.debug("Starting test process for submission")
    p.start()
    p.join(timeout + 1) # Pytest will also timeout

    #In case process is stuck in infinite loop or something
    if p.is_alive():
        logger.debug("Terminating process [TIMEOUT]")
        p.terminate()
        with open(out_file, 'w') as f:
            f.write("\n\nProcess Terminated due to timeout.")

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
        score = (0, 0, 0) # error means you get a 0

    logger.debug("Read test line [" + res_line.strip("=") + "]")
    logger.debug("Calculated score: " + str(score))

    return [score, out]
