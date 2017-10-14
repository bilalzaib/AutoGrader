import json
import zipfile
import shutil
import logging
import os
import sys
import re
import time
from datetime import datetime
from subprocess import Popen

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

    out_file =  os.path.join(target_folder, "test-results" + ".log")
    touch(out_file)

    with open(out_file, 'w') as f:
        process = Popen(["py.test", "--timeout", str(timeout)], cwd=target_folder, stdout=f, stderr=f, shell=True)
        (output, err) = process.communicate()
        exit_code = process.wait()
    
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

    timeout = (out.find("+ Timeout +") != -1)

    return [score, timeout]
