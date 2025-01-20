def convert_vehicle_schedules_to_daily_vehicles(vehicle_schedules):
    """
    vehicle_schedules: { "V1": [ (start_end or None), (start_end or None), ...],
                         "V2": [...],
                         ... }
    戻り値:
      daily_start_ends: [(day_start, day_end), ...]  # 仮想車両ごとの時間ウィンドウ
      vehicle_map: [(v_id, day_index)]  # 仮想車両が元のどの車両・どの日を表すか
        num_vehicles = len(daily_start_ends)
    """
    daily_start_ends = []
    vehicle_map = []

    for v_id, schedule in vehicle_schedules.items():
        # scheduleは日数分のリスト: [ (start,end) or None, ...]
        for day_index, day_val in enumerate(schedule):
            if day_val is None:
                # 訪問不可日なのでスキップ
                continue
            # day_valは(start_min, end_min)のタプル
            daily_start_ends.append(day_val)
            vehicle_map.append((v_id, day_index))

    return daily_start_ends, vehicle_map
