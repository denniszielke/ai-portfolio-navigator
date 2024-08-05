import os
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import (
    VectorizedQuery
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

load_dotenv()

client: AzureOpenAI

if "AZURE_OPENAI_API_KEY" in os.environ:
    client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_OPENAI_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )
else:
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        azure_ad_token_provider = token_provider,
        api_version = os.getenv("AZURE_OPENAI_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

deployment_name = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME")
index_name = "products-semantic-index"
service_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")

def get_embedding(text, model=embedding_model):
    return client.embeddings.create(input = [text], model=model).data[0].embedding

credential = None
if "AZURE_AI_SEARCH_KEY" in os.environ:
    credential = AzureKeyCredential(os.environ["AZURE_AI_SEARCH_KEY"])
else:
    credential = DefaultAzureCredential()

search_client = SearchClient(
    service_endpoint, 
    index_name, 
    credential
)

import json
pathToProductFiles = './products.json'
# with open(pathToProductFiles) as f:
#     data = json.load(f)

import pandas as pd
df = pd.read_json(pathToProductFiles)

# In-memory database (for demonstration purposes)
items = []

class QueryModel(BaseModel):
    query: str | None = None
    history: str | None = None

# Pydantic model for item data
class Item(BaseModel):
    id: int | None = None
    name: str | None = None
    brand: str | None = None
    description: str | None = None
    price: str
    svg: str | None = None
    tags: list[str] = []
    score: float | None = None
    category: str | None = None

class ResponseModel(BaseModel):
    query: str | None = None
    message: str | None = None
    results: list[Item] = []

def sort_Items(item: Item):
    return item.score

@app.post("/query", response_model=ResponseModel)
async def query_items(input: QueryModel) -> ResponseModel:
    print(input)
    vector = VectorizedQuery(vector=get_embedding(input.query), k_nearest_neighbors=12, fields="vector")
    found_docs = list(search_client.search(
        search_text=input.query,
        query_type="semantic",
        semantic_configuration_name="products-semantic-config",
        vector_queries=[vector],
        select=["id", "name", "description", "category", "brand", "price", "tags"],
        top=12
    ))
    
    print(found_docs)
    list_of_items = []
    found_docs_as_text = " "
    for doc in found_docs:   
        print(doc) 
        item = Item(
            id = doc["id"],
            name = doc["name"],
            description = doc["description"],
            brand = doc["brand"],
            price = doc["price"],
            tags = doc["tags"],
            category = doc["category"],
            score = doc["@search.score"]
        )
        list_of_items.append(item)
        found_docs_as_text += " "+ "Name: {}".format(doc["name"]) +" "+ "Description: {}".format(doc["description"]) +" "+ "Brand: {}".format(doc["brand"]) +" "+ "Price: {}".format(doc["price"]) +" "+ "Tags: {}".format(doc["tags"]) +" "+ "Category: {}".format(doc["category"]) +" "

    list_of_items.sort(key=sort_Items, reverse=True)

    system_prompt = """You are an assistant to the user, you are given some context below. Please answer the query of the user in a full sentence and refer to the question that you are responding to in less than 300 characters<. Answer only with the correct information and be as correct as possible. The user is asking about the following products:"""

    parameters = [system_prompt, ' Context:', found_docs_as_text , ' Question:', input.query]
    joined_parameters = ''.join(parameters)

    response = client.chat.completions.create(
        model = deployment_name,
        messages = [{"role" : "assistant", "content" : joined_parameters}],
    )

    print (response.choices[0].message.content)
    print(response)

    responseModel = ResponseModel()
    responseModel.query = input.query,
    responseModel.message = response.choices[0].message.content
    responseModel.results = list_of_items
    print (responseModel)
    return responseModel
    # return df.to_dict(orient='records')[0:12]

app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    
    uvicorn.run(
        "app:app",
        host    = "0.0.0.0",
        port    = 8000, 
        reload  = True
    )