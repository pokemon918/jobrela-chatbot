import uuid
import pinecone
import os
import json
import jsonref
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = 100
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
OPENAI_KEY = os.getenv('OPENAI_KEY')
PINECONE_INDEX = os.getenv('PINECONE_INDEX')

client = OpenAI(api_key=OPENAI_KEY)

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
# pinecone.init(api_key=PINECONE_API_KEY)

def get_embedding(text):
    return client.embeddings.create(input=text, model=EMBEDDING_MODEL).data[0].embedding

def get_embeddings(sentences):
    embeddings = []
    for sentence in sentences:
        embeddings.append(get_embedding(sentence))
    return embeddings

def upsert_pinecone(data):
    index = pinecone.Index(PINECONE_INDEX)
    for i in range(0, len(data), BATCH_SIZE):
        print('batch', i)
        item_ids, embeddings, metadata = [], [], []
        i_end = min(i + BATCH_SIZE, len(data))
        for record in data[i:i_end]:
            embeddings.append(record["embedding"])
            item_ids.append(str(uuid.uuid4()))
            metadata.append(record['metadata'])
        records = zip(item_ids, embeddings, metadata)
        upsert_results = index.upsert(vectors=records)
    return upsert_results

def build_knowledge_base(fpath):
    with open(fpath, 'r', encoding='utf-8') as file:
        data = jsonref.loads(file.read())
    new_data = []
    for d in data:
        tmp = f"""categories: {json.dumps(d['categories'])}\nshort summary: {d['shortSummary']}\nwork experience: {d['workExperience']}"""
        new_data.append(
            {
                'metadata': {
                    "_id": d["_id"]["$oid"],
                    "name": d["name"],
                    "categories": json.dumps(d["categories"])
                },
                'embedding': get_embedding(tmp)
            }
        )
    print('start_upserting!')
    upsert_pinecone(new_data)

def json_to_text(data):
    text = ''
    for key, value in data.items():
        text += f"{key}: {str(value)}\n"
    return text

def documents_to_prompt(data):
    prompt = '<documents>\n'
    for document in data:
        prompt += "<document>\n"
        for key, value in document.items():
            prompt += f"<{str(key)}>\n{str(value)}\n</{str(key)}>\n"
        prompt += "</document>\n"
    prompt += "</documents>"
    return prompt

def history_to_prompt(history):
    prompt = ''
    for message in history:
        for key, value in message.items():
            prompt += key + '\n' + value
    return prompt
        
def etree_to_dict(t):
    d = {t.tag: {}}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(("@" + k, v) for k, v in t.attrib.items())
    if t.text and t.text.strip():
        if children or t.attrib:
            d[t.tag]["#text"] = t.text
        else:
            d[t.tag] = t.text
    return d

def log(topic, content):
    print(f'\n\n---------------- {topic} --------------------')
    print(content)
    print('\n\n------------------------------------\n\n')
    

if __name__ == '__main__':
    build_knowledge_base("./profession.json")
    # with open('./test.json', 'r', encoding='utf-8') as file:
    #     data = jsonref.loads(file.read())
    # print(data[0]['fullDescription'])