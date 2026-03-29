from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dataclass
class TargetScope:
    direction_id: int
    city_id: int
    direction_name: str
    city_name: str
    hh_area_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json_variable(key: str, default: Any) -> Any:
    raw = Variable.get(key, default_var=None)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def get_hh_area_override(city_id: int) -> int | None:
    """
    Optional Airflow Variable:
    HH_AREA_OVERRIDES_JSON = {"1": 40, "2": 160}
    where key = internal city_id, value = HH area id.
    """
    mapping = _load_json_variable("HH_AREA_OVERRIDES_JSON", {})
    value = mapping.get(str(city_id))
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def fetch_target_scopes(postgres_conn_id: str, user_id: int | None = None) -> list[dict[str, Any]]:
    """
    Confirmed business logic:
    - user has exactly one direction_id and one city_id
    - target scope is (direction_id, city_id)
    - we join users -> directions -> cities

    Assumed physical tables based on your ERD/migrations:
    - public.users
    - public.directions
    - public.cities
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)

    sql = """
    SELECT DISTINCT
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
      AND (%(user_id)s IS NULL OR u.id = %(user_id)s)
    ORDER BY u.direction_id, u.city_id
    """

    rows = hook.get_records(sql, parameters={"user_id": user_id})

    targets: list[dict[str, Any]] = []
    for direction_id, city_id, direction_name, city_name in rows:
        city_id_int = int(city_id)
        targets.append(
            TargetScope(
                direction_id=int(direction_id),
                city_id=city_id_int,
                direction_name=str(direction_name).strip(),
                city_name=str(city_name).strip(),
                hh_area_id=get_hh_area_override(city_id_int),
            ).to_dict()
        )

    return targets