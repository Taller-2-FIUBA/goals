"""Constants for testing."""

goal_1 = {
    "title": "Caminata diaria",
    "description": "Caminar tantos kilometros por dia",
    "metric": "distance",
    "objective": 3,
    "time_limit": "6/5/2023"
}

goal_2 = {
    "title": "Perdida de grasa",
    "description": "Perder grasa en un mes",
    "metric": "fat",
    "objective": 10,
    "time_limit": "6/5/2023"
}

goal_3 = {
    "title": "Ganar musculo",
    "description": "Ganar ciertos kilos de musculo",
    "metric": "muscle",
    "objective": 15,
    "time_limit": "6/5/2023"
}


def equal_dicts(dict1, dict2, ignore_keys):
    """Compare dictionaries without taking ignore_keys into account."""
    d1_filtered = {k: v for k, v in dict1.items() if k not in ignore_keys}
    d2_filtered = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return d1_filtered == d2_filtered
