import os, sys
from flask import Flask, request
from utils import get_response_from_indianrail
import json
import requests
import traceback


app = Flask(__name__)

PAGE_ACCESS_TOKEN = ""

@app.route('/', methods=['GET'])
def verify():
	# Webhook verification
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "hello":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200   
    return "Hello world", 200

def get_messaging_text_sender_id_recipient_id_from_messenger(data):
	try:
		if data['object'] == 'page':
			for entry in data['entry']:
				for messaging_event in entry['messaging']:
					# IDs
					sender_id = messaging_event['sender']['id']
					recipient_id = messaging_event['recipient']['id']

					if messaging_event.get('message'):
						# Extracting text message
						if 'text' in messaging_event['message']:
							messaging_text = messaging_event['message']['text']
						else:
							messaging_text = 'no_text'	
						return messaging_text,sender_id,recipient_id									
	except Exception as ex:
		print ("get_messaging_text_sender_id_recipient_id_from_messenger exception "+str(ex))
		print("There is an exception from function " + str(traceback.extract_stack(None, 2)[0][2]))

def check_for_greeting_messages(messaging_text):
	try:
		greetlist=['hi','hii','hiii','hey','thanks','thank','thank you','thank u','hello','helloo']
		greetlist1=['thanks','thank','thank you','thank u']
		is_greetresp=False
		if(messaging_text.lower() in greetlist):
								is_greetresp=True
								if(messaging_text.lower() in greetlist1):
									greetresp='I am Happy you liked it! Thank you for giving me an oppurtunity to serve you!!"'
								else:	
									greetresp='Hi! My name is RailBot. I can tell you details about your railway ticket status using PNR.\nType your 10 digit PNR: 1234567890"'
								return greetresp,is_greetresp
		else:
			is_greetresp=False
			return "no_text",is_greetresp
									
	except Exception as ex:
			print ("check_for_greeting_messages exception "+str(ex))
			print("There is an exception from function " + str(traceback.extract_stack(None, 2)[0][2]))


def prepare_response_content_generic(sender_id,text):
	try:
		response_content = {
							"recipient":{
							"id": sender_id
										},
											"message": {
											"text": text	            
											}
							}
		return response_content
	except Exception as ex:
		print ("prepare_response_content_generic exception "+str(ex))
		print("There is an exception from function " + str(traceback.extract_stack(None, 2)[0][2]))						

def send_response_to_messenger(response_content):
	try:
			headers = {"Content-Type": "application/json"}
			url = "https://graph.facebook.com/v2.6/me/messages?access_token=%s" % PAGE_ACCESS_TOKEN
			resp_str = requests.post(url, data=json.dumps(response_content), headers=headers)
			print(resp_str)
			print(str(resp_str.status_code))
			print(str(resp_str.headers))
			print(str(resp_str.text))
			return resp_str
	except Exception as ex:
			print ("send_response_to_messenger exception "+str(ex))
			print("There is an exception from function " + str(traceback.extract_stack(None, 2)[0][2]))			

@app.route('/', methods=['POST'])
def webhook():
	data = request.get_json()
	#log(body)
	try:
		messaging_text,sender_id,recipient_id=get_messaging_text_sender_id_recipient_id_from_messenger(data)
		greetresp,is_greetresp=check_for_greeting_messages(messaging_text)

		if is_greetresp is True:
			response_content=prepare_response_content_generic(sender_id,greetresp)
			resp_str=send_response_to_messenger(response_content)
		elif(len(messaging_text))!=10:
			response_content=prepare_response_content_generic(sender_id,'Sorry!! Wrong PNR ,Please check PNR and Try Again.')
			send_response_to_messenger(response_content)
		else:
			final_str,booking_status=get_response_from_indianrail(messaging_text)
			if final_str!='none':
				response_content=prepare_response_content_generic(sender_id,final_str)
				send_response_to_messenger(response_content)
				for i in range(len(booking_status)):
					response_content=prepare_response_content_generic(sender_id,'Passenger '+str(i+1)+':'+booking_status[i])
					send_response_to_messenger(response_content)
			else:
				response_content=prepare_response_content_generic(sender_id,"SORRY!! WRONG PNR / FLUSHED PNR")
				send_response_to_messenger(response_content)
						
	except Exception as ex:
    		print ("main class exp "+str(ex))	

	return "ok", 200

def log(message):
	print(message)
	sys.stdout.flush()

if __name__ == "__main__":
	app.run(debug=True)