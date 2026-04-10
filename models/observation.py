from pydantic import BaseModel


class Observation(BaseModel):
    task_name: str
    phase: str
    alert_type: str
    failed_logins: int
    malware_detected: bool
    network_traffic: int
    severity: int
    source_ip_reputation: int
    host_criticality: int
    user_risk_score: int
    exfil_bytes: int
    containment_status: str
    evidence_collected: bool