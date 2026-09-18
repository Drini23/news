import requests
from django.shortcuts import render
from football.settings import S_ALL_SPORT_API
from functools import lru_cache

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.shortcuts import render


BASE_URL = "https://all-sport-live-stream.p.rapidapi.com"


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


def all_sport_api(request):
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

    print(f"[all_sport_api] Done. {len(matches)} live matches ready.")
    print("=" * 60)

    return render(request, "rapid/all_sport_api.html", {"matches": matches})


def highlights(request):
    return render(request, 'rapid/highlights.html')




import requests
from django.shortcuts import render
from django.http import JsonResponse

API_KEY = "ff182b108amshf8e8d9cb53258dbp193014jsn90d493c12420"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "football-live-stream-api.p.rapidapi.com",
}


def new_api(request):

    url = "https://football-live-stream-api.p.rapidapi.com/all-match"

    matches = []

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        print("STATUS:", response.status_code)

        data = response.json()

        print("API RESPONSE:", data)

        if response.status_code == 200:

            for match in data.get("result", []):

                matches.append({
                    "id": match.get("id"),
                    "home_name": match.get("home_name", "Unknown"),
                    "away_name": match.get("away_name", "Unknown"),
                    "score": match.get("score", "0 - 0"),
                    "status": match.get("status", "N/A"),
                })

    except requests.exceptions.RequestException as e:

        print("API ERROR:", e)

    return render(request, "rapid/new_api.html", {
        "matches": matches
    })
    
    
    
import base64

def get_stream(request, match_id):

    url = f"https://football-live-stream-api.p.rapidapi.com/link/{match_id}"

    response = requests.get(url, headers=HEADERS)
    data = response.json()

    raw = data.get("url")

    # extract base64 part
    try:
        encoded = raw.split("url=")[1]
        decoded_url = base64.b64decode(encoded).decode("utf-8")

    except:
        decoded_url = raw

    return render(request, "rapid/player.html", {
        "stream_url": decoded_url
    })