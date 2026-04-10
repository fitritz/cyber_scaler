import os
import re
from openai import OpenAI

from env.environment import CyberSOCEnv
from env.tasks import ACTIONS


TASK_ORDER = ["easy", "medium", "hard"]
EPISODES_PER_TASK = 1
MAX_STEPS = 8
DEFAULT_SEED = 11
ENV_NAME = os.getenv("OPENENV_BENCHMARK", "cybersoc-openenv")
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"


def parse_action(raw_text):
    if raw_text is None:
        return 1

    text = raw_text.strip().lower()
    match = re.search(r"\b([0-4])\b", text)
    if match:
        return int(match.group(1))

    for action_id, action_name in ACTIONS.items():
        if action_name in text:
            return action_id

    return 1


def fallback_action(state):
    if state.exfil_bytes > 0:
        return 4
    if state.malware_detected:
        return 3
    if state.failed_logins > 20:
        return 2
    return 1


def fmt_bool(value):
    return "true" if value else "false"


def env_or_default(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def main():
    api_base_url = env_or_default("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = env_or_default("MODEL_NAME", DEFAULT_MODEL)
    # Prefer validator-injected API_KEY so calls are visible in platform logs.
    api_key = (
        os.getenv("API_KEY")
        or os.getenv("HF_TOKEN")
        or os.getenv("OPENAI_API_KEY")
    )

    seed = int(os.getenv("SEED", str(DEFAULT_SEED)))

    # Keep baseline runtime bounded even if model endpoint is unavailable.
    model_available = bool(api_key and api_base_url and model_name)
    client = None
    if model_available:
        client = OpenAI(base_url=api_base_url, api_key=api_key, timeout=2.0, max_retries=0)
    env = CyberSOCEnv(seed=seed)

    for task_name in TASK_ORDER:
        for episode in range(EPISODES_PER_TASK):
            episode_seed = seed + episode
            state = env.reset(task_name=task_name, seed=episode_seed)
            done = False
            rewards = []
            step_count = 0

            print(f"[START] task={task_name} env={ENV_NAME} model={model_name}", flush=True)

            while not done and step_count < MAX_STEPS:
                step_count += 1
                prompt = f"""
                You are a SOC analyst. Return only one integer from 0 to 4.

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

                step_error = "null"

                if model_available:
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.0,
                        )
                        content = response.choices[0].message.content
                        action = parse_action(content)
                    except Exception:
                        # Avoid paying repeated network timeout costs after first failure.
                        model_available = False
                        action = fallback_action(state)
                        step_error = "model_request_failed"
                else:
                    action = fallback_action(state)
                    step_error = "null"

                state, reward, done, _ = env.step(action)
                rewards.append(reward.value)
                action_name = ACTIONS.get(action, f"action_{action}")
                print(
                    f"[STEP] step={step_count} action={action_name} reward={reward.value:.2f} "
                    f"done={fmt_bool(done)} error={step_error}",
                    flush=True,
                )

            score = sum(rewards) / max(1, len(rewards))
            score = max(0.0, min(1.0, score))
            success = done and score >= 0.5
            rewards_str = ",".join(f"{r:.2f}" for r in rewards)
            print(
                f"[END] success={fmt_bool(success)} steps={len(rewards)} score={score:.2f} rewards={rewards_str}",
                flush=True,
            )


if __name__ == "__main__":
    main()