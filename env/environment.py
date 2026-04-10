import random

from models.observation import Observation
from models.reward import Reward
from env.tasks import TASKS
from env.graders import grade_action


class CyberSOCEnv:

    def __init__(self, seed=7):

        self.rng = random.Random(seed)
        self.task_name = None
        self.task_sequence = None
        self.current_step = 0
        self.done = False
        self.state_data = None

    def generate_state(self, step_data):
        alert = step_data["alert"]
        phase = step_data["phase"]

        failed_logins = self.rng.randint(0, 60)
        network_traffic = self.rng.randint(200, 1200)
        exfil_bytes = 0
        malware_detected = False

        if "login" in alert or "bruteforce" in alert:
            failed_logins = self.rng.randint(18, 60)
        if "malware" in alert or "persistence" in alert:
            malware_detected = True
        if "exfiltration" in alert or "egress" in alert or "c2" in alert:
            network_traffic = self.rng.randint(800, 1400)
            exfil_bytes = self.rng.randint(500, 5000)
        if "regulatory" in alert:
            exfil_bytes = self.rng.randint(2000, 10000)

        return Observation(
            task_name=self.task_name,
            phase=phase,
            alert_type=alert,
            failed_logins=failed_logins,
            malware_detected=malware_detected,
            network_traffic=network_traffic,
            severity=self.rng.randint(2, 5),
            source_ip_reputation=self.rng.randint(1, 100),
            host_criticality=self.rng.randint(1, 5),
            user_risk_score=self.rng.randint(1, 100),
            exfil_bytes=exfil_bytes,
            containment_status=("in_progress" if phase in ["contain", "recover"] else "pending"),
            evidence_collected=(phase in ["eradicate", "report"]),
        )

    def reset(self, task_name=None, seed=None):

        if seed is not None:
            self.rng.seed(seed)

        self.done = False
        self.current_step = 0

        if task_name is None:
            task_name = self.rng.choice(list(TASKS.keys()))
        if task_name not in TASKS:
            raise ValueError(f"Unknown task '{task_name}'")

        self.task_name = task_name
        self.task_sequence = TASKS[task_name]["steps"]

        step_data = self.task_sequence[self.current_step]

        self.state_data = self.generate_state(step_data)

        return self.state_data

    def step(self, action):
        if self.task_sequence is None:
            raise RuntimeError("Environment not initialized. Call reset() before step().")

        if self.done:
            return self.state_data, Reward(value=0.0), True, {
                "task": self.task_name,
                "step_index": self.current_step,
                "grader_feedback": "Episode already done. Call reset() for a new episode.",
            }

        if action < 0 or action > 4:
            score = 0.0
            feedback = "Invalid action outside discrete action space 0..4."
        else:
            step_data = self.task_sequence[self.current_step]
            score, feedback = grade_action(
                self.task_name,
                step_data,
                action,
                self.current_step,
                len(self.task_sequence),
            )

        reward = Reward(value=score)
        previous_step = self.current_step

        self.current_step += 1

        if self.current_step >= len(self.task_sequence):
            self.done = True
        else:
            self.state_data = self.generate_state(self.task_sequence[self.current_step])

        info = {
            "task": self.task_name,
            "step_index": previous_step,
            "total_steps": len(self.task_sequence),
            "expected_action": self.task_sequence[previous_step]["correct_action"],
            "grader_feedback": feedback,
        }

        return self.state_data, reward, self.done, info

    def state(self):
        return self.state_data