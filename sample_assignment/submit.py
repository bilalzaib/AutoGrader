import requests
import json
import sys
import urllib.request


url = "http://127.0.0.1:8000/autograde/api/"

class Submission():
	config = {}
	config_file_name = "config.json"

	def __init__(self):
		self.read_config()

	def post(self, url, data = {}):
		cred = {
			"email": self.config['email'],
			"submission_pass": self.config['submission_pass'],
		}

		# Merging two dict
		data = data.copy()
		data.update(cred)
		print (data)
		data = bytes( urllib.parse.urlencode(data).encode() )

		request = urllib.request.Request(url)
		response = urllib.request.urlopen(request, data)
		return response.read().decode('utf-8')

	def write_config(self):
		with open(self.config_file_name, 'w') as file:
			json.dump(self.config, file)

	def read_config(self):
		try:
			with open(self.config_file_name) as file:
				self.config = json.load(file)
		except Exception:
			pass

	def auth(self, email, password):
		return True

	def get_courses(self):
		return self.post(url + "get_course");
		
	def get_assignments(self, course_id):
		return self.post(url + "get_assignment");

	def submit_assignment(self):
		return self.post(url + "submit_assignment");




s = Submission()
s.get_assignments();