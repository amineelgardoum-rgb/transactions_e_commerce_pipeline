from datetime import datetime,timezone
import json
import uuid
import random
from faker import Faker
from fastapi import FastAPI, Request
import asyncio
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from aiokafka.errors import KafkaConnectionError
import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# Initialize Faker
fake = Faker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic with Retry ---
    retries = 10
    retry_delay = 5
    for attempt in range(retries):
        try:
            print(
                f"Attempting to connect to Kafka (Attempt {attempt + 1}/{retries})..."
            )
            app.state.kafka_producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await app.state.kafka_producer.start()
            print("Successfully connected to Kafka!")
            break 
        except KafkaConnectionError:
            print(f"Kafka connection failed. Retrying in {retry_delay} seconds...")
            if attempt == retries - 1:
                print(
                    "Could not connect to Kafka after multiple retries. Application will not start."
                )
                raise
            await asyncio.sleep(retry_delay)

    yield  # The application runs after this point

    # --- Shutdown Logic ---
    print("Application Shutting down")
    await app.state.kafka_producer.stop()
    print("Kafka producer stopped successfully.")


def generate_fake_transaction():
    """
    Uses the Faker library to generate a single mock transaction dictionary.
    """
    product_name = fake.bs().title()
    quantity = random.randint(1, 5)
    price = round(random.uniform(10.0, 500.0), 2)
    total_amount = round(quantity * price, 2)

    return {
        "transaction_id": f"TXN-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_id": fake.random_int(min=1000, max=9999),
        "product_details": [
            {
                "product_id": f"PROD-{fake.random_int(min=100, max=999)}",
                "product_name": product_name,
                "quantity": quantity,
                "price": price,
            }
        ],
        "total_amount": total_amount,
        "currency": "USD",
        "payment_method": random.choice(["Credit Card", "PayPal", "Debit Card"]),
        "shipping_address": {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
            "country": "USA",
        },
        "status": random.choice(["Shipped", "Processing", "Delivered", "Cancelled"]),
    }


app = FastAPI(lifespan=lifespan)
# Using a more generic topic name now
topic_name = "transactions_topic"
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def success_message():
    return {"status": "success", "message": "the API is working...."}


@app.get("/real_time_response") 
async def real_time_generator(request: Request):

    async def event_publisher():
        producer = request.app.state.kafka_producer
        while True:
            if await request.is_disconnected():
                print("the client is disconnected....")
                break

            transaction = generate_fake_transaction()

            yield json.dumps(transaction)
            try:
                print(f"Sending data to the topic: {topic_name},with the Fastapi-fake API!")
                await producer.send_and_wait(topic_name, value=transaction)
            except Exception as e:
                print(f"Could not send messages to kafka, error: {e}")

            await asyncio.sleep(1)

    return EventSourceResponse(event_publisher())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
