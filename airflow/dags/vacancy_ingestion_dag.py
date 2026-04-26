from __future__ import annotations

import os
from typing import Any

import pendulum
from airflow.sdk import dag, get_current_context, task

from lib.normalize import deduplicate_vacancies, finalize_vacancy_record
from lib.scope import fetch_target_scopes
from lib.sources.hh_auth import ensure_hh_app_access_token, get_hh_app_access_token
from lib.sources.hh_source import HHApiClient, collect_hh_vacancies
from lib.sources.parser_source import collect_parsed_vacancies
from lib.vacancy_repository import (
    delete_target_vacancy_data,
    insert_vacancies_and_relations,
    load_known_skill_names,
    target_has_vacancies,
)

DAG_ID = "vacancy_ingestion_dag"

POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "mentorai_db")

HH_MAX_JOBS_PER_TARGET = int(os.getenv("HH_MAX_JOBS_PER_TARGET", "60"))
HH_PER_PAGE = int(os.getenv("HH_PER_PAGE", "30"))
HH_MAX_PAGES = int(os.getenv("HH_MAX_PAGES", "3"))
HH_ONLY_WITH_SALARY = os.getenv("HH_ONLY_WITH_SALARY", "false").lower() == "true"
HH_USER_AGENT = os.getenv(
    "MENTORAI_HH_USER_AGENT",
    "MentorAI-StudentResearchBot/1.0 (email: saidshabekov@gmail.com)",
)
HH_PREFLIGHT_TEXT = os.getenv("HH_PREFLIGHT_TEXT", "Backend Developer")
HH_PREFLIGHT_AREA = int(os.getenv("HH_PREFLIGHT_AREA", "160"))

ENABLE_PARSER_SOURCE = os.getenv("MENTORAI_ENABLE_PARSER_SOURCE", "false").lower() == "true"
PARSER_MAX_JOBS_PER_TARGET = int(os.getenv("PARSER_MAX_JOBS_PER_TARGET", "40"))


@dag(
    dag_id=DAG_ID,
    schedule="0 3 * * *",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["mentorai", "vacancies", "ingestion"],
)
def vacancy_ingestion_dag():
    @task
    def read_conf() -> dict[str, Any]:
        context = get_current_context()
        dag_run = context.get("dag_run")
        conf = dag_run.conf if dag_run else {}

        user_id = conf.get("user_id")
        if user_id is not None:
            user_id = int(user_id)

        return {"user_id": user_id}

    @task
    def validate_hh_api_access() -> dict[str, Any]:
        """
        Fail fast before processing targets.
        Does not return the token to XCom.
        """
        app_token = ensure_hh_app_access_token(user_agent=HH_USER_AGENT)
        hh = HHApiClient(user_agent=HH_USER_AGENT, access_token=app_token)
        response = hh.search_vacancies(
            text=HH_PREFLIGHT_TEXT,
            area=HH_PREFLIGHT_AREA,
            page=0,
            per_page=1,
            only_with_salary=False,
        )

        return {
            "status": "ok",
            "found": response.get("found"),
            "items": len(response.get("items") or []),
        }

    @task
    def prepare_storage(conf: dict[str, Any]) -> dict[str, Any]:
        """
        Scheduled run no longer truncates all vacancy tables before HH collection.
        Old vacancies for each target are deleted only after new records for that
        exact target were collected and deduplicated successfully.
        """
        if conf["user_id"] is None:
            return {"mode": "scheduled_safe_refresh", "truncated": False}

        return {"mode": "manual_single_user", "truncated": False}

    @task
    def resolve_targets(conf: dict[str, Any]) -> list[dict[str, Any]]:
        return fetch_target_scopes(
            postgres_conn_id=POSTGRES_CONN_ID,
            user_id=conf["user_id"],
        )

    @task(
        pool="hh_api_pool",
        max_active_tis_per_dag=1,
    )
    def ingest_target(target: dict[str, Any]) -> dict[str, Any]:
        context = get_current_context()
        dag_run = context.get("dag_run")
        conf = dag_run.conf if dag_run else {}
        manual_user_id = conf.get("user_id")

        direction_id = int(target["direction_id"])
        city_id = int(target["city_id"])
        direction_name = target["direction_name"]
        city_name = target["city_name"]
        hh_area_id = target.get("hh_area_id")

        if manual_user_id is not None:
            already_loaded = target_has_vacancies(
                postgres_conn_id=POSTGRES_CONN_ID,
                direction_id=direction_id,
                city_id=city_id,
            )

            if already_loaded:
                return {
                    "direction_id": direction_id,
                    "city_id": city_id,
                    "direction_name": direction_name,
                    "city_name": city_name,
                    "mode": "manual_skip_existing_target",
                    "skipped": True,
                    "source_records": 0,
                    "deduped_records": 0,
                    "vacancies_deleted": 0,
                    "vacancy_skills_deleted": 0,
                    "user_vacancies_deleted": 0,
                    "vacancies_inserted": 0,
                    "skills_inserted": 0,
                    "vacancy_skills_inserted": 0,
                }

        known_skill_names = load_known_skill_names(POSTGRES_CONN_ID)
        raw_records: list[dict[str, Any]] = []

        app_token = get_hh_app_access_token()

        hh_records = collect_hh_vacancies(
            direction_name=direction_name,
            city_name=city_name,
            user_agent=HH_USER_AGENT,
            app_access_token=app_token,
            area_override=hh_area_id,
            limit_total=HH_MAX_JOBS_PER_TARGET,
            per_page=HH_PER_PAGE,
            max_pages=HH_MAX_PAGES,
            only_with_salary=HH_ONLY_WITH_SALARY,
        )
        raw_records.extend(hh_records)

        if ENABLE_PARSER_SOURCE:
            parsed_records = collect_parsed_vacancies(
                direction_name=direction_name,
                city_name=city_name,
                limit_total=PARSER_MAX_JOBS_PER_TARGET,
            )
            raw_records.extend(parsed_records)

        finalized = [
            finalize_vacancy_record(
                raw=raw_record,
                target=target,
                known_skill_names=known_skill_names,
            )
            for raw_record in raw_records
        ]
        deduped = deduplicate_vacancies(finalized)

        delete_stats = {
            "user_vacancies_deleted": 0,
            "vacancy_skills_deleted": 0,
            "vacancies_deleted": 0,
        }

        if not deduped:
            return {
                "direction_id": direction_id,
                "city_id": city_id,
                "direction_name": direction_name,
                "city_name": city_name,
                "mode": "manual_empty_result" if manual_user_id is not None else "scheduled_empty_result_kept_old_data",
                "skipped": False,
                "source_records": len(raw_records),
                "deduped_records": 0,
                **delete_stats,
                "vacancies_inserted": 0,
                "skills_inserted": 0,
                "vacancy_skills_inserted": 0,
            }

        if manual_user_id is None:
            delete_stats = delete_target_vacancy_data(
                postgres_conn_id=POSTGRES_CONN_ID,
                direction_id=direction_id,
                city_id=city_id,
            )

        insert_stats = insert_vacancies_and_relations(
            postgres_conn_id=POSTGRES_CONN_ID,
            vacancies=deduped,
        )

        return {
            "direction_id": direction_id,
            "city_id": city_id,
            "direction_name": direction_name,
            "city_name": city_name,
            "mode": "manual_fetch" if manual_user_id is not None else "scheduled_safe_refresh",
            "skipped": False,
            "source_records": len(raw_records),
            "deduped_records": len(deduped),
            **delete_stats,
            **insert_stats,
        }

    @task
    def summarize(
        conf: dict[str, Any],
        prep: dict[str, Any],
        hh_check: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        results_list = list(results)
        skipped_targets = sum(1 for r in results_list if r["skipped"])
        processed_targets = len(results_list) - skipped_targets

        return {
            "run_mode": prep["mode"],
            "user_id": conf["user_id"],
            "hh_api_check": hh_check,
            "truncated": prep["truncated"],
            "targets_total": len(results_list),
            "targets_processed": processed_targets,
            "targets_skipped": skipped_targets,
            "source_records": sum(r["source_records"] for r in results_list),
            "deduped_records": sum(r["deduped_records"] for r in results_list),
            "vacancies_deleted": sum(r["vacancies_deleted"] for r in results_list),
            "vacancy_skills_deleted": sum(r["vacancy_skills_deleted"] for r in results_list),
            "user_vacancies_deleted": sum(r["user_vacancies_deleted"] for r in results_list),
            "vacancies_inserted": sum(r["vacancies_inserted"] for r in results_list),
            "skills_inserted": sum(r["skills_inserted"] for r in results_list),
            "vacancy_skills_inserted": sum(r["vacancy_skills_inserted"] for r in results_list),
        }

    conf = read_conf()
    hh_check = validate_hh_api_access()
    prep = prepare_storage(conf)
    targets = resolve_targets(conf)
    ingested = ingest_target.expand(target=targets)
    summary = summarize(conf, prep, hh_check, ingested)

    conf >> hh_check >> prep
    conf >> targets
    prep >> ingested
    targets >> ingested
    ingested >> summary


vacancy_ingestion_dag()