import os
import re
import json
import sqlite3
import time
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple

@dataclass
class RateWindow:
    limit: int = 100
    used: int = 0
    remaining: int = 100
    percent_left: float = 100.0
    resets_at: Optional[str] = None
    window_minutes: Optional[int] = None
    period_desc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class UsageSnapshot:
    provider_id: str
    provider_name: str
    badge: str = ""
    color: str = "0x00E5FF"
    primary_window: Optional[RateWindow] = None
    secondary_window: Optional[RateWindow] = None
    model_windows: Dict[str, RateWindow] = field(default_factory=dict)
    credits: Optional[Dict[str, Any]] = None
    plan: Optional[str] = None
    account_email: Optional[str] = None
    status: str = "ok"  # "ok" | "degraded" | "unauthenticated" | "error" | "unconfigured"
    error_message: Optional[str] = None
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.primary_window:
            d["primary_window"] = self.primary_window.to_dict()
        if self.secondary_window:
            d["secondary_window"] = self.secondary_window.to_dict()
        if self.model_windows:
            d["model_windows"] = {k: v.to_dict() for k, v in self.model_windows.items()}
        return d

def get_home_dir() -> str:
    return os.path.expanduser("~")

def resolve_app_data_path(relative_path: str, app_name: str = "") -> Optional[str]:
    """Resolves standard application configuration/data paths across macOS, Linux, Windows."""
    home = get_home_dir()
    candidates = []

    # macOS Library
    candidates.append(os.path.join(home, "Library", "Application Support", app_name, relative_path))

    # Linux / XDG
    xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.join(home, ".config"))
    candidates.append(os.path.join(xdg_config, app_name, relative_path))
    candidates.append(os.path.join(home, f".{app_name.lower()}", relative_path))

    # Windows AppData
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(os.path.join(appdata, app_name, relative_path))
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidates.append(os.path.join(localappdata, app_name, relative_path))

    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

import logging

logger = logging.getLogger("tinyscreen.providers")

VALID_SQL_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")

def read_sqlite_kv_safe(db_path: str, table: str, key_col: str, val_col: str, key_val: str) -> Optional[str]:
    """Safe read-only key-value query for SQLite databases (e.g. Cursor state.vscdb).
    Uses SQLite URI read-only mode and guarantees connection closure to prevent resource leaks."""
    if not db_path or not os.path.exists(db_path):
        return None
    for identifier in (table, key_col, val_col):
        if not identifier or not VALID_SQL_IDENTIFIER.match(identifier):
            logger.warning("Invalid SQL identifier rejected: %s", identifier)
            return None
    conn = None
    try:
        abs_path = os.path.abspath(db_path)
        uri = f"file:{abs_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        cursor = conn.cursor()
        query = f"SELECT {val_col} FROM {table} WHERE {key_col} = ? LIMIT 1"
        cursor.execute(query, (key_val,))
        row = cursor.fetchone()
        return str(row[0]) if row and row[0] is not None else None
    except sqlite3.OperationalError as e:
        logger.debug("Operational error reading SQLite DB %s: %s", db_path, e)
        return None
    except Exception as e:
        logger.debug("Failed reading SQLite DB %s: %s", db_path, e)
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

class BaseProvider(ABC):
    provider_id: str = "base"
    provider_name: str = "Base Provider"
    badge: str = "GEN"
    color: str = "0x00E5FF"
    ttl_seconds: int = 120

    @abstractmethod
    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        """Fetches quota/allowance snapshot."""
        pass

    def request_json(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 6.0,
        account_email: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[UsageSnapshot]]:
        """Standardized JSON request helper with honest User-Agent, error handling, and status mapping."""
        req_headers = {
            "Accept": "application/json",
            "User-Agent": "TinyAILimits/1.0 (ESP32-Companion; +https://github.com/Kimishiba/Tiny-AI-Limits)",
        }
        if headers:
            req_headers.update(headers)

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                json=json_data,
                params=params,
                timeout=timeout
            )

            if resp.status_code in (401, 403):
                return None, UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    account_email=account_email,
                    status="unauthenticated",
                    error_message=f"HTTP {resp.status_code}: Authentication expired or invalid"
                )

            if resp.status_code == 429:
                return None, UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    account_email=account_email,
                    primary_window=RateWindow(limit=100, used=100, remaining=0, percent_left=0.0, period_desc="rate-limited"),
                    status="degraded",
                    error_message="HTTP 429: Rate limit exhausted"
                )

            if resp.status_code not in (200, 201):
                return None, UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    account_email=account_email,
                    status="error",
                    error_message=f"HTTP {resp.status_code}: {resp.text[:120]}"
                )

            return resp.json(), None

        except requests.exceptions.Timeout:
            logger.debug("[%s] Request to %s timed out", self.provider_id, url)
            return None, UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                account_email=account_email,
                status="degraded",
                error_message="Network request timed out"
            )
        except requests.exceptions.RequestException as e:
            logger.debug("[%s] Network error connecting to %s: %s", self.provider_id, url, e)
            return None, UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                account_email=account_email,
                status="error",
                error_message=str(e)
            )
        except Exception as e:
            logger.warning("[%s] Unexpected error processing request to %s: %s", self.provider_id, url, e)
            return None, UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                account_email=account_email,
                status="error",
                error_message=str(e)
            )


class GenericHttpProvider(BaseProvider):
    """Declarative base class for providers that perform a single JSON HTTP GET request."""
    token_key: str = ""
    env_var: str = ""
    url: str = ""
    auth_header_format: str = "Bearer {}"

    def get_token(self, config: Dict[str, Any]) -> Optional[str]:
        token = config.get(self.token_key)
        if token:
            return str(token).strip()
        if self.env_var:
            env_val = os.environ.get(self.env_var)
            if env_val:
                return str(env_val).strip()
        return None

    def parse_payload(self, data: Dict[str, Any]) -> UsageSnapshot:
        raise NotImplementedError("Subclasses must implement parse_payload")

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = self.get_token(config)
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unconfigured",
                error_message=f"No {self.token_key} found in config or {self.env_var} env"
            )

        # Control-character validation to prevent header injection
        if any(c in token for c in ("\r", "\n")):
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="error",
                error_message="Configuration error: Token contains invalid control characters"
            )

        def _scrub(msg: Any) -> str:
            raw = str(msg)
            if token and token in raw:
                raw = raw.replace(token, "[REDACTED]")
            return raw

        headers = {
            "Authorization": self.auth_header_format.format(token)
        }
        data, err = self.request_json("GET", self.url, headers)
        if err:
            if isinstance(err, UsageSnapshot):
                if err.error_message and token and token in err.error_message:
                    err.error_message = err.error_message.replace(token, "[REDACTED]")
                return err
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="error",
                error_message=_scrub(err)
            )

        try:
            return self.parse_payload(data)
        except Exception as e:
            logger.warning("[%s] Failed to parse API payload: %s", self.provider_id, _scrub(e))
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="error",
                error_message=_scrub(e)
            )

