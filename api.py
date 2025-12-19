import fastapi
import logging
import uvicorn
import psycopg2

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("app.log"))

logger.info("Starting application...")

conn = psycopg2.connect(
    host="localhost",
    database="volley_ops",
    user="dq",
    password="dq",
)

logger.info("Connected to database...")
cursor = conn.cursor()
app = fastapi.FastAPI()     

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/tournaments")
def read_tournament():
    cursor.execute("SELECT * FROM ntvs.tournaments;")
    return cursor.fetchall()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    cursor.close()
    conn.close()

    
