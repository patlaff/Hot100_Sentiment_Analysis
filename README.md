# Billboard Hot 100 Sentiment Analysis

A simple game based on an idea from [this AskReddit Thread](https://www.reddit.com/r/AskReddit/comments/920c2b/whats_a_drinking_game_you_can_play_with_the_front/) (credit to u/mujump)

Game pulls top 100 monthly posts from r/TheOnion and r/NotTheOnion (stores 200 total posts), randomizes a headline, and prompts the user to guess if it is real or fake.

## Prerequisites

* Python 3 - http://www.python.org
* SQL DB (This code used an Azure SQL DB, but any )

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
