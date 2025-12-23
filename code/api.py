import fastapi
import logging
import uvicorn
import psycopg2
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("logs/api.log"))

logger.info("Starting application...")

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    logger.info("Connected to database...")
    cursor = conn.cursor()
except Exception as e:
    logger.critical(f"Failed to connect to the database: {e}")
    sys.exit(1)

app = fastapi.FastAPI()     

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/tournaments")
def read_tournaments():
    cursor.execute("SELECT * FROM ntvs.tournaments;")
    return cursor.fetchall()

@app.get("/tournaments/{tournament_id}")
def read_tournament(tournament_id: str):
    # Use parameterized query to prevent SQL Injection
    cursor.execute("SELECT * FROM ntvs.tournaments WHERE tournament_id = %s;", (tournament_id,))
    result = cursor.fetchone()
    
    if result is None:
        raise fastapi.HTTPException(status_code=404, detail="Tournament not found")
        
    return result

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        logger.info("Closing database connection...")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("Application stopped.")
