import requests
import cachecontrol
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3

class HRootParser():
	def __init__(self):
		self.soup = None
		self.source = None


	def parseSource(self, source):
		self.source = source
		self.soup = BeautifulSoup(source, "html.parser")
		return self.soup


	def getAuthenticityToken(self):
		return self.soup.find("meta", attrs={"name": "csrf-token"})["content"]


	def getActiveParticipants(self):
		stat_content = self.soup.find('h3', text="Statistik:").parent.text
		spos = stat_content.find('Poolteilnehmer:')+15
		epos = stat_content.find('Neuanmeldungen')
		num = stat_content[spos:epos]
		return int(num.strip())


class HRootScrapper():
	def __init__(self, credentialsFilename):
		self.credentialsFilename = credentialsFilename
		self.credentials = self._loadCredentialsFromFile(self.credentialsFilename)
		if not self.credentials:
			raise Exception('credentials could not be loaded from file')

		self.session = requests.session()
		self.session.mount('https://', cachecontrol.CacheControlAdapter())

		self.parser = HRootParser()

		self.baseURL = self.credentials["baseURL"]

		self.paths = {
			"index": "/",
			"login": "/users/login",
			"dashboard": "/admin",
			"logout": "/logout"
		}

		self.experimentId = None
		self.currentPage = ""
		self.currentPageSource = ""


	def _loadCredentialsFromFile(self, filename):
		with open(filename) as credentialsFile:
			fileContent = credentialsFile.read()[:-1]
		credentialsFile.close()

		if not fileContent:
			return False

		(username, password, url, log) = fileContent.split(";")
		if not username or not password or not url or not log:
			return False

		return { "username": username, "password": password, "baseURL": url, "logfile": log }


	def login(self):
		response = self.session.get(self.baseURL+self.paths["login"])
		if response.status_code != requests.codes.ok:
			return False

		self.currentPage = self.paths["login"]
		self.currentPageSource = response.content

		self.parser.parseSource(response.content)
		authToken = self.parser.getAuthenticityToken()

		payload = { 
			"user[email]": self.credentials["username"], 
			"user[password]": self.credentials["password"],
			"utf8": "&#x2713;",
			"authenticity_token": authToken,
			"user[remember_me]": 0,
			"commit": "Login" 
		}

		response = self.session.post(self.baseURL+self.paths["login"], data = payload)
		if response.status_code != requests.codes.ok:
			return False

		self.currentPage = self.paths["dashboard"]
		self.currentPageSource = response.content
		self.parser.parseSource(self.currentPageSource)

		# should validate whether we are acutally on the dashboard page

		return True

	def logout(self):
		response = self.session.get(self.baseURL+self.paths['logout'])
		# if response.status_code != requests.codes.ok:
		# 	print(response.status_code)
		# 	return False

		self.currentPage = self.paths['logout']
		self.currentPageSource = response.content
		self.parser.parseSource(self.currentPageSource)
		return True		


	def getActiveParticipants(self):
		if self.currentPage != self.paths["dashboard"]:
			response = self.session.get(self.baseURL+self.paths["dashboard"])
			if response.status_code != requests.codes.ok:
				return False

		return self.parser.getActiveParticipants()


class DatabaseHandler:
	def __init__(self):
		self.database_file = "countdata.db"
		self.count_table = "participants_table"

		db = self.get_db_connection()


		create_count_table = """
		CREATE TABLE IF NOT EXISTS %s (
		id INTEGER PRIMARY KEY,
		time TEXT,
		count INTEGER);
		""" % self.count_table
		s = db['cursor'].execute(create_count_table)
		# print(s)

		self.close_db_connection(db)



	def get_db_connection(self, database_file = None):
		if database_file == None:
			database_file = self.database_file
		c = sqlite3.connect(database_file)
		con = {
			'connection': c,
			'cursor': c.cursor()
		} 
		return con


	def close_db_connection(self, db_connection):
		db_connection['connection'].commit()
		db_connection['connection'].close()


	def store_count_data(self, count, iso_time):
		query = "INSERT INTO %s (id, time, count) VALUES (NULL,?,?);" % self.count_table
		db = self.get_db_connection()
		s = db['cursor'].execute(query, (iso_time, count))
		self.close_db_connection(db)


class statusMonitor:
	def __init__(self):
		self.s = HRootScrapper("credentials.info")
		self.D = DatabaseHandler()
		self.time_step = 3600 * 3

		self.log_file = self.s.credentials['logfile']

	def log_and_print(self, message):
		timestamp = datetime.now().isoformat()
		log_entry = timestamp + ': ' + str(message)
		with open(self.log_file, 'a') as logfile:
			logfile.write(log_entry+'\n')
		print(log_entry)

	def run(self):

		counter = 0
		start_time = time.time()
		sleep_time = 0.0

		# wait for next midnight
		self.log_and_print('waiting for next midnight')
		tomorrow = datetime.replace(datetime.now() + timedelta(days=1), hour=0, minute=0, second=0)
		delta = tomorrow - datetime.now()
		time.sleep(delta.seconds)

		try:
			while True:
				counter += 1
				execution_target = start_time + counter * self.time_step


				if self.s.login():
					t = datetime.now().isoformat()
					p = self.s.getActiveParticipants()
					self.D.store_count_data(p, t)
					self.s.logout()
					self.log_and_print(p)
				else:
					self.log_and_print('could not get / store data')

				sleep_time = execution_target - time.time()
				time.sleep(sleep_time)

		except KeyboardInterrupt:
			print('shutting down')


if __name__ == '__main__':
	s = statusMonitor()
	s.run()