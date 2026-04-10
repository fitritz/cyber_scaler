---
title: CyberSOC OpenEnv
emoji: "🛡️"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

CyberSOC OpenEnv

CyberSOC OpenEnv is a real-world incident-response simulation where an AI agent
plays the role of a SOC analyst. The environment follows the OpenEnv interface
and supports deterministic baseline evaluation.

Environment goals:

- investigate suspicious events quickly
- apply containment actions at the right phase
- avoid unsafe responses (such as ignoring severe incidents)
- escalate and report when required

OpenEnv API

- `GET /reset` start a new episode
  - optional query params: `task` (`easy|medium|hard`), `seed` (int)
- `POST /step/{action}` apply action `0..4`
- `GET /state` fetch latest environment observation
- `GET /health` liveness check for deployment validation

Action space

- `0` ignore
- `1` investigate_logs
- `2` block_ip
- `3` isolate_host
- `4` escalate_incident

Observation space

- `task_name: str`
- `phase: str`
- `alert_type: str`
- `failed_logins: int`
- `malware_detected: bool`
- `network_traffic: int`
- `severity: int`
- `source_ip_reputation: int`
- `host_criticality: int`
- `user_risk_score: int`
- `exfil_bytes: int`
- `containment_status: str`
- `evidence_collected: bool`

Tasks and graders

- `easy` (bruteforce_containment)
  - detect -> contain -> report
- `medium` (malware_triage)
  - detect -> contain -> eradicate -> report
- `hard` (data_exfiltration_response)
  - detect -> contain -> contain -> recover -> report

Each task has a dedicated grader with scores bounded in `[0.0, 1.0]` and
partial credit for progress-aligned but imperfect actions.

Reward design

- full phase-correct action gets high score + timeliness bonus
- partial alignment gets partial reward
- unsafe actions (for example `ignore` on severe phases) receive strong penalty
- anti-gaming penalties apply for blind escalation and over-aggressive actions
- SLA-style decay reduces score for late-stage correction

Step explainability payload (`/step` -> `info`)

- `task`
- `step_index`
- `total_steps`
- `expected_action`
- `grader_feedback`

Setup

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run API locally

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

3. Quick API sanity checks

```bash
curl http://127.0.0.1:7860/health
curl "http://127.0.0.1:7860/reset?task=easy&seed=11"
curl -X POST http://127.0.0.1:7860/step/1
curl http://127.0.0.1:7860/state
```

Baseline inference (`inference.py`)

The script is deterministic and emits strict structured logs required by
evaluation:

- `[START] task=<task_name> env=<benchmark_name> model=<model_name>`
- `[STEP] step=<n> action=<action_name> reward=<0.00> done=<true|false> error=<msg|null>`
- `[END] success=<true|false> steps=<n> score=<0.00> rewards=<r1,r2,...>`

Each task episode returns a normalized score in `[0, 1]`.

Required environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN` (preferred) or `OPENAI_API_KEY`

Optional variables:

- `SEED` (default `11`)

Run:

```bash
python inference.py
```

Benchmarking

Run deterministic policy benchmarks:

```bash
python scripts/benchmark.py
```

Includes:

- random policy
- rule-based policy
- llm policy (if API_BASE_URL + MODEL_NAME + HF_TOKEN are set)

Evaluator (selection-focused quality checks)

```bash
python scripts/evaluate_env.py
```

Checks:

- reward bounds in `[0.0, 1.0]`
- deterministic reset/step for fixed seeds
- required API step metadata keys exist

Docker

Build and run:

```bash
docker build -t cybersoc-openenv:latest .
docker run -p 7860:7860 cybersoc-openenv:latest
```

Hugging Face Spaces deployment

1. Create a Docker Space.
2. Push this repository contents.
3. Add Space secrets/variables:
   - `API_BASE_URL`
   - `MODEL_NAME`
   - `HF_TOKEN`
4. Wait for build success and verify:

```bash
curl https://<your-space>.hf.space/health
curl https://<your-space>.hf.space/reset
```

Pre-submission checks

- Docker image builds
- `/health` returns 200
- `/reset` returns a valid observation
- `/state` returns a valid observation
- `python scripts/evaluate_env.py` passes
- `python inference.py` completes and prints scores
- `openenv.yaml` matches API and spaces

One-command validation helper

```bash
bash scripts/validate-submission.sh https://<your-space>.hf.space .
```

Dry-run checklist report (local)

Commands executed:

```bash
python scripts/evaluate_env.py
python scripts/benchmark.py
python -c "from app import app; from fastapi.testclient import TestClient; c=TestClient(app); print('health', c.get('/health').status_code); print('reset', c.get('/reset').status_code); print('step', c.post('/step/1').status_code); print('state', c.get('/state').status_code)"
bash scripts/validate-submission.sh http://127.0.0.1:7860 .
```

Observed output summary:

- `evaluate_env.py`: PASS (reward bounds, determinism, required info keys)
- `benchmark.py`: PASS (random and rule policies ran; LLM policy skipped without API vars)
- API smoke test: `health 200`, `reset 200`, `step 200`, `state 200`
- `validate-submission.sh`: runs end-to-end; Docker build step is skipped with warning if Docker CLI is unavailable
