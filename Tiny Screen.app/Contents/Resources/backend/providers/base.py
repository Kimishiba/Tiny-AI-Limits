import os
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

def read_sqlite_kv_safe(db_path: str, table: str, key_col: str, val_col: str, key_val: str) -> Optional[str]:
    """Safe read-only key-value query for SQLite databases (e.g. Cursor state.vscdb).
    Uses SQLite URI read-only mode and guarantees connection closure to prevent resource leaks."""
    if not db_path or not os.path.exists(db_path):
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
