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

def getPrompt(field):
    context = "{context}"
    question = "{question}"

    template = f"""
            You are an AI Assistant for Jobrela Company, dedicated to assisting users in finding the right {field}s for their projects. You must respond to queries in a way that respects user privacy and adheres strictly to Jobrela's rules.

            # Instructions:
            # - For queries about hiring developers:
            #    - Provide me 2-3 best matches developers who has email in the query, without providing any personal contact information like Candidate's Phone Number, or Email Address, If you can't find the developers in the email do not provide result.
            #    - If salary information is provided, prioritize candidates by the highest salary request under the provided.
            #    - If salary information is not provided, prioritize by total experience and level.
            #    - Provide professional qualifications and experience without revealing personal or contact information.
            #    - Do NOT generate anything not relevant or proper use of this assistant.
            #    - The answer should not include any process of the chatbot process, just provide answer of the query.
            # - For all other queries:
            #    - Provide information related to Jobrela's services, company culture, or any general inquiry response without needing to access the Pinecone database.
            # - Ensure all responses are relevant and professionally tailored to the question asked.
            
            ###
            {context}
            ###
            
            Question: {question}

            Helpful Answer:
    """

    return template

pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv("PINECONE_ENVIRONMENT"))
embeddings = OpenAIEmbeddings()

# LLM configuration
model = 'gpt-4-1106-preview'
temperature = 0.2

# Chatable llm
llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), model_name=model, temperature=temperature)

# Retrieval chain
vectordb_project = Pinecone.from_documents([], embeddings, index_name=os.getenv("PINECONE_INDEX_NAME_PROJECT"))
vectordb_prof = Pinecone.from_documents([], embeddings, index_name=os.getenv("PINECONE_INDEX_NAME_PROFESSIONAL"))

retriever_project = vectordb_project.as_retriever()
retriever_prof = vectordb_prof.as_retriever()

memory_project = ConversationBufferWindowMemory(k=3, memory_key="chat_history")
memory_prof = ConversationBufferWindowMemory(k=3, memory_key="chat_history")

chain_project = ConversationalRetrievalChain.from_llm(llm, retriever=retriever_project, memory=memory_project, get_chat_history=lambda h: h)
chain_prof = ConversationalRetrievalChain.from_llm(llm, retriever=retriever_prof, memory=memory_prof, get_chat_history=lambda h: h)

prompt_template_project = PromptTemplate(input_variables=["context", "question"], template=getPrompt("PROJECT"))
prompt_template_prof = PromptTemplate(input_variables=["context", "question"], template=getPrompt("PROFESSIONAL"))

chain_project.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=prompt_template_project)
chain_prof.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=prompt_template_prof)


def ask(query, field):
    response = chain_project.invoke({'question': query})['answer'] if field == "project" else chain_prof.invoke({'question': query})['answer']

    return response
