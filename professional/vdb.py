import os

import pinecone
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone

from utils import *

load_dotenv()

pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv("PINECONE_ENVIRONMENT"))

# List of keys for which to extract values
key_list = [
    "name", "email", "phone", "active", "categories", "skillsets", "localities", "specialities", "availabilityOption", "languageIds", "shortSummary", "workExperience",  "currency", "accountManager", "level", "countryOrigin", "countryOriginAlt", "employmentProjectTypeWage", "availability", "employmentProjectTypeSuperGrossWageCZK", "freelanceProjectTypeWage", "freelanceProjectTypeWagePro", "freelanceProjectTypeSuperGrossWageCZK", "superGrossWageCZK"
]

embeddings = OpenAIEmbeddings()
txt_splitter = RecursiveCharacterTextSplitter(
    chunk_size=160000,
    chunk_overlap=200
)

if __name__ == '__main__':

    with open('professional.json', 'r', encoding='utf-8') as reader:
        projects = json.load(reader)

    for project in projects[6655:]:

        # Extracting the values using the `find_keys` function
        extracted_values = {key: None for key in key_list}  # initialize with None
        for key, value in find_keys(project, key_list):
            if key in extracted_values:
                extracted_values[key] = value

        # Output extracted values
        # for key, value in extracted_values.items():
        #     print(f'{key}: {value}')

        # Convert created `$date` to normal format
        # if 'created' in extracted_values and extracted_values['created']:
        #     extracted_values['created'] = extracted_values['created']['$date']

        # print("\nValues after converting 'created':")
        # print(extracted_values['created'])

        # Extracting the values using the `find_keys` function
        # Same extraction process as before

        formatted_value = ""
        for key, value in extracted_values.items():
            formatted_value += f'{key} is {format_value(value)}.\n'

        documents = txt_splitter.create_documents([formatted_value])
        Pinecone.from_documents(documents, embeddings, index_name=os.getenv("PINECONE_INDEX_NAME"))

        # # Write extracted values to a text file
        # with open('extracted_data.txt', 'w', encoding='utf-8') as file:
        #     for key, value in extracted_values.items():
        #         formatted_value = format_value(value)
        
        #         file.write(f'{key} is {formatted_value}.\n')
        
        # print("Data has been written to extracted_data.txt")
