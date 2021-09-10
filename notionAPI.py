# imports
import requests, json, os
from dotenv import load_dotenv
import logging

# load variables from .env
load_dotenv()

# init logging
# get script directory
scriptDir = os.path.dirname(os.path.realpath(__file__))
print(scriptDir)
loggingFormat = "%(levelname)s: [%(asctime)s]#%(filename)s:%(lineno)s %(message)s"
logging.basicConfig(filename=scriptDir + "/notionAPI.log", level=0, format=loggingFormat)
logger = logging.getLogger()
logger.info("Logger started")

def readData(token=os.getenv("notionAPI"), databaseID=os.getenv("database"), sort = None, showAll = False):
	"""
		will return data read from the notion API, default is to return only properties to get all add showAll = True
		provide database id and toke (can be in .env)
		optional: give sort array [ 'fieldname', 'asc' ] | type of sorting can be empty
	"""
	url = f"https://api.notion.com/v1/databases/{databaseID}/query"
	head = getHead(token)

	# Validation sort array if exists
	if sort:
		# make array of array if provided just array
		if(type(sort[0]) == str):
			sort = [sort]

		for s in sort:
			if len(s) > 1 and s[1] not in ["", "asc", "desc", 'ascending', 'descending'] or len(s) > 2:
				logger.error("User provided wrong 2nd argument of sort property")
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
		logger.error('Notion API return error')
		exit(1)

def readSchema(token=os.getenv("notionAPI"), databaseID=os.getenv("database"), showAll=False):
	"""
		return schema read from the notion API, by default just returns the properties to get all add showAll = True
		provide database id and toke (can be in .env)
	"""
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
		logger.error('Notion API return error')
		exit(1)

def create(data, databaseID=os.getenv("database"), token=os.getenv("notionAPI"), debug = False):
	"""
		will create a new entry in the notion database
		provide array of arrays as data variable where
			1st: field name
			2nd: field value
			3rd: color (optional), for select, multiselect fields
		Also provide database id and token (if not provided will be taken from .env file)
	"""
	url = "https://api.notion.com/v1/pages"
	header = getHead(token)

	finalData = {
		"parent": {"database_id": databaseID},
		"properties": {}
	}

	finalData = prepareProperties(finalData, data)

	if debug:
		print("--- DEBUG ---")

		print('URL: ', url)
		print("Header: ")
		printJSON(header)
		print("Data:")
		printJSON(finalData)

		print("--- DEBUG ---")

	r = requests.post(url, headers=header, json=finalData)

	if r.status_code == 200:
		return r.json()
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
	logging.error("This property not in this database")
	exit(1)

# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #

def getHead(token=os.getenv("notionAPI"), type = None):
	if token == "" or token == None:
		print("No token provided")
		logging.error("No token provided")
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

def prepareProperties(finalData, data):
	if(type(data[0]) == str):
		data = [data]

	for i in data:
		fieldType = getFieldType(i[0])

		if fieldType in ['title', 'rich_text']:
			finalData['properties'][i[0]] = {
					fieldType: [
						{
							"text": {
								"content": i[1]
							}
						}
					]
				}

		elif fieldType in ['number']:
			if type(i[1]) == str and not i[1].isnumeric():
				print(f"Wrong value for '{i[0]}'' it should be number")
				logger.error("Provided unconvertible value of numberic type")
				exit(1)

			i[1] = int(i[1])
			finalData['properties'][i[0]] = {
				fieldType: i[1]
			}

		elif fieldType in ['select']:
			if len(i) == 2:
				finalData['properties'][i[0]] = {
					fieldType: {
						"name": i[1]
					}
				}
			elif len(i) == 3 and i[2].lower() in ["default", "gray", "brown", "red", "orange", "yellow", "green", "blue", "purple", "pink"]:
				finalData['properties'][i[0]] = {
					fieldType: {
						"name": i[1],
						"color": i[2].lower()
					}
				}
			elif len(i) == 3:
				print('Color can be one of "default", "gray", "brown", "red", "orange", "yellow", "green", "blue", "purple", "pink"')
				logging.error("Wrong color provided!")
				exit(1)
			else:
				print('Wrong number of arguments should be 2 (name of field, value) or 3 (same + color)')
				logging.error("Wrong number of arguments")
				exit(1)
				
		elif fieldType in ['url']:
			finalData['properties'][i[0]] = {
				fieldType: i[1]
			}
	
		else: 
			print(f"We not support {fieldType} yet!") 
			exit(1)

	return finalData