import pendulum
from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = "/opt/airflow/taxi-pipeline"
PROFILES = f"{PROJECT}/airflow/profiles"

with DAG(
    dag_id="taxi_pipeline",
    description="Load NYC taxi data, build dbt models, run tests",
    schedule="0 8 * * 6",          # every Saturday, 8:00 AM
    start_date=pendulum.datetime(2026, 8, 1, tz="America/New_York"),
    catchup=False,
    tags=["taxi"],
) as dag:

    load_taxi_data = BashOperator(
        task_id="load_taxi_data",
        bash_command=f"cd {PROJECT} && python load_taxi.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT}/taxi_dbt && dbt deps && DBT_TARGET_PATH=/tmp/dbt_target dbt run --profiles-dir {PROFILES}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT}/taxi_dbt && DBT_TARGET_PATH=/tmp/dbt_target dbt test --profiles-dir {PROFILES}",
    )

    load_taxi_data >> dbt_run >> dbt_test