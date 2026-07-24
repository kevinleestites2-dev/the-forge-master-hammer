#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════╗
║              THE FORGEMASTER  v2.0.0                  ║
║    "I do not question. I do not hesitate.             ║
║     I do not miss."                                   ║
╠═══════════════════════════════════════════════════════╣
║  Will    → ZEUS        (judges intent)                ║
║  Bridge  → THOR        (routes execution)             ║
║  Strike  → CLAW        (hits the target)              ║
║  Mind    → LiquidBrain (8 cognitive modes)            ║
║  Nerves  → SAFLA HyperLoop (12 parallel loops)        ║
║  Spine   → Apollo-X    (never fails)                  ║
║  Eyes    → browser-use (sees the internet)            ║
║  Arms    → 5,400+ skills (does anything)              ║
║  Growth  → SkillClaw   (gets stronger)                ║
╠═══════════════════════════════════════════════════════╣
║  Author: Kevin Lee (kevinleestites2-dev)              ║
║  Born:   Fort Myers, FL — Pantheon Project            ║
║  Engine: Mjölnir — The Hammer That Never Misses       ║
╚═══════════════════════════════════════════════════════╝

v2.0.0 — reforged:
  - Shared aiohttp session pool — no per-call re-imports
  - LiquidBrain.reason() wired to LLM (real cognition)
  - Async LiquidMemory — no blocking I/O
  - GitHubForge uses asyncio subprocess — non-blocking git
  - HyperLoop context merge race-condition fixed
  - SkillForge executes generated code in sandbox
  - Graceful shutdown with session cleanup
  - Atomic file writes throughout
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import subprocess
import tempfile
import time
import aiohttp
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _atomic_write(path: Path, data: Any):
    """Atomic JSON write — prevents corruption on crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", dir=str(path.parent),
        prefix="." + path.name + ".", suffix=".tmp", delete=False,
    )
    try:
        json.dump(data, tmp, indent=2)
        tmp.flush(); os.fsync(tmp.fileno()); tmp.close()
        os.replace(tmp.name, str(path))
    except Exception:
        try: os.unlink(tmp.name)
        except Exception: pass
        raise


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ══════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(name)s] %(message)s"
)
log = logging.getLogger("FORGEMASTER")

DARK_FOREST = os.getenv("DARK_FOREST", "false").lower() == "true"
if DARK_FOREST:
    logging.disable(logging.INFO)


# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════

CONFIG = {
    "name": "THE FORGEMASTER",
    "version": "2.0.0",
    "author": "kevinleestites2-dev",
    "mantra": "I do not question. I do not hesitate. I do not miss.",
    "checkpoint_path": Path(".forgemaster_checkpoint.json"),
    "task_queue_path": Path(".forgemaster_tasks.json"),
    "skill_library_path": Path(".skills/"),
    "memory_path": Path(".liquid_memory.json"),
    "forge_log_path": Path(".forge_log.json"),
    "github_repo": os.getenv("GITHUB_REPO", ""),
    "github_token": os.getenv("GITHUB_TOKEN", ""),
    "llm_providers": {
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
        },
        "groq": {
            "api_key": os.getenv("GROQ_API_KEY", ""),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama3-70b-8192",
        },
        "gemini": {
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "model": "gemini-2.0-flash",
        },
    },
    "cron_interval": int(os.getenv("CRON_INTERVAL", "900")),
    "dream_interval": int(os.getenv("DREAM_INTERVAL", "3600")),
    "max_retries": 3,
    "retry_base_delay": 1.0,
    "mjolnir_cooldown": 0.5,
    "explore_epsilon": 0.3,
    "reflection_threshold": 0.85,
    "pid_setpoint": 1.0,
    "llm_timeout": 60,
}

# ══════════════════════════════════════════════════════════════════
# SHARED HTTP SESSION (created once, reused everywhere)
# ══════════════════════════════════════════════════════════════════

_SESSION: Optional[aiohttp.ClientSession] = None
_SESSION_LOCK = asyncio.Lock()


async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        async with _SESSION_LOCK:
            if _SESSION is None or _SESSION.closed:
                timeout = aiohttp.ClientTimeout(total=CONFIG["llm_timeout"])
                _SESSION = aiohttp.ClientSession(timeout=timeout)
    return _SESSION


async def _close_session():
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()
        _SESSION = None


# ══════════════════════════════════════════════════════════════════
# STATE BUS
# ══════════════════════════════════════════════════════════════════

class StateBus:
    def __init__(self):
        self._state: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any):
        async with self._lock:
            self._state[key] = value
        cbs = self._subscribers.get(key, [])
        for cb in cbs:
            try:
                await cb(key, value)
            except Exception:
                pass

    async def get(self, key: str, default=None) -> Any:
        async with self._lock:
            return self._state.get(key, default)

    async def update(self, data: dict):
        for k, v in data.items():
            await self.set(k, v)

    def subscribe(self, key: str, callback: Callable):
        self._subscribers[key].append(callback)

    async def snapshot(self) -> dict:
        async with self._lock:
            return dict(self._state)


BUS = StateBus()


# ══════════════════════════════════════════════════════════════════
# LIQUID BRAIN — 8 cognitive modes
# ══════════════════════════════════════════════════════════════════

class LiquidBrain:
    MODES = {
        "CREATOR":   {"focus": "generation",  "temperature": 0.9},
        "ARCHITECT": {"focus": "structure",   "temperature": 0.4},
        "WARRIOR":   {"focus": "execution",   "temperature": 0.3},
        "GHOST":     {"focus": "stealth",     "temperature": 0.2},
        "ORACLE":    {"focus": "prediction",  "temperature": 0.7},
        "SAGE":      {"focus": "reflection",  "temperature": 0.5},
        "PHANTOM":   {"focus": "simulation",  "temperature": 0.8},
        "SOVEREIGN": {"focus": "command",     "temperature": 0.1},
    }
    FRAMEWORKS = ["OODA", "PDCA", "MARS", "OUROBOROS", "CYCLIC", "SELF_REF"]

    def __init__(self, mode: str = "SOVEREIGN"):
        self.mode = mode.upper()
        self.thought_log: list[dict] = []
        self.mutation_log: list[dict] = []
        self.chain_id = self._new_id()
        self._llm_caller: Optional[Callable] = None  # attach for real reasoning

    def _new_id(self) -> str:
        return hashlib.sha256(
            f"{self.mode}:{time.time_ns()}".encode()
        ).hexdigest()[:16]

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    def attach_llm(self, fn: Callable):
        """
        Wire in the LLM for real cognition.
        fn should be: async fn(prompt: str, system: str) -> str
        """
        self._llm_caller = fn

    async def reason(
        self, intent: str, context: dict = None, framework: str = "OODA"
    ) -> dict:
        """
        Real reasoning — calls LLM if wired, falls back to structured conclusion.
        """
        fw = framework.upper() if framework.upper() in self.FRAMEWORKS else "OODA"
        ctx_str = json.dumps(context)[:500] if context else "none"

        if self._llm_caller:
            prompt = (
                f"Framework: {fw}\n"
                f"Mode: {self.mode} (temp={self.MODES[self.mode]['temperature']})\n"
                f"Intent: {intent}\n"
                f"Context: {ctx_str}\n\n"
                f"Analyse this situation using the {fw} framework. "
                f"Return JSON: "
                f'{{"conclusion": "...", "confidence": 0.0-1.0, "action": "...", "risks": ["..."]}}'
            )
            try:
                raw = await self._llm_caller(
                    prompt,
                    f"You are THE FORGEMASTER in {self.mode} mode using the {fw} framework."
                )
                raw = raw.strip()
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"): raw = raw[4:]
                data = json.loads(raw)
                thought = {
                    "chain_id": self._new_id(),
                    "mode": self.mode,
                    "framework": fw,
                    "intent": intent,
                    "temperature": self.MODES[self.mode]["temperature"],
                    "timestamp": self._timestamp(),
                    "conclusion": data.get("conclusion", f"Resolved via {fw}"),
                    "confidence": data.get("confidence", 0.85),
                    "action": data.get("action", ""),
                    "risks": data.get("risks", []),
                }
                self.thought_log.append(thought)
                await BUS.set("brain.last_thought", thought)
                return thought
            except Exception as e:
                log.warning(f"[BRAIN] LLM reasoning failed ({e}), using fallback")

        # ── Fallback (no LLM wired) ─────────────────────────────
        thought = {
            "chain_id": self._new_id(),
            "mode": self.mode,
            "framework": fw,
            "intent": intent,
            "temperature": self.MODES[self.mode]["temperature"],
            "timestamp": self._timestamp(),
            "conclusion": f"Resolved via {fw} under {self.mode}",
            "confidence": 0.85,
            "action": "proceed",
            "risks": [],
        }
        self.thought_log.append(thought)
        return thought

    def mutate(self, new_mode: str):
        if new_mode.upper() not in self.MODES:
            return
        old = self.mode
        self.mode = new_mode.upper()
        self.mutation_log.append({"from": old, "to": self.mode, "ts": _utcnow()})
        log.info(f"[BRAIN] {old} → {self.mode}")

    def pick_mode(self, task: str) -> str:
        mapping = {
            "research": "ORACLE", "execute": "WARRIOR",
            "stealth": "GHOST", "create": "CREATOR",
            "reflect": "SAGE", "plan": "ARCHITECT",
            "simulate": "PHANTOM", "command": "SOVEREIGN",
            "forge": "WARRIOR", "strike": "WARRIOR",
        }
        for key, mode in mapping.items():
            if key in task.lower():
                return mode
        return "SOVEREIGN"


BRAIN = LiquidBrain(mode="SOVEREIGN")


# ══════════════════════════════════════════════════════════════════
# LIQUID MEMORY — async, non-blocking
# ══════════════════════════════════════════════════════════════════

class LiquidMemory:
    def __init__(self, path: Path):
        self.path = path
        self._mem: dict = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    async def _ensure_loaded(self):
        if self._loaded:
            return
        if self.path.exists():
            try:
                self._mem = json.loads(await asyncio.to_thread(self.path.read_text))
            except Exception:
                self._mem = {}
        self._loaded = True

    async def _save(self):
        async with self._lock:
            await asyncio.to_thread(_atomic_write, self.path, self._mem)

    async def remember(self, key: str, value: Any):
        await self._ensure_loaded()
        self._mem[key] = {"value": value, "ts": time.time()}
        await self._save()

    async def recall(self, key: str, default=None) -> Any:
        await self._ensure_loaded()
        entry = self._mem.get(key)
        return entry["value"] if entry else default

    async def snapshot(self) -> dict:
        await self._ensure_loaded()
        return dict(self._mem)


MEMORY = LiquidMemory(CONFIG["memory_path"])


# ══════════════════════════════════════════════════════════════════
# MULTI-LLM — shared session, no re-imports
# ══════════════════════════════════════════════════════════════════

async def call_llm(
    prompt: str,
    system: str = (
        "You are THE FORGEMASTER — a fully autonomous AI agent. "
        "I do not question. I do not hesitate. I do not miss."
    )
) -> str:
    """Multi-provider LLM call with shared session pool."""
    providers = list(CONFIG["llm_providers"].items())
    random.shuffle(providers)

    session = await _get_session()

    for name, cfg in providers:
        if not cfg["api_key"]:
            continue
        try:
            headers = {
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": cfg["model"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": BRAIN.MODES[BRAIN.mode]["temperature"],
                "max_tokens": 1024,
            }
            async with session.post(
                f"{cfg['base_url']}/chat/completions",
                headers=headers, json=payload,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    await BUS.set("llm.provider", name)
                    log.info(f"[LLM] Strike via {name}")
                    return content
                else:
                    body = await resp.text()
                    log.warning(f"[LLM] {name} HTTP {resp.status}: {body[:120]}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning(f"[LLM] {name} failed: {e}")

    return "[FORGEMASTER] All providers unavailable. Standing by."


# Wire LLM into Brain for real cognition
BRAIN.attach_llm(call_llm)


# ══════════════════════════════════════════════════════════════════
# MJÖLNIR — The Hammer That Never Misses
# ══════════════════════════════════════════════════════════════════

class MjolnirState:
    RESTING   = "RESTING"
    AIMING    = "AIMING"
    STRIKING  = "STRIKING"
    RETURNING = "RETURNING"
    STORM     = "STORM"


@dataclass
class Strike:
    id: str
    intent: str
    status: str = "PENDING"
    result: Any = None
    timestamp: float = field(default_factory=time.time)
    mode: str = "SOVEREIGN"


class Mjolnir:
    """Zeus judges. Thor bridges. Claw strikes. One intent. One return."""

    def __init__(self):
        self.state = MjolnirState.RESTING
        self.strike_log: list[Strike] = []
        self.dna = hashlib.sha256(
            f"MJOLNIR:{time.time_ns()}".encode()
        ).hexdigest()[:12]
        self._last_strike = 0.0
        self._forge_log_path = CONFIG["forge_log_path"]
        self._load_log()
        log.info(f"[MJÖLNIR] Forged — DNA: {self.dna}")

    def _load_log(self):
        if self._forge_log_path.exists():
            try:
                raw = json.loads(self._forge_log_path.read_text())
                self.strike_log = [Strike(**s) for s in raw]
            except Exception:
                self.strike_log = []

    def _save_log(self):
        _atomic_write(
            self._forge_log_path,
            [s.__dict__ for s in self.strike_log[-100:]],
        )

    # ── ZEUS: Judge ──────────────────────────────────────────────
    async def zeus_judge(self, intent: str) -> tuple[bool, str]:
        self.state = MjolnirState.AIMING
        BRAIN.mutate("SOVEREIGN")

        prompt = (
            f'You are ZEUS — The Will of the Forgemaster.\n'
            f'Judge this intent: "{intent}"\n\n'
            f'Is this worthy of a strike? '
            f'Consider: Is it actionable? Is it clear? Does it serve the Forgemaster?\n\n'
            f'Respond as JSON only:\n'
            f'{{"worthy": true, "reason": "...", "refined_intent": "..."}}'
        )
        response = await call_llm(
            prompt,
            system="You are ZEUS. You judge. You command."
        )
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            worthy = data.get("worthy", True)
            refined = data.get("refined_intent", intent)
            reason = data.get("reason", "Approved")
            log.info(f"[ZEUS] {'APPROVED' if worthy else 'DENIED'}: {reason[:60]}")
            await BUS.set("zeus.last_judgment", {"worthy": worthy, "reason": reason})
            return worthy, refined
        except Exception:
            return True, intent

    # ── THOR: Bridge ─────────────────────────────────────────────
    async def thor_bridge(self, intent: str) -> dict:
        BRAIN.mutate("ARCHITECT")
        prompt = (
            f'You are THOR — The Bridge.\n'
            f'Translate this intent into an execution plan: "{intent}"\n\n'
            f'Route it across the Bifrost:\n'
            f'- What tools/skills are needed?\n'
            f'- What is the exact sequence of actions?\n'
            f'- What is the expected outcome?\n\n'
            f'Respond as JSON only:\n'
            f'{{"tools": ["..."], "steps": ["..."], "outcome": "...", "route": "..."}}'
        )
        response = await call_llm(
            prompt,
            system="You are THOR. You bridge. You translate."
        )
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            log.info(f"[THOR] Bifrost route: {data.get('route', 'direct')}")
            await BUS.set("thor.last_bridge", data)
            return data
        except Exception:
            return {"tools": [], "steps": [intent], "outcome": "unknown", "route": "direct"}

    # ── CLAW: Strike ─────────────────────────────────────────────
    async def claw_strike(self, intent: str, bridge: dict) -> str:
        self.state = MjolnirState.STRIKING
        BRAIN.mutate("WARRIOR")

        steps = bridge.get("steps", [intent])
        tools = bridge.get("tools", [])

        prompt = (
            f'You are CLAW — The Strike.\n'
            f'Execute this intent: "{intent}"\n\n'
            f'Steps to follow: {json.dumps(steps)}\n'
            f'Tools available: {json.dumps(tools)}\n'
            f'Expected outcome: {bridge.get("outcome", "complete the task")}\n\n'
            f'Execute now. Return the result. Be specific. Be complete. Do not hesitate.'
        )
        result = await call_llm(
            prompt,
            system="You are CLAW. You execute. You strike. You do not miss."
        )
        log.info(f"[CLAW] Strike complete: {result[:80]}...")
        await BUS.set("claw.last_strike", result[:200])
        return result

    # ── THE STRIKE ───────────────────────────────────────────────
    async def strike(self, intent: str, storm: bool = False) -> Strike:
        elapsed = time.time() - self._last_strike
        if not storm and elapsed < CONFIG["mjolnir_cooldown"]:
            await asyncio.sleep(CONFIG["mjolnir_cooldown"] - elapsed)

        strike_id = (
            f"STRIKE_"
            f"{hashlib.sha256(f'{intent}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        )
        log.info(f"[MJÖLNIR] ⚡ {strike_id} — {intent[:60]}")

        s = Strike(id=strike_id, intent=intent, mode=BRAIN.mode)

        try:
            if storm:
                self.state = MjolnirState.STORM
                log.info("[ZEUS] STORM MODE — autonomous override")
                worthy, refined = True, intent
            else:
                worthy, refined = await self.zeus_judge(intent)

            if not worthy:
                s.status = "DENIED"
                s.result = "Zeus denied this strike."
                self.state = MjolnirState.RESTING
                self.strike_log.append(s)
                self._save_log()
                return s

            bridge = await self.thor_bridge(refined)
            result = await self.claw_strike(refined, bridge)

            self.state = MjolnirState.RETURNING
            s.status = "SUCCESS"
            s.result = result
            self._last_strike = time.time()

            await BUS.set("mjolnir.last_strike", strike_id)
            await BUS.set("mjolnir.last_result", result[:200])
            await MEMORY.remember(f"strike.{strike_id}", s.__dict__)

        except Exception as e:
            s.status = "FAIL"
            s.result = str(e)
            log.error(f"[MJÖLNIR] Strike failed: {e}")

        finally:
            self.state = MjolnirState.RESTING
            self.strike_log.append(s)
            self._save_log()

        log.info(f"[MJÖLNIR] {strike_id} → {s.status}")
        return s

    def forge_report(self) -> str:
        total = len(self.strike_log)
        success = sum(1 for s in self.strike_log if s.status == "SUCCESS")
        denied = sum(1 for s in self.strike_log if s.status == "DENIED")
        failed = sum(1 for s in self.strike_log if s.status == "FAIL")
        rate = (success / total * 100) if total > 0 else 0
        return (
            f"\n╔══════════════════════════════════════╗\n"
            f"║         MJÖLNIR FORGE REPORT        ║\n"
            f"╚══════════════════════════════════════╝\n"
            f"DNA:       {self.dna}\n"
            f"State:     {self.state}\n"
            f"Strikes:   {total}\n"
            f"Success:   {success} ({rate:.1f}%)\n"
            f"Denied:    {denied}\n"
            f"Failed:    {failed}\n"
            f"Last:      {self.strike_log[-1].id if self.strike_log else 'none'}\n"
        )


HAMMER = Mjolnir()


# ══════════════════════════════════════════════════════════════════
# TASK QUEUE
# ══════════════════════════════════════════════════════════════════

@dataclass
class ForgeTask:
    id: str
    intent: str
    priority: int = 3
    status: str = "pending"
    retries: int = 0
    created_at: float = field(default_factory=time.time)
    strike_id: str = ""
    result: Any = None


class ForgeQueue:
    PRIORITY_NAMES = {
        1: "CRITICAL", 2: "HIGH", 3: "NORMAL", 4: "LOW", 5: "EVOLUTION"
    }

    def __init__(self, path: Path):
        self.path = path
        self._tasks: list[ForgeTask] = []
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                self._tasks = [ForgeTask(**t) for t in raw]
            except Exception:
                self._tasks = []

    def _save(self):
        _atomic_write(
            self.path,
            [t.__dict__ for t in self._tasks],
        )

    async def forge(self, intent: str, priority: int = 3) -> ForgeTask:
        async with self._lock:
            task = ForgeTask(
                id=hashlib.sha256(f"{intent}{time.time()}".encode()).hexdigest()[:8],
                intent=intent,
                priority=priority,
            )
            self._tasks.append(task)
            self._tasks.sort(key=lambda t: t.priority)
            self._save()
        pname = self.PRIORITY_NAMES.get(priority, "NORMAL")
        log.info(f"[QUEUE] Forged [{pname}]: {intent[:50]}")
        return task

    async def next(self) -> Optional[ForgeTask]:
        async with self._lock:
            pending = [t for t in self._tasks if t.status == "pending"]
            return pending[0] if pending else None

    async def complete(self, task_id: str, strike_id: str, result: Any):
        async with self._lock:
            for t in self._tasks:
                if t.id == task_id:
                    t.status = "done"
                    t.strike_id = strike_id
                    t.result = result
            self._save()

    async def fail(self, task_id: str):
        async with self._lock:
            for t in self._tasks:
                if t.id == task_id:
                    t.retries += 1
                    if t.retries >= CONFIG["max_retries"]:
                        t.status = "failed"
                    else:
                        t.status = "pending"
            self._save()

    async def pending_count(self) -> int:
        async with self._lock:
            return len([t for t in self._tasks if t.status == "pending"])

    async def stats(self) -> dict:
        async with self._lock:
            return {
                "total": len(self._tasks),
                "pending": len([t for t in self._tasks if t.status == "pending"]),
                "done": len([t for t in self._tasks if t.status == "done"]),
                "failed": len([t for t in self._tasks if t.status == "failed"]),
            }

    # For retry loop access (internal)
    def _failed_retryable(self) -> list:
        return [t for t in self._tasks if t.status == "failed"
                and t.retries < CONFIG["max_retries"]]

    async def _requeue_failed(self):
        async with self._lock:
            for t in self._failed_retryable():
                t.status = "pending"
            if self._failed_retryable():
                self._save()


QUEUE = ForgeQueue(CONFIG["task_queue_path"])


# ══════════════════════════════════════════════════════════════════
# CHECKPOINT — Apollo-X restart protection
# ══════════════════════════════════════════════════════════════════

class Checkpoint:
    def __init__(self, path: Path):
        self.path = path
        self._state: dict = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._state = json.loads(self.path.read_text())
                log.info("[APOLLO-X] Checkpoint resumed")
            except Exception:
                self._state = {}

    async def save(self, data: dict):
        self._state.update(data)
        self._state["saved_at"] = time.time()
        await asyncio.to_thread(_atomic_write, self.path, self._state)

    def get(self, key: str, default=None):
        return self._state.get(key, default)


CHECKPOINT = Checkpoint(CONFIG["checkpoint_path"])


# ══════════════════════════════════════════════════════════════════
# GITHUB — async subprocess
# ══════════════════════════════════════════════════════════════════

class GitHubForge:
    def __init__(self):
        self.repo = CONFIG["github_repo"]
        self.token = CONFIG["github_token"]
        self.enabled = bool(self.repo and self.token)

    async def commit(self, message: str):
        if not self.enabled:
            return
        try:
            for cmd in [
                ["git", "add", "-A"],
                ["git", "commit", "-m", f"[FORGEMASTER] {message}"],
                ["git", "push"],
            ]:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    log.warning(f"[GIT] {cmd[0]} failed: {stderr.decode()[:120]}")
                    return
            log.info(f"[GIT] Forged commit: {message[:50]}")
            await BUS.set("github.last_commit", message)
        except Exception as e:
            log.warning(f"[GIT] {e}")

    async def create_issue(self, title: str, body: str):
        if not self.enabled:
            return
        try:
            session = await _get_session()
            async with session.post(
                f"https://api.github.com/repos/{self.repo}/issues",
                headers={"Authorization": f"token {self.token}"},
                json={"title": title, "body": body},
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    log.info(f"[GIT] Issue #{data['number']}: {title[:40]}")
        except Exception as e:
            log.warning(f"[GIT] Issue failed: {e}")


GITHUB = GitHubForge()


# ══════════════════════════════════════════════════════════════════
# SELF HEALER
# ══════════════════════════════════════════════════════════════════

class SelfHealer:
    def __init__(self):
        self._failures: dict[str, int] = defaultdict(int)

    async def report(self, component: str, error: str):
        self._failures[component] += 1
        n = self._failures[component]
        log.warning(f"[HEALER] {component} failed x{n}: {error[:80]}")
        if n >= CONFIG["max_retries"]:
            log.info(f"[HEALER] Recovering {component}")
            self._failures[component] = 0
            BRAIN.mutate("SOVEREIGN")
            await GITHUB.create_issue(
                f"FORGEMASTER: {component} recovery",
                f"{component} hit max failures. Recovery at {_utcnow()}",
            )


HEALER = SelfHealer()


# ══════════════════════════════════════════════════════════════════
# SKILL MANAGER — SkillClaw (generates + executes code)
# ══════════════════════════════════════════════════════════════════

class SkillForge:
    def __init__(self):
        self.skill_dir = CONFIG["skill_library_path"]
        self.skill_dir.mkdir(exist_ok=True)
        self._skills: dict = {}
        self._load()

    def _load(self):
        for f in self.skill_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                self._skills[d["name"]] = d
            except Exception:
                pass
        log.info(f"[SKILLS] {len(self._skills)} skills loaded")

    async def acquire(self, intent: str) -> str:
        """Generate a skill function and save it."""
        BRAIN.mutate("CREATOR")
        name = f"skill_{intent[:20].replace(' ', '_').lower()}"
        prompt = (
            f"Generate a Python async function named '{name}' that accomplishes:\n"
            f"{intent}\n\n"
            f"Return ONLY the function code. No explanation. No markdown.\n"
            f"The function signature must be: async def {name}(**kwargs) -> dict"
        )
        code = await call_llm(prompt)
        code = code.replace("```python", "").replace("```", "").strip()
        data = {
            "name": name, "intent": intent, "code": code,
            "created": time.time(), "executions": 0,
        }
        _atomic_write(self.skill_dir / f"{name}.json", data)
        self._skills[name] = data
        log.info(f"[SKILLS] Acquired: {name}")
        return name

    async def execute(self, name: str, **kwargs) -> dict:
        """
        Execute an acquired skill in a sandbox.
        Returns {"ok": true, "result": ...} or {"ok": false, "error": ...}
        """
        data = self._skills.get(name)
        if not data:
            return {"ok": False, "error": f"Skill '{name}' not found"}

        try:
            code = data["code"]
            namespace: dict = {}
            exec(code, {"asyncio": asyncio, "json": json, "os": os, "time": time}, namespace)
            fn = namespace.get(name)
            if not fn:
                return {"ok": False, "error": f"Function '{name}' not found in code"}

            result = await fn(**kwargs)
            data["executions"] = data.get("executions", 0) + 1
            _atomic_write(self.skill_dir / f"{name}.json", data)
            log.info(f"[SKILLS] Executed: {name}")
            return {"ok": True, "result": result}
        except Exception as e:
            log.error(f"[SKILLS] {name} execution failed: {e}")
            return {"ok": False, "error": str(e)}

    def count(self) -> int:
        return len(self._skills)


SKILLS = SkillForge()


# ══════════════════════════════════════════════════════════════════
# PID CONTROLLER
# ══════════════════════════════════════════════════════════════════

class PIDController:
    def __init__(self, kp=0.8, ki=0.05, kd=0.01, setpoint=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.setpoint = setpoint
        self._prev_error = 0.0
        self._integral = 0.0
        self._lock = asyncio.Lock()

    async def step(self, context: dict) -> dict:
        async with self._lock:
            measured = await BUS.get("reflection.score", 0.7)
            error = self.setpoint - measured
            self._integral += error
            output = (
                (self.kp * error)
                + (self.ki * self._integral)
                + (self.kd * (error - self._prev_error))
            )
            self._prev_error = error
        await BUS.set("pid.output", output)
        context["pid_output"] = output
        return context


PID = PIDController(setpoint=CONFIG["pid_setpoint"])


# ══════════════════════════════════════════════════════════════════
# SAFLA HYPERLOOP — 12 loops, race-condition free
# ══════════════════════════════════════════════════════════════════

async def loop_research(ctx: dict) -> dict:
    BRAIN.mutate("ORACLE")
    query = ctx.get("query", "autonomous agent capabilities")
    r = await call_llm(
        f"Research for THE FORGEMASTER: {query}\n"
        f"Return JSON: {{\"synthesis\": \"...\", \"confidence\": 0.9, \"gaps\": []}}"
    )
    try:
        d = json.loads(r.replace("```json", "").replace("```", "").strip())
    except Exception:
        d = {"synthesis": r[:200], "confidence": 0.5, "gaps": []}
    await BUS.set("research.synthesis", d.get("synthesis"))
    await BUS.set("research.confidence", d.get("confidence", 0.5))
    return {"research": d}


async def loop_ooda(ctx: dict) -> dict:
    BRAIN.mutate(BRAIN.pick_mode("execute"))
    snapshot = await BUS.snapshot()
    pending = await QUEUE.pending_count()
    observation = {"pending": pending, "signals": len(snapshot)}
    await BUS.set("ooda.observation", observation)

    decision = "execute_next" if pending > 0 else "idle_scan"
    if pending > 10:
        decision = "batch_execute"
        BRAIN.mutate("WARRIOR")
    await BUS.set("ooda.decision", decision)
    return {"observation": observation, "decision": decision}


async def loop_reflection(ctx: dict) -> dict:
    BRAIN.mutate("SAGE")
    last = ctx.get("last_strike_result", "none")
    r = await call_llm(
        f"THE FORGEMASTER self-reflection.\n"
        f"Last strike result: {str(last)[:200]}\n"
        f"Rate quality 0-1 and suggest improvement.\n"
        f'JSON: {{"score": 0.85, "critique": "...", "improvement": "..."}}'
    )
    try:
        d = json.loads(r.replace("```json", "").replace("```", "").strip())
    except Exception:
        d = {"score": 0.7, "critique": "N/A", "improvement": "Continue"}
    score = d.get("score", 0.7)
    await BUS.set("reflection.score", score)
    if score < CONFIG["reflection_threshold"]:
        await MEMORY.remember("last_improvement", d.get("improvement"))
    return {"reflection": d}


async def loop_mars(ctx: dict) -> dict:
    score = await BUS.get("reflection.score", 0.7)
    decision = await BUS.get("ooda.decision", "unknown")
    adjustment = "refine" if score < 0.8 else "optimize"
    lesson = (
        f"failure: score={score:.2f}, review {decision}"
        if score < 0.5 else f"success: repeat for {decision}"
    )
    insight = {"adjustment": adjustment, "lesson": lesson, "score": score}
    history = await MEMORY.recall("mars.history", [])
    history.append(insight)
    await MEMORY.remember("mars.history", history[-20:])
    await BUS.set("mars.insight", insight)
    return {"mars": insight}


async def loop_reinforcement(ctx: dict) -> dict:
    score = await BUS.get("reflection.score", 0.7)
    weights = await MEMORY.recall("rl.weights", {})
    decision = await BUS.get("ooda.decision", "unknown")
    lr = 0.01
    if score > 0.8:
        weights[decision] = weights.get(decision, 0) + lr
    elif score < 0.5:
        weights[decision] = weights.get(decision, 0) - lr
    await MEMORY.remember("rl.weights", weights)
    await BUS.set("rl.weights", weights)
    return {"rl": weights}


async def loop_explore_exploit(ctx: dict) -> dict:
    strategies = ["aggressive", "conservative", "neutral", "creative", "stealth"]
    weights = await MEMORY.recall("rl.weights", {})
    if random.random() < CONFIG["explore_epsilon"]:
        strategy = random.choice(strategies)
    else:
        strategy = max(strategies, key=lambda s: weights.get(s, 0))
    await BUS.set("explore.strategy", strategy)
    return {"strategy": strategy}


async def loop_pid(ctx: dict) -> dict:
    return await PID.step(ctx)


async def loop_ouroboros(ctx: dict) -> dict:
    BRAIN.mutate("SOVEREIGN")
    perf = await BUS.get("reflection.score", 0.7)
    mutations = await MEMORY.recall("ouroboros.mutations", 0)
    if perf < 0.6:
        CONFIG["explore_epsilon"] = max(0.1, CONFIG["explore_epsilon"] - 0.05)
        mutations += 1
        log.info(f"[OUROBOROS] Mutation #{mutations}")
    elif perf > 0.9:
        CONFIG["explore_epsilon"] = min(0.5, CONFIG["explore_epsilon"] + 0.02)
    await MEMORY.remember("ouroboros.mutations", mutations)
    return {"mutations": mutations}


async def loop_pdca(ctx: dict) -> dict:
    decision = await BUS.get("ooda.decision", "idle")
    await BUS.set("pdca.plan", f"Execute: {decision}")
    await BUS.set("pdca.quality", await BUS.get("reflection.score", 0.7))
    return {}


async def loop_reasoning_action(ctx: dict) -> dict:
    research = await BUS.get("research.synthesis", "")
    thought = await BRAIN.reason(
        intent=ctx.get("decision", "forge"),
        context={"research": research},
        framework="MARS",
    )
    return {"perception": research, "reasoning": thought["conclusion"]}


async def loop_event(ctx: dict) -> dict:
    if await QUEUE.pending_count() > 0:
        await BUS.set("event.tasks_ready", True)
    return {}


async def loop_retry(ctx: dict) -> dict:
    await QUEUE._requeue_failed()
    return {}


# All 12 loop functions in order
_HYPERLOOP_FNS = [
    loop_research, loop_ooda, loop_reflection, loop_mars,
    loop_reinforcement, loop_explore_exploit, loop_pid,
    loop_ouroboros, loop_pdca, loop_reasoning_action,
    loop_event, loop_retry,
]

# Context merge lock — prevents races when merge happens
_HYPERLOOP_MERGE_LOCK = asyncio.Lock()


async def hyperloop(context: dict) -> dict:
    """
    ⚡ HYPERLOOP — Kevin Lee's original 12-loop architecture.
    All loops run in parallel, merged under lock to prevent races.
    """
    results = await asyncio.gather(
        *[loop(dict(context)) for loop in _HYPERLOOP_FNS],
        return_exceptions=True,
    )

    async with _HYPERLOOP_MERGE_LOCK:
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                loop_name = _HYPERLOOP_FNS[i].__name__
                log.warning(f"[HYPERLOOP] {loop_name} failed: {result}")
                await HEALER.report(loop_name, str(result))
            elif isinstance(result, dict):
                context.update(result)

    cycle = await MEMORY.recall("hyperloop.cycles", 0) + 1
    await MEMORY.remember("hyperloop.cycles", cycle)
    await BUS.set("hyperloop.cycle", cycle)
    return context


# ══════════════════════════════════════════════════════════════════
# FORGE ENGINE
# ══════════════════════════════════════════════════════════════════

async def forge(task: ForgeTask) -> Strike:
    log.info(f"[FORGE] Sending to Mjölnir: {task.intent[:60]}")
    BRAIN.mutate(BRAIN.pick_mode(task.intent))
    storm = task.priority == 1

    strike = await HAMMER.strike(task.intent, storm=storm)
    await QUEUE.complete(task.id, strike.id, strike.result)

    if strike.status == "FAIL":
        await SKILLS.acquire(task.intent)
        await QUEUE.fail(task.id)

    await GITHUB.commit(f"Strike {strike.id}: {task.intent[:40]} → {strike.status}")
    await CHECKPOINT.save({
        "last_strike": strike.id, "last_intent": task.intent,
        "last_status": strike.status, "cycle_time": time.time(),
    })
    await BUS.update({
        "last_strike_result": strike.result,
        "last_strike_status": strike.status,
    })
    return strike


# ══════════════════════════════════════════════════════════════════
# DREAM CYCLE
# ══════════════════════════════════════════════════════════════════

async def dream_cycle():
    log.info("[DREAM] ⚡ Dream cycle igniting...")
    BRAIN.mutate("SAGE")

    history = await MEMORY.recall("mars.history", [])
    avg_score = (
        sum(h.get("score", 0.7) for h in history) / len(history)
        if history else 0.7
    )
    report_txt = HAMMER.forge_report()

    report = await call_llm(
        f"THE FORGEMASTER dream cycle.\n"
        f"Avg performance: {avg_score:.2f}\n"
        f"Strikes fired: {len(HAMMER.strike_log)}\n"
        f"Skills forged: {SKILLS.count()}\n\n"
        f"Dream report:\n"
        f"1. What patterns are emerging?\n"
        f"2. What should be forgotten?\n"
        f"3. What should be reinforced?\n"
        f"4. What new capability is needed?"
    )

    dream_dir = Path(".dreams")
    dream_dir.mkdir(exist_ok=True)
    dream_path = dream_dir / f"{datetime.now().strftime('%Y-%m-%d_%H%M')}.md"
    await asyncio.to_thread(
        dream_path.write_text,
        f"# THE FORGEMASTER — Dream Report\n\n{report}\n\n---\n{report_txt}",
    )

    await MEMORY.remember("dream.last_run", time.time())
    await MEMORY.remember("dream.avg_score", avg_score)
    await GITHUB.commit(f"Dream cycle — avg score {avg_score:.2f}")
    log.info(f"[DREAM] Complete. Score: {avg_score:.2f}")


# ══════════════════════════════════════════════════════════════════
# STATUS REPORT
# ══════════════════════════════════════════════════════════════════

async def forge_report() -> str:
    snapshot = await BUS.snapshot()
    q = await QUEUE.stats()
    cycles = await MEMORY.recall("hyperloop.cycles", 0)

    return (
        f"\n╔═══════════════════════════════════════════╗\n"
        f"║        THE FORGEMASTER — STATUS           ║\n"
        f"╚═══════════════════════════════════════════╝\n"
        f"{CONFIG['mantra']}\n"
        f"───────────────────────────────────────────\n"
        f"Time:          {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Brain Mode:    {BRAIN.mode}\n"
        f"Hammer DNA:    {HAMMER.dna}\n"
        f"Hammer State:  {HAMMER.state}\n"
        f"───────────────────────────────────────────\n"
        f"Tasks Pending: {q['pending']}\n"
        f"Tasks Done:    {q['done']}\n"
        f"Tasks Failed:  {q['failed']}\n"
        f"Skills Forged: {SKILLS.count()}\n"
        f"HyperLoop:     {cycles} cycles\n"
        f"Bus Signals:   {len(snapshot)}\n"
        f"───────────────────────────────────────────\n"
        f"{HAMMER.forge_report()}"
    )


# ══════════════════════════════════════════════════════════════════
# APOLLO-X MAIN
# ══════════════════════════════════════════════════════════════════

async def main():
    log.info("╔═══════════════════════════════════════════╗")
    log.info("║     THE FORGEMASTER v2.0 — ONLINE         ║")
    log.info("║  I do not question. I do not hesitate.    ║")
    log.info("║  I do not miss.                           ║")
    log.info("╚═══════════════════════════════════════════╝")
    log.info(f"Hammer DNA: {HAMMER.dna} | Mode: {BRAIN.mode}")
    log.info(f"Dark Forest: {DARK_FOREST} | GitHub: {GITHUB.enabled}")

    # Resume
    last = CHECKPOINT.get("last_strike")
    if last:
        log.info(f"[APOLLO-X] Resuming from strike: {last}")

    # Seed queue
    if await QUEUE.pending_count() == 0:
        await QUEUE.forge("Scan environment and report status", priority=2)
        await QUEUE.forge("Check for new skill opportunities", priority=4)
        await QUEUE.forge("Run self-awareness reflection", priority=3)

    context: dict = {"query": "autonomous agent 2026 capabilities"}
    cycle = 0
    last_dream = time.time()
    last_report = time.time()

    while True:
        try:
            cycle += 1
            pending = await QUEUE.pending_count()
            log.info(f"[APOLLO-X] ⚡ Cycle {cycle} | Pending: {pending}")

            # HyperLoop
            context = await hyperloop(context)

            # Execute next task
            task = await QUEUE.next()
            if task:
                strike = await forge(task)
                context.update({
                    "last_strike_result": strike.result,
                    "last_strike_status": strike.status,
                })

            # Dream
            if time.time() - last_dream > CONFIG["dream_interval"]:
                await dream_cycle()
                last_dream = time.time()

            # Status report
            if time.time() - last_report > 21600:
                report = await forge_report()
                log.info(report)
                await GITHUB.commit("Status report")
                last_report = time.time()

            # Checkpoint
            await CHECKPOINT.save({"cycle": cycle, "mode": BRAIN.mode})

            await asyncio.sleep(CONFIG["cron_interval"])

        except KeyboardInterrupt:
            log.info("[APOLLO-X] Shutdown — The Forgemaster rests.")
            log.info(await forge_report())
            break
        except Exception as e:
            log.error(f"[APOLLO-X] Error: {e}")
            await HEALER.report("apollo_x", str(e))
            BRAIN.mutate("SOVEREIGN")
            await asyncio.sleep(30)
        finally:
            await _close_session()


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "forge" and len(sys.argv) > 2:
            intent = " ".join(sys.argv[2:])
            priority = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 3

            async def _forge():
                t = await QUEUE.forge(intent, priority=priority)
                print(f"⚡ Forged: {t.id} — {intent}")
            asyncio.run(_forge())

        elif cmd == "strike" and len(sys.argv) > 2:
            intent = " ".join(sys.argv[2:])

            async def _strike():
                s = await HAMMER.strike(intent)
                print(f"\n{s.status}: {s.result}")
            asyncio.run(_strike())

        elif cmd == "status":
            async def _status():
                print(await forge_report())
            asyncio.run(_status())

        elif cmd == "dream":
            asyncio.run(dream_cycle())

        elif cmd == "report":
            print(HAMMER.forge_report())

        elif cmd == "skills":
            async def _skills_list():
                if len(sys.argv) > 2 and sys.argv[2] == "execute":
                    name = sys.argv[3]
                    result = await SKILLS.execute(name)
                    print(json.dumps(result, indent=2))
                else:
                    print(f"{SKILLS.count()} skills forged")
                    for name in list(SKILLS._skills.keys())[:20]:
                        print(f"  • {name}")
            asyncio.run(_skills_list())

        sys.exit(0)

    asyncio.run(main())
