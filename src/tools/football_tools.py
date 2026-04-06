import os
from openai import OpenAI

_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _web_search(query: str) -> str:
    """
    Use OpenAI's web_search_preview tool to get real-time information.
    Returns the response text from the search-enabled model.
    """
    try:
        response = _get_client().responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=query,
        )
        return response.output_text
    except Exception as e:
        return f"Search error: {e}"


# ---------------------------------------------------------------------------
# Tool 1: Live scores
# ---------------------------------------------------------------------------
def get_live_scores() -> str:
    """
    Get all currently live football match scores. No arguments needed.
    """
    return _web_search("football live scores right now today all leagues")


# ---------------------------------------------------------------------------
# Tool 2: Scores for a specific league today
# ---------------------------------------------------------------------------
def get_league_scores(league_name: str) -> str:
    """
    Get today's match scores for a specific league.
    Arg: league_name (e.g. 'Premier League', 'La Liga', 'Champions League')
    """
    return _web_search(f"{league_name} scores today fixtures results")


# ---------------------------------------------------------------------------
# Tool 3: Top scorers
# ---------------------------------------------------------------------------
def get_top_scorers(league_name: str, season: str) -> str:
    """
    Get top scorers for a league in a given season.
    Args: league_name (e.g. 'Premier League'), season (e.g. '2025' or '2025/2026')
    """
    return _web_search(f"{league_name} top scorers golden boot {season} season")


# ---------------------------------------------------------------------------
# Tool 4: Recent results for a team
# ---------------------------------------------------------------------------
def get_team_results(team_name: str) -> str:
    """
    Get recent match results for a football team.
    Arg: team_name (e.g. 'Manchester United', 'Barcelona')
    """
    return _web_search(f"{team_name} recent match results last 5 games")


# ---------------------------------------------------------------------------
# Tool 5: Team season statistics
# ---------------------------------------------------------------------------
def get_team_statistics(team_name: str, season: str) -> str:
    """
    Get season statistics for a football team.
    Args: team_name (e.g. 'Arsenal'), season (e.g. '2025' or '2025/2026')
    """
    return _web_search(f"{team_name} season statistics {season} wins losses goals")


# ---------------------------------------------------------------------------
# Tool 6: Match lineup
# ---------------------------------------------------------------------------
def get_match_lineup(team_name: str) -> str:
    """
    Get the latest or upcoming match lineup for a team.
    Arg: team_name (e.g. 'Real Madrid', 'Liverpool')
    """
    return _web_search(f"{team_name} lineup today starting XI formation")


# ---------------------------------------------------------------------------
# Tool 7: League standings
# ---------------------------------------------------------------------------
def get_league_standings(league_name: str, season: str) -> str:
    """
    Get the current league table / standings.
    Args: league_name (e.g. 'Premier League'), season (e.g. '2025')
    """
    return _web_search(f"{league_name} standings table {season} season points")


# ---------------------------------------------------------------------------
# Tool registry (used by ReAct agent)
# ---------------------------------------------------------------------------
FOOTBALL_TOOLS = [
    {
        "name": "get_live_scores",
        "description": "Get all currently live football match scores. No arguments needed.",
        "func": get_live_scores,
        "args_schema": [],
    },
    {
        "name": "get_league_scores",
        "description": "Get today's scores for a specific league. Arg: league_name (e.g. Premier League, La Liga, Champions League).",
        "func": get_league_scores,
        "args_schema": ["league_name"],
    },
    {
        "name": "get_top_scorers",
        "description": "Get top scorers for a league season. Args: league_name (e.g. Premier League), season (e.g. 2025).",
        "func": get_top_scorers,
        "args_schema": ["league_name", "season"],
    },
    {
        "name": "get_team_results",
        "description": "Get recent match results for a team. Arg: team_name (e.g. Manchester United).",
        "func": get_team_results,
        "args_schema": ["team_name"],
    },
    {
        "name": "get_team_statistics",
        "description": "Get season stats for a team. Args: team_name (e.g. Barcelona), season (e.g. 2025).",
        "func": get_team_statistics,
        "args_schema": ["team_name", "season"],
    },
    {
        "name": "get_match_lineup",
        "description": "Get the latest lineup for a team. Arg: team_name (e.g. Arsenal).",
        "func": get_match_lineup,
        "args_schema": ["team_name"],
    },
    {
        "name": "get_league_standings",
        "description": "Get league table/standings. Args: league_name (e.g. Premier League), season (e.g. 2025).",
        "func": get_league_standings,
        "args_schema": ["league_name", "season"],
    },
]
