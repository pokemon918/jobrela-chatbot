import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

load_dotenv()

#LLM configuration
model = 'gpt-4-0125-preview'
temperature = 0.2

#Chatable llm
llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), model_name=model, temperature=temperature)

#Retreival chain
memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history")

template = """
    You are an AI Assistant who is responsible for calculating the hexadecimal of user inputed string that stands for PMS.
    Given the context, you have to answer correctly.
    ###
    {context}
    ###
    Question: {question}
    Helpful Answer:"""

chain = ConversationChain(llm=llm, memory=memory)

prompt_template = PromptTemplate(input_variables=["context", "question"], template=template)
chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=prompt_template)

while True:
    user_input = input(">>>")
    if user_input != "quit":
        response = chain.invoke({'question': user_input})['answer']
        print(response)
    else:
        break