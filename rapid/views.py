from football.settings import S_ALL_SPORT_API
from functools import lru_cache
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.shortcuts import render
from django.core.cache import cache          # ← NEW
from index.decorators import paywall
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import base64


BASE_URL = "https://all-sport-live-stream.p.rapidapi.com"

# ---------- Cache config for all_sport_api ----------
ALL_SPORT_CACHE_KEY = "all_sport_api:live_matches"
ALL_SPORT_CACHE_TTL = 60 * 2   # 2 minutes — tune as needed


def fetch_stream(gmid, headers):
    """Fetch one stream URL. Returns (gmid, url_or_None)."""
    try:
        r = requests.get(
            f"{BASE_URL}/api/d/stream_source",
            headers=headers,
            params={"gmid": str(gmid)},
            timeout=15
        )
        if r.status_code != 200:
            print(f"[stream] gmid={gmid} HTTP {r.status_code} -> {r.text[:120]}")
            return gmid, None

        data = r.json()

        # Try every shape we've seen
        url = None
        if data.get("status") == "success" and "data" in data:
            url = (data.get("data") or {}).get("source")
        if not url:
            url = data.get("stream_url")
        if not url:
            url = data.get("url")

        print(f"[stream] gmid={gmid} -> {url}")
        return gmid, url

    except Exception as e:
        print(f"[stream] gmid={gmid} ERROR: {e}")
        return gmid, None


@login_required(login_url='login')
@paywall
def all_sport_api(request):
    # ---------- 0. Try cache first ----------
    cached_matches = cache.get(ALL_SPORT_CACHE_KEY)
    if cached_matches is not None:
        print(f"[all_sport_api] Cache HIT ({len(cached_matches)} matches)")
        return render(request, "rapid/all_sport_api.html", {"matches": cached_matches})

    print("[all_sport_api] Cache MISS — hitting API")

    headers = {
        "x-rapidapi-key": S_ALL_SPORT_API,
        "x-rapidapi-host": "all-sport-live-stream.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    print("=" * 60)
    print("[all_sport_api] REQUEST 1: fetching /esid ...")

    # ---------- REQUEST 1: match list ----------
    list_response = requests.get(
        f"{BASE_URL}/esid",
        headers=headers,
        params={"sid": "1"},
        timeout=15
    )

    print(f"[all_sport_api] /esid status: {list_response.status_code}")

    if list_response.status_code != 200:
        print(f"[all_sport_api] /esid failed: {list_response.text}")
        # Do NOT cache failures — let next request retry
        return render(request, "rapid/all_sport_api.html", {"matches": []})

    data = (list_response.json() or {}).get("data") or {}
    match_items = data.get("t1") or []

    # Filter live matches only
    live_matches = [m for m in match_items if m.get("iplay") and m.get("gmid")]
    print(f"[all_sport_api] {len(match_items)} matches, {len(live_matches)} live")

    # ---------- REQUEST 2: all stream URLs, in parallel ----------
    print("[all_sport_api] REQUEST 2: fetching all stream sources in parallel ...")

    stream_map = {}   # gmid -> url
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(fetch_stream, m["gmid"], headers): m["gmid"]
            for m in live_matches
        }
        for fut in as_completed(futures):
            gmid, url = fut.result()
            stream_map[gmid] = url

    # ---------- Build result list ----------
    matches = []
    for m in live_matches:
        matches.append({
            "teams_name": m.get("ename", "Unknown"),
            "team_two":   m.get("cname", ""),
            "score":      m.get("sc", "vs"),
            "start_time": m.get("stime", "Live"),
            "iframe_source": stream_map.get(m.get("gmid")),
            "m3u8_source": None,
        })

    # ---------- 3. Store in Redis cache ----------
    cache.set(ALL_SPORT_CACHE_KEY, matches, ALL_SPORT_CACHE_TTL)
    print(f"[all_sport_api] Cached {len(matches)} matches for {ALL_SPORT_CACHE_TTL}s")

    print(f"[all_sport_api] Done. {len(matches)} live matches ready.")
    print("=" * 60)

    return render(request, "rapid/all_sport_api.html", {"matches": matches})


def highlights(request):
    return render(request, 'rapid/highlights.html')



API_KEY = S_ALL_SPORT_API

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "football-live-stream-api.p.rapidapi.com",
}


def new_api(request):
    url = "https://football-live-stream-api.p.rapidapi.com/all-match"

    matches = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print("STATUS:", response.status_code)

        data = response.json()

        if response.status_code == 200:
            result = data.get("result", [])

            # ---- Debug: print keys of the first match once ----
            if result:
                print("=" * 60)
                print("FIRST MATCH KEYS:", list(result[0].keys()))
                print("FIRST MATCH:", result[0])
                print("=" * 60)

            for match in result:
                match_id = match.get("id")
                raw_status = match.get("status", "N/A") or "N/A"
                status = raw_status.strip().upper()   # "Live" -> "LIVE"

                print(
                    "MATCH:",
                    match.get("home_name"),
                    "vs",
                    match.get("away_name"),
                    "| ID:", match_id,
                    "| RAW:", raw_status,
                    "| NORM:", status,
                )

                matches.append({
                    "id":          match_id,

                    # Teams
                    "home_name":   match.get("home_name", "Unknown"),
                    "away_name":   match.get("away_name", "Unknown"),
                    "home_flag":   match.get("home_flag", ""),
                    "away_flag":   match.get("away_flag", ""),

                    # League / competition
                    "league": (
                        match.get("league")
                        or match.get("league_name")
                        or match.get("competition")
                        or match.get("tournament")
                        or ""
                    ),

                    # Date / time
                    "date":        match.get("date", ""),
                    "time":        match.get("time", ""),
                    "kickoff":     match.get("kickoff", ""),

                    # Score / status
                    "score":       match.get("score", "0 - 0"),
                    "status":      status,
                    "raw_status":  raw_status,
                })

    except requests.exceptions.RequestException as e:
        print("API ERROR:", e)

    return render(request, "rapid/new_api.html", {"matches": matches})


def get_stream(request, match_id):
    print("=" * 60)
    print("GET_STREAM CALLED WITH ID:", match_id)
    print("=" * 60)

    url = f"https://football-live-stream-api.p.rapidapi.com/link/{match_id}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print("STREAM STATUS:", response.status_code)
        print("STREAM RAW TEXT:", response.text)

        data = response.json()
        stream_url = (data.get("url") or "").strip()

        # --- No stream available: render the player page in "error" mode ---
        if not stream_url:
            print("NO STREAM URL — rendering error state")
            return render(request, "rapid/player.html", {
                "stream_url": None,
                "error": "Ky transmetim nuk është i disponueshëm për momentin.",
                "match_id": match_id,
            })

        print("FINAL STREAM URL:", stream_url)

        return render(request, "rapid/player.html", {
            "stream_url": stream_url,
            "error": None,
            "match_id": match_id,
        })

    except Exception as e:
        print("STREAM ERROR:", e)
        return render(request, "rapid/player.html", {
            "stream_url": None,
            "error": f"Gabim gjatë ngarkimit: {e}",
            "match_id": match_id,
        })