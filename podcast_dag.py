from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import asyncio
from db.mongo_ops import insert_episode, close_client

default_args = {
    'start_date': datetime(2023, 1, 1),
}

def insert_task():
    new_ep = {
        "uuid": "airflow-ep001",
        "title": "Added by Airflow",
        "description": "This was added during a DAG run",
        "published": True
    }
    asyncio.run(insert_episode(new_ep))
    close_client()

with DAG("podcast_mongo_ops",
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    insert = PythonOperator(
        task_id="insert_episode_task",
        python_callable=insert_task
    )
