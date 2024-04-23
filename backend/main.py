from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
import uvicorn
from dotenv import load_dotenv
import os
import chatbot
from fetch_from_mongodb import query_and_fetch

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return "Welcome to Jobrela Chatbot"

@app.get('/project')
def project(query):
    
    return chatbot.ask(query=query, field="PROJECT")

@app.get('/professional')
def professional(query):
    result_emails = query_and_fetch(query)

    if not result_emails:
        formatted_string = f'"query": "{query}", "email": []'
        print(formatted_string)
        return chatbot.ask(query=formatted_string, field="PROFESSIONAL")
    

    formatted_string = f'"query": "{query}", "email": {result_emails}'
    print(formatted_string)
    return chatbot.ask(query=formatted_string
                       , field="PROFESSIONAL")

def main():
    uvicorn.run('main:app', port=5000, host="127.0.0.1")


if __name__ == "__main__":
    main()
