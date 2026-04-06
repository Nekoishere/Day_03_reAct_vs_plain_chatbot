import os
from openai import OpenAI

_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _web_search(query: str) -> str:
    """Use OpenAI web_search_preview to fetch real-time football data."""
    try:
        response = _get_client().responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=query,
        )
        return response.output_text
    except Exception as e:
        return f"Search error: {e}"


# ===========================================================================
# Group 1 — Live Match Data
# ===========================================================================

def get_live_scores() -> str:
    """Get all currently live football match scores. No arguments needed."""
    return _web_search("football live scores right now today all leagues")


def get_league_scores(league_name: str) -> str:
    """
    Get today's scores for a specific league.
    Arg: league_name (e.g. Premier League, La Liga, Champions League)
    """
    return _web_search(f"{league_name} scores today fixtures results")


# ===========================================================================
# Group 2 — Team Info
# ===========================================================================

def get_team_form(team_name: str) -> str:
    """
    Get a team's last 5 match results and current form streak.
    Arg: team_name (e.g. Arsenal, Barcelona)
    """
    return _web_search(f"{team_name} last 5 results form streak win loss draw 2026")


def get_team_season_record(team_name: str, season: str) -> str:
    """
    Get a team's season record: wins, draws, losses, goals for/against.
    Args: team_name (e.g. Manchester City), season (e.g. 2025/2026)
    """
    return _web_search(f"{team_name} season record {season} wins draws losses goals")


def get_head_to_head(team1: str, team2: str) -> str:
    """
    Get head-to-head history between two teams.
    Args: team1 (e.g. Arsenal), team2 (e.g. Chelsea)
    """
    return _web_search(f"{team1} vs {team2} head to head history recent meetings results")


# ===========================================================================
# Group 3 — Player Info
# ===========================================================================

def get_top_scorers(league_name: str, season: str) -> str:
    """
    Get the top scorers (golden boot race) for a league season.
    Args: league_name (e.g. Premier League), season (e.g. 2025/2026)
    """
    return _web_search(f"{league_name} top scorers golden boot {season} season goals")


def get_player_stats(player_name: str, season: str) -> str:
    """
    Get individual stats for a player: goals, assists, minutes played.
    Args: player_name (e.g. Mohamed Salah), season (e.g. 2025/2026)
    """
    return _web_search(f"{player_name} stats {season} goals assists appearances minutes")


def get_injury_report(team_name: str) -> str:
    """
    Get current injury and suspension list for a team.
    Arg: team_name (e.g. Liverpool, Real Madrid)
    """
    return _web_search(f"{team_name} injury report suspension list 2026 latest")


# ===========================================================================
# Group 4 — Competition Info
# ===========================================================================

def get_league_standings(league_name: str, season: str) -> str:
    """
    Get the current league table / standings.
    Args: league_name (e.g. Premier League), season (e.g. 2025/2026)
    """
    return _web_search(f"{league_name} standings table {season} season points")


def get_next_fixture(team_name: str) -> str:
    """
    Get the next upcoming match for a team: date, opponent, competition.
    Arg: team_name (e.g. Liverpool, Bayern Munich)
    """
    return _web_search(f"{team_name} next match fixture date opponent 2026")


def get_match_lineup(team_name: str) -> str:
    """
    Get the latest or upcoming starting lineup and formation for a team.
    Arg: team_name (e.g. Real Madrid, Manchester United)
    """
    return _web_search(f"{team_name} lineup today starting XI formation 2026")


def get_match_result(team1: str, team2: str, date: str) -> str:
    """
    Get the result of a specific match between two teams on a given date.
    Args: team1 (e.g. Manchester United), team2 (e.g. West Ham), date (e.g. 5/12/2025 or December 5 2025)
    """
    return _web_search(f"{team1} vs {team2} result score {date}")


# ===========================================================================
# Tool registry (used by ReAct agent)
# ===========================================================================

FOOTBALL_TOOLS = [
    # --- Live ---
    {
        "name": "get_live_scores",
        "description": "Get all currently live football match scores. No arguments needed.",
        "func": get_live_scores,
        "args_schema": [],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_league_scores",
        "description": "Get today's scores for a specific league.",
        "func": get_league_scores,
        "args_schema": ["league_name"],
        "parameters": {
            "type": "object",
            "properties": {
                "league_name": {"type": "string", "description": "League name, e.g. Premier League, La Liga, Champions League"},
            },
            "required": ["league_name"],
        },
    },
    # --- Team ---
    {
        "name": "get_team_form",
        "description": "Get a team's last 5 results and current form streak.",
        "func": get_team_form,
        "args_schema": ["team_name"],
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string", "description": "Team name, e.g. Arsenal, Barcelona"},
            },
            "required": ["team_name"],
        },
    },
    {
        "name": "get_team_season_record",
        "description": "Get a team's season record: wins, draws, losses, goals for/against.",
        "func": get_team_season_record,
        "args_schema": ["team_name", "season"],
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string", "description": "Team name, e.g. Manchester City"},
                "season":    {"type": "string", "description": "Season in YYYY/YYYY format, e.g. 2025/2026"},
            },
            "required": ["team_name", "season"],
        },
    },
    {
        "name": "get_head_to_head",
        "description": "Get head-to-head history between two teams.",
        "func": get_head_to_head,
        "args_schema": ["team1", "team2"],
        "parameters": {
            "type": "object",
            "properties": {
                "team1": {"type": "string", "description": "First team name, e.g. Arsenal"},
                "team2": {"type": "string", "description": "Second team name, e.g. Chelsea"},
            },
            "required": ["team1", "team2"],
        },
    },
    # --- Player ---
    {
        "name": "get_top_scorers",
        "description": "Get the top scorers (golden boot race) for a league season.",
        "func": get_top_scorers,
        "args_schema": ["league_name", "season"],
        "parameters": {
            "type": "object",
            "properties": {
                "league_name": {"type": "string", "description": "League name, e.g. Premier League"},
                "season":      {"type": "string", "description": "Season in YYYY/YYYY format, e.g. 2025/2026"},
            },
            "required": ["league_name", "season"],
        },
    },
    {
        "name": "get_player_stats",
        "description": "Get individual stats for a player: goals, assists, minutes played.",
        "func": get_player_stats,
        "args_schema": ["player_name", "season"],
        "parameters": {
            "type": "object",
            "properties": {
                "player_name": {"type": "string", "description": "Player full name, e.g. Mohamed Salah"},
                "season":      {"type": "string", "description": "Season in YYYY/YYYY format, e.g. 2025/2026"},
            },
            "required": ["player_name", "season"],
        },
    },
    {
        "name": "get_injury_report",
        "description": "Get current injury and suspension list for a team.",
        "func": get_injury_report,
        "args_schema": ["team_name"],
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string", "description": "Team name, e.g. Liverpool"},
            },
            "required": ["team_name"],
        },
    },
    # --- Competition ---
    {
        "name": "get_league_standings",
        "description": "Get the current league table and standings.",
        "func": get_league_standings,
        "args_schema": ["league_name", "season"],
        "parameters": {
            "type": "object",
            "properties": {
                "league_name": {"type": "string", "description": "League name, e.g. Premier League"},
                "season":      {"type": "string", "description": "Season in YYYY/YYYY format, e.g. 2025/2026"},
            },
            "required": ["league_name", "season"],
        },
    },
    {
        "name": "get_next_fixture",
        "description": "Get the next upcoming match for a team: date, opponent, competition.",
        "func": get_next_fixture,
        "args_schema": ["team_name"],
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string", "description": "Team name, e.g. Liverpool"},
            },
            "required": ["team_name"],
        },
    },
    {
        "name": "get_match_lineup",
        "description": "Get the latest starting lineup and formation for a team.",
        "func": get_match_lineup,
        "args_schema": ["team_name"],
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string", "description": "Team name, e.g. Real Madrid"},
            },
            "required": ["team_name"],
        },
    },
    {
        "name": "get_match_result",
        "description": "Get the result of a specific match between two teams on a given date.",
        "func": get_match_result,
        "args_schema": ["team1", "team2", "date"],
        "parameters": {
            "type": "object",
            "properties": {
                "team1": {"type": "string", "description": "First team name, e.g. Manchester United"},
                "team2": {"type": "string", "description": "Second team name, e.g. West Ham"},
                "date":  {"type": "string", "description": "Match date, e.g. 5/12/2025 or December 5 2025"},
            },
            "required": ["team1", "team2", "date"],
        },
    },
]
