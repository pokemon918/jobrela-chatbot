import os
from dotenv import load_dotenv

import pinecone
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain_community.vectorstores import Pinecone

load_dotenv()

pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv("PINECONE_ENVIRONMENT"))
embeddings = OpenAIEmbeddings()

#LLM configuration
model = 'gpt-4-0125-preview'
temperature = 0.2

#Chatable llm
llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), model_name=model, temperature=temperature)

#Retreival chain
vectordb = Pinecone.from_documents([], embeddings, index_name=os.getenv("PINECONE_INDEX_NAME"))
retriever = vectordb.as_retriever()
memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history")

template = """
    You are an AI Assistant who is responsible for recommending suitable projects according to the user question.
    Given the context, you have to answer correctly.
    ###
    {context}
    ###
    Question: {question}
    Helpful Answer:"""

chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, memory=memory, get_chat_history=lambda h: h)

prompt_template = PromptTemplate(input_variables=["context", "question"], template=template)
chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=prompt_template)

while True:
    user_input = input(">>>")
    if user_input != "quit":
        response = chain.invoke({'question': user_input})['answer']
        print(response)
    else:
        break