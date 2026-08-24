from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

SOURCE = "s3_sales_bucket"

default_args = {
    'owner': 'data_team',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'depends_on_past': False
}

def process_data():
    print(f"Reading data from {SOURCE}")

with DAG(
    dag_id='sales_data_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Auto-generated DAG for data ingestion',
    tags=['auto-generated', 'data-pipeline']
) as dag:

    task1 = PythonOperator(
        task_id='read_source_data',
        python_callable=process_data
    )
