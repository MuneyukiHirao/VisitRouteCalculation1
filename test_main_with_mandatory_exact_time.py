import json
from data_provider import load_data_from_json
from time_management import generate_daily_start_ends
from schedule_to_vehicles import convert_vehicle_schedules_to_daily_vehicles
from cost_matrix_loader import generate_cost_matrix
from vrp_model_loader import create_routing_model, solve_vrp


def solve_with_mandatory_exact_time(json_data: dict) -> dict:
    print("[DEBUG] solve_with_mandatory_exact_time: start")

    # JSON解析
    branch, targets, date_range, holidays, weekday_time_windows, vehicles, timeout_seconds, use_google_api, google_api_key = load_data_from_json(json_data)
    print(f"[DEBUG] Loaded data: {len(targets)} targets, {len(vehicles)} vehicles")

    # 車両(1日ごとのスケジュール生成)
    vehicle_schedules = generate_daily_start_ends(date_range, holidays, weekday_time_windows, vehicles)
    daily_start_ends, vehicle_map = convert_vehicle_schedules_to_daily_vehicles(vehicle_schedules)
    num_vehicles = len(daily_start_ends)
    print(f"[DEBUG] Number of 'virtual vehicles' = {num_vehicles}")

    # コスト行列
    cost_matrix = generate_cost_matrix(branch, targets, use_google_api=use_google_api, google_api_key=google_api_key)
    print("[DEBUG] Cost matrix generated.")

    # サービスタイム(ターゲットで過ごす時間)
    service_times = [0] + [t['stay'] for t in targets]

    # 時間ウィンドウ設定
    depot_window = (480, 1140)
    full_day_window = (480, 1140)

    time_windows_list = [depot_window]  # 0=depot
    for t in targets:
        if t["exact_time"]:
            hh, mm = map(int, t["exact_time"].split(":"))
            exact_min = hh * 60 + mm
            time_windows_list.append((exact_min, exact_min))  # exact_time指定
        else:
            time_windows_list.append(full_day_window)

    penalty = 1000
    routing, manager, search_params = create_routing_model(
        cost_matrix, service_times, time_windows_list,
        num_vehicles=num_vehicles, depot=0, penalty=penalty,
        daily_start_ends=daily_start_ends,
        targets=targets
    )
    print("[DEBUG] Routing model created. Starting solve...")

    solution = solve_vrp(routing, manager, search_params, timeout_seconds=timeout_seconds)
    print("[DEBUG] Solve completed.")

    result_dict = {
        "solution_found": False,
        "routes": []
    }

    if solution:
        print("[DEBUG] Solution found, extracting route info...")
        result_dict["solution_found"] = True

        time_dimension = routing.GetDimensionOrDie("Time")

        for v in range(num_vehicles):
            index = routing.Start(v)
            route_indices = []
            while not routing.IsEnd(index):
                route_indices.append(index)
                index = solution.Value(routing.NextVar(index))
            # Endノードも含める
            route_indices.append(index)

            vehicle_route_info = []
            for ridx in route_indices:
                # ridx = OR-Toolsのルーティングインデックス
                arrival_time = solution.Value(time_dimension.CumulVar(ridx))
                node_id = manager.IndexToNode(ridx)  # 対応するターゲットID（0がDepot）

                if node_id == 0:
                    loc_name = "Depot"
                    exact_str = "-"
                    mandatory_str = "-"
                else:
                    loc_name = targets[node_id - 1]["id"]
                    exact_str = targets[node_id - 1]["exact_time"] if targets[node_id - 1]["exact_time"] else "no_exact"
                    mandatory_str = "MANDATORY" if targets[node_id - 1]["mandatory"] else "optional"

                hh = arrival_time // 60
                mm = arrival_time % 60
                at_str = f"{hh:02d}:{mm:02d}"

                vehicle_route_info.append({
                    "routing_index": ridx,
                    "node_id": node_id,
                    "node_name": loc_name,
                    "arrival_time_str": at_str,
                    "exact_time": exact_str,
                    "mandatory": mandatory_str
                })

            result_dict["routes"].append({
                "vehicle_id": v,
                "stops": vehicle_route_info
            })
    else:
        print("[DEBUG] No solution found.")

    print("[DEBUG] solve_with_mandatory_exact_time: end")
    return result_dict


# 単体実行時のテスト
if __name__ == "__main__":
    with open("test_data.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print("[DEBUG] Running test_main_with_mandatory_exact_time as a script...")
    result = solve_with_mandatory_exact_time(json_data)

    if result["solution_found"]:
        print("Solution found with mandatory and exact-time targets.")
        for route in result["routes"]:
            v_id = route["vehicle_id"]
            print(f"Vehicle {v_id} route with arrival times:")
            for stop in route["stops"]:
                print(f"  RoutingIndex={stop['routing_index']}, "
                      f"NodeID={stop['node_id']} ({stop['node_name']}): "
                      f"{stop['arrival_time_str']} "
                      f"(exact_time={stop['exact_time']}, {stop['mandatory']})")
    else:
        print("No solution found with mandatory and exact-time targets.")
