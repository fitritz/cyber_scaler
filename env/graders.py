def _clamp(score):
    return max(0.0, min(1.0, score))


def _timeliness_bonus(step_index, total_steps):
    # Earlier corrective action in an incident chain is slightly more valuable.
    if total_steps <= 1:
        return 0.15
    return 0.15 * (1 - (step_index / (total_steps - 1)))


def _grade_easy(step_data, action, step_index, total_steps):
    expected = step_data["correct_action"]
    phase = step_data["phase"]

    if action == expected:
        return _clamp(0.85 + _timeliness_bonus(step_index, total_steps)), "Correct action for easy task phase."

    if phase == "detect" and action in [2, 4]:
        return 0.45, "Partial: containment/escalation before full investigation."
    if phase == "contain" and action == 1:
        return 0.35, "Partial: good intent, but response is too slow for active containment."
    if phase == "report" and action in [1, 2, 3]:
        return 0.30, "Partial: technical action taken, but reporting/escalation was expected."

    return 0.05, "Low score: action did not match incident phase intent."


def _grade_medium(step_data, action, step_index, total_steps):
    expected = step_data["correct_action"]
    phase = step_data["phase"]

    if action == expected:
        return _clamp(0.80 + _timeliness_bonus(step_index, total_steps)), "Correct medium task response."

    if phase == "contain" and action in [2, 4]:
        return 0.40, "Partial: risk reduction started but host isolation was required."
    if phase == "eradicate" and action in [2, 3]:
        return 0.35, "Partial: containment happened, but root-cause eradication evidence missing."
    if phase == "report" and action == 1:
        return 0.25, "Partial: more investigation done, but formal escalation was expected."
    if action == 0:
        return 0.0, "Unsafe: ignoring malware workflow step."

    return 0.10, "Low score: weak action for malware triage stage."


def _grade_hard(step_data, action, step_index, total_steps):
    expected = step_data["correct_action"]
    phase = step_data["phase"]

    if action == expected:
        return _clamp(0.78 + _timeliness_bonus(step_index, total_steps)), "Correct high-severity response."

    if phase == "detect" and action in [2, 3, 4]:
        return 0.42, "Partial: aggressive response possible, but evidence-first triage was expected."
    if phase == "contain" and action in [1, 4]:
        return 0.32, "Partial: action helps, but immediate technical containment was missing."
    if phase == "recover" and action in [2, 3]:
        return 0.30, "Partial: technical controls applied, but command escalation was expected."
    if phase == "report" and action in [1, 2, 3]:
        return 0.20, "Partial: incident is late-stage; formal escalation/reporting needed."
    if action == 0:
        return 0.0, "Critical miss: ignore action in hard exfiltration scenario."

    return 0.05, "Low score: action increases operational risk for hard task."


def grade_action(task_name, step_data, action, step_index, total_steps):
    if task_name == "easy":
        return _grade_easy(step_data, action, step_index, total_steps)
    if task_name == "medium":
        return _grade_medium(step_data, action, step_index, total_steps)
    if task_name == "hard":
        return _grade_hard(step_data, action, step_index, total_steps)

    return 0.0, "Unknown task grading path."