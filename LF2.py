import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
from pprint import pprint
from botocore.exceptions import ClientError
import random




def sendMessage(message, phone_num):
    client = boto3.client('sns')
    response = client.publish(
        PhoneNumber = phone_num,
        Message = message
    )
    
    return response
    
    

def elasticSearch(cuisine):
    region = 'us-east-1' # For example, us-west-1
    service = 'es'
    awsauth = AWS4Auth('AKIAYLWJ724TVF32QFVR', 'uEyfTMhsE9yNsMcXmDU6rgDztEEq4Mq1ig0qWNCe', region, service)
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
    
    
def pick_restaurant(city, cuisine):
    id1, id2, id3 = elasticSearch(cuisine)
    restaurant_info1 = searchDynamoDB(id1, cuisine+' cuisine')
    restaurant_info2 = searchDynamoDB(id2, cuisine+' cuisine')
    restaurant_info3 = searchDynamoDB(id3, cuisine+' cuisine')
    return restaurant_info1, restaurant_info2, restaurant_info3
    
def generateMessage(info1, info2, info3, people, date, time, cuisine):
        
    message = "Hello! Here are my {0} restaurant suggestions for {1} people, for {2} at {3}: 1. {4}, located at {5}, 2. {6}, located at {7}, 3. {8}, located at {9}. Enjoy your meal!".format(
        cuisine, people, date, time, info1['name'], info1['address'], info2['name'], info2['address'], info3['name'], info3['address'])
        
        
    # message = "The restaurant we recommended for you is {0}\n the location is {1} {2}.\n It has a {3} rating over {4} reviews".format(
    #     restaurant_info['name'], restaurant_info['address'], restaurant_info['zip'], restaurant_info['rating'], restaurant_info['num_review'])
    return message

def searchHistory(user_id):
    client = boto3.resource('dynamodb')
    table = client.Table('search_history')
    key = table.get_item(Key={'user_id': user_id})
    return key['Item']

def updateDynamoDB(user_id,cuisine_type):
    client = boto3.resource('dynamodb')
    table = client.Table('search_history')
    response = table.put_item(
        Item={
        'user_id': user_id,
        'cuisine_type': cuisine_type,
        }
    )
    return response
    
def lambda_handler(event, context):

    
    ###################################
    #take out input
    b = event['Records'][0]['body']
    print(b)
    info = json.loads(b)
    print(info)
    city = info['city']
    cuisine = info['cuisine']
    date = info['date']
    time = info['time']
    peoplenumber = info['peoplenumber']
    phone = "+1"+info['phone']
    print('not string')
    restaurant1, restaurant2, restaurant3 = pick_restaurant(city, cuisine)
    message = generateMessage(restaurant1, restaurant2, restaurant3, peoplenumber, date, time, cuisine.capitalize())
    res = sendMessage(message, phone)
    updateDynamoDB('1',cuisine)
    
    return res

