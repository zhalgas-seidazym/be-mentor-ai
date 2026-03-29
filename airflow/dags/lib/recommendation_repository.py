from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from airflow.providers.postgres.hooks.postgres import PostgresHook


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def fetch_recommendation_users(
    postgres_conn_id: str,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Если user_id передан -> один пользователь.
    Если нет -> все пользователи с direction_id и city_id.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            if user_id is None:
                cur.execute(
                    """
                    SELECT
                        u.id AS user_id,
                        u.direction_id,
                        u.city_id,
                        d.name AS direction_name,
                        c.name AS city_name
                    FROM public.users u
                    JOIN public.directions d
                      ON d.id = u.direction_id
                    JOIN public.cities c
                      ON c.id = u.city_id
                    WHERE u.direction_id IS NOT NULL
                      AND u.city_id IS NOT NULL
                    ORDER BY u.id
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT
                        u.id AS user_id,
                        u.direction_id,
                        u.city_id,
                        d.name AS direction_name,
                        c.name AS city_name
                    FROM public.users u
                    JOIN public.directions d
                      ON d.id = u.direction_id
                    JOIN public.cities c
                      ON c.id = u.city_id
                    WHERE u.id = %s
                      AND u.direction_id IS NOT NULL
                      AND u.city_id IS NOT NULL
                    ORDER BY u.id
                    """,
                    (user_id,),
                )

            rows = cur.fetchall()

        return [
            {
                "user_id": int(row[0]),
                "direction_id": int(row[1]),
                "city_id": int(row[2]),
                "direction_name": row[3],
                "city_name": row[4],
            }
            for row in rows
        ]
    finally:
        conn.close()


def load_user_skill_ids(
    postgres_conn_id: str,
    user_id: int,
) -> set[int]:
    """
    Берём навыки пользователя.
    Используем только user_id + skill_id, без завязки на другие поля,
    чтобы код оставался совместимым.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT skill_id
                FROM public.user_skills
                WHERE user_id = %s
                """,
                (user_id,),
            )
            rows = cur.fetchall()

        return {int(row[0]) for row in rows}
    finally:
        conn.close()


def load_candidate_vacancies_with_skills(
    postgres_conn_id: str,
    direction_id: int,
    city_id: int,
) -> list[dict[str, Any]]:
    """
    Берём только вакансии того же direction_id и city_id, что и у пользователя.
    Это главный фильтр рекомендаций.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    v.id AS vacancy_id,
                    v.title,
                    v.url,
                    COALESCE(
                        array_agg(vs.skill_id ORDER BY vs.skill_id)
                        FILTER (WHERE vs.skill_id IS NOT NULL),
                        '{}'
                    ) AS required_skill_ids
                FROM public.vacancies v
                LEFT JOIN public.vacancy_skills vs
                  ON vs.vacancy_id = v.id
                  WHERE v.direction_id = %s
                  AND v.city_id = %s
                GROUP BY v.id, v.title, v.url
                ORDER BY v.id
                """,
                (direction_id, city_id),
            )
            rows = cur.fetchall()

        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "vacancy_id": int(row[0]),
                    "title": row[1],
                    "url": row[2],
                    "required_skill_ids": [int(x) for x in (row[3] or [])],
                }
            )
        return result
    finally:
        conn.close()


def build_recommendations_for_user(
    postgres_conn_id: str,
    user_row: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:
    user_id = int(user_row["user_id"])
    direction_id = int(user_row["direction_id"])
    city_id = int(user_row["city_id"])

    user_skill_ids = load_user_skill_ids(
        postgres_conn_id=postgres_conn_id,
        user_id=user_id,
    )

    if not user_skill_ids:
        return {
            "user_id": user_id,
            "direction_id": direction_id,
            "city_id": city_id,
            "candidate_vacancies": 0,
            "recommended_vacancies": 0,
            "rows": [],
        }

    candidate_vacancies = load_candidate_vacancies_with_skills(
        postgres_conn_id=postgres_conn_id,
        direction_id=direction_id,
        city_id=city_id,
    )

    scored_rows: list[dict[str, Any]] = []

    for vacancy in candidate_vacancies:
        required_skill_ids = set(vacancy["required_skill_ids"])

        # если у вакансии нет skill-требований, пропускаем
        if not required_skill_ids:
            continue

        matched_skill_ids = user_skill_ids & required_skill_ids
        matched_count = len(matched_skill_ids)
        required_count = len(required_skill_ids)

        if matched_count == 0:
            continue

        score = round(matched_count / required_count, 4)

        scored_rows.append(
            {
                "user_id": user_id,
                "vacancy_id": int(vacancy["vacancy_id"]),
                "score": score,
                "matched_skills_count": matched_count,
                "required_skills_count": required_count,
            }
        )

    scored_rows.sort(
        key=lambda r: (
            -r["score"],
            -r["matched_skills_count"],
            r["required_skills_count"],
            r["vacancy_id"],
        )
    )

    top_rows = scored_rows[:top_k]

    return {
        "user_id": user_id,
        "direction_id": direction_id,
        "city_id": city_id,
        "candidate_vacancies": len(candidate_vacancies),
        "recommended_vacancies": len(top_rows),
        "rows": top_rows,
    }


def replace_user_vacancies(
    postgres_conn_id: str,
    affected_user_ids: list[int],
    recommendation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Сохраняем рекомендации в public.user_vacancies.

    Код написан под минимальную схему:
        public.user_vacancies(user_id, vacancy_id)

    Если у тебя в реальной таблице есть дополнительные обязательные поля,
    менять нужно только INSERT ниже.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            if affected_user_ids:
                cur.execute(
                    """
                    DELETE FROM public.user_vacancies
                    WHERE user_id = ANY(%s)
                    """,
                    (affected_user_ids,),
                )

            if recommendation_rows:
                values = [
                    (int(row["user_id"]), int(row["vacancy_id"]))
                    for row in recommendation_rows
                ]
                cur.executemany(
                    """
                    INSERT INTO public.user_vacancies (user_id, vacancy_id)
                    VALUES (%s, %s)
                    """,
                    values,
                )

        conn.commit()
        return {
            "affected_users": len(affected_user_ids),
            "inserted_rows": len(recommendation_rows),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()