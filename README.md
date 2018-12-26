# Count 'Em For

A Twitter analysis tool that is interactable via mentions. Count 'Em For will loop through the maximum accessible twitter history of a user and provide total unique words per tweet, most common words, and total tweets analyzed as a reply to a request.

### Motivation

This project was created as a learning exercise for the Serverless Framework, and AWS Lambda and SQS infrastructure.

### Application Structure

`/services/worker.py` - Lambda for filling SQS with unprocessed twitter requests

`/functions/process.py` - Lambda for analyzing tweets and replying to request

`/secrets.yml` - Use `secrets_sample.yml` as a template and provide all needed Twitter authentication information

`/serverless.yml` - Configuration file for the Serverless framework

### Getting Started

##### Setup

[Serverless](https://github.com/serverless/serverless) is a prerequisite.
You can follow the installation guide provided on their github. Our target will be AWS.

[Twitter Developer Account](https://developer.twitter.com) will provide access information.
The Twitter API is used retrieve requests and reply with analysis. Configured in `secrets.yml`

Commands to install and run application:

```
$ sls deploy
```

##### Instructions

Requests will be accepted by mentioning the authenticated twitter account and a second twitter username.

Example of a reply:

```
Unique Words Per Tweet:
5.84

Most Common Words:
team - 20
amazon - 16
thank - 16
today - 14
new - 14

Tweets Analyzed:
182
```

A live demo can be accessed at:
[@countemfor](https://twitter.com/countemfor/with_replies)

##### Testing

Coming Soon

### Built With

* [Serverless](https://github.com/serverless/serverless) - Open-source CLI for building and deploying serverless applications
* [Python Twitter](https://github.com/bear/python-twitter) - A Python wrapper around the Twitter API

### Author

Mike Dunn is a senior Front-end Developer with 5+ years of professional experience. Seeking to help deliver high quality applications through excellent coding practices and technical leadership. Specializing in semantics, optimization and system design.
