from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add the code directory to the path so we can import our scripts
sys.path.append('/opt/airflow/code')

def run_extraction():
    from extract import main as extract_main
    extract_main()

def run_loading():
    from load_data import main as load_main
    load_main()

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ntvs_volleyball_etl',
    default_args=default_args,
    description='Extract volleyball results and load to Postgres',
    schedule_interval='0 2 * * 0',  # Every Sunday at 2:00 AM
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['ntvs', 'volleyball'],
) as dag:

    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=run_extraction,
    )

    load_task = PythonOperator(
        task_id='load_data',
        python_callable=run_loading,
    )

    extract_task >> load_task
