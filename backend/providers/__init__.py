import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from .base import BaseProvider, UsageSnapshot, RateWindow
from .antigravity import AntigravityProvider
from .claude import ClaudeProvider
from .codex import CodexProvider
from .cursor import CursorProvider
from .copilot import CopilotProvider
from .gemini import GeminiProvider
from .openrouter import OpenRouterProvider
from .deepseek import DeepSeekProvider
from .mistral import MistralProvider
from .groq import GroqProvider

ALL_PROVIDERS: List[BaseProvider] = [
    AntigravityProvider(),
    ClaudeProvider(),
    CodexProvider(),
    CursorProvider(),
    CopilotProvider(),
    GeminiProvider(),
    OpenRouterProvider(),
    DeepSeekProvider(),
    MistralProvider(),
    GroqProvider(),
]

class ProviderPoller:
    def __init__(self, providers: Optional[List[BaseProvider]] = None):
        self.providers = {p.provider_id: p for p in (providers or ALL_PROVIDERS)}
        self._cache: Dict[str, UsageSnapshot] = {}
        self._last_refresh: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, config_getter=None):
        if self._running:
            return
        self._running = True
        self._config_getter = config_getter or (lambda: {})
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="ProviderPoller")
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)

    def _poll_one_provider(self, pid: str, provider: BaseProvider, cfg: Dict[str, Any]):
        try:
            snapshot = provider.fetch_usage(cfg)
            with self._lock:
                self._cache[pid] = snapshot
                self._last_refresh[pid] = time.time()
        except Exception as e:
            with self._lock:
                prev = self._cache.get(pid)
                self._cache[pid] = UsageSnapshot(
                    provider_id=pid,
                    provider_name=provider.provider_name,
                    badge=provider.badge,
                    color=provider.color,
                    status="degraded" if prev else "error",
                    error_message=str(e),
                    primary_window=prev.primary_window if prev else None
                )
                self._last_refresh[pid] = time.time()

    def _poll_loop(self):
        time.sleep(0.5)
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="PollerWorker") as executor:
            while self._running:
                try:
                    cfg = self._config_getter()
                    now = time.time()
                    futures = []

                    for pid, provider in self.providers.items():
                        if not self._running:
                            break
                        last_time = self._last_refresh.get(pid, 0)
                        if now - last_time >= provider.ttl_seconds:
                            futures.append(executor.submit(self._poll_one_provider, pid, provider, cfg))

                    for f in futures:
                        try:
                            f.result(timeout=10.0)
                        except Exception:
                            pass

                except Exception as e:
                    print(f"[ProviderPoller] Error in loop: {e}")

                time.sleep(2.0)

    def get_snapshot(self, provider_id: str) -> Optional[UsageSnapshot]:
        with self._lock:
            return self._cache.get(provider_id)

    def get_all_snapshots(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {pid: snap.to_dict() for pid, snap in self._cache.items()}

    def get_compact_summary(self) -> List[Dict[str, Any]]:
        """Returns a minimal summary for ESP32 `/data` payload safety (<200 bytes)"""
        summary = []
        with self._lock:
            for pid, snap in self._cache.items():
                if snap.status in ("ok", "degraded") and snap.primary_window:
                    summary.append({
                        "id": pid,
                        "badge": snap.badge,
                        "pct": round(snap.primary_window.percent_left),
                        "st": snap.status
                    })
        return summary

# Global poller instance
poller = ProviderPoller()
