import os
import random
import sys
from statistics import mean, pstdev
from pathlib import Path

# Ensure project root is importable when running as `python scripts/benchmark.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.environment import CyberSOCEnv
from env.tasks import ACTIONS


TASK_ORDER = ["easy", "medium", "hard"]
SEEDS = [11, 12, 13, 14, 15]
MAX_STEPS = 10


def parse_action(raw_text):
    text = (raw_text or "").strip().lower()
    for token in text.split():
        if token.isdigit() and int(token) in ACTIONS:
            return int(token)
    for action_id, action_name in ACTIONS.items():
        if action_name in text:
            return action_id
    return 1


def random_policy(_state, rng):
    return rng.randint(0, 4)


def rule_policy(state):
    if state.phase == "detect":
        return 1
    if state.phase == "contain":
        if state.malware_detected:
            return 3
        return 2
    if state.phase in ["recover", "report"]:
        return 4
    return 1


def llm_policy(state, client, model_name):
    prompt = f"""
You are a SOC analyst. Return exactly one integer from 0 to 4.
Task: {state.task_name}
Phase: {state.phase}
Alert: {state.alert_type}
failed_logins: {state.failed_logins}
malware_detected: {state.malware_detected}
network_traffic: {state.network_traffic}
severity: {state.severity}
source_ip_reputation: {state.source_ip_reputation}
host_criticality: {state.host_criticality}
user_risk_score: {state.user_risk_score}
exfil_bytes: {state.exfil_bytes}
containment_status: {state.containment_status}
evidence_collected: {state.evidence_collected}

Actions:
0 ignore
1 investigate_logs
2 block_ip
3 isolate_host
4 escalate_incident
"""
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return parse_action(response.choices[0].message.content)


def run_episode(env, task_name, seed, policy_name, rng=None, client=None, model_name=None):
    state = env.reset(task_name=task_name, seed=seed)
    done = False
    total_reward = 0.0
    steps = 0

    while not done and steps < MAX_STEPS:
        steps += 1

        if policy_name == "random":
            action = random_policy(state, rng)
        elif policy_name == "rule":
            action = rule_policy(state)
        else:
            try:
                action = llm_policy(state, client, model_name)
            except Exception:
                action = rule_policy(state)

        state, reward, done, _ = env.step(action)
        total_reward += reward.value

    return total_reward


def summarize(scores):
    if not scores:
        return 0.0, 0.0
    if len(scores) == 1:
        return scores[0], 0.0
    return mean(scores), pstdev(scores)


def run_policy(policy_name, client=None, model_name=None):
    env = CyberSOCEnv(seed=SEEDS[0])
    rng = random.Random(123)
    task_results = {task: [] for task in TASK_ORDER}

    for task_name in TASK_ORDER:
        for seed in SEEDS:
            score = run_episode(
                env,
                task_name=task_name,
                seed=seed,
                policy_name=policy_name,
                rng=rng,
                client=client,
                model_name=model_name,
            )
            task_results[task_name].append(score)

    all_scores = [s for vals in task_results.values() for s in vals]
    avg, std = summarize(all_scores)

    print(f"\nPolicy: {policy_name}")
    for task_name in TASK_ORDER:
        task_avg, task_std = summarize(task_results[task_name])
        print(f"  {task_name}: mean={task_avg:.3f}, std={task_std:.3f}, runs={len(task_results[task_name])}")
    print(f"  overall: mean={avg:.3f}, std={std:.3f}, runs={len(all_scores)}")


def main():
    print("Deterministic benchmark started")
    print(f"tasks={TASK_ORDER}, seeds={SEEDS}")

    run_policy("random")
    run_policy("rule")

    api_base_url = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    api_key = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")

    if api_base_url and model_name and api_key:
        try:
            from openai import OpenAI
        except ImportError:
            print("\nPolicy: llm")
            print("  skipped: install openai package to run LLM benchmark")
            return

        client = OpenAI(base_url=api_base_url, api_key=api_key)
        run_policy("llm", client=client, model_name=model_name)
    else:
        print("\nPolicy: llm")
        print("  skipped: set API_BASE_URL, MODEL_NAME and HF_TOKEN (or OPENAI_API_KEY) to run")


if __name__ == "__main__":
    main()
