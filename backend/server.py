from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os
import logging
import requests
import json
from pathlib import Path
from datetime import datetime, timezone
from models.chat import ChatRequest, ChatResponse
from rag.init_rag import RAGSystem
from db import init_db, upsert_session, insert_message, fetch_analytics, fetch_analytics_sessions
from ipaddress import ip_address


# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize RAG System
rag_system = None
openrouter_key = os.environ.get('OPENROUTER_API_KEY')

# Simple in-memory cache for IP -> geo lookups
_GEO_CACHE: dict[str, dict] = {}


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ip_address(ip)
        return any([
            addr.is_private,
            addr.is_loopback,
            addr.is_link_local,
        ])
    except Exception:
        return True


def _parse_xff(xff: str) -> list[str]:
    parts = [p.strip() for p in (xff or "").split(",")]
    ips: list[str] = []
    for p in parts:
        try:
            ip_address(p)
            ips.append(p)
        except Exception:
            continue
    return ips

def _extract_client_ip(req: Request) -> str | None:
    """Extract the most likely real client IP from common proxy/CDN headers.
    Priority order: CF-Connecting-IP, True-Client-IP, X-Real-IP, Fly-Client-IP, first public in X-Forwarded-For, fallback to req.client.host
    """
    h = req.headers
    for key in ["cf-connecting-ip", "true-client-ip", "x-real-ip", "fly-client-ip"]:
        val = h.get(key)
        if val:
            return val
    # X-Forwarded-For may contain multiple IPs. Take the first public one.
    xff = h.get("x-forwarded-for")
    if xff:
        for ip in _parse_xff(xff):
            try:
                if not _is_private_ip(ip):
                    return ip
            except Exception:
                continue
        # if none public, fall back to first
        ips = _parse_xff(xff)
        if ips:
            return ips[0]
    return req.client.host if req.client else None

def _geo_from_ip(ip: str) -> dict | None:
    """Best-effort geolocation for an IP using ipapi.co by default, ipinfo (token), and ipwho.is as fallback.
    Returns dict with keys: country, region, city, lat, lon, timezone, asn, org, isp (where available).
    """
    if not ip or _is_private_ip(ip):
        return None
    if ip in _GEO_CACHE:
        return _GEO_CACHE[ip]

    provider = os.environ.get('GEOIP_PROVIDER', 'ipapi').lower()
    try:
        if provider == 'ipinfo':
            token = os.environ.get('GEOIP_TOKEN')
            url = f"https://ipinfo.io/{ip}/json"
            params = {"token": token} if token else {}
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                d = r.json() or {}
                loc = d.get('loc') or ''
                lat, lon = (loc.split(',') + [None, None])[:2]
                res = {
                    'country': d.get('country'),
                    'region': d.get('region'),
                    'city': d.get('city'),
                    'lat': float(lat) if lat else None,
                    'lon': float(lon) if lon else None,
                    'timezone': d.get('timezone'),
                    'asn': (d.get('asn') or {}).get('asn') if isinstance(d.get('asn'), dict) else None,
                    'org': d.get('org'),
                    'isp': d.get('org'),
                }
                _GEO_CACHE[ip] = res
                return res
        # default: ipapi.co (no token required, free tier limits)
        url = f"https://ipapi.co/{ip}/json/"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            d = r.json() or {}
            res = {
                'country': d.get('country_name') or d.get('country'),
                'region': d.get('region'),
                'city': d.get('city'),
                'lat': d.get('latitude'),
                'lon': d.get('longitude'),
                'timezone': d.get('timezone'),
                'asn': d.get('asn'),
                'org': d.get('org'),
                'isp': d.get('org'),
            }
            # Normalize numeric
            try:
                res['lat'] = float(res['lat']) if res['lat'] is not None else None
                res['lon'] = float(res['lon']) if res['lon'] is not None else None
            except Exception:
                pass
            _GEO_CACHE[ip] = res
            return res
        # Fallback: ipwho.is
        url = f"https://ipwho.is/{ip}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            d = r.json() or {}
            if d.get('success') is True:
                conn = d.get('connection') or {}
                res = {
                    'country': d.get('country'),
                    'region': d.get('region'),
                    'city': d.get('city'),
                    'lat': d.get('latitude'),
                    'lon': d.get('longitude'),
                    'timezone': (d.get('timezone') or {}).get('id') if isinstance(d.get('timezone'), dict) else d.get('timezone'),
                    'asn': conn.get('asn'),
                    'org': conn.get('org'),
                    'isp': conn.get('isp') or conn.get('org'),
                }
                try:
                    res['lat'] = float(res['lat']) if res['lat'] is not None else None
                    res['lon'] = float(res['lon']) if res['lon'] is not None else None
                except Exception:
                    pass
                _GEO_CACHE[ip] = res
                return res
            else:
                logger.warning(f"ipwho.is lookup unsuccessful for {ip}: {d}")
    except Exception as e:
        logger.warning(f"GeoIP lookup failed for {ip}: {e}")
    return None

try:
    # Initialize DB first
    db_path = init_db()
    logging.info(f"App DB initialized at: {db_path}")
    # Override model via env if desired
    model_name = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-oss-20b:free')
    rag_system = RAGSystem(openrouter_api_key=openrouter_key, model_name=model_name)
    data_dir = ROOT_DIR / 'data'
    rag_system.initialize(str(data_dir))
    logging.info(f"RAG system initialized successfully with model: {model_name}")
except Exception as e:
    logging.error(f"Failed to initialize systems: {e}")
    rag_system = None

# Create the main app without a prefix
app = FastAPI(redirect_slashes=False)

# Middleware to normalize trailing slashes (e.g., /api/chat/ -> /api/chat)
class StripTrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if len(path) > 1 and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
        return await call_next(request)

app.add_middleware(StripTrailingSlashMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api", redirect_slashes=False)

# Health check endpoint (no trailing slash path)
@api_router.get("")
async def root():
    return {"message": "Portfolio API is running", "status": "healthy"}

# Download resume
@api_router.get("/resume")
async def download_resume():
    resume_path = ROOT_DIR / 'data' / 'resume.pdf'
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(
        path=str(resume_path),
        filename="resume.pdf",
        media_type="application/pdf",
    )

# Chat endpoints
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request):
    """Chat with AI assistant about Tejas's portfolio"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized. Please check OPENROUTER_API_KEY.")
    
    # Respect Do Not Track if explicitly set
    dnt_header = raw_request.headers.get("DNT")
    dnt = True if dnt_header == "1" else (request.meta.dnt if request.meta and request.meta.dnt is not None else False)

    # Upsert session row with metadata
    try:
        client_host = _extract_client_ip(raw_request)
        # Geolocation headers (may be provided by some CDNs/proxies)
        geo_country = raw_request.headers.get("cf-ipcountry") or raw_request.headers.get("x-country")
        # Extended IP and network metadata placeholder — fill if your edge sets these headers
        net_asn = raw_request.headers.get("x-asn")
        net_org = raw_request.headers.get("x-as-org") or raw_request.headers.get("x-org")
        net_isp = raw_request.headers.get("x-isp")

        # If we have a public IP and no client-provided precise geo, try server-side IP geolocation
        precise_geo = {
            'lat': request.meta.geo_lat if request.meta else None,
            'lon': request.meta.geo_lon if request.meta else None,
            'country': request.meta.geo_country if request.meta else None,
            'region': request.meta.geo_region if request.meta else None,
            'city': request.meta.geo_city if request.meta else None,
        }
        geo_from_ip = None
        if client_host and not precise_geo['lat'] and not _is_private_ip(client_host):
            geo_from_ip = _geo_from_ip(client_host)

        ua = request.meta.user_agent if request.meta else raw_request.headers.get("User-Agent")
        upsert_session(
            session_id=request.session_id,
            visitor_id=request.meta.visitor_id if request.meta else None,
            ip=client_host,
            user_agent=ua,
            locale=request.meta.locale if request.meta else None,
            timezone_s=request.meta.timezone if request.meta else None,
            referrer=request.meta.referrer if request.meta else None,
            page_url=request.meta.page_url if request.meta else None,
            dnt=dnt,
            # Browser network hints
            net_effective_type=request.meta.net_effective_type if request.meta else None,
            net_downlink=request.meta.net_downlink if request.meta else None,
            net_rtt=request.meta.net_rtt if request.meta else None,
            net_save_data=request.meta.net_save_data if request.meta else None,
            device_memory=request.meta.device_memory if request.meta else None,
            # Geo/IP enrichment: prefer client-provided precise location if available, else headers
            ip_plain=client_host,
            geo_country=(precise_geo['country'] or (geo_from_ip or {}).get('country') or geo_country),
            geo_region=(precise_geo['region'] or (geo_from_ip or {}).get('region')),
            geo_city=(precise_geo['city'] or (geo_from_ip or {}).get('city')),
            geo_lat=(precise_geo['lat'] or (geo_from_ip or {}).get('lat')),
            geo_lon=(precise_geo['lon'] or (geo_from_ip or {}).get('lon')),
            geo_timezone=(request.meta.timezone if request.meta else (geo_from_ip or {}).get('timezone')),
            net_asn=(net_asn or (geo_from_ip or {}).get('asn')),
            net_org=(net_org or (geo_from_ip or {}).get('org')),
            net_isp=(net_isp or (geo_from_ip or {}).get('isp')),
        )
    except Exception as e:
        logger.warning(f"Session upsert failed: {e}")

    start = datetime.now(timezone.utc)
    try:
        # Log user message
        insert_message(
            session_id=request.session_id,
            role="user",
            content=request.message,
            timestamp=start.isoformat(),
            message_len=len(request.message or ""),
        )

        response_text = rag_system.chat(request.message, request.session_id)

        end = datetime.now(timezone.utc)
        duration_ms = int((end - start).total_seconds() * 1000)

        # Extract diagnostics from agent
        diags = rag_system.agent.get_last_diagnostics(request.session_id) if rag_system and rag_system.agent else {}
        retrieved_sources = diags.get("retrieved_sources")
        context_chars = diags.get("context_chars")
        missing_info = diags.get("missing_info")

        # Store response_len and model name
        model_name = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-oss-20b:free')

        insert_message(
            session_id=request.session_id,
            role="assistant",
            content=response_text,
            timestamp=end.isoformat(),
            response_len=len(response_text or ""),
            model_name=model_name,
            server_duration_ms=duration_ms,
            missing_info=missing_info,
            retrieved_sources=retrieved_sources,
            context_chars=context_chars,
        )

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=end
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    
    try:
        history = rag_system.get_history(session_id)
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

@api_router.get("/debug/geo")
async def debug_geo(ip: str):
    """Debug endpoint to test server-side geolocation."""
    try:
        res = _geo_from_ip(ip)
        return {"ip": ip, "geo": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geo debug failed: {e}")

@api_router.get("/debug/openrouter")
async def debug_openrouter():
    """Call OpenRouter with the configured model and return raw response."""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3.1:free')
    key = os.environ.get('OPENROUTER_API_KEY')
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if os.environ.get("OPENROUTER_SITE_URL"):
        headers["HTTP-Referer"] = os.environ["OPENROUTER_SITE_URL"]
    if os.environ.get("OPENROUTER_APP_NAME"):
        headers["X-Title"] = os.environ["OPENROUTER_APP_NAME"]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello from /debug/openrouter"},
        ],
        "max_tokens": 50,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        return {
            "model": model,
            "status": resp.status_code,
            "api_url": url,
            "raw": resp.text[:2000],
        }
    except Exception as e:
        logger.error(f"OpenRouter debug failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenRouter debug failed: {e}")

# RAG management endpoints
@api_router.post("/rag/reindex")
async def rag_reindex():
    """Force reindex of the data directory."""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    try:
        data_dir = ROOT_DIR / 'data'
        rag_system.reindex(str(data_dir))
        return {"status": "reindexed", "summary": rag_system.get_sources_summary()}
    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Error reindexing: {str(e)}")

@api_router.get("/rag/sources")
async def rag_sources():
    """Summary of indexed sources"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    try:
        return rag_system.get_sources_summary()
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sources: {str(e)}")

@api_router.get("/analytics/download")
async def download_analytics(days: int = 30, limit: int = 1000, format: str = "jsonl"):
    """Download analytics with only visitor_id, IP, location, and duration per session.
    - format=jsonl: NDJSON (one JSON object per line)
    - format=csv: simple CSV
    """
    try:
        rows = fetch_analytics_sessions(days=days, limit=limit)

        if format == "csv":
            import csv
            from io import StringIO
            buf = StringIO()
            writer = csv.writer(buf)
            header = [
                "session_id", "visitor_id", "ip", "country", "region", "city", "lat", "lon", "duration_seconds", "updated_at"
            ]
            writer.writerow(header)
            for r in rows:
                writer.writerow([
                    r.get("session_id"), r.get("visitor_id"), r.get("ip_plain"), r.get("geo_country"), r.get("geo_region"), r.get("geo_city"),
                    r.get("geo_lat"), r.get("geo_lon"), r.get("duration_seconds"), r.get("updated_at")
                ])
            buf.seek(0)
            filename = f"analytics_{days}d_sessions.csv"
            return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
        else:
            from io import StringIO
            buf = StringIO()
            for r in rows:
                # Emit only the requested fields
                out = {
                    "session_id": r.get("session_id"),
                    "visitor_id": r.get("visitor_id"),
                    "ip": r.get("ip_plain"),
                    "country": r.get("geo_country"),
                    "region": r.get("geo_region"),
                    "city": r.get("geo_city"),
                    "lat": r.get("geo_lat"),
                    "lon": r.get("geo_lon"),
                    "duration_seconds": r.get("duration_seconds"),
                    "updated_at": r.get("updated_at"),
                }
                buf.write(json.dumps(out, ensure_ascii=False) + "\n")
            buf.seek(0)
            filename = f"analytics_{days}d_sessions.jsonl"
            return StreamingResponse(buf, media_type="application/x-ndjson", headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        logger.error(f"Error generating analytics download: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {e}")

# Simple root OK route
@app.get("/")
def root_ok():
    return {"status": "ok"}

# Include the router in the main app
app.include_router(api_router)

_origins_raw = os.environ.get('CORS_ORIGINS', '')
_origins = [o.strip() for o in _origins_raw.split(',') if o.strip()]
if not _origins:
    _origins = ["*"]
_allow_creds = False if "*" in _origins else True

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No shutdown hooks required currently
