import io
# 既存のimport
from branch_loader import load_branch_info_from_csv
from targets_loader import load_targets_from_csv

def load_data_from_csv_files(branch_csv_path: str, targets_csv_path: str):
    with open(branch_csv_path, "r", encoding="utf-8") as f:
        branch = load_branch_info_from_csv(f)
    with open(targets_csv_path, "r", encoding="utf-8") as f:
        targets = load_targets_from_csv(f)
    return branch, targets

def load_data_from_json(json_data: dict):
    branch = json_data["branch"]
    targets = json_data["targets"]
    # targetsはすでにid,lat,lon,stayがある前提。
    # mandatory, exact_timeをもつか確認し、なければdefault値設定
    for t in targets:
        if "mandatory" not in t:
            t["mandatory"] = False
        if "exact_time" not in t:
            t["exact_time"] = None

    date_range = json_data["date_range"]
    holidays = json_data.get("holidays", [])
    weekday_time_windows = json_data["weekday_time_windows"]
    vehicles = json_data["vehicles"]
    timeout_seconds = json_data.get("timeout_seconds", 600)
    use_google_api = json_data.get("use_google_api", False)
    google_api_key = json_data.get("google_api_key", None)

    return branch, targets, date_range, holidays, weekday_time_windows, vehicles, timeout_seconds, use_google_api, google_api_key

