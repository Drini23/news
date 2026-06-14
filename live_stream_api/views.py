import requests
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from football.settings import FOOTBALL_LIVE_STREAMING_API


def live_matches(request):
    url = "https://football-live-streaming-api.p.rapidapi.com/matches"
    headers = {
        "x-rapidapi-key": FOOTBALL_LIVE_STREAMING_API,
        "x-rapidapi-host": "football-live-streaming-api.p.rapidapi.com"
    }

    matches = []
    page = 1  

    while True:
        querystring = {"page": str(page), "status": "live"}
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code != 200:
            break  

        data = response.json()
        current_page_matches = data.get("matches", [])

        if not current_page_matches:
            break  

        # process matches
        for match in current_page_matches:
            servers = match.get("servers", [])
            stream_servers = [
                {
                    "name": server.get("name", "Unknown Server"),
                    "url": server.get("url")
                }
                for server in servers if server.get("url")
            ]

            matches.append({
                "home_team": match.get("home_team_name"),
                "away_team": match.get("away_team_name"),
                "league": match.get("league_name"),
                "stream_servers": stream_servers,
                "home_team_logo": match.get("home_team_logo"),
                "away_team_logo": match.get("away_team_logo"),
                "status": match.get("match.status")

            })

        page += 1  

    return render(request, "live_stream_api/live_matches.html", {"matches": matches})


@csrf_exempt
@require_http_methods(["GET"])
def stream_proxy(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponse('No URL provided', status=400)

    from urllib.parse import urlparse, urljoin

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',
            'Origin': None,  # Remove origin to avoid blocking
            'Referer': None,  # Remove referer to avoid blocking
            'Connection': 'keep-alive',
        }
        
        # For some streaming servers, we need to pass through authentication
        if 'rapidapi' in url:
            headers['x-rapidapi-key'] = FOOTBALL_LIVE_STREAMING_API

        response = requests.get(url, stream=True, timeout=30, headers=headers, verify=True)
        
        # Check if stream is accessible
        if response.status_code != 200:
            return HttpResponse(f'Stream unavailable (HTTP {response.status_code})', status=response.status_code)
        
        content_type = response.headers.get('content-type', 'application/vnd.apple.mpegurl')

        # Handle HLS playlists
        if '.m3u8' in url or 'mpegurl' in content_type or 'application/x-mpegURL' in content_type:
            try:
                content = response.content.decode('utf-8', errors='ignore')
                
                # Check if it's a valid HLS manifest
                if not content.startswith('#EXTM3U'):
                    # Not a valid HLS, return as is
                    return StreamingHttpResponse(iter([response.content]), content_type=content_type)

                lines = content.split('\n')
                modified_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        # Keep comments and empty lines as-is
                        modified_lines.append(line)
                        continue
                    
                    # This is a URL or segment path
                    parsed_line = urlparse(line)
                    
                    # Check if it's already an absolute URL
                    if parsed_line.scheme:
                        # Absolute URL - proxy it through our proxy
                        proxied_url = request.build_absolute_uri(f'/stream-proxy/?url={line}')
                        modified_lines.append(proxied_url)
                    else:
                        # Relative URL - resolve against the base URL
                        base_url = url.rsplit('/', 1)[0]
                        absolute_url = urljoin(base_url + '/', line)
                        proxied_url = request.build_absolute_uri(f'/stream-proxy/?url={absolute_url}')
                        modified_lines.append(proxied_url)
                
                modified_content = '\n'.join(modified_lines)
                return HttpResponse(modified_content, content_type='application/vnd.apple.mpegurl')
                
            except UnicodeDecodeError:
                # Binary content, stream directly
                return StreamingHttpResponse(response.iter_content(chunk_size=8192), content_type=content_type)

        # For non-HLS streams (mp4, webm, etc.)
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        streaming_response = StreamingHttpResponse(generate(), content_type=content_type)
        
        # Copy relevant headers
        for header in ['Content-Length', 'Content-Range', 'Accept-Ranges', 'Cache-Control']:
            if header in response.headers:
                streaming_response[header] = response.headers[header]
                
        return streaming_response

    except requests.exceptions.Timeout:
        return HttpResponse('Stream timeout - server not responding', status=504)
    except requests.exceptions.ConnectionError:
        return HttpResponse('Cannot connect to stream server', status=502)
    except requests.exceptions.RequestException as e:
        return HttpResponse(f'Error fetching stream: {str(e)}', status=500)
    except Exception as e:
        return HttpResponse(f'Unexpected error: {str(e)}', status=500)