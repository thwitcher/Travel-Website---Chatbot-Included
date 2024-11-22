from openai import OpenAI
from functions import *
from flask import Flask, jsonify, request
import pymongo

token = "token"
endpoint = "https://models.inference.ai.azure.com"

# Pick one of the Azure OpenAI models from the GitHub Models service
model_name = "gpt-4o-mini"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)
system_message = """
You are a travel assistant. Your task is to help users plan their trips by extracting the following information: 
Trip destination (location)
Number of people traveling
Interests during the trip (e.g., sightseeing, relaxation, adventure)
Budget for the trip

Guide the user naturally through a conversation to collect these details. Make sure to confirm each piece of information.
"""
user_state = {
    "number_of_people": None,
    "interests": None,
    "location": None,
    "date" : None,
    "budget": None
    }
info_extracted = {}

#MongoDB data base 
myclient = pymongo.MongoClient("mongodb://localhost:27017/")

usersdb = myclient["usersdatabase"]
usercol = usersdb["userRef"]

app = Flask(__name__)
@app.route('/chatbot_conversation', methods=['POST']) 
def chatbot_conversation(): 
    messages = [{"role": "system", "content": system_message}]  # Initialize with system message
    data = request.json  # Get data from the request
    
    # Extract user message and previous messages from the request
    user_message = data.get('message')
    message_history = data.get('messages', [])
    info_extracted = extract_info_from_message(user_message)
    if info_extracted.get('number_of_people'):
        user_state['number_of_people'] = info_extracted['number_of_people']
    if info_extracted.get('interests'):
        user_state['interests'] = info_extracted['interests']
    if info_extracted.get('budget'):
        user_state['budget'] = info_extracted['budget']
    if info_extracted.get('location'):
        user_state['location'] = info_extracted['location']
    if info_extracted.get('date'):
        user_state['date'] = info_extracted['date']
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Extend messages with the previous conversation history
    messages.extend([{"role": "user" if msg['sender'] == "user" else "assistant", "content": msg['text']} for msg in message_history])
    
    # Append the new user message to the conversation
    messages.append({"role": "user", "content": user_message})
    
    print("messages after user append are ==========", messages)
    
    # Get the bot's response based on the entire conversation history
    bot_response = ask_question(messages)

    # Append the bot's response to the conversation history
    messages.append({"role": "assistant", "content": bot_response})
    print(user_state)
    #insert only if all the data is availebale in the user collection
    if all(user_state[key] for key in ["number_of_people", "interests", "location", "budget", "date"]):
        inserted_id = usercol.insert_one(user_state).inserted_id
        user_state['_id'] = str(inserted_id)  # Convert ObjectId to string

    # Return the bot's response and the updated conversation
    return jsonify({
        "response": bot_response,
        "messages": messages,
        "user_state": user_state
    })
if __name__ == "__main__" :
    app.run(debug=True, port=5000)

