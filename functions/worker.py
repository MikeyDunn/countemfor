# system imports
import calendar
import boto3
import time
import json
import os

# dependency imports
import twitter

# constants
SQS_URL = os.environ['SQS_URL']
TWITTER_MAX_COUNT = int(os.environ['TWITTER_MAX_COUNT'])

# services
sqs_client = boto3.client('sqs')
twitter_client = twitter.Api(
    consumer_key=os.environ['API_KEY'],
    consumer_secret=os.environ['API_SECRET'],
    access_token_key=os.environ['ACCESS_TOKEN'],
    access_token_secret=os.environ['SECRET_TOKEN'],
    tweet_mode='extended')

# handler will retrieve mentions from twitter for processing.
# The queue tag 'LastUpdated' will be used as a date limit for
# unprocessed requests.
def handler(json_input, context):
    # get the last updated epoch
    last_updated_epoch = last_updated_tag()

    # retrieve new mentions
    entries = get_mentions(last_updated_epoch)

    # send unprocessed mentions to queue
    sent_response = None
    if len(entries) > 0:
        sent_response = sqs_client.send_message_batch(
            QueueUrl=SQS_URL,
            Entries=entries)

    return sent_response

# last_updated_tag will return the last processed epoch.
# This is the last time mentions were requested from twitter.
# The tag will be updated after retrieving for the next run.
def last_updated_tag():
    now_epoch = int(time.time())

    # get last updated time
    tag_response = sqs_client.list_queue_tags(QueueUrl=SQS_URL)
    last_updated_epoch = int(tag_response['Tags'].get('LastUpdated', now_epoch))

    # set last updated time to now
    sqs_client.tag_queue(
        QueueUrl=SQS_URL,
        Tags={'LastUpdated': str(now_epoch)})

    return last_updated_epoch

# get_mentions will make requests to the twitter getMentions endpoint.
# This will iterate until the request returns entries that are older
# than the last processed epoch. Returns a list of entries for
# sending to the sqs.
def get_mentions(limit_epoch):
    at_end = False
    entries = []

    while not at_end:
        # make mentions request
        tweet_list = twitter_client.GetMentions(
            count=TWITTER_MAX_COUNT,
            return_json=True)

        # iterate through teweets
        for index, tweet in enumerate(tweet_list):
            tweet_time = time.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
            tweet_epoch = calendar.timegm(tweet_time)

            # if the tweet is older than last update
            # the loops has reached the end
            if tweet_epoch < limit_epoch:
                at_end = True
                break

            # append tweet to entry message
            tweet_string = json.dumps(tweet)
            entries.append({
                'Id': str(index),
                'MessageBody': tweet_string
            })

    return entries
