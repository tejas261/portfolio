import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

_DB_PATH: Optional[str] = None


def init_db(db_path: Optional[str] = None) -> str:
    """Initialize a SQLite database with sessions and messages tables.
    Returns the absolute DB path in use.
    """
    global _DB_PATH
    if not db_path:
        db_path = os.environ.get("APP_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "app.db"))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _DB_PATH = db_path

    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                visitor_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ip_hash TEXT,
                ip_plain TEXT,
                user_agent TEXT,
                locale TEXT,
                timezone TEXT,
                referrer TEXT,
                page_url TEXT,
                dnt INTEGER,
                -- Browser-provided network hints
                net_effective_type TEXT,
                net_downlink REAL,
                net_rtt INTEGER,
                net_save_data INTEGER,
                device_memory REAL,
                -- Geo/IP provider enrichment
                geo_country TEXT,
                geo_region TEXT,
                geo_city TEXT,
                geo_lat REAL,
                geo_lon REAL,
                geo_timezone TEXT,
                net_asn TEXT,
                net_org TEXT,
                net_isp TEXT
            );
            """
        )
        # Backward-compatible migrations: add columns if missing
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(sessions);")
        existing_cols = {row[1] for row in cur.fetchall()}
        def add_col(name: str, decl: str):
            if name not in existing_cols:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {name} {decl};")
        add_col("ip_plain", "TEXT")
        add_col("net_effective_type", "TEXT")
        add_col("net_downlink", "REAL")
        add_col("net_rtt", "INTEGER")
        add_col("net_save_data", "INTEGER")
        add_col("device_memory", "REAL")
        add_col("geo_country", "TEXT")
        add_col("geo_region", "TEXT")
        add_col("geo_city", "TEXT")
        add_col("geo_lat", "REAL")
        add_col("geo_lon", "REAL")
        add_col("geo_timezone", "TEXT")
        add_col("net_asn", "TEXT")
        add_col("net_org", "TEXT")
        add_col("net_isp", "TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message_len INTEGER,
                response_len INTEGER,
                model_name TEXT,
                server_duration_ms INTEGER,
                missing_info INTEGER,
                retrieved_sources TEXT,
                context_chars INTEGER,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_time ON messages(session_id, timestamp);")
    return _DB_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn() -> sqlite3.Connection:
    if not _DB_PATH:
        init_db()
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def sha256_hex(value: str) -> str:
    salt = os.environ.get("ANALYTICS_SALT", "")
    hasher = hashlib.sha256()
    hasher.update((value + salt).encode("utf-8"))
    return hasher.hexdigest()


def upsert_session(
    session_id: str,
    visitor_id: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    locale: Optional[str] = None,
    timezone_s: Optional[str] = None,
    referrer: Optional[str] = None,
    page_url: Optional[str] = None,
    dnt: Optional[bool] = None,
    # Browser network hints
    net_effective_type: Optional[str] = None,
    net_downlink: Optional[float] = None,
    net_rtt: Optional[int] = None,
    net_save_data: Optional[bool] = None,
    device_memory: Optional[float] = None,
    # Geo/IP enrichment
    ip_plain: Optional[str] = None,
    geo_country: Optional[str] = None,
    geo_region: Optional[str] = None,
    geo_city: Optional[str] = None,
    geo_lat: Optional[float] = None,
    geo_lon: Optional[float] = None,
    geo_timezone: Optional[str] = None,
    net_asn: Optional[str] = None,
    net_org: Optional[str] = None,
    net_isp: Optional[str] = None,
) -> None:
    now = _now_iso()
    ip_hash = sha256_hex(ip) if ip else None
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT session_id FROM sessions WHERE session_id=?", (session_id,))
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO sessions (
                    session_id, visitor_id, created_at, updated_at, ip_hash, ip_plain, user_agent, locale, timezone, referrer, page_url, dnt,
                    net_effective_type, net_downlink, net_rtt, net_save_data, device_memory,
                    geo_country, geo_region, geo_city, geo_lat, geo_lon, geo_timezone, net_asn, net_org, net_isp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    visitor_id,
                    now,
                    now,
                    ip_hash,
                    ip_plain or ip,
                    user_agent,
                    locale,
                    timezone_s,
                    referrer,
                    page_url,
                    1 if dnt else 0 if dnt is not None else None,
                    net_effective_type,
                    net_downlink,
                    net_rtt,
                    1 if net_save_data else 0 if net_save_data is not None else None,
                    device_memory,
                    geo_country,
                    geo_region,
                    geo_city,
                    geo_lat,
                    geo_lon,
                    geo_timezone,
                    net_asn,
                    net_org,
                    net_isp,
                ),
            )
        else:
            cur.execute(
                """
                UPDATE sessions
                SET updated_at=?, visitor_id=COALESCE(?, visitor_id), ip_hash=COALESCE(?, ip_hash), ip_plain=COALESCE(?, ip_plain),
                    user_agent=COALESCE(?, user_agent), locale=COALESCE(?, locale), timezone=COALESCE(?, timezone),
                    referrer=COALESCE(?, referrer), page_url=COALESCE(?, page_url), dnt=COALESCE(?, dnt),
                    net_effective_type=COALESCE(?, net_effective_type), net_downlink=COALESCE(?, net_downlink), net_rtt=COALESCE(?, net_rtt),
                    net_save_data=COALESCE(?, net_save_data), device_memory=COALESCE(?, device_memory),
                    geo_country=COALESCE(?, geo_country), geo_region=COALESCE(?, geo_region), geo_city=COALESCE(?, geo_city),
                    geo_lat=COALESCE(?, geo_lat), geo_lon=COALESCE(?, geo_lon), geo_timezone=COALESCE(?, geo_timezone),
                    net_asn=COALESCE(?, net_asn), net_org=COALESCE(?, net_org), net_isp=COALESCE(?, net_isp)
                WHERE session_id=?
                """,
                (
                    now,
                    visitor_id,
                    ip_hash,
                    ip_plain or ip,
                    user_agent,
                    locale,
                    timezone_s,
                    referrer,
                    page_url,
                    1 if dnt else 0 if dnt is not None else None,
                    net_effective_type,
                    net_downlink,
                    net_rtt,
                    1 if net_save_data else 0 if net_save_data is not None else None,
                    device_memory,
                    geo_country,
                    geo_region,
                    geo_city,
                    geo_lat,
                    geo_lon,
                    geo_timezone,
                    net_asn,
                    net_org,
                    net_isp,
                    session_id,
                ),
            )
        conn.commit()


def insert_message(
    session_id: str,
    role: str,
    content: str,
    timestamp: Optional[str] = None,
    message_len: Optional[int] = None,
    response_len: Optional[int] = None,
    model_name: Optional[str] = None,
    server_duration_ms: Optional[int] = None,
    missing_info: Optional[bool] = None,
    retrieved_sources: Optional[List[str]] = None,
    context_chars: Optional[int] = None,
) -> int:
    ts = timestamp or _now_iso()
    sources_json = json.dumps(retrieved_sources) if isinstance(retrieved_sources, list) else None
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (
                session_id, role, content, timestamp, message_len, response_len, model_name, server_duration_ms, missing_info, retrieved_sources, context_chars
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                ts,
                message_len,
                response_len,
                model_name,
                server_duration_ms,
                1 if missing_info else 0 if missing_info is not None else None,
                sources_json,
                context_chars,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def fetch_history(session_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id=? ORDER BY id ASC",
            (session_id,),
        )
        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]


def fetch_analytics(days: Optional[int] = 30, limit: Optional[int] = 5000) -> List[Dict[str, Any]]:
    """Return flattened analytics rows joining messages with session metadata.
    days: number of days back from now to include (None for all)
    limit: max number of rows (None for all)
    """
    since_iso = None
    if days is not None:
        since_dt = datetime.now(timezone.utc) - timedelta(days=days)
        since_iso = since_dt.isoformat()

    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = (
            "SELECT m.timestamp, m.session_id, s.visitor_id, m.role, m.content, "
            "m.message_len, m.response_len, m.model_name, m.server_duration_ms, "
            "m.missing_info, m.retrieved_sources, m.context_chars, "
            "s.user_agent, s.locale, s.timezone, s.referrer, s.page_url, s.dnt, s.ip_plain, s.ip_hash, "
            "s.geo_country, s.geo_region, s.geo_city, s.geo_lat, s.geo_lon, s.geo_timezone, s.net_asn, s.net_org, s.net_isp, "
            "s.net_effective_type, s.net_downlink, s.net_rtt, s.net_save_data, s.device_memory "
            "FROM messages m LEFT JOIN sessions s ON m.session_id = s.session_id "
        )
        params: List[Any] = []
        if since_iso:
            sql += "WHERE m.timestamp >= ? "
            params.append(since_iso)
        sql += "ORDER BY m.timestamp DESC "
        if limit is not None:
            sql += "LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            # Normalize retrieved_sources to list
            try:
                if d.get("retrieved_sources"):
                    d["retrieved_sources"] = json.loads(d["retrieved_sources"]) if isinstance(d["retrieved_sources"], str) else d["retrieved_sources"]
            except Exception:
                pass
            out.append(d)
        return out


def fetch_analytics_sessions(days: Optional[int] = 30, limit: Optional[int] = 1000) -> List[Dict[str, Any]]:
    """Return per-session analytics: visitor_id, ip, location, duration.
    duration_seconds = updated_at - created_at
    """
    since_iso = None
    if days is not None:
        since_dt = datetime.now(timezone.utc) - timedelta(days=days)
        since_iso = since_dt.isoformat()
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = (
            "SELECT session_id, visitor_id, ip_plain, geo_country, geo_region, geo_city, geo_lat, geo_lon, "
            "created_at, updated_at, ROUND((julianday(updated_at) - julianday(created_at)) * 86400, 0) AS duration_seconds "
            "FROM sessions "
        )
        params: List[Any] = []
        if since_iso:
            sql += "WHERE updated_at >= ? "
            params.append(since_iso)
        sql += "ORDER BY updated_at DESC "
        if limit is not None:
            sql += "LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
