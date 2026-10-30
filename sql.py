import sqlite3
import pandas as pd
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

groq_client = Groq()
load_dotenv()
db_path = Path(__file__).resolve().parent / "resources" / "db_amazon.sqlite"
MODEL = os.getenv('GROQ_MODEL')

sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags. 
<schema> 
table: amazon_product_data

fields: 
product_link - string (hyperlink to product)
asin - string (Product id of the product)	
title - string (name of the product)	
brand - string (brand of the product)	
price - integer (price of the product in Indian Rupees)	
discount_percent - float (discount on the product in percent.)	
avg_rating - float (average rating of the product. Range 0-5, 5 is the highest.)	
total_ratings - integer (total number of ratings for the product)
availability - string(product stock availability.) 

</schema>
Make sure whenever you try to search for the brand name, the name can be in any case. 
So, make sure to use %LIKE% to find the brand in condition. Never use "ILIKE". 
Create a single SQL query for the question provided. 
The query should have all the fields in SELECT clause (i.e. SELECT *)
If any abstract or gibberish text is provided ask the user to provide proper question to get SQL query. 

Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags."""

comprehension_prompt = """You are an expert in understanding the context of the question and replying based on the data pertaining to the question provided. 
You will be provided with Question: and Data:. The data will be in the form of an array or a dataframe or dict. 
Reply based on only the data provided as Data for answering the question asked as Question. 
Do not write anything like 'Based on the data' or any other technical words. Just a plain simple natural language response.
The Data would always be in context to the question asked. 
For example is the question is “What is the average rating?” and data is “4.3”, 
then answer should be “The average rating for the product is 4.3”. 
So make sure the response is curated with the question and data. 
Make sure to note the column names to have some context, if needed, for your response.
There can also be cases where you are given an entire dataframe in the Data: field. 
Always remember that the data field contains the answer of the question asked. 
All you need to do is to always reply in the following format when asked about a product: 
Product title, price in Indian rupees, discount, and rating, and then product link. 
Take care that all the products are listed in list format, one line after the other. Not as a paragraph.
For example:
1. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 Link: <give product link here>
2. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 Link: <give product link here>
3. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 Link: <give product link here>

"""

def generate_sql_query(question):
    chat_completion = groq_client.chat.completions.create(
        model=MODEL,
        temperature=0,
        #max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": sql_prompt,
            },
            {
                "role": "user",
                "content": question,
            }
        ]
    )

    return chat_completion.choices[0].message.content

def run_query(query):
    if query.strip().upper().startswith('SELECT'):
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df


def data_comprehension(question, context):
    chat_completion = groq_client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": comprehension_prompt,
            },
            {
                "role": "user",
                "content": f'Question: {question} Data: {context}',
            }
        ]
    )

    return chat_completion.choices[0].message.content

def sql_chain(question):
    sql_query = generate_sql_query(question)
    pattern = "<SQL>(.*?)</SQL>"
    matches = re.findall(pattern, sql_query, re.DOTALL)
    if len(matches)==0:
        return "Sorry, LLM is not able to generate a query for your question"

    response = run_query(matches[0].strip())
    if response is None:
        return "Sorry, there was a problem in execution of query"

    context = response.to_dict(orient='records')
    answer = data_comprehension(question, context)
    return answer


if __name__ =='__main__':
    question = "All shoes with rating higher than 4.8 and total ratings greater than 15"
    answer = sql_chain(question)
    print(answer)
    # df = run_query(query)
    # pass
