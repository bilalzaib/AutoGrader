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
                logging.error("Failed to parse score line: " + res_line)
                # TODO: throw exception
                return (0,0,0)

    percent = ((float(passed) * total_points / (passed+failed)) / total_points) * 100
    return (passed, failed, percent)

def run_test(out_file, timeout):
    with open(out_file, 'w') as f:
        sys.stdout = f
        import pytest
        pytest.main(['--timeout=' + str(timeout)])
        sys.stdout = sys.__stdout__

def run_student_tests(q, target_folder, total_points, timeout):
    # TODO: Disable networking for submission file
    # Source: https://gist.github.com/hangtwenty/9200597e3be274c79896
    # Source: https://github.com/miketheman/pytest-socket
    #import socket
    #def guard(*args, **kwargs):
    #    raise Exception("I told you not to use the Internet!")
    #socket.socket = guard
    #os.nice()
    #os.setuid()

    logging.debug("Running student tests in: " +target_folder)
    cur_directory = os.getcwd()

    init_file = os.path.join(target_folder, "__init__.py")
    touch(init_file)

    logging.debug("Changing directory ... ")
    os.chdir(target_folder)
    score = (0, 0, 0) # passed, failed, percent

    logging.debug("Capturing stdout")

    out_file = "test-results" + ".log"
    touch(out_file)

    p = Process(target=run_test, args=(out_file, timeout,))
    logging.debug("Starting test process for submission")
    p.start()
    p.join(timeout + 1) # Pytest will also timeout

    #In case process is stuck in infinite loop or something
    if p.is_alive():
        logging.debug("Terminating process [TIMEOUT]")
        p.terminate()
        with open(out_file, 'w') as f:
            f.write("\n\nProcess Terminated")

    with open(out_file) as f:
        out = f.read()

    logging.debug("Restoring stdout")

    # print out
    res_line = out.splitlines()[-1]
    score = get_score_from_result_line(res_line, total_points)

    logging.debug("Restoring working directory ...")
    os.chdir(cur_directory)

    logging.debug("Read test line [" + res_line.strip("=") + "]")
    logging.debug("Calculated score: " + str(score))

    # return [score, out]
    q.put([score, out])

def write_student_log(student_assignment_folder, outlog):
    out_file = os.path.join(student_assignment_folder, "test-results" + ".log")
    logging.debug("Writing log to: " + out_file)
    with open(out_file, "a") as text_file:
        text_file.write(outlog)
