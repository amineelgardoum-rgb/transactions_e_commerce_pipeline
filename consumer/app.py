import asyncio
import json
import os
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# --- CONFIGURATION: Read environment variables ---
# This part is fine, it sets up the configuration for the application(from t the docker-compose can set the env variables with the environment section...)
KAFKA_BROKER = os.getenv(
    "KAFKA_BROKER", "localhost:9092"
)  # if the docker-compose didn't find the KAFKA_BROKER inside the docker-compose file it can replace it with localhost:9092
MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://localhost:27017"
)  # the same as the Kafka Broker
KAFKA_TOPIC = "transactions_topic"
KAFKA_GROUP_ID = "transactions_group"


async def save_data_to_mongodb(data_list: list, client: AsyncIOMotorClient):
    """
    Saves a list of data documents to MongoDB using a provided async client.
    This helper function is clean and focuses on a single task.
    """
    # Guard clause: Don't do anything if the client isn't available or the list is empty.
    if not client or not data_list:
        return

    try:
        # NOTE: This is the database you must look for in MongoDB Compass.
        db = client["mocked_data"]  # this is the db
        collection = db["transactions"]  # this is the collection name to look
        # to access the data you can use the the mongosh (mongodb shell) or you can use the mongodb compass for more friendly user interface
        # The actual database operation, which must be awaited.
        result = await collection.insert_many(data_list)
        print(f"--> SUCCESS: Saved {len(result.inserted_ids)} document(s) to MongoDB.")
    except Exception as e:
        # This will catch and print any errors that occur during the insert operation.
        print(f"!!! DATABASE ERROR during save operation: {e}")


async def consume_and_save():
    """
    The main application logic:
    1. Manages connections to Kafka and MongoDB within the same async context.
    2. Consumes messages from a Kafka topic.
    3. Saves the processed messages to MongoDB.
    """
    # Initialize clients to None to ensure they exist for the 'finally' block.
    consumer = None
    mongo_client = None

    try:
        # --- ESTABLISH CONNECTIONS ---
        # The clients are created *inside* the main async function.
        # This ensures they are attached to the correct asyncio event loop.

        print("Attempting to connect to Kafka...")
        consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",  # Start from the beginning of the topic if the group is new.
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            retry_backoff_ms=2000,  # Wait 2s between retries.
        )
        await consumer.start()
        print("Successfully connected to Kafka!")

        print("Attempting to connect to MongoDB...")
        mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Verify connection by pinging the admin database. This is an async operation.
        await mongo_client.admin.command(
            "ping"
        )  # to see if the mongodb container work perfectly
        print("Successfully connected to MongoDB!")

        # --- CONSUMPTION LOOP ---
        print(f"\nConsumer started for topic '{KAFKA_TOPIC}'. Waiting for messages...")

        async for message in consumer:
            print("\n" + "=" * 50)
            print(f"Received message: Offset={message.offset}, Topic={message.topic}")

            # Use a separate try/except for each message to prevent one bad
            # message from crashing the entire consumer.
            try:
                transaction_data = message.value
                if transaction_data:
                    # Pass the correctly-scoped mongo_client to the save function.
                    await save_data_to_mongodb([transaction_data], mongo_client)
                else:
                    print("--> Message value is empty. Skipping save.")
            except Exception as e:
                print(
                    f"!!! PROCESSING ERROR for message at offset {message.offset}: {e}"
                )

    except (KafkaConnectionError, ServerSelectionTimeoutError, ConnectionFailure) as e:
        print(
            f"\nCRITICAL ERROR: Could not connect to services. Shutting down. Error: {e}"
        )
    except KeyboardInterrupt:
        print("\nConsumer stopped by user.")
    except Exception as e:
        print(f"\nAn unexpected and fatal error occurred: {e}")
    finally:
        # --- CLEANUP ---
        # This block will always run, ensuring connections are closed gracefully.
        print("\nCleaning up resources...")
        if consumer:
            await consumer.stop()
            print("Kafka consumer stopped.")
        if mongo_client:
            mongo_client.close()  # motor's close() is synchronous.
            print("MongoDB connection closed.")
        print("Cleanup complete.")


# --- EXECUTION ---
# This is the entry point of the script.
if __name__ == "__main__":
    # asyncio.run() creates a new event loop, runs our main function until it's
    # complete, and then closes the loop. This is the standard way to run an
    # asyncio application.
    asyncio.run(consume_and_save())
