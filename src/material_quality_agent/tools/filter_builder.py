def build_filter(selected_component: str) -> dict:
    if not selected_component:
        return {}
    return {"component": selected_component}


def relax_filter(filter_dict: dict) -> dict:
    # Fallback: return empty filter (full search)
    return {}
