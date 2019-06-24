import sys
import json
import pyodbc
import requests
import billboard
import pandas as pd
from datetime import datetime
import socket

### OPEN CONFIG FILE ###
with open('config.json') as c:
    config = json.load(c)
########################

### GLOBAL FUNCTIONS ###
def printProgressBar (iteration, total, collectedRecords, prefix = ' Progress:', suffix = 'Complete', decimals = 1, length = 50, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s | Records: %s' % (prefix, bar, percent, suffix, collectedRecords), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()
########################

### GLOBAL VARIABLES ###
start_time = datetime.now()
max_errors = 100
errors = 0
error_log = []
# Billboard vars
chart_end_date 	 = '1995-12-31'
chart_start_date = '1990-01-01'
chart = billboard.ChartData('hot-100', date=chart_end_date)
days_between = (datetime.strptime(chart_end_date, "%Y-%m-%d") - datetime.strptime(chart_start_date, "%Y-%m-%d")).days
# MusixMatch vars
base_url = "https://api.musixmatch.com/ws/1.1/"
api_match_endpoint = "matcher.track.get"
api_lyrics_endpoint = "track.lyrics.get"
format_url = "?format=json&callback=callback"
api_key = "&apikey=" + config['mxm_api_key']
# Azure Cognitive Services vars
text_analytics_subscription_key = config['text_analytics_subscription_key']
text_analytics_base_url = "https://eastus.api.cognitive.microsoft.com/text/analytics/v2.0/"
max_docs = 200
########################

# CREATE MASTER DATAFRAME 
df = pd.DataFrame(columns=['keys', 'songNames', 'artistNames', 'chartDates', 'genres', 'lyrics'])

##########################
# GET EVERY SONG AND ARTIST THAT APPEARED ON HOT 100 CHART FROM NOW UNTIL THE SPECIFIED START DATE
##########################
i = 0
l = int(days_between)
print(" Getting Songs and Lyrics...")
printProgressBar(i,l, len(df))

while chart.previousDate >= chart_start_date:
	try:
		# Get current chart data. Future loops will walk backwards in time.
		chart_data = chart.json()
		chart_json = json.loads(chart_data)
		entries_json = chart_json['entries']

		new_entries = []

		for entry in entries_json:
			key = entry['artist'] + entry['title']
			if key not in list(df['keys']):

				# BEGIN CALLS TO MUSIXMATCH API TO GET SONG LYRICS #

				# Construct first API call, matcher.track.get, to get the MXM track_id
				api_match_call = base_url + api_match_endpoint + format_url + "&q_artist=" + entry['artist'].replace('&', '') + "&q_track=" + entry['title'].replace('&', '') + api_key
				request = requests.get(api_match_call)
				mxm_match = request.json()

				# Parse MXM match request and check for errors. Handle accordingly.
				if mxm_match['message']['header']['status_code'] == 401:
					errors += 1
					error_entry = {
						"key" : key,
						"songName" : entry['title'],
						"artistName" : entry['artist'],
						"runDate" : str(datetime.now())
					}
					error_log.append(error_entry)
					if errors >= max_errors:
						print()
						print('Max 401 Error Limit Reached. :( ')
						sys.exit()
				elif mxm_match['message']['header']['status_code'] == 404:
					pass
				else:
					# Parse MXM returned track data to get MXM track_id
					try:
						mxm_id = mxm_match['message']['body']['track']['track_id']
					except TypeError:
						pass

					# Parse MXM returned track data and get genre
					try:
						genre = mxm_match['message']['body']['track']['primary_genres']['music_genre_list'][0]['music_genre']['music_genre_name']
					except (TypeError, IndexError):
						genre = ''

					# Construct second API call, track.lyrics.get, to get song lyrics
					api_lyrics_call = base_url + api_lyrics_endpoint + format_url + "&track_id=" + str(mxm_id) + api_key
					request = requests.get(api_lyrics_call)
					mxm_lyrics = request.json()

					# Parse MXM returned track data and get lyrics
					try:
						lyrics = mxm_lyrics['message']['body']['lyrics']['lyrics_body']
					except TypeError:
						lyrics = ''

					# Organize responses into Dictionary to add to List
					new_entry = {
						'keys' : key,
						'songNames' : entry['title'],
						'artistNames' : entry['artist'],
						'chartDates' : chart_json['date'],
						'genres' : genre,
						'lyrics' : lyrics
					}
					new_entries.append(new_entry)
		
		# Commit new entries for this loop's chart.date to the master DF
		new_entries_df = pd.DataFrame(new_entries)
		df = pd.concat([df, new_entries_df], sort=False, ignore_index=True)

		# Walk backwards to next chart.date for next loop
		chart = billboard.ChartData('hot-100', chart.previousDate)

		# Update Progress Bar
		new_chart_date = chart.date
		i_date = (datetime.strptime(new_chart_date, "%Y-%m-%d") - datetime.strptime(chart_start_date, "%Y-%m-%d")).days
		i = l - int(i_date)
		printProgressBar(i,l, len(df))
	except Exception as e:
		print(e)
		print("--------------END ERROR--------------")
		print("Query Failed at: " + new_chart_date)
		print(entry['title'] + " by " + entry['artist'] + ' skipped.')
		pass

if i != l:
	printProgressBar(l,l, len(df))

# Trim Waiver from end of lyrics
df['lyrics'] = df['lyrics'].str[:-70]


##########################
# SEND LYRICS TO LANGUAGE DETECTION
##########################
print("Detecting Languages...")
# Create Payload
lyrics_list = [{"id": index, "text": row['lyrics']} for index,row in df.iterrows()]
lang_list = []
# Send Request(s) (max number of documents per request = 1000)
language_api_url = text_analytics_base_url + "languages"
first = -(max_docs)
last = -1
while last < len(lyrics_list):
	# Increment slice of lyrics_list for new API call
	first += max_docs
	if last + max_docs > len(lyrics_list):
		last = len(lyrics_list)
	else:
		last += max_docs
	# Format payload and send to API
	documents = {"documents" : lyrics_list[first:last]}
	lang_response = requests.post(language_api_url, headers={"Ocp-Apim-Subscription-Key": text_analytics_subscription_key}, json=documents)
	# Get and parse API Response
	languages = lang_response.json()
	try:
		if languages['error']['statusCode'] == 403:
			print('Azure Text Analytics: ' + languages['error']['message'])
			sys.exit()
	except KeyError:
		pass
	# Format Response to list and append each document to new list
	for lang in languages['documents']:
		lang_list.append({"id": lang['id'], "languages": lang['detectedLanguages'][0]['iso6391Name']})

# Commit resulting documents list to DF
df_lang = pd.DataFrame(lang_list).set_index('id')
df_lang.index = df_lang.index.map(int)
# Merge response DF with Master DF
df = pd.merge(df, df_lang, left_index=True, right_index=True)

##########################
# SEND LYRICS AND LANGUAGE TO SENTIMENT ANALYSIS
##########################
print("Analyzing Sentiment...")
# Create Payload
lyrics_list = [{"id": index, "language": row['languages'], "text": row['lyrics']} for index,row in df.iterrows()]
sent_list = []
# Send Request(s) (max number of documents per request = 1000)
sentiment_api_url = text_analytics_base_url + "sentiment"
first = -(max_docs)
last = -1
while last < len(lyrics_list):
	# Increment slice of lyrics_list for new API call	
	first += max_docs
	if last + max_docs > len(lyrics_list):
		last = len(lyrics_list)
	else:
		last += max_docs
	# Format payload and send to API
	documents = {"documents" : lyrics_list[first:last]}
	sent_response = requests.post(sentiment_api_url, headers={"Ocp-Apim-Subscription-Key": text_analytics_subscription_key}, json=documents)
	# Get and parse API Response
	sentiments = sent_response.json()
	try:
		if sentiments['error']['statusCode'] == 403:
			print('Azure Text Analytics: ' + sentiments['error']['message'])
			sys.exit()
	except KeyError:
		pass
	# Format Response to list and append each document to new list
	for sent in sentiments['documents']:
		sent_list.append(sent)

# Commit resulting documents list to DF
df_sent = pd.DataFrame(sent_list).set_index('id')
df_sent.index = df_sent.index.map(int)
# Merge response DF with Master DF
df = pd.merge(df, df_sent, left_index=True, right_index=True)

##########################
# WRITE PANDAS DATAFRAME TO SQL DB
##########################
# Prompt user to start write to DB
write_to_db = ''
while write_to_db != 'y':
	write_to_db = input('Data Prepared. Write Data to SQL? (y/n) ')
	if write_to_db == 'y':
		pass
	elif write_to_db == 'n':
		print('Terminating Program...')
		sys.exit()
	else:
		print('Enter Valid Response...')

# Start write to SQL DB
print()
print(" Writing Data to Azure SQL DB...")
sqlConnStr = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server}; SERVER='+config['db_server']+'; DATABASE='+config['db']+'; UID='+config['db_username']+'; PWD='+config['db_password'])
cursor = sqlConnStr.cursor()
i = 0
l = len(df)
printProgressBar(i,l, i)
for index,row in df.iterrows():
	cursor.execute("INSERT INTO dbo.Hot100_Lyrics([songName],[artistName],[chartDate],[genre],[lyrics],[language],[sentiment]) values (?,?,?,?,?,?,?)", row['songNames'], row['artistNames'], row['chartDates'], row['genres'], row['lyrics'], row['languages'], row['score']) 
	sqlConnStr.commit()
	i = i+1
	printProgressBar(i,l, i)
cursor.close()
sqlConnStr.close()

##########################
# WRITE 401 ERRORS OUT TO JSON FILE
##########################
with open('errors.json', 'a+') as ej:
    json.dump(error_log, ej)

##########################
# PRINT OUT SCRIPT RESULTS
##########################
print()
print(" Number of unique Hot 100 Tracks between " + chart_start_date + " and " + chart_end_date +": " + str(len(df)))
print()
print(" Script run time: " + str(datetime.now() - start_time))
print()