import requests
import json
import sys
import requests
import getpass
import zipfile
import os

url = "http://127.0.0.1:8000/autograde/api/"

class Submission():
	config = {}
	config_file_name = "student_config.json"
	credential_success = True;

	def __init__(self):
		try:
			with open(self.config_file_name) as file:
				self.config = json.load(file)
		except Exception:
			sys.exit("ERR: No config file detected.")

	def get_cred(self):
		if 'email' in self.config and 'submission_pass' in self.config and self.credential_success != False:
			cred = {
				"email": self.config['email'],
				"submission_pass": self.config['submission_pass'],
			}
		else:
			cred = {
				"email": raw_input("Enter Email: "),
				"submission_pass":  getpass.getpass('Submission Password: '),
			}

		return cred

	def submit_assignment(self):
		submission_file = "_submission.zip"

		try:
			os.remove(submission_file)
		except Exception:
			pass

		modifiable_files 	= self.config['modifiable_files']
		other_files 	 	= self.config['other_files']

		zip_file = zipfile.ZipFile(submission_file, 'w', zipfile.ZIP_DEFLATED)
		files = modifiable_files + other_files
		for file in files:
			zip_file.write(file)
		zip_file.close()

		data = self.get_cred()
		data['assignment'] = self.config['assignment']

		r = requests.post(url + 'submit_assignment', 
			files = {'submission_file': open(submission_file, 'rb')}, 
			data = data)

		return r

	def run(self):
		r = self.submit_assignment()
		print (r.content)


s = Submission()
s.run()