# imports
import requests, json, os
from dotenv import load_dotenv
import logging

# load variables from .env
load_dotenv()

# ini logging
loggingFormat = "%(levelname)s: [%(asctime)s]#%(filename)s:%(lineno)s %(message)s"
logging.basicConfig(filename="notionAPI.log", level=0, format=loggingFormat)
logger = logging.getLogger()
logger.info("Logger started")
def readData(token=os.getenv("notionAPI"), databaseID=os.getenv("database"), sort = None, showAll = False):
	url = f"https://api.notion.com/v1/databases/{databaseID}/query"
	head = getHead(token)

	# Validation sort array if exists
	if sort:
		for s in sort:
			if type(s) == str:
				print("sort should be array of arrays")
				print("For example: readData(sort=[['sortCode']]) or readData(sort=[['sortCode'], ['sort']])")
				exit(1)

			if len(s) > 1 and s[1] not in ["", "asc", "desc", 'ascending', 'descending'] or len(s) > 2:
				print("parameter sort is wrong can be in [asc, ascending, desc, descenging, /empty/, /no-exist/]")
				print("For example: readData(sort=[['sortCode']]) or readData(sort=[['sortCode', '']]) or readData(sort=[['sortCode', 'desc']])")
				exit(1)

	# prepare sort array
	if sort is not None:
		finalSort = {
			"sorts": [] }

		for s in sort:
			finalSort['sorts'].append({
				"property": s[0],
				"direction": "ascending" if len(s) == 1 or s[1] == "asc" or s[1] == '' else "descending" })

	# run request
	if sort is None:
		r = requests.post(url, headers=head)
	else:
		r = requests.post(url, headers=head, json=finalSort)

	# return result or error
	if r.status_code == 200:
		if showAll:
			return r.json()
		else:
			return r.json()['results']
	else:
		printJSON(r.json())
		exit(1)

# return schema read from the notion API, by default just returns the properties to get all add showAll = True
# provide database id and toke (can be in .env)
def readSchema(token=os.getenv("notionAPI"), databaseID=os.getenv("database"), showAll=False):
	url = f"https://api.notion.com/v1/databases/{databaseID}"
	header = getHead(token)

	r = requests.get(url, headers=header)

	if r.status_code == 200:
		if showAll:
			return r.json()
		else:
			return r.json()['properties']
	else:
		printJSON(r.json())
		exit(1)


# # # - - - # # # - - - # # # - - - # # # - - - # # # - - - # # # - - - # # # 

def isValidField(field, ignoreCase = False, token=os.getenv("notionAPI"), databaseID=os.getenv("database")):
	data = readSchema(token, databaseID)

	for i in data:
		if ignoreCase and i.lower() == field.lower() or i == field:
			return True
	return False

def getFieldType(field, token=os.getenv("notionAPI"), databaseID=os.getenv("database")):
	data = readSchema(token, databaseID)

	for i in data:
		if i == field:
			return data[i]['type']

	print(f"field '{field}' not found in schema")
	exit(1)

# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #

def getHead(token=os.getenv("notionAPI"), type = None):
	if token == "" or token == None:
		print("No token provided")
		exit(1)

	if not type:
		return {
			"Authorization": "Bearer " + token,
			"Notion-Version": "2021-05-13"
		}
	else:
		return {
			"Authorization": "Bearer " + token,
			"Content-Type": "application/json",
			"Notion-Version": "2021-05-13"
		}

def printJSON(data, tabSize = 2):
	print(json.dumps(data, indent=tabSize, sort_keys=False))
