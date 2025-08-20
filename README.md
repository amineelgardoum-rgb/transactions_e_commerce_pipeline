# Real-Time E-commerce Transaction Pipeline

This project demonstrates a complete, end-to-end real-time data pipeline designed to simulate and process e-commerce transactions. It captures data from multiple sources, streams it through Apache Kafka, and stores it in MongoDB for persistence and future analysis.

---

## 🏛️ Architecture

The entire system is designed with decoupled services, making it scalable and resilient. Data flows from producers through Kafka to a consumer that persists it, with a front-end for visualization.

![Project Architecture Diagram](./archi/archi.png)

---

## ✨ Features

- **Real-Time Data Streaming:** Utilizes Apache Kafka as a high-throughput, distributed message broker.
- **Multiple Data Sources:** Ingests data from two independent sources:
  - A **Faker**-based generator for producing realistic, mocked JSON data (`producer` service).
  - A **Mockoon** API simulator, mimicking a real-world third-party API (`producer-mockoon` service).
- **Decoupled Services:** Each component (producer, consumer) runs as a separate service, communicating only through the Kafka message bus.
- **High-Performance Producers:** Kafka producers are exposed via Python **FastAPI** endpoints, which include interactive documentation.
- **Persistent Storage:** A dedicated Kafka consumer subscribes to the data stream and saves all incoming transactions to a **MongoDB** database.
- **Data Visualization:** Includes a **Chart.js** dashboard (`users_transactions_over_time` service) to demonstrate front-end consumption of the data.
- **Containerized Environment:** The entire stack is managed with **Docker** and **Docker Compose** for a simple, one-command setup.

---

## 🛠️ Tech Stack

| Component                    | Technology                                                                                                                                                                                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Streaming**     | ![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white) ![Apache ZooKeeper](https://img.shields.io/badge/Apache%20ZooKeeper-F39217?style=for-the-badge&logo=apachezookeeper&logoColor=white) |
| **Database**           | ![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)                                                                                                                                                    |
| **Backend / Services** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)                                                |
| **Mocking / Data Gen** | ![Faker](https://img.shields.io/badge/Faker-D22572?style=for-the-badge) ![Mockoon](https://img.shields.io/badge/Mockoon-2563EB?style=for-the-badge&logo=mockoon&logoColor=white)                                                                              |
| **Frontend**           | ![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)                                                                                                                                               |
| **Containerization**   | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)                                                                                                                                                       |

---

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/amineelgardoum-rgb/transactions_e_commerce_pipeline.git
   cd transactions_e_commerce_pipeline
   ```

---

## 🏃‍♀️ Running the Project

The entire infrastructure can be launched with a single Docker Compose command.

### 1. Start All Services

Run this command from the root of the project directory. The `--build` flag will build the images if they don't exist, and `-d` will run the containers in detached mode.

```bash
docker-compose -f docker-compose.project.yml up --build -d
```

To check the status of all running containers:

```bash
docker-compose -f docker-compose.project.yml ps
```

### 2. Generate Transaction Data

The producers are exposed via FastAPI. You can use the interactive API documentation (Swagger UI) to send messages to Kafka.

- **Source 1 (Faker Data):**

  1. Open [http://localhost:8000/real_time_response](http://localhost:8000/docs) in your browser.
  2. Every time you click "Execute", a new transaction is sent to the `transactions-topic` Kafka topic.
- **Source 2 (Mockoon Data):**

  1. Open [http://localhost:8001/transactions](http://localhost:8001/transactions) in your browser.
  2. This service will fetch data from the Mockoon API and send it to the `transactions_topic` Kafka topic.

> **What's Happening?**
> When you click "Execute", the FastAPI service sends a message to a Kafka topic. The `consumer` service is listening to these topics, and upon receiving a message, it immediately writes the data into MongoDB.

### 3. Observe the Pipeline

You can watch the real-time logs to see the data flow through the system.

```bash
# View logs from all services at once
docker-compose -f docker-compose.project.yml logs -f

# Or, view logs for a specific service (e.g., the consumer)
docker-compose -f docker-compose.project.yml logs -f consumer
```

Press `Ctrl + C` to exit the logs.

### 4. Check the Data in MongoDB

You can connect to the MongoDB instance to verify that the data has been saved.

1. **Enter the MongoDB shell:**

   ```bash
   docker-compose -f docker-compose.project.yml exec mongo mongosh
   ```
2. **Inside the `mongosh` shell, run these commands:**

   ```javascript
   // Show all available databases
   show dbs;

   // Switch to the database used by the consumer
   use mocked_data;

   // View the data in the transactions collection
   db.transactions.find().pretty();
   ```

### 5. View the Frontend Dashboard

Open [http://localhost:8080](http://localhost:8080) in your browser to see the data visualization.

### 6. Stop the Services

When you are finished, stop and remove all the running containers.

```bash
# Stop containers and remove them
docker-compose -f docker-compose.project.yml down

# To also remove the data volumes (deleting all MongoDB data):
docker-compose -f docker-compose.project.yml down -v
```

---

## 📁 Project Structure

```
.
├── archi/                        # Contains architecture diagram images
├── consumer/                     # Kafka consumer service (writes to DB)
├── mockoon/                      # Configuration for the Mockoon API simulator
├── producer/                     # Kafka producer (Faker data)
├── producer-mockoon/             # Kafka producer (Mockoon data)
├── users_transactions_over_time/ # Frontend dashboard application
├── .dockerignore                 # Files for Docker to ignore
├── .gitignore                    # Files for Git to ignore
├── docker-compose.project.yml    # Main Docker Compose file
└── README.md                     # You are here!
```
