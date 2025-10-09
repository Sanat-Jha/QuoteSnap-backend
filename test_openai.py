#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Test OpenAI connection
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        print("OpenAI client created successfully")
        
        print("Making API call...")
        # Test a simple API call with timeout
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            temperature=0,
            timeout=10  # Shorter timeout for testing
        )
        
        print("API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Try with a different timeout or different approach
        try:
            print("Trying with shorter timeout...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                temperature=0,
                timeout=5
            )
            print("Short timeout call successful!")
            print(f"Response: {response.choices[0].message.content}")
        except Exception as e2:
            print(f"Second attempt also failed: {str(e2)}")
            print("This indicates a network or API key issue")
else:
    print("No OpenAI API key found in environment")