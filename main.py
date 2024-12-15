import os
import json
from dotenv import load_dotenv
import requests
from models import User, Session
from faker import Faker

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# Validate API Key
if not API_KEY:
    raise ValueError("API_KEY not found. Please check your .env file.")

# Initialize Faker and SQLAlchemy Session
session = Session()
fake = Faker()

# Seed the database
for _ in range(5):
    user = User(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.unique.email(),
        username=fake.unique.user_name()
    )
    session.add(user)

session.commit()
print("Database seeded successfully!")

# Define calculator functions
def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b): return a / b if b != 0 else "Error: Division by zero"

# Call Groq API for LLM function calling
def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",  # Example model name
        "messages": [{"role": "user", "content": prompt}],
        "functions": [
            {"name": "add", "parameters": {"a": "number", "b": "number"}},
            {"name": "subtract", "parameters": {"a": "number", "b": "number"}},
            {"name": "multiply", "parameters": {"a": "number", "b": "number"}},
            {"name": "divide", "parameters": {"a": "number", "b": "number"}}
        ]
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise error for bad HTTP status codes
        data = response.json()

        # Extract function and arguments
        function_calls = data['choices'][0]['message'].get('tool_calls', None)
        if function_calls:
            try:
                function_name = function_calls[0]['function']['name']
                arguments = json.loads(function_calls[0]['function']['arguments'])
            except (KeyError, json.JSONDecodeError):
                return "Error: Invalid arguments or function name in API response."

            # Execute the corresponding local function
            if function_name == "add":
                return f"The sum of {arguments['a']} and {arguments['b']} is {add(arguments['a'], arguments['b'])}."
            elif function_name == "subtract":
                return f"The difference between {arguments['a']} and {arguments['b']} is {subtract(arguments['a'], arguments['b'])}."
            elif function_name == "multiply":
                return f"The product of {arguments['a']} and {arguments['b']} is {multiply(arguments['a'], arguments['b'])}."
            elif function_name == "divide":
                return f"The result of dividing {arguments['a']} by {arguments['b']} is {divide(arguments['a'], arguments['b'])}."
            else:
                return f"Error: Function {function_name} not implemented."

        return "Error: No valid function call in response."

    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq API: {e}")
        return None

# Main loop for LLM-based calculator
def main():
    print("Database seeded successfully! Now ready for calculations.")
    while True:
        prompt = input("Enter a calculation (e.g., Add 5 and 3) or 'exit' to quit: ")
        if prompt.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        result = call_llm(prompt)
        if result is not None:
            print(f"Result: {result}")
        else:
            print("Error: Could not process your request.")

if __name__ == "__main__":
    main()
