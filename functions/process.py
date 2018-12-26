# system imports
import collections
import boto3
import time
import json
import re
import os

# dependency imports
import twitter

# constants
SQS_URL = os.environ['SQS_URL']
TWITTER_MAX_COUNT = int(os.environ['TWITTER_MAX_COUNT'])
ANALYSIS_LIMIT = 3200
FILTER_LIST = set({"'tis", "'twas", "a", "able", "about", "across", "after", "ain't", "all", "almost", "also", "am", "among", "an", "and", "any", "are", "aren't", "as", "at", "be", "because", "been", "but", "by", "can", "can't", "cannot", "could", "could've", "couldn't", "dear", "did", "didn't", "do", "does", "doesn't", "don't", "either", "else", "ever", "every", "for", "from", "get", "got", "had", "has", "hasn't", "have", "he", "he'd", "he'll", "he's", "her", "hers", "him", "his", "how", "how'd", "how'll", "how's", "however", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "just", "least", "let", "like", "likely", "may", "me", "might", "might've", "mightn't", "most", "must", "must've", "mustn't", "my", "neither", "no", "nor", "not", "of", "off", "often", "on", "only", "or", "other", "our", "own", "rather", "said", "say", "says", "shan't", "she", "she'd", "she'll", "she's", "should", "should've", "shouldn't", "since", "so", "some", "than", "that", "that'll", "that's", "the", "their", "them", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "tis", "to", "too", "twas", "us", "wants", "was", "wasn't", "we", "we'd", "we'll", "we're", "were", "weren't", "what", "what'd", "what's", "when", "when", "when'd", "when'll", "when's", "where", "where'd", "where'll", "where's", "which", "while", "who", "who'd", "who'll", "who's", "whom", "why", "why'd", "why'll", "why's", "will", "with", "won't", "would", "would've", "wouldn't", "yet", "you", "you'd", "you'll", "you're", "you've", "your", "http", "https", "www", "com", "amp"})

# services
sqs_client = boto3.client('sqs')
twitter_client = twitter.Api(
    consumer_key=os.environ['API_KEY'],
    consumer_secret=os.environ['API_SECRET'],
    access_token_key=os.environ['ACCESS_TOKEN'],
    access_token_secret=os.environ['SECRET_TOKEN'],
    tweet_mode='extended')

# handler will process a tweet on an SQS event.
# The ANALYSIS_LIMIT will be used to gather a target's tweets
# and a count will be built and delivered as a reply
# to the original tweet request
def handler(json_input, context):
    record = json_input['Records'][0]
    receipt_handle = record['receiptHandle']
    stored_tweet = record['body']
    tweet = json.loads(stored_tweet)
    tweet_id = tweet['id']

    try:
        # attempt to get and analyze target's tweets
        target = tweet['entities']['user_mentions'][1]['screen_name']
        tweet_list = get_tweets(target, ANALYSIS_LIMIT)
        word_count = get_counter_by_list(tweet_list)
        tweet_count = len(tweet_list)
        post_response = post_count(tweet_id, word_count, tweet_count)
    except Exception as e:
        print('error', e)

    # remove queue message
    delete_response = sqs_client.delete_message(
        QueueUrl=SQS_URL,
        ReceiptHandle=receipt_handle
    )

    return delete_response

# get tweets will iterate and aggregate a users tweets
# until reaching the end or meeting the provided limit
def get_tweets(user, limit):
    tweet_list = []
    count = limit
    max_id = None

    while count > 0:
        # use maximum allowable count if request size is too large
        max_count = TWITTER_MAX_COUNT if count > TWITTER_MAX_COUNT else count
        tweet_list += twitter_client.GetUserTimeline(
            screen_name=user,
            count=max_count,
            max_id=max_id)
        count -= max_count
        # remove one from id to not return it in next request
        max_id = tweet_list[-1].id - 1

    return tweet_list

# performs get_counter_by_tweet over a list of tweets
# and aggregates the returned word counters
def get_counter_by_list(tweet_list):
    word_counter = collections.Counter()

    for tweet in tweet_list:
        word_counter += get_counter_by_tweet(tweet)

    # return aggregated counts of words
    return word_counter

# process tweets and return a unique word set that doesn't
# contain links, mentions, hashtags or common words provided
# by the FILTER_LIST
def get_counter_by_tweet(tweet):
    output_list = []
    tweet_string = tweet.full_text.lower()
    word_list = tweet_string.split()

    # filter words
    for word in word_list:
        word_clean = re.sub('[^A-Za-z0-9]+', '', word)
        if (word_clean not in FILTER_LIST and
        not word.startswith(('@', '#', 'http')) and
        len(word_clean) > 2):
            output_list.append(word_clean)

    word_counter = collections.Counter(output_list)

    return word_counter

# build and reply a status message to the original request
def post_count(tweet_id, word_count, tweet_count):
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

    post_response = twitter_client.PostUpdate(
        status=status,
        in_reply_to_status_id=str(tweet_id),
        auto_populate_reply_metadata=True)

    return post_response
