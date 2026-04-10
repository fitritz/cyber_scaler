ACTIONS = {
    0: "ignore",
    1: "investigate_logs",
    2: "block_ip",
    3: "isolate_host",
    4: "escalate_incident",
}


TASKS = {
    "easy": {
        "name": "bruteforce_containment",
        "description": "Contain repeated login failures from a malicious source.",
        "steps": [
            {
                "phase": "detect",
                "alert": "suspicious_login",
                "correct_action": 1,
            },
            {
                "phase": "contain",
                "alert": "bruteforce_attempt",
                "correct_action": 2,
            },
            {
                "phase": "report",
                "alert": "post_containment_review",
                "correct_action": 4,
            },
        ],
    },
    "medium": {
        "name": "malware_triage",
        "description": "Investigate and contain suspicious endpoint malware activity.",
        "steps": [
            {
                "phase": "detect",
                "alert": "malware_suspected",
                "correct_action": 1,
            },
            {
                "phase": "contain",
                "alert": "malware_detected",
                "correct_action": 3,
            },
            {
                "phase": "eradicate",
                "alert": "persistence_mechanism_found",
                "correct_action": 1,
            },
            {
                "phase": "report",
                "alert": "executive_incident_brief",
                "correct_action": 4,
            },
        ],
    },
    "hard": {
        "name": "data_exfiltration_response",
        "description": "Stop ongoing data exfiltration with controlled escalation.",
        "steps": [
            {
                "phase": "detect",
                "alert": "unusual_egress_spike",
                "correct_action": 1,
            },
            {
                "phase": "contain",
                "alert": "confirmed_c2_channel",
                "correct_action": 2,
            },
            {
                "phase": "contain",
                "alert": "sensitive_host_compromised",
                "correct_action": 3,
            },
            {
                "phase": "recover",
                "alert": "exfiltration_attempt_persists",
                "correct_action": 4,
            },
            {
                "phase": "report",
                "alert": "regulatory_reporting_window",
                "correct_action": 4,
            },
        ],
    },
}