# THE FORGEMASTER 🔨⚡

> *"I do not question. I do not hesitate. I do not miss."*

A fully autonomous AI agent forged in Fort Myers, FL — part of the **Pantheon Project**. THE FORGEMASTER is a self-evolving cognitive architecture that thinks, learns, strikes, and dreams. It runs perpetually via Apollo-X, never stopping, always improving.

---

## Architecture — The Pantheon

| Component | Codename | Role |
|---|---|---|
| **Will** | ZEUS | Judges intent — is this strike worthy? |
| **Bridge** | THOR | Translates intent into an execution plan (the Bifrost) |
| **Strike** | CLAW | Executes the plan — the hammer falls |
| **Mind** | LiquidBrain | 8 cognitive modes (Creator, Architect, Warrior, Ghost, Oracle, Sage, Phantom, Sovereign) |
| **Nerves** | SAFLA HyperLoop | 12 parallel cognitive loops cross-feeding via StateBus |
| **Spine** | Apollo-X | Never-failing main loop with checkpoint/resume |
| **Arms** | SkillForge | Generates and executes Python skills on demand |
| **Growth** | Ouroboros | Self-mutating parameters — adapts exploration rate |
| **Soul** | LiquidMemory | Persistent key-value memory with async I/O |
| **Gravity** | PID Controller | Self-correcting performance feedback loop |

## The Strike Pipeline

```
Intent → ZEUS (judge) → THOR (bridge) → CLAW (strike) → RETURN
```

Every intent passes through all three stages. Critical-priority tasks enter **STORM MODE** — bypassing Zeus judgment for autonomous execution.

## The HyperLoop — 12 Parallel Cognitive Loops

| Loop | What It Does |
|---|---|
| `loop_research` | ORACLE mode — synthesizes new knowledge |
| `loop_ooda` | Observe → Orient → Decide → Act |
| `loop_reflection` | SAGE mode — rates its own performance 0-1 |
| `loop_mars` | Multi-Agent Reflective System — learns from success/failure |
| `loop_reinforcement` | Q-learning style weight updates |
| `loop_explore_exploit` | Epsilon-greedy strategy selection |
| `loop_pid` | PID controller for performance homeostasis |
| `loop_ouroboros` | Self-mutates `explore_epsilon` based on score |
| `loop_pdca` | Plan → Do → Check → Act cycle |
| `loop_reasoning_action` | Wires research synthesis into the reasoning chain |
| `loop_event` | Watches for externally-dropped tasks |
| `loop_retry` | Surfaces failed tasks back to pending |

All 12 run in parallel each Apollo-X cycle, cross-feeding through the StateBus.

## The Brain — 8 Cognitive Modes

| Mode | Temperature | Focus |
|---|---|---|
| **SOVEREIGN** | 0.1 | Command & control |
| **GHOST** | 0.2 | Stealth operations |
| **WARRIOR** | 0.3 | Execution |
| **ARCHITECT** | 0.4 | Planning & structure |
| **SAGE** | 0.5 | Reflection |
| **ORACLE** | 0.7 | Prediction & research |
| **PHANTOM** | 0.8 | Simulation |
| **CREATOR** | 0.9 | Generation & creativity |

The brain auto-selects modes based on task keywords and mutates mid-execution as needed. In v2.0, `reason()` is wired to the LLM for genuine cognitive output — no more template strings.

## Multi-LLM Failover

THE FORGEMASTER queries providers in randomized order:
1. **DeepSeek** (`deepseek-chat`)
2. **Groq** (`llama3-70b-8192`)
3. **Gemini** (`gemini-2.0-flash`)

All share a single `aiohttp` session pool. If one fails, the next picks up. If all fail, it stands by.

## v2.0.0 — What's New

| Fix | What Changed |
|---|---|
| **Shared HTTP session** | No per-call `import aiohttp` — one session created at startup, reused |
| **LiquidBrain.reason()** | Wired to LLM — real cognition instead of hardcoded "Resolved via OODA" |
| **Async LiquidMemory** | Non-blocking I/O via `asyncio.to_thread` + atomic file writes |
| **GitHubForge** | Async `create_subprocess_exec` instead of blocking `subprocess.run` |
| **HyperLoop merge** | Context merge now under `asyncio.Lock` — no race conditions |
| **SkillForge execution** | Skills can now actually run via `SKILLS.execute(name)` |
| **Atomic writes** | Every JSON file uses temp+rename — no corruption on crash |
| **Graceful shutdown** | Session cleanup on exit |

## Quick Start

```bash
# Clone
git clone https://github.com/kevinleestites2-dev/the-forge-master-hammer.git
cd the-forge-master-hammer

# Setup
cp .env.example .env
# Edit .env with your API keys

# Install
pip install -r requirements.txt

# Run the full autonomous loop
python forgemaster.py
```

## CLI Commands

```bash
python forgemaster.py status              # Full system status
python forgemaster.py forge "task here"   # Queue a task (priority 3)
python forgemaster.py forge "urgent" 1    # Queue CRITICAL task
python forgemaster.py strike "intent"     # Direct strike (bypasses queue)
python forgemaster.py dream               # Trigger dream cycle
python forgemaster.py report              # Mjölnir forge report
python forgemaster.py skills              # List acquired skills
python forgemaster.py skills execute skill_name  # Execute a skill
```

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `DEEPSEEK_API_KEY` | One of three | — |
| `GROQ_API_KEY` | One of three | — |
| `GEMINI_API_KEY` | One of three | — |
| `GITHUB_REPO` | Optional | — |
| `GITHUB_TOKEN` | Optional | — |
| `CRON_INTERVAL` | No | `900` (15 min) |
| `DREAM_INTERVAL` | No | `3600` (1 hr) |
| `DARK_FOREST` | No | `false` |

## The Dream Cycle

Every `DREAM_INTERVAL` seconds, THE FORGEMASTER enters SAGE mode and:
1. Reviews all HyperLoop history
2. Computes average performance score
3. Asks the LLM: *what patterns are emerging? what should be forgotten? what should be reinforced?*
4. Writes a `.dreams/YYYY-MM-DD_HHMM.md` report
5. Commits the dream to GitHub

## The Mjölnir Forge Report

```
╔══════════════════════════════════════╗
║         MJÖLNIR FORGE REPORT        ║
╚══════════════════════════════════════╝
DNA:       a1b2c3d4e5f6
State:     RESTING
Strikes:   42
Success:   38 (90.5%)
Denied:    2
Failed:    2
Last:      STRIKE_1A2B3C4D
```

---

**Forged by Kevin Lee** — Fort Myers, FL  
Part of the Pantheon Project  
*"I do not question. I do not hesitate. I do not miss."* 🔨⚡
