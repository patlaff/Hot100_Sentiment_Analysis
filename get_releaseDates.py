import sys
import json
import pyodbc
import requests
import billboard
import pandas as pd
from datetime import datetime

### OPEN CONFIG FILE ###
with open('config.json') as c:
    config = json.load(c)
########################

### GLOBAL FUNCTIONS ###
def printProgressBar (iteration, total, prefix = ' Progress:', suffix = 'Complete', decimals = 1, length = 50, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s ' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()
########################

### GLOBAL VARIABLES ###
start_time = datetime.now()
base_url = "https://api.musixmatch.com/ws/1.1/"
api_match_endpoint = "matcher.track.get"
api_album_endpoint = "album.get"
format_url = "?format=json&callback=callback"
api_key = "&apikey=102da159729cf7e66c9be065ef0d88b0"        #c56c251612909ec56b07b9411bd136b8"

sqlConnStr = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server}; SERVER='+config['db_server']+'; DATABASE='+config['db']+'; UID='+config['username']+'; PWD='+config['password'])
cursor = sqlConnStr.cursor()

df = pd.read_sql("SELECT [songKey],[songName],[artistName] FROM dbo.Hot100 WHERE [releaseDate] IS NULL", sqlConnStr)

print(' Getting and Assigning Track Release Dates...')
l=len(df)
printProgressBar(0,l)

for index,row in df.iterrows():
    printProgressBar(index, l)
    # Construct first API call, matcher.track.get, to get the MXM track_id
    api_match_call = base_url + api_match_endpoint + format_url + "&q_artist=" + row['artistName'].replace('&', '') + "&q_track=" + row['songName'].replace('&', '') + api_key
    request = requests.get(api_match_call)
    mxm_match = request.json()

    try:
        album_id = mxm_match['message']['body']['track']['album_id']
    except Exception as e:
        print(e)
        print(api_match_call)
        print(mxm_match)

    api_album_call = base_url + api_album_endpoint + format_url + "&album_id=" + str(album_id) + api_key
    album_request = requests.get(api_album_call)
    mxm_album = album_request.json()
    
    try:
        album_name = mxm_album['message']['body']['album']['album_name']
        album_release_date = mxm_album['message']['body']['album']['album_release_date']
    except Exception as e:
        print(e)
        print(api_album_call)
        print(mxm_album)

    if len(album_release_date) == 7:
        album_release_date += '-01'
    if len(album_release_date) == 4:
        album_release_date += '-01-01'

    try:
        cursor.execute("UPDATE dbo.Hot100 SET [albumName] = ?, [releaseDate] = ? WHERE [songKey] = ?", album_name,album_release_date,row['songKey']) 
        sqlConnStr.commit()
    except Exception as e:
        print(e)
        print(album_name)
        print(album_release_date)
        print(row['songKey'])

printProgressBar(l,l)

cursor.close()
sqlConnStr.close()

print(" Script run time: " + str(datetime.now() - start_time))