from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from airflow.providers.postgres.hooks.postgres import PostgresHook

from lib.normalize import normalize_skill_name


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def target_has_vacancies(postgres_conn_id: str, direction_id: int, city_id: int) -> bool:
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM public.vacancies
                    WHERE direction_id = %s
                      AND city_id = %s
                    LIMIT 1
                )
                """,
                (direction_id, city_id),
            )
            return bool(cur.fetchone()[0])
    finally:
        conn.close()


def truncate_vacancy_data(postgres_conn_id: str) -> None:
    """
    Hard full truncate. Kept for emergency/manual maintenance only.
    The scheduled DAG should not call this before successful HH collection.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                TRUNCATE TABLE
                    public.user_vacancies,
                    public.vacancy_skills,
                    public.vacancies
                RESTART IDENTITY CASCADE
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_target_vacancy_data(
    postgres_conn_id: str,
    direction_id: int,
    city_id: int,
) -> dict[str, int]:
    """
    Delete vacancies only for one target pair after new data was collected successfully.
    This prevents a failed HH request from wiping all previously collected vacancies.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.user_vacancies
                WHERE vacancy_id IN (
                    SELECT id
                    FROM public.vacancies
                    WHERE direction_id = %s
                      AND city_id = %s
                )
                """,
                (direction_id, city_id),
            )
            user_vacancies_deleted = cur.rowcount

            cur.execute(
                """
                DELETE FROM public.vacancy_skills
                WHERE vacancy_id IN (
                    SELECT id
                    FROM public.vacancies
                    WHERE direction_id = %s
                      AND city_id = %s
                )
                """,
                (direction_id, city_id),
            )
            vacancy_skills_deleted = cur.rowcount

            cur.execute(
                """
                DELETE FROM public.vacancies
                WHERE direction_id = %s
                  AND city_id = %s
                """,
                (direction_id, city_id),
            )
            vacancies_deleted = cur.rowcount

        conn.commit()

        return {
            "user_vacancies_deleted": user_vacancies_deleted,
            "vacancy_skills_deleted": vacancy_skills_deleted,
            "vacancies_deleted": vacancies_deleted,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_known_skill_names(postgres_conn_id: str) -> list[str]:
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM public.skills")
            return [row[0] for row in cur.fetchall() if row[0]]
    finally:
        conn.close()


def insert_vacancies_and_relations(
    postgres_conn_id: str,
    vacancies: list[dict[str, Any]],
) -> dict[str, Any]:
    if not vacancies:
        return {
            "vacancies_inserted": 0,
            "skills_inserted": 0,
            "vacancy_skills_inserted": 0,
        }

    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM public.skills")
            skill_id_by_normalized = {
                normalize_skill_name(name): int(skill_id)
                for skill_id, name in cur.fetchall()
                if name
            }

            inserted_vacancies = 0
            inserted_skills = 0
            inserted_relations = 0

            for vacancy in vacancies:
                title = vacancy.get("title")
                url = vacancy.get("url")
                direction_id = vacancy.get("direction_id")
                city_id = vacancy.get("city_id")
                vacancy_type = vacancy.get("vacancy_type") or "OFFLINE"

                if not title or not url or not direction_id or not city_id:
                    continue

                cur.execute(
                    """
                    INSERT INTO public.vacancies (
                        title,
                        direction_id,
                        city_id,
                        salary_amount,
                        salary_currency,
                        vacancy_type,
                        url,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        title,
                        direction_id,
                        city_id,
                        vacancy.get("salary_amount"),
                        vacancy.get("salary_currency"),
                        vacancy_type,
                        url,
                        now_utc(),
                        now_utc(),
                    ),
                )

                vacancy_id = int(cur.fetchone()[0])
                inserted_vacancies += 1

                seen_skill_ids: set[int] = set()

                for skill_name in vacancy.get("skills", []):
                    normalized = normalize_skill_name(skill_name)

                    if not normalized:
                        continue

                    skill_id = skill_id_by_normalized.get(normalized)

                    if skill_id is None:
                        cur.execute(
                            """
                            INSERT INTO public.skills (name, created_at, updated_at)
                            VALUES (%s, %s, %s)
                            RETURNING id
                            """,
                            (skill_name, now_utc(), now_utc()),
                        )
                        skill_id = int(cur.fetchone()[0])
                        skill_id_by_normalized[normalized] = skill_id
                        inserted_skills += 1

                    if skill_id in seen_skill_ids:
                        continue

                    seen_skill_ids.add(skill_id)

                    cur.execute(
                        """
                        INSERT INTO public.vacancy_skills (vacancy_id, skill_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (vacancy_id, skill_id),
                    )
                    inserted_relations += 1

        conn.commit()

        return {
            "vacancies_inserted": inserted_vacancies,
            "skills_inserted": inserted_skills,
            "vacancy_skills_inserted": inserted_relations,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()