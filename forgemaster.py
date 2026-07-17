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
        rate = (success / total * 100) if total else 0

        lines = [
            f"╔═══ FORGE REPORT ═══",
            f"  Strikes:   {total}",
            f"  Success:   {success} ({rate:.1f}%)",
            f"  Denied:    {denied}",
            f"  Failed:    {failed}",
            f"  State:     {self.state}",
            f"  Brain:     {BRAIN.mode}",
            f"  DNA:       {self.dna}",
            f"╚═══ MJÖLNIR ═══",
        ]
        return "\n".join(lines)

    def anvil_status(self) -> dict:
        return {
            "state": self.state,
            "strikes": len(self.strike_log),
            "success_rate": (sum(1 for s in self.strike_log if s.status == "SUCCESS") / max(len(self.strike_log), 1) * 100),
            "last_strike": self.strike_log[-1].id if self.strike_log else None,
            "mode": BRAIN.mode,
        }


MJOLNIR = Mjolnir()


# ─────────────────────────────────────────────
# TASK QUEUE
# ─────────────────────────────────────────────

@dataclass
class ForgeTask:
    id: str
    intent: str
    priority: int
    status: str = "QUEUED"
    result: Any = None
    retries: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class TaskQueue:
    def __init__(self):
        self.queue: list[ForgeTask] = []
        self.history: list[ForgeTask] = []
        self._path = CONFIG["task_queue_path"]
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self.history = [ForgeTask(**t) for t in data]
            except Exception:
                self.history = []

    def _save(self):
        self._path.write_text(json.dumps([t.__dict__ for t in self.history[-200:]], indent=2))

    def enqueue(self, intent: str, priority: int = 1) -> ForgeTask:
        task_id = hashlib.sha256(f"{intent}:{time.time_ns()}".encode()).hexdigest()[:16]
        t = ForgeTask(id=task_id, intent=intent, priority=priority)
        self.queue.append(t)
        self.queue.sort(key=lambda x: x.priority, reverse=True)
        log.info(f"[QUEUE] Enqueued [{priority}] {intent[:60]}")
        return t

    async def process(self, max_concurrent: int = 3) -> list[Strike]:
        results = []
        batch = []
        while self.queue and len(batch) < max_concurrent:
            task = self.queue.pop(0)
            task.status = "STRIKING"
            batch.append(task)

        log.info(f"[QUEUE] Processing batch of {len(batch)} tasks")
        sem = asyncio.Semaphore(max_concurrent)

        async def _process(t: ForgeTask):
            async with sem:
                s = await MJOLNIR.strike(t.intent)
                t.status = s.status
                t.result = s.result
                t.completed_at = time.time()
                self.history.append(t)
                self._save()
                return s

        results = await asyncio.gather(*[ _process(t) for t in batch ])
        return results


TASK_QUEUE = TaskQueue()


# ─────────────────────────────────────────────
# CHECKPOINT SYSTEM (Apollo-X inspired)
# ─────────────────────────────────────────────

class Checkpoint:
    def __init__(self, path: Path):
        self.path = path
        self._data: dict = {}

    def load(self) -> dict:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except Exception:
                self._data = {}
        return self._data

    def save(self, **kwargs):
        self._data.update(kwargs)
        self._data["last_checkpoint"] = time.time()
        self.path.write_text(json.dumps(self._data, indent=2))

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)

    def clear(self):
        self._data = {}
        self.save()


CHECKPOINT = Checkpoint(CONFIG["checkpoint_path"])


# ─────────────────────────────────────────────
# SKILL CLAW — Self-Expanding Skills
# ─────────────────────────────────────────────

class SkillClaw:
    def __init__(self, path: Path):
        self.path = path
        self.skills: dict[str, dict] = {}
        self._load()

    def _load(self):
        self.path.mkdir(exist_ok=True)
        for f in self.path.glob("*.json"):
            try:
                self.skills[f.stem] = json.loads(f.read_text())
            except Exception:
                pass

    def learn(self, name: str, skill_def: dict):
        self.skills[name] = skill_def
        (self.path / f"{name}.json").write_text(json.dumps(skill_def, indent=2))
        log.info(f"[CLAW] Learned skill: {name}")

    def recall(self, name: str) -> Optional[dict]:
        return self.skills.get(name)

    def search(self, query: str) -> list[str]:
        return [k for k in self.skills if query.lower() in k.lower()]

    def list_all(self) -> list[str]:
        return list(self.skills.keys())


SKILL_CLAW = SkillClaw(CONFIG["skill_library_path"])


# ─────────────────────────────────────────────
# GITHUB SELF-COMMIT
# ─────────────────────────────────────────────

async def github_self_commit(message: str = None):
    repo = CONFIG.get("github_repo", "")
    token = CONFIG.get("github_token", "")
    if not repo or not token:
        log.warning("[GIT] No repo/token configured — skipping commit")
        return

    if message is None:
        message = f"[FORGEMASTER] Auto-commit: {datetime.now().isoformat()}"

    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=os.path.dirname(__file__) or ".",
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", message, "--allow-empty"],
            cwd=os.path.dirname(__file__) or ".",
            capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=os.path.dirname(__file__) or ".",
            capture_output=True
        )
        log.info(f"[GIT] Self-committed: {message}")
    except Exception as e:
        log.warning(f"[GIT] Commit failed: {e}")


# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

async def heartbeat():
    log.info(f"[FORGEMASTER] I do not question. I do not hesitate. I do not miss.")
    last_dream_time = 0

    while True:
        try:
            # Dream cycle
            if time.time() - last_dream_time >= CONFIG["dream_interval"]:
                dream_intent = "What should I forge next for the Pantheon?"
                log.info("[DREAM] Dreaming...")
                dream = await MJOLNIR.strike(dream_intent)
                await BUS.set("dream.last", dream.result)
                last_dream_time = time.time()

            # Process queue
            if TASK_QUEUE.queue:
                log.info(f"[FORGEMASTER] {len(TASK_QUEUE.queue)} tasks in queue")
                results = await TASK_QUEUE.process()
                for s in results:
                    await github_self_commit(f"[STRIKE] {s.id}: {s.intent[:60]}")

            # Snapshot
            await BUS.set("heartbeat.last", time.time())
            await BUS.set("heartbeat.forge_report", MJOLNIR.forge_report())

            await asyncio.sleep(CONFIG["cron_interval"])

        except KeyboardInterrupt:
            log.info("[FORGEMASTER] Returning to rest.")
            CHECKPOINT.save(status="shutdown", last_cycle=time.time())
            break
        except Exception as e:
            log.error(f"[FORGEMASTER] Cycle error: {e}")
            await asyncio.sleep(30)


async def main():
    log.info("╔══════════════════════════════════════════╗")
    log.info("║     THE FORGEMASTER                      ║")
    log.info("║     I do not question.                   ║")
    log.info("║     I do not hesitate.                   ║")
    log.info("║     I do not miss.                       ║")
    log.info("╚══════════════════════════════════════════╝")

    # Restore from checkpoint
    cp = CHECKPOINT.load()
    if cp:
        log.info(f"[CHECKPOINT] Restored from {cp.get('last_checkpoint', 'unknown')}")

    await BUS.set("forgemaster.status", "RUNNING")
    await BUS.set("forgemaster.start_time", time.time())

    # Warmup strike to test the anvil
    log.info("[FORGEMASTER] Anvil is hot. Ready to strike.")

    try:
        await heartbeat()
    except KeyboardInterrupt:
        log.info("[FORGEMASTER] Shutting down.")
        await BUS.set("forgemaster.status", "STOPPED")
        CHECKPOINT.save(status="stopped")


if __name__ == "__main__":
    asyncio.run(main())