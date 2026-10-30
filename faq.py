import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
faqs_path = Path(__file__).parent / 'resources/faq_data.csv'
chroma_client = chromadb.Client()
collection_name_faq = 'faqs'
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='sentence-transformers/all-MiniLM-L6-v2')
MODEL = os.environ['GROQ_MODEL']
groq_client = Groq()

def ingest_faq_data(path):
    if collection_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print(f'Ingesting the data into ChromaDB....')
        collection = chroma_client.get_or_create_collection(
            name=collection_name_faq,
            embedding_function=ef
        )

        df = pd.read_csv(path)
        docs = df['question'].to_list()
        metadata = [{'answer': ans} for ans in df['answer'].to_list()]
        ids = [f'id_{i}' for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=metadata,
            ids=ids
        )
        print(f'FAQ Data successfully ingested into Chroma collection: {collection_name_faq}')
    else:
        print(f'Collection {collection_name_faq} already exists!')


def get_relevant_qa(query):
    collection = chroma_client.get_collection(name=collection_name_faq)
    result = collection.query(
        query_texts=[query],
        n_results=2
    )
    return result

def faq_chain(query):
    result = get_relevant_qa(query)
    context = ''.join([r.get('answer') for r in result['metadatas'][0]])
    answer = generate_answer(query, context)
    return answer

def generate_answer(query, context):
    prompt = f'''Given the question and context below, generate the answer based on the context only. If you dont 
    find the answer inside the context then say "I dont know". Do not make things up. Also dont say 
    'Based on context provided'.
    
    Question: {query}
    
    Context: {context}
    '''
    chat_completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user",
             "content": prompt}
        ]
    )

    return chat_completion.choices[0].message.content


if __name__ == '__main__':
    ingest_faq_data(faqs_path)
    query = "Do you take cash as a payment option?"
    # result = get_relevant_qa(query)
    # print(result)
    answer = faq_chain(query)
    print(answer)