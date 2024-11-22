from openai import OpenAI
import re
import ast
token = "token"
endpoint = "https://models.inference.ai.azure.com"

# Pick one of the Azure OpenAI models from the GitHub Models service
model_name = "gpt-4o-mini"
client = OpenAI(
    base_url=endpoint,
    api_key=token,
)
# Track user state
system_message = """
You are a travel assistant. Your task is to help users plan their trips by extracting the following information: 
1. Trip destination (location)
2. Number of people traveling
3. Interests during the trip (e.g., sightseeing, relaxation, adventure)
4. Budget for the trip

Guide the user naturally through a conversation to collect these details. Make sure to confirm each piece of information.
"""
user_state = {
    "number_of_people": None,
    "interests": None,
    "location": None,
    "date" : None,
    "budget": None
    }
def ask_question(messages):
    response = client.chat.completions.create(
        model=model_name,  # Replace with the correct model you're using
        messages=messages,
        max_tokens=150,
        temperature=0.7,  # Adjust temperature for more creative/varied responses
    )
    return response.choices[0].message.content.strip()
# Chatbot conversation loop
def chatbot_conversation():
    messages = [{"role": "system", "content": system_message}]
    
    print("Bot: Hi! I'm your travel assistant. Let's plan your trip.")
    while True:
        # User input
        user_input = input("You: ")
        messages.append({"role": "user", "content": user_input})
        
        # Get the bot's response
        bot_response = ask_question(messages)
        # Extract relevant information (number of people, interests, budget, etc.)
        print(f"Bot: {bot_response}")
        
        # Append the bot's response to the conversation history
        messages.append({"role": "assistant", "content": bot_response})

        # Break the conversation loop if bot detects it's finished gathering data
        if any(keyword in bot_response.lower() for keyword in ["thank you", "that's all", "done"]):
            break
        return {bot_response}
    
def parse_extracted_info(extracted_info):
    # Using simple regex to extract structured information
    print(extracted_info)
    people_match = re.search(r"Number of people: (\d+)", extracted_info)
    print(people_match)
    interests_match = re.search(r'- *Interests*: (.+)', extracted_info)
    budget_match = re.search(r'- *Budget*: (.+)', extracted_info)
    location_match = re.search(r'- *Location*: (.+)', extracted_info)
    
    if people_match:
        user_state['people'] = people_match.group(1)
    if interests_match:
        user_state['interests'] = interests_match.group(1).split(", ")
    if budget_match:
        user_state['budget'] = budget_match.group(1)
    if location_match:
        user_state['location'] = location_match.group(1)
    
    return user_state

# Function to interact with ChatGPT-4
def extract_info_from_message(user_message):
    response = client.chat.completions.create(
      model=model_name,
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Extract the number of people, interests, location, date, and budget from this message in a dictionairy format '{user_message}'"}
      ]
    )
    # Extract the response content
    extracted_info = response.choices[0].message.content
    # Step 1: Find the positions of the first '{' and the last '}'
    start_index = extracted_info.find('{')
    end_index = extracted_info.rfind('}')

    # Step 2: Extract the substring that contains the dictionary
    if start_index != -1 and end_index != -1 and start_index < end_index:
        dict_string = extracted_info[start_index:end_index + 1]  # Extract from '{' to '}'
    else:
        dict_string = ""

    # Step 3: Convert the cleaned string into a dictionary
    try:
        extracted_info = ast.literal_eval(dict_string)
        print(extracted_info)
    except SyntaxError as e:
        print(f"Error parsing the dictionary: {e}")
    return extracted_info

# Function to parse the string into a dictionary
  

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message['role'] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


def streaming_message(messages):
    # Initialize an empty string to store the conversation
    full_conversation = ""
    
    # Loop through the messages and build the conversation string
    for message in messages:
        role = message['role']
        content = message['content']
        
        # Differentiate roles (system, user, assistant)
        if role == 'system':
            full_conversation += f"System: {content}\n"
        elif role == 'user':
            full_conversation += f"User: {content}\n"
        elif role == 'assistant':
            full_conversation += f"Assistant: {content}\n"
    
    # Simulate streaming by breaking the full conversation into chunks
    for i in range(0, len(full_conversation), 100):  # Assuming chunk size is 100 characters
        # Return or yield conversation in chunks
        yield full_conversation[i:i+100]  # Modify this for actual streaming behavior if needed


def update_user_state(info_extracted, user_message):
    response = client.chat.completions.create(
      model=model_name,
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Extract the number of people, interests, location, date, and budget from this message in a dictionairy format if the data need to be over writen associate overwrite, else if data need to be appended associate append  '{user_message}'"}
      ]
    )
    for key, new_value in info_extracted.items():
        if new_value is not None:
            if response.get(key) == "overwrite":
                # Overwrite the existing value
                user_state[key] = new_value
            elif response.get(key) == "append":
                # Append to the existing list or set
                if not isinstance(user_state[key], list):
                    # Ensure the field is a list if we want to append
                    user_state[key] = [user_state[key]] if user_state[key] else []
                # Add new values to the list, avoiding duplicates
                if isinstance(new_value, list):
                    user_state[key].extend(new_value)
                else:
                    user_state[key].append(new_value)
                # Optional: Remove duplicates if needed
                user_state[key] = list(set(user_state[key]))