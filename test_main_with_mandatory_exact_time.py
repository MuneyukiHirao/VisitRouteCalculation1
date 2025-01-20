import json
from data_provider import load_data_from_json
from time_management import generate_daily_windows, generate_node_time_windows, generate_daily_start_ends
from schedule_to_vehicles import convert_vehicle_schedules_to_daily_vehicles
from cost_matrix_loader import generate_cost_matrix
from vrp_model_loader import create_routing_model, solve_vrp

if __name__ == "__main__":
    # JSON読み込み（test_data.json）
    with open("test_data.json","r",encoding="utf-8") as f:
        json_data = json.load(f)

    branch, targets, date_range, holidays, weekday_time_windows, vehicles, timeout_seconds, use_google_api, google_api_key = load_data_from_json(json_data)

    # スケジュール計算
    vehicle_schedules = generate_daily_start_ends(date_range, holidays, weekday_time_windows, vehicles)
    daily_start_ends, vehicle_map = convert_vehicle_schedules_to_daily_vehicles(vehicle_schedules)
    num_vehicles = len(daily_start_ends)

    cost_matrix = generate_cost_matrix(branch, targets, use_google_api=use_google_api, google_api_key=google_api_key)
    service_times = [0] + [t['stay'] for t in targets]

    # time_windows設定
    # デポ(0)は8:00～19:00(480,1140)
    # mandatory=trueなら通常のtime_window適用
    # exact_time指定があれば、例えば "10:30" → 10*60+30=630分 で(630,630)
    # 他はペナルティ付きスキップ可能→自由なウィンドウ0～200000などにするか、全員8:00～19:00でもよいが、
    # 今回は全て8:00～19:00にして、exact_time指定ノードは強制的に(630,630)にする

    depot_window = (480,1140)
    full_day_window = (480,1140) # 通常ターゲット
    time_windows_list = [depot_window] # 0=depot

    for t in targets:
        if t["exact_time"]:
            hh,mm = map(int,t["exact_time"].split(":"))
            exact_min = hh*60+mm
            time_windows_list.append((exact_min, exact_min))
        else:
            time_windows_list.append(full_day_window)

    penalty = 1000
    routing, manager, search_params = create_routing_model(
        cost_matrix, service_times, time_windows_list,
        num_vehicles=num_vehicles, depot=0, penalty=penalty,
        daily_start_ends=daily_start_ends,
        targets=targets
    )
    solution = solve_vrp(routing, manager, search_params, timeout_seconds=timeout_seconds)

    if solution:
        print("Solution found with mandatory and exact-time targets.")
        time_dimension = routing.GetDimensionOrDie("Time")
        for v in range(num_vehicles):
            index = routing.Start(v)
            route_nodes = []
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                arrival_time = solution.Value(time_dimension.CumulVar(index))
                route_nodes.append((node, arrival_time))
                index = solution.Value(routing.NextVar(index))
            node = manager.IndexToNode(index)
            arrival_time = solution.Value(time_dimension.CumulVar(index))
            route_nodes.append((node, arrival_time))

            print(f"Vehicle {v} route with arrival times:")
            for (n,t) in route_nodes:
                if n==0:
                    loc_name="Depot"
                else:
                    loc_name=targets[n-1]['id']
                hh=t//60
                mm=t%60
                at=f"{hh:02d}:{mm:02d}"
                tw_str = "exact_time="+targets[n-1]['exact_time'] if n>0 and targets[n-1]['exact_time'] else "no_exact"
                mand_str = "MANDATORY" if n>0 and targets[n-1]['mandatory'] else "optional"
                print(f"  Node {n} ({loc_name}): {at} ({tw_str}, {mand_str})")

        # 確認:
        # mandatoryなT1が必ずルートに含まれているか
        # exact_timeなT2が10:30に到着しているか
    else:
        print("No solution found with mandatory and exact-time targets.")
