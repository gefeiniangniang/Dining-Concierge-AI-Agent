import json
import boto3
response = {
        "sessionAttributes":{},
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                },
            }
    }
    

    
def sendMessage(sqs, message):
    # send collected data to Q1
    response = sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/574875490087/a',
        MessageBody=json.dumps(message),
        DelaySeconds=2
    )
    
    print(response)
    print('!!!!!!!!!')
    for i in message:
        print(i)
    return

def extractInfomation(lexOutput):
    slots = lexOutput["currentIntent"]["slots"]
    return slots

def validatePhoneNumber(event):
    if len(event["currentIntent"]["slots"]["phone"]) != 10:
        return False
    return True
    
def lambda_handler(event, context):
    
    slots = event["currentIntent"]["slots"]
    # data ="We have received the following information :\n city: {0}\nfood type: {1}\nnumber of people: {2}\ntime: {3}{4}\nphone number: {5}".format(
    #     slots['city'], slots['cuisine'], slots['peoplenumber'], slots['date'], slots['time'], slots['phone'])
    data = "You're all set. Expect my suggestions shortly! Have a good day."
    response["dialogAction"]["message"]["content"] = data
    if validatePhoneNumber(event):
        print('valid')
        sqs = boto3.client('sqs')
        sendMessage(sqs, extractInfomation(event))
    else:
        return {
            "sessionAttributes":{},
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content" : "Invalid phone number, it should have 10 digists. Please try again. "
                },
                "intentName": "DiningSuggestionsIntent",
                "slots": event["currentIntent"]["slots"],
                "slotToElicit" : "phone",
            }
        }
    
    return response
