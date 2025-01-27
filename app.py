# app.py
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn

# 既存の関数を利用
from test_main_with_mandatory_exact_time import solve_with_mandatory_exact_time

app = FastAPI()

class SolveRequest(BaseModel):
    branch: Dict[str, Any]
    targets: List[Dict[str, Any]]
    date_range: Dict[str, str]
    holidays: List[str]
    weekday_time_windows: Dict[str, List[str]]
    vehicles: List[Dict[str, Any]]
    timeout_seconds: int
    use_google_api: bool
    google_api_key: str = None

@app.post("/solve")
def solve_endpoint(request: SolveRequest = Body(...)):
    """
    test_data.json と同じ構造のJSONを受け取り、
    訪問計画の結果をJSONとして返す。
    """
    print("[INFO] POST /solve endpoint called. Start solving...")
    json_data = request.dict()

    # ここでVRPを計算
    result = solve_with_mandatory_exact_time(json_data)

    print("[INFO] Done solving. Returning result...")
    return result


if __name__ == "__main__":
    print("[INFO] Starting FastAPI server with Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
