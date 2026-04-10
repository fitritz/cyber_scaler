import sys
from pathlib import Path

# Ensure project root is importable when running as `python scripts/evaluate_env.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.environment import CyberSOCEnv
from env.tasks import TASKS


REQUIRED_INFO_KEYS = [
    "task",
    "step_index",
    "total_steps",
    "expected_action",
    "grader_feedback",
]


def assert_reward_bounds():
    env = CyberSOCEnv(seed=101)
    for task_name in TASKS.keys():
        for action in range(5):
            env.reset(task_name=task_name, seed=101)
            _, reward, _, _ = env.step(action)
            if not (0.0 <= reward.value <= 1.0):
                raise AssertionError(
                    f"Reward out of bounds for task={task_name}, action={action}, value={reward.value}"
                )


def assert_determinism():
    seed = 77
    task_name = "hard"
    action_sequence = [1, 2, 3, 4, 4]

    env_a = CyberSOCEnv(seed=seed)
    env_b = CyberSOCEnv(seed=seed)

    state_a = env_a.reset(task_name=task_name, seed=seed)
    state_b = env_b.reset(task_name=task_name, seed=seed)

    if state_a.model_dump() != state_b.model_dump():
        raise AssertionError("Reset is not deterministic for same task and seed")

    for action in action_sequence:
        state_a, reward_a, done_a, info_a = env_a.step(action)
        state_b, reward_b, done_b, info_b = env_b.step(action)

        if reward_a.value != reward_b.value:
            raise AssertionError("Reward is not deterministic")
        if done_a != done_b:
            raise AssertionError("Done signal is not deterministic")
        if info_a != info_b:
            raise AssertionError("Info payload is not deterministic")
        if state_a.model_dump() != state_b.model_dump():
            raise AssertionError("Next state is not deterministic")


def assert_info_keys():
    env = CyberSOCEnv(seed=11)
    env.reset(task_name="easy", seed=11)
    _, _, _, info = env.step(1)

    missing = [key for key in REQUIRED_INFO_KEYS if key not in info]
    if missing:
        raise AssertionError(f"Missing required info keys: {missing}")


def main():
    print("OpenEnv evaluator started")
    assert_reward_bounds()
    print("[PASS] reward bounds in [0.0, 1.0]")

    assert_determinism()
    print("[PASS] deterministic reset/step for fixed seeds")

    assert_info_keys()
    print("[PASS] required API step metadata keys exist")

    print("All evaluator checks passed.")


if __name__ == "__main__":
    main()
