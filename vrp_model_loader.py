from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def create_routing_model(cost_matrix, service_times, time_windows,
                         num_vehicles=15, depot=0, penalty=1000,
                         daily_start_ends=None,
                         targets=None,
                         start_nodes=None,
                         end_nodes=None):
    if start_nodes is None:
        start_nodes = [depot]*num_vehicles
    if end_nodes is None:
        end_nodes = [depot]*num_vehicles

    manager = pywrapcp.RoutingIndexManager(len(cost_matrix), num_vehicles, start_nodes, end_nodes)
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel_time = cost_matrix[from_node][to_node]
        service_time = service_times[to_node]
        return int(travel_time + service_time)

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time dimension
    routing.AddDimension(
        transit_callback_index,
        10000,    # waiting slack
        200000,   # max time
        False,    # don't force start cumul to zero
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    # Apply time windows
    for node_index, tw in enumerate(time_windows):
        if tw is not None:
            index = manager.NodeToIndex(node_index)
            time_dimension.CumulVar(index).SetRange(tw[0], tw[1])

    # Apply daily start ends
    if daily_start_ends is not None:
        for v in range(num_vehicles):
            day_start, day_end = daily_start_ends[v]
            # start_varはstart_nodesで既に設定、ここではend_varに日範囲をセット
            end_var = time_dimension.CumulVar(routing.End(v))
            end_var.SetRange(day_start, day_end)

    # Mandatory / optional targets
    # Depot=0はスキップ不可
    if targets is not None:
        for node_index in range(1, len(cost_matrix)):
            tgt = targets[node_index-1]
            if tgt["mandatory"]:
                # Skipなし（AddDisjunctionしない）
                pass
            else:
                routing.AddDisjunction([manager.NodeToIndex(node_index)], penalty)
    else:
        # No targets info
        for node_index in range(1, len(cost_matrix)):
            routing.AddDisjunction([manager.NodeToIndex(node_index)], penalty)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    return routing, manager, search_parameters

def solve_vrp(routing, manager, search_parameters, timeout_seconds=600):
    search_parameters.time_limit.seconds = timeout_seconds
    solution = routing.SolveWithParameters(search_parameters)
    return solution
