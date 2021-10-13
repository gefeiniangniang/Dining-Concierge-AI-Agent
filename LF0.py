import json
import boto3
import uuid
import requests
from requests_aws4auth import AWS4Auth
from pprint import pprint
from botocore.exceptions import ClientError
import random

def generateLexInput(event):
    return event["messages"][0]["unstructured"]["text"]

def generateS3Output(response, userId):
    text = response['message']
    return {
        'statusCode': 200,
        'messages': [
            {
                "type": "unstructured",
                "unstructured": {
                    "text": text
                }
            }
        ]
    }

def searchHistory(user_id):
    client = boto3.resource('dynamodb')
    table = client.Table('search_history')
    key = table.get_item(Key={'user_id': user_id})
    if key is None:
        return []
    return key
    
def removeHistory(user_id):
    client = boto3.resource('dynamodb')
    table = client.Table('search_history')
    key = table.delete_item(Key={'user_id': user_id})
    return key

def elasticSearch(cuisine):
    region = 'us-east-1' # For example, us-west-1
    service = 'es'
    awsauth = AWS4Auth('key', 'key', region, service)
    host = 'https://search-restaurants-zkflthtpnmeizyixegrluaylkq.us-east-1.es.amazonaws.com' 
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    headers = { "Content-Type": "application/json" }
    query = {
        "size": 100,
        "query": {
            "multi_match": {
                "query": cuisine,
            }
        }
    }
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    data = json.loads(r.text)['hits']['hits']
    rand = random.randint(0, len(data)-4)
    return data[rand]['_source']['RestaurantID'], data[rand+1]['_source']['RestaurantID'], data[rand+2]['_source']['RestaurantID'] 
    
    
def searchDynamoDB(business_id, cuisine_type):
    client = boto3.resource('dynamodb')
    table = client.Table('yelp-restaurants')
    key = table.get_item(Key={'business_id': business_id, 'cuisine_type':cuisine_type.capitalize()})
    print(cuisine_type, business_id)
    return key['Item']
    
    
def pick_restaurant(cuisine):
    id1, id2, id3 = elasticSearch(cuisine)
    restaurant_info1 = searchDynamoDB(id1, cuisine+' cuisine')
    restaurant_info2 = searchDynamoDB(id2, cuisine+' cuisine')
    restaurant_info3 = searchDynamoDB(id3, cuisine+' cuisine')
    return restaurant_info1, restaurant_info2, restaurant_info3

def generateMessage(info1, info2, info3):
    message = "Welcome back! Here are my restaurant suggestions based on your last search: 1. {0}, located at {1}, 2. {2}, located at {3}, 3. {4}, located at {5}.".format(
        info1['name'], info1['address'], info2['name'], info2['address'], info3['name'], info3['address'])
    return message

def ads():
    history = searchHistory("1")['Item']
    cuisine = history['cuisine_type']
    restaurant1, restaurant2, restaurant3 = pick_restaurant(cuisine)
    message = generateMessage(restaurant1, restaurant2, restaurant3)
    return message

userId = str(uuid.uuid1())

def lambda_handler(event, context):
    try:
        # give recommendations based on search history
        recommendation_message = ads() 
        removeHistory("1")
        return {
            'statusCode': 200,
            'messages': [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "text": recommendation_message
                    }
                }
            ]
        }
        
    except:
        
        lex = boto3.client('lex-runtime')
        input = generateLexInput(event)
        print(input)
        
        response = lex.post_text(
        botName='diningChatbot',
        botAlias='DiningOne',
        userId=str(userId),
        sessionAttributes={
            #'string': 'string'
        },
        inputText=input
        )
        
        print(response)
            
        return generateS3Output(response, userId)
