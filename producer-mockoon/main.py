import asyncio
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn
import json
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
import os
KAFKA_BROKER=os.getenv("KAFKA_BROKER","localhost:9092")

@asynccontextmanager
async def lifespan(app:FastAPI):
    retries=10
    retry_delay=5
    for attempt in range(retries):
        try:
            print(f"Attempting to connect to kafka (Attempt{attempt+1}/{retries})")
            app.state.kafka_producer=AIOKafkaProducer( # the state in the app is like a variables that launching in startup of the api
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v:json.dumps(v).encode('utf-8') # because kafka send only the bytes 
            )
            await app.state.kafka_producer.start() # wait for the kafka producer to start
            print("Successfully Connected to Kafka") # after thee kafka producer is started this message will print to say that the producer of kafka is started 
            break # here break the loop because the Kafka producer is started 
        except KafkaConnectionError:
            print(f"Kafka connection failed. Retrying in {retry_delay} secondes .....") # just in case the kafka-init service in docker is healthy or not
            if attempt==retries-1:
                
                print("Could not connect to Kafka. Application Will not Start...")
                raise # just to stop the programme 
            await asyncio.sleep(retry_delay) # to make it more efficient the app will run every 5 secondes 
    
    yield # the application will run here its like return but the yield its not stopping the logic
    
    print("Application Shutting down...")
    await app.state.kafka_producer.stop()
    print("Kafka producer stopped successfully...")
    
app = FastAPI(lifespan=lifespan)
topic_name="transactions_topic"
origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)
# We don't use async here just make it in thread to not block the async because it sync
def fetch_data_from_api():
    try:
        response = requests.get("http://mockoon:3000/transactions", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while requesting from the API: {e}")
        return None
    except ValueError:
        print("Failed to decode JSON from the response.")
        return None

@app.get("/")
def success_message():
    return {"status": "200 OK", "message": "The API is working"}

@app.get("/transactions")
async def real_time_transactions(request:Request):
    async def event_publisher():
        producer=request.app.state.kafka_producer
        while True:
            if await request.is_disconnected():
                print("Client disconnected, closing stream.")
                break
            data = await asyncio.to_thread(fetch_data_from_api)

            if data:
                yield json.dumps(data)
                try:
                    print(f"Sending data to topic:{topic_name},with the mockoon API!")
                    await producer.send_and_wait(topic_name,value=data)
                except Exception as e:
                    print(f"There is an error while sending messages to Kafka....,Error:{e}") 
            else:
                print("No new data or an error occurred. Retrying...")
            await asyncio.sleep(1)
        
    return EventSourceResponse(event_publisher())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
