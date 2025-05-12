def find_role_with_true_use_flag(data):
    last_role = data["context"].get("last_role", "")
    if last_role != "":
        cause_by = data["env"]["roles"][last_role].get("cause_action", "")
        return last_role, cause_by
    else:
        return "Architect", "metagpt.actions.design_api.WriteDesign"