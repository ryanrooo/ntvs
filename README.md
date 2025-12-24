# NTVS (North Texas Volleyball Series) Data Pipeline & API

This project is a comprehensive data engineering solution designed to extract, transform, and serve volleyball tournament results from the North Texas region. It utilizes an ETL pipeline orchestrated by Apache Airflow to scrape data from VStar Volleyball, stores it in a PostgreSQL database, and exposes it via a fast and modern REST API.

## 🚀 Features

*   **Automated ETL Pipeline**: Weekly scheduled extraction of tournament data (Teams, Pools, Standings, Matches).
*   **Robust Database**: Relational schema in PostgreSQL to handle complex tournament structures.
*   **REST API**: FastAPI-based service to query tournament data easily.
*   **Containerized**: Fully Dockerized environment for easy deployment and consistency.
*   **Database Management**: Integrated Adminer interface for direct database inspection.

## 🛠 Tech Stack

*   **Orchestration**: Apache Airflow 2.7.1
*   **Database**: PostgreSQL 15
*   **API Framework**: FastAPI (Python)
*   **Extraction**: BeautifulSoup4, Requests
*   **Infrastructure**: Docker & Docker Compose

## 📂 Project Structure

```
ntvs/
├── code/               # Application source code
│   ├── api.py          # FastAPI application
│   ├── extract.py      # Web scraping and data extraction logic
│   ├── load_data.py    # Database loading logic
│   └── requirements.txt
├── dags/               # Airflow DAGs
│   └── ntvs_etl.py     # Main ETL pipeline definition
├── data/               # Temporary storage for extracted CSVs
├── db/                 # Database initialization scripts
│   └── init.sql
├── compose.yml         # Docker Compose configuration
└── .env                # Environment configuration
```

## 🏁 Getting Started

### Prerequisites

*   Docker Desktop installed on your machine.
*   Git.

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ntvs
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the root directory (or use the default provided in `compose.yml` for development).

3.  **Start the Services:**
    Run the following command to build and start all containers:
    ```bash
    docker compose up --build
    ```

    *   **Note**: The first run might take a few minutes as it initializes the Airflow database and creates the `admin` user.

### Accessing Services

Once up and running, you can access the following services:

*   **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Airflow Webserver**: [http://localhost:8081](http://localhost:8081)
    *   *Username*: `admin`
    *   *Password*: `admin`
*   **Adminer (DB GUI)**: [http://localhost:8080](http://localhost:8080)
    *   *System*: PostgreSQL
    *   *Server*: `db`
    *   *Username*: `admin`
    *   *Password*: `example`
    *   *Database*: `ntvs_db`

## 🔄 Data Pipeline

The project includes an Airflow DAG named `ntvs_volleyball_etl` which is scheduled to run every Sunday at 2:00 AM.

1.  **Extract**: Scrapes tournament pages from the configured VStar URLs.
2.  **Transform**: Cleanses data and normalizes it into entities: Tournaments, Teams, Pools, Standings, Matches.
3.  **Load**: Inserts or updates the normalized data into the PostgreSQL database.

You can trigger this DAG manually from the Airflow UI to populate your database immediately.

## 📡 API Endpoints

*   `GET /`: Health check.
*   `GET /tournaments`: List all tracked tournaments.
*   `GET /tournaments/{tournament_id}`: Get details for a specific tournament.

## ✍️ Authors

*   **Ryan Nguyen** - *Initial Work*
