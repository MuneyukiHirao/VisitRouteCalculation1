# recalculation_assignment.py
import import_ipynb
from time_management import generate_daily_start_ends
from schedule_to_vehicles import convert_vehicle_schedules_to_daily_vehicles
from cost_matrix_loader import generate_cost_matrix
from vrp_model_loader import create_routing_model, solve_vrp

def extract_solution_route(solution, routing, manager):
    vehicle_routes = {}
    for v in range(routing.vehicles()):
        index = routing.Start(v)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        vehicle_routes[v] = route
    return vehicle_routes

def recalculate_routing(branch, updated_targets, date_range, holidays, weekday_time_windows, vehicles,
                        vehicle_positions, timeout_seconds=600, use_google_api=False, google_api_key=None):
    print("[DEBUG] recalculate_routing start_nodes=0 test (no assignment method)")
    vehicle_schedules = generate_daily_start_ends(date_range, holidays, weekday_time_windows, vehicles)
    daily_start_ends, vehicle_map = convert_vehicle_schedules_to_daily_vehicles(vehicle_schedules)
    num_vehicles = len(daily_start_ends)

    cost_matrix = generate_cost_matrix(branch, updated_targets, use_google_api=use_google_api, google_api_key=google_api_key)
    service_times = [0] + [t['stay'] for t in updated_targets]

    depot_window = (480,1140)
    time_windows = [depot_window]*(1+len(updated_targets))

    start_nodes=[0]*num_vehicles
    end_nodes=[0]*num_vehicles

    routing, manager, search_params = create_routing_model(
        cost_matrix, service_times, time_windows,
        num_vehicles=num_vehicles, depot=0, penalty=1000,
        daily_start_ends=daily_start_ends,
        targets=updated_targets,
        start_nodes=start_nodes,
        end_nodes=end_nodes
    )

    time_dimension = routing.GetDimensionOrDie("Time")
    for v,vp in enumerate(vehicle_positions):
        ctime=vp['current_time']
        start_var=time_dimension.CumulVar(routing.Start(v))
        start_var.SetRange(ctime, ctime)

    solution = solve_vrp(routing, manager, search_params, timeout_seconds=timeout_seconds)
    print("[DEBUG] recalculate_routing solve_vrp done:", "found" if solution else "None")
    return solution, routing, manager, search_params

def recalculate_routing_from_assignment(branch, updated_targets, date_range, holidays, weekday_time_windows, vehicles,
                                        vehicle_positions, prev_solution, prev_routing, prev_manager,
                                        prev_targets, # 初回計算時のtargetsを受け取る
                                        timeout_seconds=600, use_google_api=False, google_api_key=None):
    """
    prev_targets: 初回計算時のtargetsリスト
    """
    print("[DEBUG] recalculate_routing_from_assignment start")

    # ヒントなしで一度モデル構築しておく（同様）
    vehicle_schedules = generate_daily_start_ends(date_range, holidays, weekday_time_windows, vehicles)
    daily_start_ends, vehicle_map = convert_vehicle_schedules_to_daily_vehicles(vehicle_schedules)
    num_vehicles = len(daily_start_ends)

    # ID→Indexマップを初回、更新後両方で作成
    id_to_index_initial={"Branch":0}
    for i,t in enumerate(prev_targets):
        id_to_index_initial[t['id']] = i+1

    id_to_index_updated={"Branch":0}
    for i,t in enumerate(updated_targets):
        id_to_index_updated[t['id']] = i+1

    cost_matrix = generate_cost_matrix(branch, updated_targets, use_google_api=use_google_api, google_api_key=google_api_key)
    service_times = [0] + [t['stay'] for t in updated_targets]
    depot_window = (480,1140)
    time_windows = [depot_window]*(1+len(updated_targets))

    start_nodes=[0]*num_vehicles
    end_nodes=[0]*num_vehicles

    routing_h, manager_h, search_params_h = create_routing_model(
        cost_matrix, service_times, time_windows,
        num_vehicles=num_vehicles, depot=0, penalty=1000,
        daily_start_ends=daily_start_ends,
        targets=updated_targets,
        start_nodes=start_nodes,
        end_nodes=end_nodes
    )

    time_dimension_h = routing_h.GetDimensionOrDie("Time")
    for v,vp in enumerate(vehicle_positions):
        ctime=vp['current_time']
        start_var=time_dimension_h.CumulVar(routing_h.Start(v))
        start_var.SetRange(ctime, ctime)

    # 前回ルート抽出（初回問題定義に基づくインデックス）
    prev_routes = extract_solution_route(prev_solution, prev_routing, prev_manager)
    print("[DEBUG] prev_routes:", prev_routes)

    # prev_routesは初回問題定義のNodeIndexを使用(0=depot, 1..=len(prev_targets))  
    # 更新後、使えないターゲットやインデックスがズレている可能性があるのでIDで再マップする
    # 手順:
    #   1. prev_routes[v]からNodeIndexをIDに変換(逆方向)
    #   2. IDからid_to_index_updatedで更新後インデックスに再マッピング
    #   3. キャンセルされたIDはupdated_targetsに存在しないので無視
    #   4. デポ0はstart/endなので中間を抽出

    # 初回: NodeIndex→ID変換には、初回id_to_index_initialを逆引きが必要
    # 逆引き辞書:
    inv_id_to_index_initial = {val:key for key,val in id_to_index_initial.items()}
    # val=NodeIndex(初回),key=ID
    # inv_id_to_index_initial[node_index]→ID

    routes_for_assignment = []
    for v in range(num_vehicles):
        full_route = prev_routes[v]  # 初回問題定義のNodeIndex列
        # depotを除く中間を取得
        if len(full_route)>2:
            intermediate_nodes = full_route[1:-1]
        else:
            intermediate_nodes = []

        remapped_nodes = []
        for old_node in intermediate_nodes:
            if old_node in inv_id_to_index_initial:
                nid = inv_id_to_index_initial[old_node]  # ID
            elif old_node == 0:
                nid = "Branch"
            else:
                # 万が一不明ノード
                continue

            if nid in id_to_index_updated:
                new_node = id_to_index_updated[nid]
                remapped_nodes.append(new_node)
            # 存在しないIDはキャンセルされたターゲット、無視

        print(f"[DEBUG] Vehicle {v} remapped_nodes:", remapped_nodes)
        routes_for_assignment.append(remapped_nodes)

    print("[DEBUG] routes_for_assignment:", routes_for_assignment)
    assignment = routing_h.ReadAssignmentFromRoutes(routes_for_assignment, True)
    if assignment is None:
        print("[DEBUG] ReadAssignmentFromRoutes returned None, can't use assignment.")
        return None, routing_h, manager_h, search_params_h

    print("[DEBUG] assignment read successful.")
    search_params_h.time_limit.seconds = timeout_seconds
    print("[DEBUG] SolveFromAssignmentWithParameters start")
    solution_uh = routing_h.SolveFromAssignmentWithParameters(assignment, search_params_h)
    print("[DEBUG] SolveFromAssignmentWithParameters done:", "found" if solution_uh else "None")

    return solution_uh, routing_h, manager_h, search_params_h
