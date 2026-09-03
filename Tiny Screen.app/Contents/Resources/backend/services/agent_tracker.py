import os
import re
import json
import time
import glob
import platform
import threading
import logging
import shlex
import pathlib
try:
    import fcntl
except ImportError:
    fcntl = None

logger = logging.getLogger("tinyscreen.services.agent_tracker")

_session_registry = {}
_session_counters = {"claude": 0, "antigravity": 0}
_session_registry_lock = threading.RLock()

IN_FLIGHT_TIMEOUT_SECONDS = 45

test_agents_override = None
test_idle_override = False
test_alert_override = False
test_complete_override = False
test_alert_prompt = "WAITING ON HUMAN APPROVAL"
test_complete_prompt = "WORK COMPLETE"

def _format_context_phrase(words, max_len=12):
    if not words:
        return ""

    acronyms = {"3D", "CAD", "UI", "UX", "QA", "API", "RPC", "OTA", "LCD", "ESP", "PCB", "CLI", "AGY", "CLD", "AI"}
    cleaned_words = []
    for w in words:
        clean = re.sub(r"[^A-Za-z0-9]", "", w)
        if not clean:
            continue
        if clean.upper() in acronyms or (len(clean) <= 3 and clean.isupper()):
            cleaned_words.append(clean.upper())
        elif len(clean) <= 2:
            cleaned_words.append(clean.upper())
        else:
            cleaned_words.append(clean.capitalize())

    if not cleaned_words:
        return ""

    if len(cleaned_words) >= 2:
        combined = f"{cleaned_words[0]} {cleaned_words[1]}"
        if len(combined) <= max_len:
            return combined

    if len(cleaned_words) >= 2 and len(cleaned_words[0]) <= 3:
        combined = f"{cleaned_words[0]} {cleaned_words[1]}"
        return combined[:max_len].strip()

    return cleaned_words[0][:max_len]

def _clean_context_word(word, max_len=12):
    return _format_context_phrase([word] if word else [], max_len=max_len)

def _extract_antigravity_context(transcript_lines=None, role=None, objective=None):
    generic_words = {
        "agent", "worker", "specialist", "engineer", "subagent", "reviewer",
        "tester", "ticket", "task", "user", "objective", "display", "multi",
        "service", "system", "request", "tool", "call", "please", "help"
    }
    acronyms = {"3d", "cad", "ui", "ux", "qa", "api", "rpc", "ota", "lcd", "esp", "pcb", "cli", "ai"}

    if role:
        words = re.findall(r"[A-Za-z0-9]+", role)
        filtered = [w for w in words if w.lower() not in generic_words]
        phrase = _format_context_phrase(filtered or words, max_len=12)
        if phrase:
            return phrase

    if objective:
        words = re.findall(r"[A-Za-z0-9]+", objective)
        filtered = [w for w in words if w.lower() not in generic_words]
        phrase = _format_context_phrase(filtered or words, max_len=12)
        if phrase:
            return phrase

    if transcript_lines:
        for line in transcript_lines:
            entry = {}
            if isinstance(line, dict):
                entry = line
            elif isinstance(line, str):
                try:
                    entry = json.loads(line)
                except Exception:
                    entry = {}

            if not isinstance(entry, dict):
                continue

            content = entry.get("content", "")
            if isinstance(content, str) and "# USER Objective:" in content:
                m = re.search(r"# USER Objective:\s*([^\n\r]+)", content)
                if m:
                    words = re.findall(r"[A-Za-z0-9]+", m.group(1))
                    filtered = [w for w in words if w.lower() not in generic_words]
                    phrase = _format_context_phrase(filtered or words, max_len=12)
                    if phrase:
                        return phrase

            tool_calls = entry.get("tool_calls", [])
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    args = tc.get("args", {}) if isinstance(tc, dict) else {}
                    subagents = args.get("Subagents", []) if isinstance(args, dict) else []
                    if isinstance(subagents, list):
                        for sa in subagents:
                            if isinstance(sa, dict) and sa.get("Role"):
                                words = re.findall(r"[A-Za-z0-9]+", sa["Role"])
                                filtered = [w for w in words if w.lower() not in generic_words]
                                phrase = _format_context_phrase(filtered or words, max_len=12)
                                if phrase:
                                    return phrase

        stop_words = {
            "can", "we", "the", "a", "an", "to", "for", "in", "of", "and", "is", "it",
            "you", "i", "me", "my", "our", "have", "has", "do", "does", "did", "please",
            "make", "write", "create", "update", "fix", "add", "show", "get", "let", "lets",
            "why", "what", "how", "when", "where", "this", "that", "there", "with", "instead"
        }
        for line in transcript_lines:
            entry = {}
            if isinstance(line, dict):
                entry = line
            elif isinstance(line, str):
                try:
                    entry = json.loads(line)
                except Exception:
                    entry = {}

            if not isinstance(entry, dict):
                continue

            if entry.get("type") in ("USER_INPUT", "user") or entry.get("source") == "USER_EXPLICIT":
                raw_content = entry.get("content", "")
                if isinstance(raw_content, str):
                    stripped = re.sub(r"<[^>]+>", " ", raw_content)
                    words = re.findall(r"[A-Za-z0-9]+", stripped)
                    filtered = [w for w in words if w.lower() not in stop_words and w.lower() not in generic_words and (len(w) >= 3 or w.lower() in acronyms)]
                    if filtered:
                        phrase = _format_context_phrase(filtered, max_len=12)
                        if phrase:
                            return phrase
    return ""

def _extract_claude_context(cwd=None, transcript_lines=None):
    if transcript_lines:
        generic_words = {"please", "help", "project", "work", "start", "working", "need", "make", "file"}
        stop_words = {"the", "and", "for", "with", "this", "that", "from", "also", "into", "we"}
        for line in transcript_lines:
            entry = {}
            if isinstance(line, dict):
                entry = line
            elif isinstance(line, str):
                try:
                    entry = json.loads(line)
                except Exception:
                    entry = {}
            if not isinstance(entry, dict):
                continue
            if entry.get("type") == "user":
                msg = entry.get("message", {})
                content = msg.get("content", "") if isinstance(msg, dict) else entry.get("content", "")
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
                if isinstance(content, str) and content.strip():
                    words = re.findall(r"[A-Za-z0-9]+", content)
                    filtered = [w for w in words if w.lower() not in stop_words and w.lower() not in generic_words and len(w) >= 3]
                    if filtered:
                        phrase = _format_context_phrase(filtered, max_len=12)
                        if phrase:
                            return phrase
    if cwd:
        base = os.path.basename(os.path.normpath(cwd))
        if not base.startswith("local_"):
            words = re.findall(r"[A-Za-z0-9]+", base)
            if words:
                phrase = _format_context_phrase(words, max_len=12)
                if phrase:
                    return phrase
    return ""

def get_stable_agent_label(source, session_key, transcript_lines=None, cwd=None, role=None, objective=None):
    reg_key = f"{source}:{session_key}"
    with _session_registry_lock:
        if reg_key in _session_registry:
            return _session_registry[reg_key]

        _session_counters[source] = _session_counters.get(source, 0) + 1
        seq_num = _session_counters[source]

        label = ""
        if source == "antigravity":
            ctx = _extract_antigravity_context(transcript_lines, role=role, objective=objective)
            if ctx:
                label = ctx[:12]
            else:
                label = f"Agent {seq_num}"[:12]
        else:
            ctx = _extract_claude_context(cwd=cwd, transcript_lines=transcript_lines)
            if ctx:
                label = ctx[:12]
            else:
                label = f"Claude {seq_num}"[:12]

        assigned_values = set(_session_registry.values())
        if label in assigned_values:
            if len(label) <= 10:
                label = f"{label} {seq_num}"[:12]
            else:
                label = f"{label[:10]} {seq_num}"[:12]

        _session_registry[reg_key] = label
        return label

def resolve_session_state(found_pending, turn_pending_prompt, has_in_flight_tools, is_final_turn_response, age, cfg=None, source="claude"):
    completion_duration = (cfg.get("completion_duration_seconds", 10) if isinstance(cfg, dict) else 10) if cfg else 10
    working_color = "#FF7A00" if source == "antigravity" else "#00E5FF"

    if found_pending:
        return "WAITING", "waiting_approval", turn_pending_prompt, "#FFB800"
    elif is_final_turn_response:
        if age < completion_duration:
            return "COMPLETE", "work_complete", "WORK COMPLETE", "#00FF88"
        else:
            return "IDLE", "idle", "IDLE", "#94A3B8"
    elif has_in_flight_tools or age < IN_FLIGHT_TIMEOUT_SECONDS:
        return "WORKING", "working", "EXECUTING...", working_color
    else:
        return "IDLE", "idle", "IDLE", "#94A3B8"

_HOOK_STATE_FILE = os.path.expanduser("~/.claude/tinyscreen_hook_state.json")
_HOOK_LOCK_FILE = _HOOK_STATE_FILE + ".lock"
_hook_sessions = {}
_hook_lock = threading.Lock()

def _load_hook_state():
    global _hook_sessions
    if not os.path.exists(_HOOK_STATE_FILE):
        _hook_sessions = {}
        return
    try:
        if fcntl:
            os.makedirs(os.path.dirname(_HOOK_LOCK_FILE), exist_ok=True)
            with open(_HOOK_LOCK_FILE, "a") as lf:
                fcntl.flock(lf, fcntl.LOCK_SH)
                try:
                    with open(_HOOK_STATE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        _hook_sessions = data if isinstance(data, dict) else {}
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)
        else:
            with open(_HOOK_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _hook_sessions = data if isinstance(data, dict) else {}
    except Exception:
        _hook_sessions = {}

def _save_hook_state():
    try:
        os.makedirs(os.path.dirname(_HOOK_STATE_FILE), exist_ok=True)
        if fcntl:
            with open(_HOOK_LOCK_FILE, "a") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    tmp = _HOOK_STATE_FILE + f".tmp.{os.getpid()}"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(_hook_sessions, f)
                    os.replace(tmp, _HOOK_STATE_FILE)
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)
        else:
            tmp = _HOOK_STATE_FILE + f".tmp.{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_hook_sessions, f)
            os.replace(tmp, _HOOK_STATE_FILE)
    except Exception:
        pass

def _is_pid_alive(pid):
    if not pid or not isinstance(pid, int) or pid <= 0:
        return True
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (ProcessLookupError, OSError):
        return False

def handle_hook_event(data, now_ts=None):
    if now_ts is None:
        now_ts = time.time()
    
    if not isinstance(data, dict):
        return None

    session_id = data.get("session_id")
    if not session_id:
        return None
    
    hook_event = data.get("hook_event_name") or data.get("event") or ""
    notification_type = data.get("notification_type", "")
    cwd = data.get("cwd") or data.get("directory") or ""
    owner_pid = data.get("owner_pid") or data.get("pid")
    if owner_pid is not None:
        try:
            owner_pid = int(owner_pid)
        except Exception:
            owner_pid = None

    with _hook_lock:
        _load_hook_state()
        if hook_event == "SessionEnd":
            _hook_sessions.pop(session_id, None)
            _save_hook_state()
            return {"status": "removed", "session_id": session_id}
        
        if hook_event == "Notification":
            if notification_type == "idle_prompt":
                return {"status": "ignored", "session_id": session_id}
            state = "WAITING"
            code = "waiting_approval"
            detail = "GRANT PERM"
            color = "#FFB800"
        elif hook_event == "PreToolUse":
            tool_name = (data.get("tool_name") or "").lower()
            if tool_name in ("askuserquestion", "ask_user_question"):
                state = "WAITING"
                code = "waiting_approval"
                detail = "ANSWER Q"
                color = "#FFB800"
            elif tool_name in ("ask_permission", "request_permission") or "permission" in tool_name or "confirm" in tool_name:
                state = "WAITING"
                code = "waiting_approval"
                detail = "GRANT PERM"
                color = "#FFB800"
            else:
                state = "WORKING"
                code = "working"
                detail = "EXECUTING..."
                color = "#00E5FF"
        elif hook_event in ("SessionStart", "UserPromptSubmit", "working", "resumed"):
            state = "WORKING"
            code = "working"
            detail = "EXECUTING..."
            color = "#00E5FF"
        elif hook_event in ("Stop", "idle", "ended"):
            state = "COMPLETE"
            code = "work_complete"
            detail = "WORK COMPLETE"
            color = "#00FF88"
        else:
            return {"status": "ignored", "session_id": session_id}
        
        existing = _hook_sessions.get(session_id, {})
        label = get_stable_agent_label("claude", session_id, cwd=cwd or existing.get("cwd", ""))
        
        entry = {
            "id": session_id,
            "name": label,
            "source": "claude",
            "state": state,
            "code": code,
            "detail": detail,
            "color": color,
            "mtime": now_ts,
            "cwd": cwd or existing.get("cwd", ""),
            "owner_pid": owner_pid or existing.get("owner_pid"),
            "hook_event": hook_event
        }
        _hook_sessions[session_id] = entry
        _save_hook_state()
        return entry

def get_hook_sessions(now_ts=None, cfg=None):
    if now_ts is None:
        now_ts = time.time()
    cfg = cfg or {}
    
    with _hook_lock:
        _load_hook_state()
        active = []
        to_delete = []
        completion_duration = cfg.get("completion_duration_seconds", 10) if isinstance(cfg, dict) else 10
        
        for s_id, s in list(_hook_sessions.items()):
            pid = s.get("owner_pid")
            if pid and not _is_pid_alive(pid):
                to_delete.append(s_id)
                continue
            
            mtime = s.get("mtime", now_ts)
            age = now_ts - mtime
            if age >= 1800:
                to_delete.append(s_id)
                continue
            
            state = s.get("state", "IDLE")
            code = s.get("code", "idle")
            detail = s.get("detail", "IDLE")
            color = s.get("color", "#94A3B8")
            
            if state == "COMPLETE" and age >= completion_duration:
                state = "IDLE"
                code = "idle"
                detail = "IDLE"
                color = "#94A3B8"
            
            active.append({
                "id": s["id"],
                "name": s["name"],
                "source": "claude",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
        
        if to_delete:
            for s_id in to_delete:
                _hook_sessions.pop(s_id, None)
            _save_hook_state()
            
        return active

def install_claude_hooks(app_path=None):
    if app_path is None:
        app_path = os.path.abspath(__file__)
    settings_path = os.path.expanduser("~/.claude/settings.json")
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}
    
    if not isinstance(settings, dict):
        settings = {}
    
    hooks = settings.setdefault("hooks", {})
    hook_events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "Stop", "Notification", "SessionEnd"]
    resolved_path = str(pathlib.Path(app_path).resolve())
    hook_cmd = f"python3 {shlex.quote(resolved_path)} --hook"
    
    for event in hook_events:
        event_hooks = hooks.setdefault(event, [])
        already_registered = False
        for h in event_hooks:
            for item in h.get("hooks", []):
                cmd = item.get("command", "")
                if "--hook" in cmd and (app_path in cmd or "app.py" in cmd or "tinyscreen" in cmd.lower()):
                    already_registered = True
                    break
        if not already_registered:
            event_hooks.append({
                "hooks": [{
                    "type": "command",
                    "command": hook_cmd
                }]
            })
            
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    return True

def uninstall_claude_hooks(app_path=None):
    if app_path is None:
        app_path = os.path.abspath(__file__)
    settings_path = os.path.expanduser("~/.claude/settings.json")
    if not os.path.exists(settings_path):
        return True
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        if not isinstance(settings, dict):
            return True
        hooks = settings.get("hooks", {})
        for event, event_hooks in list(hooks.items()):
            if isinstance(event_hooks, list):
                new_list = []
                for h in event_hooks:
                    keep = True
                    for item in h.get("hooks", []):
                        cmd = item.get("command", "")
                        if "--hook" in cmd and (app_path in cmd or "app.py" in cmd or "tinyscreen" in cmd.lower()):
                            keep = False
                    if keep:
                        new_list.append(h)
                hooks[event] = new_list
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False

def _antigravity_brain_dirs():
    dirs = []
    base_user = os.path.expanduser("~")
    dirs.append(os.path.join(base_user, ".gemini", "antigravity", "brain"))
    dirs.append(os.path.join(base_user, ".antigravity", "brain"))
    return [d for d in dirs if os.path.exists(d)]

def get_antigravity_accounts():
    accounts = []
    antigravity_base = os.path.expanduser("~/.antigravity")
    if os.path.exists(antigravity_base):
        for acc_dir in glob.glob(os.path.join(antigravity_base, "accounts", "*")):
            if os.path.isdir(acc_dir):
                email = os.path.basename(acc_dir)
                accounts.append({"email": email, "path": acc_dir})
    return accounts

def get_claude_dirs():
    dirs = []
    user_home = os.path.expanduser("~")
    dirs.append(os.path.join(user_home, ".claude"))
    dirs.append(os.path.join(user_home, ".config", "claude"))
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            dirs.append(os.path.join(appdata, "Claude"))
            dirs.append(os.path.join(appdata, "claude-code"))
    elif system == "Darwin":
        dirs.append(os.path.join(user_home, "Library", "Application Support", "Claude"))
        dirs.append(os.path.join(user_home, "Library", "Application Support", "claude-code"))
    return [d for d in dirs if os.path.exists(d)]

def scan_antigravity_sessions(brain_dirs=None, now_ts=None):
    if brain_dirs is None:
        brain_dirs = _antigravity_brain_dirs()
    if now_ts is None:
        now_ts = time.time()

    sessions = []
    for brain_dir in brain_dirs:
        for root, dirs, files in os.walk(brain_dir):
            if "transcript.jsonl" not in files:
                continue
            fp = os.path.join(root, "transcript.jsonl")
            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                continue

            age = now_ts - mtime
            if age >= 1800:
                continue

            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l for l in f.readlines() if l.strip()]
            except Exception:
                continue
            if not lines:
                continue

            last_user_idx = -1
            for idx in range(len(lines) - 1, -1, -1):
                try:
                    entry = json.loads(lines[idx])
                    if entry.get("type") == "USER_INPUT" or entry.get("source") == "USER_EXPLICIT":
                        last_user_idx = idx
                        break
                except Exception:
                    pass

            parts = os.path.normpath(fp).split(os.sep)
            session_id = parts[-4] if len(parts) >= 4 and parts[-3] == ".system_generated" else os.path.basename(root)
            label = get_stable_agent_label("antigravity", session_id, transcript_lines=lines)

            if last_user_idx == len(lines) - 1:
                if age < 45:
                    sessions.append({
                        "id": session_id,
                        "name": label,
                        "source": "antigravity",
                        "state": "WORKING",
                        "code": "working",
                        "detail": "EXECUTING...",
                        "color": "#00E5FF",
                        "age_seconds": int(age),
                        "mtime": mtime
                    })
                continue

            turn_lines = lines[last_user_idx + 1:] if last_user_idx != -1 else lines
            if not turn_lines:
                continue

            last_step_entry = {}
            try:
                last_step_entry = json.loads(turn_lines[-1])
            except Exception:
                pass

            found_pending = False
            turn_pending_prompt = "INPUT REQ"

            step_type = last_step_entry.get("type")
            is_final_turn_response = False
            has_in_flight_tools = False

            if step_type in ("ASK_QUESTION", "ASK_PERMISSION"):
                found_pending = True
                turn_pending_prompt = "ANSWER Q" if step_type == "ASK_QUESTION" else "GRANT PERM"
            elif step_type == "PLANNER_RESPONSE":
                tool_calls = last_step_entry.get("tool_calls", []) or []
                if tool_calls:
                    for tc in tool_calls:
                        name = tc.get("name")
                        args = tc.get("args", {}) or {}
                        meta = args.get("ArtifactMetadata") if isinstance(args, dict) else None
                        if isinstance(meta, str):
                            try: meta = json.loads(meta)
                            except Exception: meta = {}
                        if isinstance(meta, dict) and meta.get("RequestFeedback") is True:
                            found_pending = True
                            turn_pending_prompt = "APPROVE PLAN"
                            break
                        name_lower = (name or "").lower()
                        if name_lower in ("ask_question", "ask_user_question"):
                            found_pending = True
                            turn_pending_prompt = "ANSWER Q"
                            break
                        elif name_lower in ("ask_permission", "request_permission") or "permission" in name_lower or "confirm" in name_lower:
                            found_pending = True
                            turn_pending_prompt = "GRANT PERM"
                            break
                        else:
                            has_in_flight_tools = True
                elif last_step_entry.get("content"):
                    is_final_turn_response = True
                else:
                    has_in_flight_tools = True
            elif step_type == "GENERIC":
                has_in_flight_tools = True

            state, code, detail, color = resolve_session_state(
                found_pending=found_pending,
                turn_pending_prompt=turn_pending_prompt,
                has_in_flight_tools=has_in_flight_tools,
                is_final_turn_response=is_final_turn_response,
                age=age,
                cfg=None,
                source="antigravity"
            )

            sessions.append({
                "id": session_id,
                "name": label,
                "source": "antigravity",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
    return sessions

def check_antigravity_status(brain_dirs=None, now_ts=None):
    sessions = scan_antigravity_sessions(brain_dirs, now_ts)
    waiting = next((s for s in sessions if s["state"] == "WAITING"), None)
    if waiting:
        return {
            "waiting_for_input": True,
            "work_completed": False,
            "prompt_text": waiting["detail"],
            "source": "antigravity"
        }
    complete = next((s for s in sessions if s["state"] == "COMPLETE"), None)
    if complete:
        return {
            "waiting_for_input": False,
            "work_completed": True,
            "prompt_text": "INPUT REQ",
            "source": "antigravity"
        }
    return {
        "waiting_for_input": False,
        "work_completed": False,
        "prompt_text": "INPUT REQ",
        "source": "antigravity"
    }

def scan_claude_sessions(claude_dirs=None, now_ts=None):
    if claude_dirs is None:
        claude_dirs = get_claude_dirs()
    if now_ts is None:
        now_ts = time.time()

    sessions = []
    for c_dir in claude_dirs:
        pattern = os.path.join(c_dir, "**", "*.jsonl")
        for fp in glob.glob(pattern, recursive=True):
            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                continue

            age = now_ts - mtime
            if age >= 1800:
                continue

            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
            except Exception:
                continue
            if not lines:
                continue
            if len(lines) > 2000:
                lines = lines[-2000:]

            last_user_idx = -1
            for idx in range(len(lines) - 1, -1, -1):
                try:
                    entry = json.loads(lines[idx])
                    if entry.get("type") == "user":
                        msg = entry.get("message", {})
                        content = msg.get("content")
                        if isinstance(content, str):
                            last_user_idx = idx
                            break
                        elif isinstance(content, list):
                            has_text = any(isinstance(c, dict) and c.get("type") == "text" for c in content)
                            if has_text:
                                last_user_idx = idx
                                break
                except Exception:
                    pass

            if os.path.basename(fp) == "audit.jsonl":
                parent_dir = os.path.basename(os.path.dirname(fp))
                session_id = (parent_dir[6:] if parent_dir.startswith("local_") else parent_dir) or parent_dir
            else:
                session_id = os.path.splitext(os.path.basename(fp))[0]

            label = get_stable_agent_label("claude", session_id, cwd=os.path.dirname(fp), transcript_lines=lines)

            if last_user_idx == len(lines) - 1:
                if age < 45:
                    sessions.append({
                        "id": session_id,
                        "name": label,
                        "source": "claude",
                        "state": "WORKING",
                        "code": "working",
                        "detail": "EXECUTING...",
                        "color": "#00E5FF",
                        "age_seconds": int(age),
                        "mtime": mtime
                    })
                continue

            turn_lines = lines[last_user_idx + 1:] if last_user_idx != -1 else lines
            if not turn_lines:
                continue

            found_pending = False
            turn_pending_prompt = "GRANT PERM"
            has_in_flight_tools = False
            is_final_turn_response = False

            pending_permissions = {}
            unanswered_tool_calls = {}
            has_result_success = False
            last_assistant_has_text = False
            last_assistant_has_tools = False

            for tl in turn_lines:
                try:
                    entry = json.loads(tl) if isinstance(tl, str) else tl
                except Exception:
                    continue
                if not isinstance(entry, dict):
                    continue

                etype = entry.get("type")
                esubtype = entry.get("subtype")

                # Claude Desktop App permission requests & responses (with 30-min TTL bound)
                if etype == "system" and esubtype in ("permission_request", "confirm_request"):
                    ts_str = entry.get("timestamp")
                    if ts_str:
                        try:
                            req_ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
                            if (now_ts - req_ts) > 1800:
                                continue
                        except Exception:
                            pass
                    p_id = str(entry.get("uuid") or entry.get("id") or "req")[:64]
                    pending_permissions[p_id] = entry
                elif etype == "system" and esubtype in ("permission_response", "permission_auto_approved"):
                    p_id = str(entry.get("uuid") or entry.get("id") or "req")[:64]
                    pending_permissions.pop(p_id, None)

                # Final result marker (Desktop App / CLI completion)
                elif etype == "result" and esubtype in ("success", "completed"):
                    has_result_success = True

                # Assistant messages and tool calls
                elif etype == "assistant":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    has_tools_in_entry = False
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                has_tools_in_entry = True
                                tu_id = item.get("id") or item.get("tool_use_id") or "tu"
                                tu_name = (item.get("name") or "").lower()
                                unanswered_tool_calls[tu_id] = tu_name
                        last_assistant_has_text = any(isinstance(item, dict) and item.get("type") == "text" for item in content)
                    elif isinstance(content, str) and content.strip():
                        last_assistant_has_text = True
                    last_assistant_has_tools = has_tools_in_entry

                # User messages / tool results answering prior tool uses
                elif etype == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_result":
                                tu_id = item.get("tool_use_id") or item.get("id")
                                if tu_id:
                                    unanswered_tool_calls.pop(tu_id, None)

            if pending_permissions:
                found_pending = True
                turn_pending_prompt = "GRANT PERM"
            else:
                for tu_id, tu_name in list(unanswered_tool_calls.items()):
                    if tu_name in ("askuserquestion", "ask_user_question", "ask_question"):
                        found_pending = True
                        turn_pending_prompt = "ANSWER Q"
                        break
                    elif tu_name in ("ask_permission", "request_permission") or "permission" in tu_name or "confirm" in tu_name:
                        found_pending = True
                        turn_pending_prompt = "GRANT PERM"
                        break

            if not found_pending:
                if unanswered_tool_calls:
                    has_in_flight_tools = True
                elif has_result_success or (last_assistant_has_text and not last_assistant_has_tools):
                    is_final_turn_response = True

            state, code, detail, color = resolve_session_state(
                found_pending=found_pending,
                turn_pending_prompt=turn_pending_prompt,
                has_in_flight_tools=has_in_flight_tools,
                is_final_turn_response=is_final_turn_response,
                age=age,
                cfg=None,
                source="claude"
            )

            sessions.append({
                "id": session_id,
                "name": label,
                "source": "claude",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
    return sessions

def check_claude_status(claude_dirs=None, now_ts=None):
    if now_ts is None:
        now_ts = time.time()
    hook_sessions = get_hook_sessions(now_ts)
    hooked_ids = {s["id"] for s in hook_sessions}
    scanned_sessions = [s for s in scan_claude_sessions(claude_dirs, now_ts) if s["id"] not in hooked_ids]
    sessions = hook_sessions + scanned_sessions

    waiting = next((s for s in sessions if s["state"] == "WAITING"), None)
    if waiting:
        return {
            "waiting_for_input": True,
            "work_completed": False,
            "prompt_text": waiting["detail"],
            "source": "claude"
        }
    complete = next((s for s in sessions if s["state"] == "COMPLETE"), None)
    if complete:
        return {
            "waiting_for_input": False,
            "work_completed": True,
            "prompt_text": "INPUT REQ",
            "source": "claude"
        }
    return {
        "waiting_for_input": False,
        "work_completed": False,
        "prompt_text": "INPUT REQ",
        "source": "claude"
    }

def get_multi_agent_status(cfg=None, now_ts=None):
    if now_ts is None:
        now_ts = time.time()
    cfg = cfg or {}

    if test_agents_override is not None:
        active = test_agents_override
    else:
        claude_sessions = get_hook_sessions(now_ts=now_ts, cfg=cfg)
        hooked_ids = {s["id"] for s in claude_sessions}
        scanned_claude = [s for s in scan_claude_sessions(now_ts=now_ts) if s["id"] not in hooked_ids]
        ag_sessions = scan_antigravity_sessions(now_ts=now_ts)
        active = claude_sessions + scanned_claude + ag_sessions
        active.sort(key=lambda a: a.get("mtime", 0), reverse=True)

    waiting_session = next((s for s in active if s["state"] == "WAITING"), None)
    complete_session = next((s for s in active if s["state"] == "COMPLETE"), None)
    waiting_for_input = waiting_session is not None
    work_completed = complete_session is not None and not waiting_for_input
    prompt_text = waiting_session["detail"] if waiting_session else "INPUT REQ"
    completion_text = complete_session["detail"] if complete_session else "WORK COMPLETE"
    source = waiting_session["source"] if waiting_session else (complete_session["source"] if complete_session else "none")

    return {
        "waiting_for_input": waiting_for_input,
        "work_completed": work_completed,
        "prompt_text": prompt_text,
        "completion_text": completion_text,
        "source": source,
        "active_agents": active[:8],
        "has_active_agents": len(active) > 0,
        "agents": active,
        "active_count": len(active),
        "waiting_count": sum(1 for a in active if a.get("state") == "WAITING"),
        "working_count": sum(1 for a in active if a.get("state") == "WORKING"),
        "complete_count": sum(1 for a in active if a.get("state") == "COMPLETE"),
        "idle_count": sum(1 for a in active if a.get("state") == "IDLE")
    }

def check_agent_status(antigravity_dirs=None, claude_dirs=None, now_ts=None):
    ag_stat = check_antigravity_status(antigravity_dirs, now_ts)
    if ag_stat["waiting_for_input"] or ag_stat["work_completed"]:
        return ag_stat
    cl_stat = check_claude_status(claude_dirs, now_ts)
    if cl_stat["waiting_for_input"] or cl_stat["work_completed"]:
        return cl_stat
    return ag_stat
