#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════╗
║              THE FORGEMASTER                          ║
║    "I do not question. I do not hesitate.             ║
║     I do not miss."                                   ║
╠═══════════════════════════════════════════════════════╣
║  Will    → ZEUS        (judges intent)                ║
║  Bridge  → THOR        (routes execution)             ║
║  Strike  → CLAW        (hits the target)              ║
║  Mind    → LiquidBrain (8 cognitive modes)            ║
║  Soul    → Liquid Trinity (DNA + Memory)              ║
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
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(name)s] %(message)s"
)
log = logging.getLogger("FORGEMASTER")

DARK_FOREST = os.getenv("DARK_FOREST", "false").lower() == "true"
if DARK_FOREST:
    logging.disable(logging.INFO)


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

CONFIG = {
    "name": "THE FORGEMASTER",
    "version": "1.0.0",
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
}


# ─────────────────────────────────────────────
# STATE BUS
# ─────────────────────────────────────────────

class StateBus:
    def __init__(self):
        self._state: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any):
        async with self._lock:
            self._state[key] = value
        for cb in self._subscribers.get(key, []):
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


# ─────────────────────────────────────────────
# LIQUID BRAIN — 8 cognitive modes
# ─────────────────────────────────────────────

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
        self.thought_log = []
        self.mutation_log = []
        self.chain_id = self._new_id()

    def _new_id(self) -> str:
        return hashlib.sha256(f"{self.mode}:{time.time_ns()}".encode()).hexdigest()[:16]

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    def reason(self, intent: str, context: dict = None, framework: str = "OODA") -> dict:
        fw = framework.upper() if framework.upper() in self.FRAMEWORKS else "OODA"
        thought = {
            "chain_id": self._new_id(),
            "mode": self.mode,
            "framework": fw,
            "intent": intent,
            "temperature": self.MODES[self.mode]["temperature"],
            "timestamp": self._timestamp(),
            "conclusion": f"Resolved via {fw} under {self.mode}",
            "confidence": 0.85,
        }
        self.thought_log.append(thought)
        return thought

    def mutate(self, new_mode: str):
        if new_mode.upper() not in self.MODES:
            return
        old = self.mode
        self.mode = new_mode.upper()
        self.mutation_log.append({"from": old, "to": self.mode})
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


# ─────────────────────────────────────────────
# LIQUID MEMORY
# ─────────────────────────────────────────────

class LiquidMemory:
    def __init__(self, path: Path):
        self.path = path
        self._mem: dict = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._mem = json.loads(self.path.read_text())
            except Exception:
                self._mem = {}

    def _save(self):
        self.path.write_text(json.dumps(self._mem, indent=2))

    def remember(self, key: str, value: Any):
        self._mem[key] = {"value": value, "ts": time.time()}
        self._save()

    def recall(self, key: str, default=None) -> Any:
        entry = self._mem.get(key)
        return entry["value"] if entry else default

    def snapshot(self) -> dict:
        return dict(self._mem)


MEMORY = LiquidMemory(CONFIG["memory_path"])


# ─────────────────────────────────────────────
# MULTI-LLM — DeepSeek + Groq + Gemini
# ─────────────────────────────────────────────

async def call_llm(
    prompt: str,
    system: str = "You are THE FORGEMASTER — a fully autonomous AI agent. I do not question. I do not hesitate. I do not miss."
) -> str:
    providers = list(CONFIG["llm_providers"].items())
    random.shuffle(providers)

    for name, cfg in providers:
        if not cfg["api_key"]:
            continue
        try:
            import aiohttp
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
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cfg['base_url']}/chat/completions",
                    headers=headers, json=payload, timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        await BUS.set("llm.provider", name)
                        log.info(f"[LLM] Strike via {name}")
                        return content
        except Exception as e:
            log.warning(f"[LLM] {name} failed: {e}")

    return "[FORGEMASTER] All providers unavailable. Standing by."


# ─────────────────────────────────────────────
# ⚡ MJÖLNIR — The Hammer That Never Misses
# ─────────────────────────────────────────────

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
    """
    The Hammer of Zeus.
    Zeus judges. Thor bridges. Claw strikes.
    One intent. One strike. One return.
    """

    def __init__(self):
        self.state = MjolnirState.RESTING
        self.strike_log: list[Strike] = []
        self.dna = hashlib.sha256(f"MJOLNIR:{time.time_ns()}".encode()).hexdigest()[:12]
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
        self._forge_log_path.write_text(
            json.dumps([s.__dict__ for s in self.strike_log[-100:]], indent=2)
        )

    # ── ZEUS: Judge the intent ──
    async def zeus_judge(self, intent: str) -> tuple[bool, str]:
        self.state = MjolnirState.AIMING
        BRAIN.mutate("SOVEREIGN")

        prompt = f"""
You are ZEUS — The Will of the Forgemaster.
Judge this intent: "{intent}"

Is this worthy of a strike?
Consider: Is it actionable? Is it clear? Does it serve the Forgemaster?

Respond as JSON only:
{{"worthy": true, "reason": "...", "refined_intent": "..."}}
"""
        response = await call_llm(prompt, system="You are ZEUS. You judge. You command.")
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
            return True, intent  # Default: trust the Forgemaster

    # ── THOR: Bridge the intent to action ──
    async def thor_bridge(self, intent: str) -> dict:
        BRAIN.mutate("ARCHITECT")

        prompt = f"""
You are THOR — The Bridge.
Translate this intent into an execution plan: "{intent}"

Route it across the Bifrost:
- What tools/skills are needed?
- What is the exact sequence of actions?
- What is the expected outcome?

Respond as JSON only:
{{"tools": ["..."], "steps": ["..."], "outcome": "...", "route": "..."}}
"""
        response = await call_llm(prompt, system="You are THOR. You bridge. You translate.")
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            log.info(f"[THOR] Bifrost route: {data.get('route', 'direct')}")
            await BUS.set("thor.last_bridge", data)
            return data
        except Exception:
            return {"tools": [], "steps": [intent], "outcome": "unknown", "route": "direct"}

    # ── CLAW: Execute the strike ──
    async def claw_strike(self, intent: str, bridge: dict) -> str:
        self.state = MjolnirState.STRIKING
        BRAIN.mutate("WARRIOR")

        steps = bridge.get("steps", [intent])
        tools = bridge.get("tools", [])

        prompt = f"""
You are CLAW — The Strike.
Execute this intent: "{intent}"

Steps to follow: {json.dumps(steps)}
Tools available: {json.dumps(tools)}
Expected outcome: {bridge.get('outcome', 'complete the task')}

Execute now. Return the result.
Be specific. Be complete. Do not hesitate.
"""
        result = await call_llm(prompt, system="You are CLAW. You execute. You strike. You do not miss.")
        log.info(f"[CLAW] Strike complete: {result[:80]}...")
        await BUS.set("claw.last_strike", result[:200])
        return result

    # ── THE STRIKE — full pipeline ──
    async def strike(self, intent: str, storm: bool = False) -> Strike:
        """
        One intent. One strike. One return.
        Zeus → Thor → Claw → Return.
        """
        # Cooldown check (unless STORM mode)
        elapsed = time.time() - self._last_strike
        if not storm and elapsed < CONFIG["mjolnir_cooldown"]:
            await asyncio.sleep(CONFIG["mjolnir_cooldown"] - elapsed)

        strike_id = f"STRIKE_{hashlib.sha256(f'{intent}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        log.info(f"[MJÖLNIR] ⚡ {strike_id} — {intent[:60]}")

        s = Strike(id=strike_id, intent=intent, mode=BRAIN.mode)

        try:
            # ZEUS — judge
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

            # THOR — bridge
            bridge = await self.thor_bridge(refined)

            # CLAW — strike
            result = await self.claw_strike(refined, bridge)

            # RETURN
            self.state = MjolnirState.RETURNING
            s.status = "SUCCESS"
            s.result = result
            self._last_strike = time.time()

            await BUS.set("mjolnir.last_strike", strike_id)
            await BUS.set("mjolnir.last_result", result[:200])
            MEMORY.remember(f"strike.{strike_id}", s.__dict__)

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

        return f"""
╔══════════════════════════════════════╗
║         MJÖLNIR FORGE REPORT        ║
╚══════════════════════════════════════╝
DNA:       {self.dna}
State:     {self.state}
Strikes:   {total}
Success:   {success} ({rate:.1f}%)
Denied:    {denied}
Failed:    {failed}
Last:      {self.strike_log[-1].id if self.strike_log else 'none'}
"""


HAMMER = Mjolnir()


# ─────────────────────────────────────────────
# TASK QUEUE
# ─────────────────────────────────────────────

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
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                self._tasks = [ForgeTask(**t) for t in raw]
            except Exception:
                self._tasks = []

    def _save(self):
        self.path.write_text(json.dumps(
            [t.__dict__ for t in self._tasks], indent=2
        ))

    def forge(self, intent: str, priority: int = 3) -> ForgeTask:
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

    def next(self) -> Optional[ForgeTask]:
        pending = [t for t in self._tasks if t.status == "pending"]
        return pending[0] if pending else None

    def complete(self, task_id: str, strike_id: str, result: Any):
        for t in self._tasks:
            if t.id == task_id:
                t.status = "done"
                t.strike_id = strike_id
                t.result = result
        self._save()

    def fail(self, task_id: str):
        for t in self._tasks:
            if t.id == task_id:
                t.retries += 1
                if t.retries >= CONFIG["max_retries"]:
                    t.status = "failed"
                else:
                    t.status = "pending"
        self._save()

    def pending_count(self) -> int:
        return len([t for t in self._tasks if t.status == "pending"])

    def stats(self) -> dict:
        return {
            "total": len(self._tasks),
            "pending": self.pending_count(),
            "done": len([t for t in self._tasks if t.status == "done"]),
            "failed": len([t for t in self._tasks if t.status == "failed"]),
        }


QUEUE = ForgeQueue(CONFIG["task_queue_path"])


# ─────────────────────────────────────────────
# CHECKPOINT — Apollo-X restart protection
# ─────────────────────────────────────────────

class Checkpoint:
    def __init__(self, path: Path):
        self.path = path
        self._state: dict = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._state = json.loads(self.path.read_text())
                log.info(f"[APOLLO-X] Checkpoint resumed")
            except Exception:
                self._state = {}

    def save(self, data: dict):
        self._state.update(data)
        self._state["saved_at"] = time.time()
        self.path.write_text(json.dumps(self._state, indent=2))

    def get(self, key: str, default=None):
        return self._state.get(key, default)


CHECKPOINT = Checkpoint(CONFIG["checkpoint_path"])


# ─────────────────────────────────────────────
# GITHUB — self-committing
# ─────────────────────────────────────────────

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
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode != 0:
                    break
            log.info(f"[GIT] Forged commit: {message[:50]}")
            await BUS.set("github.last_commit", message)
        except Exception as e:
            log.warning(f"[GIT] {e}")

    async def create_issue(self, title: str, body: str):
        if not self.enabled:
            return
        try:
            import aiohttp
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"https://api.github.com/repos/{self.repo}/issues",
                    headers={"Authorization": f"token {self.token}"},
                    json={"title": title, "body": body}
                ) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        log.info(f"[GIT] Issue #{data['number']}: {title[:40]}")
        except Exception as e:
            log.warning(f"[GIT] Issue failed: {e}")


GITHUB = GitHubForge()


# ─────────────────────────────────────────────
# SELF HEALER
# ─────────────────────────────────────────────

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
                f"{component} hit max failures. Recovery at {datetime.now().isoformat()}"
            )


HEALER = SelfHealer()


# ─────────────────────────────────────────────
# SKILL MANAGER — SkillClaw integration
# ─────────────────────────────────────────────

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
        BRAIN.mutate("CREATOR")
        name = f"skill_{intent[:20].replace(' ', '_').lower()}"
        prompt = f"""
Generate a Python async function named '{name}' that accomplishes:
{intent}

Return only the function code. No explanation.
"""
        code = await call_llm(prompt)
        data = {"name": name, "intent": intent, "code": code, "created": time.time()}
        (self.skill_dir / f"{name}.json").write_text(json.dumps(data, indent=2))
        self._skills[name] = data
        log.info(f"[SKILLS] Acquired: {name}")
        return name

    def count(self) -> int:
        return len(self._skills)


SKILLS = SkillForge()


# ─────────────────────────────────────────────
# PID CONTROLLER
# ─────────────────────────────────────────────

class PIDController:
    def __init__(self, kp=0.8, ki=0.05, kd=0.01, setpoint=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.setpoint = setpoint
        self._prev_error = 0.0
        self._integral = 0.0

    async def step(self, context: dict) -> dict:
        measured = await BUS.get("reflection.score", 0.7)
        error = self.setpoint - measured
        self._integral += error
        output = (self.kp * error) + (self.ki * self._integral) + (self.kd * (error - self._prev_error))
        self._prev_error = error
        await BUS.set("pid.output", output)
        context["pid_output"] = output
        return context


PID = PIDController(setpoint=CONFIG["pid_setpoint"])


# ─────────────────────────────────────────────
# SAFLA HYPERLOOP — 12 loops in parallel
# ─────────────────────────────────────────────

async def loop_research(ctx: dict) -> dict:
    BRAIN.mutate("ORACLE")
    query = ctx.get("query", "autonomous agent capabilities")
    prompt = f"""
Research for THE FORGEMASTER: {query}
Return JSON: {{"synthesis": "...", "confidence": 0.9, "gaps": []}}
"""
    r = await call_llm(prompt)
    try:
        d = json.loads(r.replace("```json","").replace("```","").strip())
    except Exception:
        d = {"synthesis": r[:200], "confidence": 0.5, "gaps": []}
    await BUS.set("research.synthesis", d.get("synthesis"))
    await BUS.set("research.confidence", d.get("confidence", 0.5))
    ctx["research"] = d
    return ctx

async def loop_ooda(ctx: dict) -> dict:
    BRAIN.mutate(BRAIN.pick_mode("execute"))
    snapshot = await BUS.snapshot()
    pending = QUEUE.pending_count()
    ctx["observation"] = {"pending": pending, "signals": len(snapshot)}
    await BUS.set("ooda.observation", ctx["observation"])
    decision = "execute_next" if pending > 0 else "idle_scan"
    if pending > 10:
        decision = "batch_execute"
        BRAIN.mutate("WARRIOR")
    await BUS.set("ooda.decision", decision)
    ctx["decision"] = decision
    return ctx

async def loop_reflection(ctx: dict) -> dict:
    BRAIN.mutate("SAGE")
    last = ctx.get("last_strike_result", "none")
    prompt = f"""
THE FORGEMASTER self-reflection.
Last strike result: {str(last)[:200]}
Rate quality 0-1 and suggest improvement.
JSON: {{"score": 0.85, "critique": "...", "improvement": "..."}}
"""
    r = await call_llm(prompt)
    try:
        d = json.loads(r.replace("```json","").replace("```","").strip())
    except Exception:
        d = {"score": 0.7, "critique": "N/A", "improvement": "Continue"}
    score = d.get("score", 0.7)
    await BUS.set("reflection.score", score)
    ctx["reflection"] = d
    if score < CONFIG["reflection_threshold"]:
        MEMORY.remember("last_improvement", d.get("improvement"))
    return ctx

async def loop_mars(ctx: dict) -> dict:
    score = await BUS.get("reflection.score", 0.7)
    decision = await BUS.get("ooda.decision", "unknown")
    adjustment = "refine" if score < 0.8 else "optimize"
    lesson = (
        f"failure: score={score:.2f}, review {decision}"
        if score < 0.5
        else f"success: repeat for {decision}"
    )
    insight = {"adjustment": adjustment, "lesson": lesson, "score": score}
    history = MEMORY.recall("mars.history", [])
    history.append(insight)
    MEMORY.remember("mars.history", history[-20:])
    await BUS.set("mars.insight", insight)
    ctx["mars"] = insight
    return ctx

async def loop_reinforcement(ctx: dict) -> dict:
    score = await BUS.get("reflection.score", 0.7)
    weights = MEMORY.recall("rl.weights", {})
    decision = await BUS.get("ooda.decision", "unknown")
    lr = 0.01
    if score > 0.8:
        weights[decision] = weights.get(decision, 0) + lr
    elif score < 0.5:
        weights[decision] = weights.get(decision, 0) - lr
    MEMORY.remember("rl.weights", weights)
    await BUS.set("rl.weights", weights)
    ctx["rl"] = weights
    return ctx

async def loop_explore_exploit(ctx: dict) -> dict:
    strategies = ["aggressive", "conservative", "neutral", "creative", "stealth"]
    weights = MEMORY.recall("rl.weights", {})
    if random.random() < CONFIG["explore_epsilon"]:
        strategy = random.choice(strategies)
    else:
        strategy = max(strategies, key=lambda s: weights.get(s, 0))
    await BUS.set("explore.strategy", strategy)
    ctx["strategy"] = strategy
    return ctx

async def loop_pid(ctx: dict) -> dict:
    return await PID.step(ctx)

async def loop_ouroboros(ctx: dict) -> dict:
    BRAIN.mutate("SOVEREIGN")
    perf = await BUS.get("reflection.score", 0.7)
    mutations = MEMORY.recall("ouroboros.mutations", 0)
    if perf < 0.6:
        CONFIG["explore_epsilon"] = max(0.1, CONFIG["explore_epsilon"] - 0.05)
        mutations += 1
        log.info(f"[OUROBOROS] Mutation #{mutations}")
    elif perf > 0.9:
        CONFIG["explore_epsilon"] = min(0.5, CONFIG["explore_epsilon"] + 0.02)
    MEMORY.remember("ouroboros.mutations", mutations)
    ctx["mutations"] = mutations
    return ctx

async def loop_pdca(ctx: dict) -> dict:
    decision = await BUS.get("ooda.decision", "idle")
    await BUS.set("pdca.plan", f"Execute: {decision}")
    await BUS.set("pdca.quality", await BUS.get("reflection.score", 0.7))
    return ctx

async def loop_reasoning_action(ctx: dict) -> dict:
    research = await BUS.get("research.synthesis", "")
    ctx["perception"] = research
    thought = BRAIN.reason(
        intent=ctx.get("decision", "forge"),
        framework="MARS"
    )
    ctx["reasoning"] = thought["conclusion"]
    return ctx

async def loop_event(ctx: dict) -> dict:
    # Event-driven: check for new tasks dropped externally
    if QUEUE.pending_count() > 0:
        await BUS.set("event.tasks_ready", True)
    return ctx

async def loop_retry(ctx: dict) -> dict:
    # Surface failed tasks back to pending if retries remain
    failed = [t for t in QUEUE._tasks if t.status == "failed" and t.retries < CONFIG["max_retries"]]
    for t in failed:
        t.status = "pending"
    if failed:
        QUEUE._save()
        log.info(f"[RETRY] Re-queued {len(failed)} tasks")
    return ctx


# HyperLoop — Kevin's original: all 12 loops in parallel
async def hyperloop(context: dict) -> dict:
    """
    ⚡ HYPERLOOP — Kevin Lee's original architecture.
    All 12 loops run in parallel, cross-feeding via StateBus.
    """
    loops = [
        loop_research,
        loop_ooda,
        loop_reflection,
        loop_mars,
        loop_reinforcement,
        loop_explore_exploit,
        loop_pid,
        loop_ouroboros,
        loop_pdca,
        loop_reasoning_action,
        loop_event,
        loop_retry,
    ]

    # Run all 12 in parallel
    results = await asyncio.gather(
        *[loop(dict(context)) for loop in loops],
        return_exceptions=True
    )

    # Merge results back into context
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            loop_name = loops[i].__name__
            log.warning(f"[HYPERLOOP] {loop_name} failed: {result}")
            await HEALER.report(loop_name, str(result))
        elif isinstance(result, dict):
            context.update(result)

    await BUS.set("hyperloop.cycle", MEMORY.recall("hyperloop.cycles", 0) + 1)
    MEMORY.remember("hyperloop.cycles", MEMORY.recall("hyperloop.cycles", 0) + 1)
    return context


# ─────────────────────────────────────────────
# FORGE ENGINE — execute via Mjölnir
# ─────────────────────────────────────────────

async def forge(task: ForgeTask) -> Strike:
    """Route a task through the full Mjölnir pipeline"""
    log.info(f"[FORGE] Sending to Mjölnir: {task.intent[:60]}")
    BRAIN.mutate(BRAIN.pick_mode(task.intent))

    # Critical tasks enter STORM mode
    storm = task.priority == 1

    strike = await HAMMER.strike(task.intent, storm=storm)
    QUEUE.complete(task.id, strike.id, strike.result)

    # Acquire skill if needed
    if strike.status == "FAIL":
        await SKILLS.acquire(task.intent)
        QUEUE.fail(task.id)

    # Commit to GitHub
    await GITHUB.commit(f"Strike {strike.id}: {task.intent[:40]} → {strike.status}")

    # Save checkpoint
    CHECKPOINT.save({
        "last_strike": strike.id,
        "last_intent": task.intent,
        "last_status": strike.status,
        "cycle_time": time.time(),
    })

    ctx_update = {"last_strike_result": strike.result, "last_strike_status": strike.status}
    await BUS.update(ctx_update)
    return strike


# ─────────────────────────────────────────────
# DREAM CYCLE
# ─────────────────────────────────────────────

async def dream_cycle():
    log.info("[DREAM] ⚡ Dream cycle igniting...")
    BRAIN.mutate("SAGE")

    history = MEMORY.recall("mars.history", [])
    avg_score = (
        sum(h.get("score", 0.7) for h in history) / len(history)
        if history else 0.7
    )
    report_txt = HAMMER.forge_report()

    prompt = f"""
THE FORGEMASTER dream cycle.
Avg performance: {avg_score:.2f}
Strikes fired: {len(HAMMER.strike_log)}
Skills forged: {SKILLS.count()}

Dream report:
1. What patterns are emerging?
2. What should be forgotten?
3. What should be reinforced?
4. What new capability is needed?
"""
    report = await call_llm(prompt)

    dream_path = Path(f".dreams/{datetime.now().strftime('%Y-%m-%d_%H%M')}.md")
    dream_path.parent.mkdir(exist_ok=True)
    dream_path.write_text(
        f"# THE FORGEMASTER — Dream Report\n\n{report}\n\n---\n{report_txt}"
    )

    MEMORY.remember("dream.last_run", time.time())
    MEMORY.remember("dream.avg_score", avg_score)
    await GITHUB.commit(f"Dream cycle — avg score {avg_score:.2f}")
    log.info(f"[DREAM] Complete. Score: {avg_score:.2f}")


# ─────────────────────────────────────────────
# STATUS REPORT
# ─────────────────────────────────────────────

async def forge_report() -> str:
    snapshot = await BUS.snapshot()
    q = QUEUE.stats()
    cycles = MEMORY.recall("hyperloop.cycles", 0)

    return f"""
╔═══════════════════════════════════════════╗
║        THE FORGEMASTER — STATUS           ║
╚═══════════════════════════════════════════╝
{CONFIG['mantra']}
───────────────────────────────────────────
Time:          {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
Brain Mode:    {BRAIN.mode}
Hammer DNA:    {HAMMER.dna}
Hammer State:  {HAMMER.state}
───────────────────────────────────────────
Tasks Pending: {q['pending']}
Tasks Done:    {q['done']}
Tasks Failed:  {q['failed']}
Skills Forged: {SKILLS.count()}
HyperLoop:     {cycles} cycles
Bus Signals:   {len(snapshot)}
───────────────────────────────────────────
{HAMMER.forge_report()}
"""


# ─────────────────────────────────────────────
# APOLLO-X MAIN — The engine that never stops
# ─────────────────────────────────────────────

async def main():
    log.info("╔═══════════════════════════════════════════╗")
    log.info("║          THE FORGEMASTER — ONLINE         ║")
    log.info("║  I do not question. I do not hesitate.    ║")
    log.info("║  I do not miss.                           ║")
    log.info("╚═══════════════════════════════════════════╝")
    log.info(f"Hammer DNA: {HAMMER.dna} | Mode: {BRAIN.mode}")
    log.info(f"Dark Forest: {DARK_FOREST} | GitHub: {GITHUB.enabled}")

    # Resume from checkpoint
    last = CHECKPOINT.get("last_strike")
    if last:
        log.info(f"[APOLLO-X] Resuming from strike: {last}")

    # Seed queue if empty
    if QUEUE.pending_count() == 0:
        QUEUE.forge("Scan environment and report status", priority=2)
        QUEUE.forge("Check for new skill opportunities", priority=4)
        QUEUE.forge("Run self-awareness reflection", priority=3)

    context: dict = {"query": "autonomous agent 2026 capabilities"}
    cycle = 0
    last_dream = time.time()
    last_report = time.time()

    while True:
        try:
            cycle += 1
            log.info(f"[APOLLO-X] ⚡ Cycle {cycle} | Pending: {QUEUE.pending_count()}")

            # HyperLoop — all 12 loops in parallel
            context = await hyperloop(context)

            # Execute next task through Mjölnir
            task = QUEUE.next()
            if task:
                strike = await forge(task)
                context["last_strike_result"] = strike.result
                context["last_strike_status"] = strike.status

            # Dream cycle
            if time.time() - last_dream > CONFIG["dream_interval"]:
                await dream_cycle()
                last_dream = time.time()

            # Status report every 6 hours
            if time.time() - last_report > 21600:
                report = await forge_report()
                log.info(report)
                await GITHUB.commit("Status report")
                last_report = time.time()

            # Checkpoint
            CHECKPOINT.save({"cycle": cycle, "mode": BRAIN.mode})

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


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "forge" and len(sys.argv) > 2:
            intent = " ".join(sys.argv[2:])
            priority = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 3
            t = QUEUE.forge(intent, priority=priority)
            print(f"⚡ Forged: {t.id} — {intent}")

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

        sys.exit(0)

    asyncio.run(main())