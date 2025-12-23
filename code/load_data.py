import os
import csv
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/load.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def load_csv(cursor, file_path, table_name, columns, conflict_col):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    # Handle single or multiple conflict keys
    conflict_keys = [k.strip() for k in conflict_col.split(",")]

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cols = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            
            # Only update columns that are NOT part of the primary key
            update_cols = [col for col in columns if col not in conflict_keys]
            updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            
            if updates:
                sql = f"""
                    INSERT INTO ntvs.{table_name} ({cols})
                    VALUES ({placeholders})
                    ON CONFLICT ({conflict_col})
                    DO UPDATE SET {updates};
                """
            else:
                # If all columns are keys, do nothing on conflict
                sql = f"""
                    INSERT INTO ntvs.{table_name} ({cols})
                    VALUES ({placeholders})
                    ON CONFLICT ({conflict_col})
                    DO NOTHING;
                """

            # Handle empty strings by converting them to None (NULL in SQL)
            values = [row[col] if row[col] != "" else None for col in columns]
            cursor.execute(sql, values)
    
    logger.info(f"Loaded {file_path} into {table_name}")

def main():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Define loading order (important for Foreign Keys)
        
        # 1. Tournaments
        load_csv(cursor, "data/tournaments.csv", "tournaments", 
                 ["tournament_id", "name"], "tournament_id")
        
        # 2. Teams
        load_csv(cursor, "data/teams.csv", "teams", 
                 ["team_name", "club_name", "division"], "team_name")
        
        # 3. Pools
        load_csv(cursor, "data/pools.csv", "pools", 
                 ["pool_id", "tournament_id", "division", "pool_name", "team_count"], "pool_id")
        
        # 4. Standings (Compound Key)
        load_csv(cursor, "data/pool_standings.csv", "pool_standings", 
                 ["pool_id", "team_name", "rank_seed", "matches_won", "matches_lost", "point_diff", "pool_finish"], "pool_id, team_name")

        # 5. Matches (Compound Key)
        load_csv(cursor, "data/match_results.csv", "match_results", 
                 ["match_id", "pool_id", "team_name", "opponent_name", "outcome", "sets_won", "sets_lost", "score_log"], "match_id, team_name")

        conn.commit()
        logger.info("Successfully loaded all data into Postgres.")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    main()
