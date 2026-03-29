from __future__ import annotations

from typing import Any


def collect_parsed_vacancies(
    direction_name: str,
    city_name: str,
    limit_total: int = 50,
) -> list[dict[str, Any]]:
    """
    Safe placeholder.

    Why it is intentionally empty now:
    - you clarified that city filtering is mandatory
    - the previously shared WWR parser is remote-oriented and breaks that rule
    - I prefer a logically correct DAG over plugging in a wrong source

    When you provide a city-aware parser source, replace this function
    with a real implementation and keep the DAG orchestration unchanged.
    """
    _ = direction_name, city_name, limit_total
    return []




# from __future__ import annotations

# import re
# import time
# from typing import Any
# from urllib.parse import quote_plus, urljoin

# import httpx
# from bs4 import BeautifulSoup


# BASE = "https://weworkremotely.com"


# def _sleep(min_s: float = 0.8, max_s: float = 1.6) -> None:
#     time.sleep(min_s + (max_s - min_s) * 0.5)


# def fetch_html(client: httpx.Client, url: str) -> str:
#     response = client.get(url, follow_redirects=True)
#     response.raise_for_status()
#     return response.text


# def parse_search_job_links(search_html: str) -> list[str]:
#     soup = BeautifulSoup(search_html, "html.parser")
#     links = set()

#     for a in soup.select('a[href^="/remote-jobs/"]'):
#         href = a.get("href")
#         if not href:
#             continue
#         if href.startswith("/remote-jobs/search"):
#             continue
#         if href.count("/") < 2:
#             continue
#         links.add(urljoin(BASE, href))

#     return sorted(links)


# def _find_company_from_view_company_block(soup: BeautifulSoup) -> str | None:
#     view = soup.find("a", string=re.compile(r"^\s*View company\s*$", re.I))
#     if not view:
#         return None

#     for tag in ["h3", "h2", "h4"]:
#         prev = view.find_previous(tag)
#         if prev:
#             name = prev.get_text(" ", strip=True)
#             if name:
#                 return name
#     return None


# def _find_region_as_location(soup: BeautifulSoup) -> str | None:
#     region_label = soup.find(string=re.compile(r"^\s*Region\s*$", re.I))
#     if not region_label:
#         return None

#     a = region_label.find_next("a")
#     if a:
#         txt = a.get_text(" ", strip=True)
#         return txt or None

#     nxt = region_label.find_next(string=True)
#     if nxt:
#         txt = str(nxt).strip()
#         return txt or None

#     return None


# def _extract_skills(soup: BeautifulSoup) -> list[str]:
#     skills: list[str] = []
#     for a in soup.select('a[href^="/remote-jobs/search?term="]'):
#         txt = a.get_text(" ", strip=True)
#         if txt:
#             skills.append(txt)

#     uniq: list[str] = []
#     seen: set[str] = set()
#     for skill in skills:
#         key = skill.lower()
#         if key in seen:
#             continue
#         seen.add(key)
#         uniq.append(skill)
#     return uniq


# def _extract_salary_from_text(full_text: str) -> str | None:
#     for line in full_text.splitlines():
#         if re.search(r"salary", line, re.I) and "$" in line:
#             cleaned = re.sub(r"\s+", " ", line).strip(" -•\t")
#             if cleaned:
#                 return cleaned

#     match = re.search(r"(\$[\d,]+\s*[-–]\s*\$?[\d,]+)", full_text)
#     if match:
#         return match.group(1).strip()

#     return None


# def _extract_description(soup: BeautifulSoup) -> str | None:
#     h1 = soup.find("h1")
#     if not h1:
#         return None

#     parts: list[str] = []
#     node = h1

#     for _ in range(2000):
#         node = node.find_next()
#         if node is None:
#             break

#         if node.name in ("h2", "h3"):
#             t = node.get_text(" ", strip=True).lower()
#             if t in ("apply now", "meet jobcopilot: your personal ai job hunter"):
#                 break

#         if node.name in ("p", "li", "h2", "h3", "h4"):
#             txt = node.get_text(" ", strip=True)
#             if txt:
#                 parts.append(txt)

#     text = "\n".join(parts).strip()
#     return text or None


# def parse_job(job_url: str, job_html: str) -> dict[str, Any]:
#     soup = BeautifulSoup(job_html, "html.parser")

#     title = soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else None

#     company = _find_company_from_view_company_block(soup)
#     if not company:
#         for a in soup.select('a[href^="http"]'):
#             href = a.get("href", "")
#             txt = a.get_text(" ", strip=True)
#             if not txt:
#                 continue
#             if "weworkremotely.com" in href:
#                 continue
#             if txt.lower() in ("apply now", "apply"):
#                 continue
#             company = txt
#             break

#     location = _find_region_as_location(soup)
#     skills = _extract_skills(soup)
#     description = _extract_description(soup)
#     full_text = soup.get_text("\n", strip=True)
#     salary_text = _extract_salary_from_text(full_text)

#     return {
#         "source": "wwr",
#         "external_id": job_url,
#         "title": title,
#         "company": company,
#         "location": location,
#         "description": description,
#         "url": job_url,
#         "posted_at": None,
#         "fetched_at": None,
#         "salary_from": None,
#         "salary_to": None,
#         "currency": None,
#         "salary_text": salary_text,
#         "skills": skills,
#         "raw_payload": {
#             "url": job_url,
#             "title": title,
#             "company": company,
#             "location": location,
#             "salary_text": salary_text,
#             "skills": skills,
#             "description": description,
#         },
#     }


# def collect_wwr_vacancies(
#     query_text: str,
#     limit_total: int = 80,
#     user_agent: str = "MentorAI-AirflowBot/1.0",
# ) -> list[dict[str, Any]]:
#     client = httpx.Client(
#         headers={
#             "User-Agent": user_agent,
#             "Accept-Language": "en-US,en;q=0.9",
#         },
#         timeout=25,
#     )

#     search_url = f"{BASE}/remote-jobs/search?term={quote_plus(query_text)}"
#     search_html = fetch_html(client, search_url)
#     _sleep()

#     job_links = parse_search_job_links(search_html)
#     out: list[dict[str, Any]] = []

#     for url in job_links[:limit_total]:
#         try:
#             html = fetch_html(client, url)
#             _sleep()
#             out.append(parse_job(url, html))
#         except Exception:
#             continue

#     return out