import os
import json
from dotenv import load_dotenv
import requests
from models import User, History, Session
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
        "model": "llama3-8b-8192",
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
        response.raise_for_status()
        data = response.json()

        # Extract function and arguments
        function_calls = data['choices'][0]['message'].get('tool_calls', None)
        if function_calls:
            function_name = function_calls[0]['function']['name']
            arguments = json.loads(function_calls[0]['function']['arguments'])

            # Execute the corresponding local function
            a = float(arguments['a'])
            b = float(arguments['b'])
            if function_name == "add":
                return add(a, b)
            elif function_name == "subtract":
                return subtract(a, b)
            elif function_name == "multiply":
                return multiply(a, b)
            elif function_name == "divide":
                return divide(a, b)
        return "Error: No valid function call in response."
    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq API: {e}")
        return None

# Save input and output to the database
def save_to_history(user_input, result):
    new_entry = History(user_input=user_input, result=result)
    session = Session()
    session.add(new_entry)
    session.commit()
    session.close()

# Fetch and display history from the database
def fetch_history():
    session = Session()
    history = session.query(History).all()
    if not history:
        print("No history found.")
    else:
        print("\n--- Calculation History ---")
        for entry in history:
            print(f"Input: {entry.user_input}\nOutput: {entry.result}\n")
    session.close()

# Main loop for LLM-based calculator
def main():
    print("Database seeded successfully! Now ready for calculations.")
    print("Type 'history' to view past inputs/outputs, or 'exit' to quit.")

    while True:
        prompt = input("Enter a calculation (e.g., Add 5 and 3) or 'history': ").strip()

        # Handle 'exit' or 'quit' command
        if prompt.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Handle 'history' command
        elif prompt.lower() == "history":
            fetch_history()

        # Prevent SQL-like inputs or invalid commands
        elif any(keyword in prompt.lower() for keyword in ["select", "insert", "delete", "update"]):
            print("Error: Invalid input. Please enter a valid calculation or type 'history' to see past results.")
        
        # Send valid inputs to LLM API for processing
        else:
            result = call_llm(prompt)
            if result is not None:
                print(f"Result: {result}")
                save_to_history(prompt, result)  # Save input and result to history
            else:
                print("Error: Could not process your request.")

if __name__ == "__main__":
    main()
