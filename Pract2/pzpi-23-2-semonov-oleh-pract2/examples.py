import redis
import json
from kafka import KafkaProducer, KafkaConsumer
import requests

r = redis.Redis(host='localhost', port=6379)
producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

CELEBRITY_THRESHOLD = 100_000
MAX_TIMELINE_SIZE = 800


def post_tweet(author_id: int, tweet_id: int):
    follower_count = int(r.get(f"user:followers:count:{author_id}") or 0)

    if follower_count < CELEBRITY_THRESHOLD:
        followers = get_followers(author_id)
        for follower_id in followers:
            r.lpush(f"timeline:{follower_id}", tweet_id)
            r.ltrim(f"timeline:{follower_id}", 0, MAX_TIMELINE_SIZE - 1)

    event = {'tweet_id': tweet_id, 'author_id': author_id,
             'type': 'TWEET_CREATED'}
    producer.send('tweet-events', value=event)
    producer.flush()


def get_home_timeline(user_id: int) -> list:
    tweets = r.lrange(f"timeline:{user_id}", 0, 99)
    tweets = [int(t) for t in tweets]

    celebrity_follows = get_celebrity_follows(user_id)
    celebrity_tweets = []
    for celebrity_id in celebrity_follows:
        recent = get_recent_tweet_ids(celebrity_id, limit=10)
        celebrity_tweets.extend(recent)

    all_ids = list(set(tweets + celebrity_tweets))
    return sorted(all_ids, reverse=True)[:100]


# В.2 Кешування твіту та лічильника лайків у Redis

CACHE_TTL = 3600


def get_tweet(tweet_id: int) -> dict:
    cache_key = f"tweet:{tweet_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    tweet = db.query("SELECT * FROM tweets WHERE id = %s", tweet_id)
    r.setex(cache_key, CACHE_TTL, json.dumps(tweet))
    return tweet


def increment_like(tweet_id: int) -> int:
    counter_key = f"tweet:likes:{tweet_id}"
    new_count = r.incr(counter_key)
    event = {'tweet_id': tweet_id, 'likes': new_count,
             'type': 'LIKE_UPDATED'}
    producer.send('like-events', json.dumps(event).encode())
    return new_count


# В.3 Публікація та споживання події через Apache Kafka

class TweetEventProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def publish(self, tweet_id: int, author_id: int):
        event = {
            'event_type': 'TWEET_CREATED',
            'tweet_id': tweet_id,
            'author_id': author_id
        }
        self.producer.send('tweet-events', value=event)
        self.producer.flush()


class TimelineConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'tweet-events',
            bootstrap_servers=['kafka:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

    def run(self):
        for message in self.consumer:
            event = message.value
            if event['event_type'] == 'TWEET_CREATED':
                fanout(event['author_id'], event['tweet_id'])


# В.4 Звернення до Twitter API v2

BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"
BASE_URL = "https://api.twitter.com/2"


def get_user_tweets(user_id: str, max_results: int = 10) -> dict:
    url = f"{BASE_URL}/users/{user_id}/tweets"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
        "expansions": "author_id"
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def search_recent(query: str) -> dict:
    url = f"{BASE_URL}/tweets/search/recent"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": 10,
        "tweet.fields": "created_at,public_metrics,author_id"
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
