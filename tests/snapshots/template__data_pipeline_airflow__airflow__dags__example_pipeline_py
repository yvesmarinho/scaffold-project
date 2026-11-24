# -*- coding: utf-8 -*-
"""
example_pipeline.py — DAG exemplo usando Apache Airflow TaskFlow API.

Demonstra boas práticas:
- @dag / @task decorators (TaskFlow API)
- catchup=False para evitar backfill acidental
- retries configurado nos default_args
- credenciais via Variable ou Connection (nunca hardcoded)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="example_pipeline",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["example", "data-pipeline"],
)
def example_pipeline():
    """Pipeline de exemplo usando TaskFlow API."""

    @task()
    def extract() -> dict:
        """Extrai dados da fonte (substituir por lógica real)."""
        source_url = Variable.get("source_url", default_var="http://example.com/data")
        return {"source": source_url, "rows": 0}

    @task()
    def transform(raw: dict) -> dict:
        """Transforma dados extraídos."""
        return {**raw, "transformed": True}

    @task()
    def load(data: dict) -> None:
        """Carrega dados no destino."""
        # Credenciais via Airflow Connection, nunca hardcoded
        # conn = BaseHook.get_connection("postgres_default")
        print(f"Loaded {data['rows']} rows from {data['source']}")

    raw = extract()
    transformed = transform(raw)
    load(transformed)


dag_instance = example_pipeline()
