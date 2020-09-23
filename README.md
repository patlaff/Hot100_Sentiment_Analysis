# Billboard Hot 100 Sentiment Analysis

Script to pull a (mostly) unique list of all songs to ever apear on the Billboard Hot 100 List.  
Lyrics for all these songs are then pulled from the MusixMatch API.  
Those lyrics are run through Language Detection using Azure Cognitive Services.  
The lyrics and their corresponding language are passed to Sentiment Analysis using Azure Cognitive Services.  
A second script was written to supplement the previously gathered dataset with song release date (This should have been included in the original script, but I didn't think of it at the time until I realized that "latest chart date" is not an accurate way of showing what I was trying to show)  

## Prerequisites

* SQL DB (This code used an Azure SQL DB, but any DB will do)
* Python 3 - http://www.python.org
* Packages: `pip install requirements.txt`

## Getting Started

* Clone the repo
* Create a config.json file in the same directory you cloned to and copy the following object:
```
{
    "db_username" : "",
    "db_password" : "",
    "db_server" : "",
    "db" : "",
    "mxm_api_key" : "",
    "text_analytics_subscription_key" : ""
} 
```
* Create a [MusixMatch Developer account](https://developer.musixmatch.com/) and get your API key
* Create an [Azure Cognitive Services Text Analytics Account](https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-signup) and get your API key
* Fill in config.json with the keys you just received as well as your database information
* In the GLOBAL VARIABLES section of get_hot100_lyrics.py, change `chart_end_date` and `chart_start_date` to the desired time period to get
    * In my experience, the wider you set this, the more likely the Billboard API is to fail. 5 year increments worked the best for me. Some de-duplication in the dataset will be required after the fact if you do this though.

## Running the scripts

* Run get_hot100_lyrics FIRST using `py get_hot100_lyrics.py` - This will write all collected data out to your specified SQL DB.
* To add song release dates to the dataset run the second script using `py get_releaseDates.py`

## Authors

* [**Patrick Lafferty**](https://github.com/patlaff) - *Owner*
