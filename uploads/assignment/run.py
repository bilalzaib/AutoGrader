import requests
import json
import sys
import requests
import zipfile
import os
import logging
import json
import zipfile
import shutil
import logging
import os
import sys
import re
import time
from datetime import datetime

# Using input() in python 2 or 3
try:
    # set raw_input as input in python2
    input = raw_input
except:
    pass

# logging.basicConfig(filename='submission.log')
logging.basicConfig(level=logging.DEBUG)


url = "##RUN_API_URL##"

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def get_score_from_result_line(res_line, total_points):
    # case where we have failures and passes
    match = re.match(r"=*\s(\d*)\sfailed,\s(\d*)\spassed,\s.*", res_line)
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

def run_student_tests(target_folder, total_points, timeout):
    logging.debug("Running student tests in: " + target_folder)
    cur_directory = os.getcwd()

    init_file = os.path.join(target_folder, "__init__.py")
    touch(init_file)

    logging.debug("Changing directory ... ")
    os.chdir(target_folder)
    score = (0, 0, 0) # passed, failed, percent

    logging.debug("Capturing stdout")

    try:
        from cStringIO import StringIO
    except ImportError:
        from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    import pytest
    pytest.main(["--timeout=" + str(timeout)])
    logging.debug("Restoring stdout")

    sys.stdout = old_stdout
    out = mystdout.getvalue()

    # print out
    res_line = out.splitlines()[-1]
    score = get_score_from_result_line(res_line, total_points)

    logging.debug("Restoring working directory ...")

    logging.debug("Read test line [" + res_line.strip("=") + "]")
    logging.debug("Calculated score: " + str(score))
    os.chdir(cur_directory)

    return (score, out)

def write_student_log(student_assignment_folder, outlog):
    out_file = os.path.join(student_assignment_folder, "test-results" + ".log")
    logging.debug("Writing log to: " + out_file)
    with open(out_file, "a") as text_file:
        text_file.write(outlog)

class Submission():
    config = {}
    config_file_name = "config.json"

    def __init__(self):
        logging.info('Initiated')
        try:
            logging.info('Reading config file')
            with open(self.config_file_name) as file:
                self.config = json.load(file)
        except Exception:
            logging.error("No config file found")
            sys.exit()

    def save_cred(self, cred):
        logging.info('Saving credentials to config file')
        self.config['email'] = cred['email']
        self.config['submission_pass'] = cred['submission_pass']

        # Save File
        with open(self.config_file_name, 'w') as file:
            json.dump(self.config, file)


    def get_cred(self):
        if 'email' in self.config and 'submission_pass' in self.config :
            logging.info('Using credentials of config file')
            cred = {
                "email": self.config['email'],
                "submission_pass": self.config['submission_pass'],
            }
        else:
            logging.info('Asking for API login details')
            cred = {
                "email": input("Enter Email: "),
                "submission_pass": input('Submission Password: '),
            }
            logging.info("")
        return cred

    def submit_assignment(self):
        submission_file = "_submission.zip"

        try:
            logging.info('Deleting old submission file')
            os.remove(submission_file)
        except Exception:
            logging.info('No submission file found')
            pass

        modifiable_files     = self.config['modifiable_files']
        for mf in modifiable_files:
            if not os.path.exists(mf):
                logging.error("Required assignment file not found: ", mf)
                sys.exit("ERROR: needed file not found")

        zip_file = zipfile.ZipFile(submission_file, 'w', zipfile.ZIP_DEFLATED)
        files = modifiable_files

        logging.info('Creating compressed submission file')
        for file in files:
            if file != []:
                zip_file.write(file)
        zip_file.close()
        logging.info('Closing zipped submission file')

        cred = data = self.get_cred()
        data['assignment'] = self.config['assignment']

        logging.info('Sending submission file to server')

        try:
            r = requests.post(url + 'submit_assignment',
                files = {'submission_file': open(submission_file, 'rb')},
                data = data)
        except requests.exceptions.RequestException as e:
            logging.error("ERROR: {}".format(e))
            sys.exit(1)
        finally:
            try:
                logging.info('Deleting submission file')
                os.remove(submission_file)
            except Exception:
                logging.info('No submission file found')
                pass

        if r.status_code == 200:
            result_json = r.json()

            self.save_cred(cred)

            return r
        elif r.status_code == 403:
            logging.error('Login failed, Removing credentials from config file')
            try:
                del self.config['email'];
                del self.config['submission_pass'];
            except Exception:
                pass

            with open(self.config_file_name, 'w') as file:
                json.dump(self.config, file)

            result_json = r.json()
            sys.exit("ERROR: " + result_json['message'])
        elif r.status_code == 400:
            self.save_cred(cred)
            result_json = r.json()
            sys.exit("ERROR: " + result_json['message'])
        else:
            logging.error('Error code in response: ' + str(r.status_code))
            sys.exit("ERROR: Invalid request")

    def run(self):
        if len(sys.argv) == 1:
            sys.exit("ERROR: No argument supplied")
        elif sys.argv[1] == "remote":
            r = self.submit_assignment()
            result = r.json()
            score = result['message']

            if (result['status'] == 200):
                logging.info("RESPONSE: " + " passed: " + str(score[0]) + " failed: " + str(score[1]) + " percent: " + str(score[2]))
                logging.info("NOTE: You can see your submission on web interface also.")
            else:
                logging.error("="*80)
                logging.error(result['message'])
                logging.error("="*80)

        elif sys.argv[1] == "local":
            (result, out) = run_student_tests(os.getcwd(), self.config['total_points'], self.config['timeout'])
            logging.info("RESULT: " + " passed: " + str(result[0]) + " failed: " + str(result[1]) + " percent: " + str(result[2]))
            write_student_log(os.getcwd(), out)
        else:
            sys.exit("ERROR: Invalid argument supplied")



s = Submission()
s.run()
