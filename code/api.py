import logging
import os
from pathlib import Path
from typing import Generator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services import coach_commands, db, endorsement_policy, rate_limit
from services.analytics_queries import (
    get_club_comparison,
    get_club_profile,
    get_club_rankings,
    get_homepage_data,
    get_pool_results,
    get_tournaments,
)
from services.coach_queries import get_coach_directory, get_coach_profile, get_director_queue
from services.view_models import compute_profile_strength, serialize_data_state

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler(LOG_DIR / "api.log"))

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Cache-busting version for static assets: the stylesheet/JS URLs get `?v=<mtime>`
# so a changed file is fetched fresh instead of served from a stale browser cache
# (Safari in particular over-caches CSS that lacks a cache-control header).
try:
    ASSET_VERSION = str(int((BASE_DIR / "static" / "css" / "club_analytics.css").stat().st_mtime))
except OSError:
    ASSET_VERSION = "1"
templates.env.globals["asset_v"] = ASSET_VERSION


def fetch_with_connection(func, *args, **kwargs):
    """Read shim (PR-1): borrow a pooled read connection and run ``func(conn, ...)``.

    Reads go through ``db.read_conn`` (never commits); writes use ``db.write_conn``.
    """
    with db.read_conn() as conn:
        return func(conn, *args, **kwargs)


def create_app() -> FastAPI:
    app = FastAPI(title="NTVS Volleyball")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/api/home")
    def api_home(tournament_id: str | None = None):
        data = fetch_with_connection(get_homepage_data, tournament_id)
        data["data_state"] = serialize_data_state(
            data.get("featured_pools", []),
            partial=not bool(data.get("featured_tournament")),
            message="Homepage analytics loaded." if data.get("featured_tournament") else "No tournament data is available.",
        )
        logger.info("api_home tournament_id=%s state=%s", tournament_id, data["data_state"]["completeness"])
        return data

    @app.get("/api/pool-results")
    def api_pool_results(
        tournament_id: str | None = None,
        age_group: str | None = None,
        division: str | None = None,
        club_name: str | None = None,
    ):
        data = fetch_with_connection(get_pool_results, tournament_id, age_group, division, club_name)
        logger.info(
            "api_pool_results tournament_id=%s age_group=%s division=%s club_name=%s state=%s",
            tournament_id,
            age_group,
            division,
            club_name,
            data["data_state"]["completeness"],
        )
        return data

    @app.get("/api/clubs")
    def api_clubs(q: str | None = None, sort: str = "rank", division: str | None = None):
        clubs = fetch_with_connection(get_club_rankings, q, sort, division)
        state = serialize_data_state(clubs)
        logger.info("api_clubs q=%s sort=%s division=%s state=%s", q, sort, division, state["completeness"])
        return {"clubs": clubs, "data_state": state}

    @app.get("/api/clubs/compare")
    def api_club_compare(club_a: str = Query(...), club_b: str = Query(...)):
        comparison = fetch_with_connection(get_club_comparison, club_a, club_b)
        logger.info(
            "api_club_compare club_a=%s club_b=%s state=%s",
            club_a,
            club_b,
            comparison["data_state"]["completeness"],
        )
        return comparison

    @app.get("/api/clubs/{club_key}")
    def api_club_profile(club_key: str):
        profile = fetch_with_connection(get_club_profile, club_key)
        if not profile["teams"]:
            raise HTTPException(status_code=404, detail="Club not found")
        has_data = bool(profile["recent_matchups"]) or bool(profile["recent_bracket_matchups"])
        state = serialize_data_state(profile["teams"], partial=not has_data)
        logger.info("api_club_profile club_key=%s state=%s", club_key, state["completeness"])
        profile["data_state"] = state
        return profile

    @app.get("/", response_class=HTMLResponse)
    def home_page(request: Request, tournament_id: str | None = None):
        data = api_home(tournament_id)
        return templates.TemplateResponse("home.html", {"request": request, **data})

    @app.get("/pool-results", response_class=HTMLResponse)
    def pool_results_page(
        request: Request,
        tournament_id: str | None = None,
        age_group: str | None = None,
        division: str | None = None,
        club_name: str | None = None,
    ):
        data = api_pool_results(tournament_id, age_group, division, club_name)
        return templates.TemplateResponse("saturday_pool_results.html", {"request": request, **data})

    @app.get("/clubs", response_class=HTMLResponse)
    def clubs_page(request: Request, q: str | None = None, sort: str = "rank", division: str | None = None):
        data = api_clubs(q, sort, division)
        data["query"] = {"q": q or "", "sort": sort, "division": division or ""}
        return templates.TemplateResponse("club_rankings.html", {"request": request, **data})

    @app.get("/clubs/{club_key}", response_class=HTMLResponse)
    def club_profile_page(request: Request, club_key: str, team: str | None = Query(None)):
        profile = api_club_profile(club_key)
        selected_team_data = profile["team_seasons"].get(team) if team else None
        return templates.TemplateResponse("club_profile.html", {
            "request": request, **profile,
            "selected_team": team,
            "selected_team_data": selected_team_data,
        })

    @app.get("/compare", response_class=HTMLResponse)
    def compare_page(request: Request, club_a: str | None = None, club_b: str | None = None):
        clubs = api_clubs()
        comparison = None
        if club_a and club_b:
            comparison = api_club_compare(club_a, club_b)
        return templates.TemplateResponse(
            "club_comparison.html",
            {
                "request": request,
                "club_options": clubs["clubs"],
                "comparison": comparison,
                "club_a": club_a or "",
                "club_b": club_b or "",
            },
        )

    @app.get("/api/coaches")
    def api_coaches(q: str | None = None, verified_only: bool = False):
        coaches = fetch_with_connection(get_coach_directory, q, verified_only)
        state = serialize_data_state(
            coaches,
            message="No coaches match your search." if not coaches else "Coaches loaded.",
        )
        logger.info("api_coaches q=%s verified_only=%s state=%s", q, verified_only, state["completeness"])
        return {"coaches": coaches, "data_state": state}

    @app.get("/api/coaches/{coach_key}")
    def api_coach_profile(coach_key: str):
        profile = fetch_with_connection(get_coach_profile, coach_key)
        if profile is None:
            raise HTTPException(status_code=404, detail="Coach not found")
        logger.info("api_coach_profile coach_key=%s state=%s", coach_key, profile["data_state"]["completeness"])
        return profile

    @app.post("/api/coaches/{coach_key}/endorsements")
    async def api_add_endorsement(coach_key: str, request: Request):
        data = await request.json()
        client_ip = request.client.host if request.client else None
        # Production write gating (PR-3/FR-035): no-op when NTVS_WRITE_GATING is off.
        if rate_limit.is_honeypot_tripped(data.get("website")):
            logger.info("api_add_endorsement coach=%s rejected=honeypot", coach_key)
            return JSONResponse(status_code=429, content={"error": "honeypot", "message": "Submission blocked."})
        if not rate_limit.check_rate_limit(client_ip):
            logger.info("api_add_endorsement coach=%s rejected=rate_limited", coach_key)
            return JSONResponse(status_code=429, content={"error": "rate_limited", "message": "Too many submissions — please wait a bit."})

        author_label = (data.get("author_label") or "").strip()
        relationship = (data.get("relationship") or "").strip()
        body = (data.get("body") or "").strip()
        tags = data.get("tags") or []
        if relationship not in endorsement_policy.RELATIONSHIPS or not body:
            return JSONResponse(status_code=422, content={"error": "invalid", "message": "A relationship and a short note are required."})
        if not author_label:
            author_label = relationship

        try:
            stars, body = endorsement_policy.check_endorsement(data.get("stars"), body)
        except endorsement_policy.PolicyError as exc:
            logger.info("api_add_endorsement coach=%s rejected=%s", coach_key, exc.code)
            return JSONResponse(status_code=422, content={"error": exc.code, "message": exc.message})

        result = coach_commands.add_endorsement(coach_key, author_label, relationship, stars, list(tags), body)
        if result is None:
            raise HTTPException(status_code=404, detail="Coach not found")
        logger.info("api_add_endorsement coach=%s applied=%s", coach_key, result["applied"])
        return JSONResponse(status_code=201, content=result["endorsement"])

    @app.post("/api/coaches/{coach_key}/positions")
    async def api_add_position(coach_key: str, request: Request):
        data = await request.json()
        client_ip = request.client.host if request.client else None
        if rate_limit.is_honeypot_tripped(data.get("website")):
            return JSONResponse(status_code=429, content={"error": "honeypot", "message": "Submission blocked."})
        if not rate_limit.check_rate_limit(client_ip):
            return JSONResponse(status_code=429, content={"error": "rate_limited", "message": "Too many submissions — please wait a bit."})
        club_label = (data.get("club_label") or "").strip()
        role = (data.get("role") or "").strip()
        if not club_label or not role:
            return JSONResponse(status_code=422, content={"error": "invalid", "message": "Club and role are required."})
        result = coach_commands.add_position(
            coach_key, club_label, role,
            age_group=(data.get("age_group") or "").strip() or None,
            years=(data.get("years") or "").strip() or None,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Coach not found")
        logger.info("api_add_position coach=%s applied=%s", coach_key, result["applied"])
        return JSONResponse(status_code=201, content=result["position"])

    @app.delete("/api/coaches/{coach_key}/positions/{position_id}")
    def api_delete_position(coach_key: str, position_id: int):
        result = coach_commands.delete_position(coach_key, position_id)
        if not result["removed"] and result["reason"] == "verified":
            return JSONResponse(status_code=409, content={"error": "verified", "message": "Verified positions can't be removed."})
        logger.info("api_delete_position coach=%s position=%s reason=%s", coach_key, position_id, result["reason"])
        return Response(status_code=204)

    @app.post("/api/coaches/{coach_key}/verification-requests")
    async def api_create_verification_request(coach_key: str, request: Request):
        data = await request.json()
        client_ip = request.client.host if request.client else None
        if rate_limit.is_honeypot_tripped(data.get("website")):
            return JSONResponse(status_code=429, content={"error": "honeypot", "message": "Submission blocked."})
        if not rate_limit.check_rate_limit(client_ip):
            return JSONResponse(status_code=429, content={"error": "rate_limited", "message": "Too many submissions — please wait a bit."})
        club_key = (data.get("club_key") or "").strip()
        if not club_key:
            return JSONResponse(status_code=422, content={"error": "invalid", "message": "A club is required."})
        result = coach_commands.create_verification_request(
            coach_key, club_key,
            position_id=data.get("position_id"),
            note=(data.get("note") or "").strip() or None,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Coach not found")
        logger.info("api_create_verification_request coach=%s club=%s applied=%s", coach_key, club_key, result["applied"])
        return JSONResponse(status_code=201, content=result)

    @app.get("/api/director/requests")
    def api_director_requests(club_key: str | None = None):
        data = fetch_with_connection(get_director_queue, club_key)
        logger.info("api_director_requests club=%s pending=%s state=%s", data["club_key"], data["stats"]["pending"], data["data_state"]["completeness"])
        return data

    @app.post("/api/director/requests/{request_id}/resolve")
    async def api_resolve_request(request_id: int, request: Request):
        data = await request.json()
        decision = (data.get("decision") or "").strip()
        if decision not in ("approve", "deny"):
            return JSONResponse(status_code=422, content={"error": "invalid", "message": "decision must be 'approve' or 'deny'."})
        token = request.headers.get("X-Director-Token") or data.get("director_token")
        result = coach_commands.resolve_request(request_id, decision, token=token)
        if result.get("error") == "unauthorized":
            return JSONResponse(status_code=403, content={"error": "missing_director_token", "message": "A valid director token is required to resolve requests."})
        logger.info("api_resolve_request request=%s decision=%s applied=%s", request_id, decision, result["applied"])
        return JSONResponse(status_code=200, content={"request_id": result["request_id"], "status": result["status"], "applied": result["applied"]})

    @app.get("/coaches", response_class=HTMLResponse)
    def coaches_page(request: Request, q: str | None = None, verified_only: bool = False):
        data = api_coaches(q, verified_only)
        data["query"] = {"q": q or "", "verified_only": verified_only}
        return templates.TemplateResponse("coaches_directory.html", {"request": request, **data})

    @app.get("/coaches/{coach_key}", response_class=HTMLResponse)
    def coach_profile_page(request: Request, coach_key: str):
        profile = api_coach_profile(coach_key)
        return templates.TemplateResponse("coach_profile.html", {"request": request, **profile})

    @app.get("/coaches/{coach_key}/edit", response_class=HTMLResponse)
    def coach_editor_page(request: Request, coach_key: str):
        profile = api_coach_profile(coach_key)
        profile["profile_strength"] = compute_profile_strength(len(profile["career"]), bool(profile["about"]))
        club_options = [c["display_name"] for c in fetch_with_connection(get_club_rankings, None, "rank", None)]
        return templates.TemplateResponse("coach_editor.html", {"request": request, **profile, "club_options": club_options})

    @app.get("/director", response_class=HTMLResponse)
    def director_page(request: Request, club_key: str | None = None):
        data = fetch_with_connection(get_director_queue, club_key)
        return templates.TemplateResponse("director.html", {"request": request, **data})

    @app.get("/tournaments")
    def read_tournaments():
        return fetch_with_connection(get_tournaments)

    @app.get("/tournaments/{tournament_id}")
    def read_tournament(tournament_id: str):
        tournaments = fetch_with_connection(get_tournaments)
        result = next((t for t in tournaments if t["tournament_id"] == tournament_id), None)
        if result is None:
            raise HTTPException(status_code=404, detail="Tournament not found")
        return result

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
