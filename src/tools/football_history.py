from typing import List, Dict, Any


FOOTBALL_EVENTS = [
    {"year": 2010, "competition": "World Cup", "champion": "Spain", "runner_up": "Netherlands", "result": "1-0"},
    {"year": 2014, "competition": "World Cup", "champion": "Germany", "runner_up": "Argentina", "result": "1-0"},
    {"year": 2018, "competition": "World Cup", "champion": "France", "runner_up": "Croatia", "result": "4-2"},
    {"year": 2022, "competition": "World Cup", "champion": "Argentina", "runner_up": "France", "result": "3-3 (4-2 pens)"},
    {"year": 2012, "competition": "Euro", "champion": "Spain", "runner_up": "Italy", "result": "4-0"},
    {"year": 2016, "competition": "Euro", "champion": "Portugal", "runner_up": "France", "result": "1-0"},
    {"year": 2020, "competition": "Euro", "champion": "Italy", "runner_up": "England", "result": "1-1 (3-2 pens)"},
    {"year": 2024, "competition": "Euro", "champion": "Spain", "runner_up": "England", "result": "2-1"},
    {"year": 2019, "competition": "Champions League", "champion": "Liverpool", "runner_up": "Tottenham", "result": "2-0"},
    {"year": 2020, "competition": "Champions League", "champion": "Bayern Munich", "runner_up": "PSG", "result": "1-0"},
    {"year": 2021, "competition": "Champions League", "champion": "Chelsea", "runner_up": "Manchester City", "result": "1-0"},
    {"year": 2022, "competition": "Champions League", "champion": "Real Madrid", "runner_up": "Liverpool", "result": "1-0"},
    {"year": 2023, "competition": "Champions League", "champion": "Manchester City", "runner_up": "Inter Milan", "result": "1-0"},
    {"year": 2024, "competition": "Champions League", "champion": "Real Madrid", "runner_up": "Borussia Dortmund", "result": "2-0"},
]


def _normalize(value: str) -> str:
    return value.lower().strip()


def _format_event(event: Dict[str, Any]) -> str:
    return (
        f"{event['year']} {event['competition']}: "
        f"{event['champion']} beat {event['runner_up']} ({event['result']})"
    )


def search_football_history(query: str) -> str:
    query = _normalize(query)
    terms = [term for term in query.split() if term]

    if not terms:
        matches = FOOTBALL_EVENTS[:5]
    else:
        matches = []
        for event in FOOTBALL_EVENTS:
            searchable = _normalize(
                f"{event['year']} {event['competition']} {event['champion']} {event['runner_up']} {event['result']}"
            )
            if all(term in searchable for term in terms):
                matches.append(event)

    if not matches:
        return "No matching football history found in local tool dataset."

    return "\n".join(_format_event(event) for event in matches[:5])


def world_cup_champion_by_year(year_text: str) -> str:
    year_text = year_text.strip()
    if not year_text.isdigit():
        return "Please provide a numeric year, for example: 2018."

    year = int(year_text)
    for event in FOOTBALL_EVENTS:
        if event["competition"] == "World Cup" and event["year"] == year:
            return _format_event(event)
    return f"No World Cup final data found for {year} in local dataset."


def team_major_titles(team_name: str) -> str:
    team = _normalize(team_name)
    if not team:
        return "Please provide a team name."

    wins = [event for event in FOOTBALL_EVENTS if _normalize(event["champion"]) == team]
    if not wins:
        return f"{team_name} has no title entry in local dataset."

    grouped = {}
    for event in wins:
        grouped[event["competition"]] = grouped.get(event["competition"], 0) + 1

    parts = [f"{competition}: {count}" for competition, count in sorted(grouped.items())]
    return f"{team_name} titles in local dataset -> " + ", ".join(parts)


def get_football_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "search_football_history",
            "description": "Search football finals by year, tournament, team, or score keywords.",
            "func": search_football_history,
        },
        {
            "name": "world_cup_champion_by_year",
            "description": "Get World Cup final result by year. Input should be one year, e.g. 2018.",
            "func": world_cup_champion_by_year,
        },
        {
            "name": "team_major_titles",
            "description": "Count major titles in the local dataset for one team.",
            "func": team_major_titles,
        },
    ]
