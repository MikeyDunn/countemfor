# system imports
from calendar import timegm
import configparser
import collections
import time
import csv
import re

# dependency imports
import twitter

# config parser
parser = configparser.RawConfigParser()
config_file_ath = 'config.txt'
parser.read(config_file_ath)

# read exclude list
# used as stop words to ignore for unique word counts
with open('exclude.csv', 'r') as f:
  reader = csv.reader(f)
  filter_list = list(reader)[0]
  filter_list = set(filter_list)

# constants
API_KEY = parser.get('config', 'api_key')
SECRET_KEY = parser.get('config', 'secret_key')
ACCESS_TOKEN = parser.get('config', 'access_token')
SECRET_TOKEN = parser.get('config', 'secret_token')
# 900 seconds is twitter period time
# 75 is max requests per period
TWITTER_MAX_REQ_TIME = 900 / 75
TWITTER_API_URL = 'https://api.twitter.com/1.1/'
TWITTER_API_MENTIONS_PATH = 'statuses/mentions_timeline.json'
TWITTER_MAX_COUNT = 200
ANALYSIS_LIMIT = 3200

# services
client = twitter.Api(
    consumer_key=API_KEY,
    consumer_secret=SECRET_KEY,
    access_token_key=ACCESS_TOKEN,
    access_token_secret=SECRET_TOKEN,
    tweet_mode='extended')

# app functions
def getTweets(user, limit):
    tweet_list = []
    count = limit
    max_id = None

    while count > 0:
        # use maximum allowable count if request size is too large
        max_count = TWITTER_MAX_COUNT if count > TWITTER_MAX_COUNT else count
        tweet_list += client.GetUserTimeline(
            screen_name=user,
            count=max_count,
            max_id=max_id)
        count -= max_count
        # remove one from id to not return it in next request
        max_id = tweet_list[-1].id - 1

    return tweet_list

def getMentions():
    tweet_list = client.GetMentions(count=TWITTER_MAX_COUNT)

    for index, tweet in enumerate(tweet_list):
        tweet_time = time.strptime(tweet.created_at,'%a %b %d %H:%M:%S +0000 %Y')
        now_epoch = int(time.time())
        tweet_epoch = timegm(tweet_time)

        # iterate through tweets until reaching a tweet older than needed
        if tweet_epoch < now_epoch - TWITTER_MAX_REQ_TIME:
            tweet_list = tweet_list[:index]
            break

    # return list of tweets that have not been processed
    return tweet_list

def getCounterByList(tweet_list):
    word_counter = collections.Counter()

    for tweet in tweet_list:
        word_counter += getCounterByTweet(tweet)

    # return aggregated counts of words
    return word_counter

def getCounterByTweet(tweet):
    tweet_string = tweet.full_text.lower()
    # match on words larger than 3 characters
    word_reg = re.compile(r'[a-zA-Z]{3,}')
    word_list = word_reg.findall(tweet_string)
    # filter out stop words from exclude.csv
    word_list_filtered = [word for word in word_list if word not in filter_list]
    word_counter = collections.Counter(word_list_filtered)

    return word_counter

def postCount(requestMessageId, word_count, tweet_count):
    total_unique_words = len(word_count)
    unique_words_per_tweet = round(total_unique_words / tweet_count, 2)
    most_common_words = word_count.most_common(5)

    # create tweet message
    status = 'Unique Words Per Tweet:\n'
    status += str(unique_words_per_tweet) + '\n'
    status += '\nMost Common Words:\n'

    for word, count in most_common_words:
        status += word + ' - ' + str(count) + '\n'

    status += '\nTweets Analyzed:\n'
    status += str(tweet_count)

    client.PostUpdate(
        status=status,
        in_reply_to_status_id=str(requestMessageId),
        auto_populate_reply_metadata=True)

def postError(requestMessageId, error):
    client.PostUpdate(
        status=str(error),
        in_reply_to_status_id=str(requestMessageId),
        auto_populate_reply_metadata=True)

# entry point
while True:
    # mentions are considered requests
    # generate a list of unprocessed mentions
    mention_list = getMentions()

    # iterate through mentions and process
    for tweet in mention_list:
        requestMessageId = tweet.id
        target = tweet.user_mentions[1].screen_name
        try:
            tweet_list = getTweets(target, ANALYSIS_LIMIT)
            word_count = getCounterByList(tweet_list)
            tweet_count = len(tweet_list)
            postCount(requestMessageId, word_count, tweet_count)
        except Exception as e:
            postError(requestMessageId, e)

    # sleep for required time not to
    # trigger twitter rate limiting
    time.sleep(TWITTER_MAX_REQ_TIME)
