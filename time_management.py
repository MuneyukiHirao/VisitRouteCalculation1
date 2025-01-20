import datetime

def parse_time_to_minutes(timestr):
    """
    "HH:MM"形式の文字列を分単位(int)に変換する。
    例: "08:00" -> 480
    """
    hh, mm = map(int, timestr.split(":"))
    return hh * 60 + mm

def generate_daily_start_ends(date_range, holidays, weekday_time_windows, vehicles):
    """
    date_range: {"start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}
    holidays: ["YYYY-MM-DD",...]
    weekday_time_windows: {"Monday":["HH:MM","HH:MM"],...}
    vehicles: [{"id":"V1","off_days":["YYYY-MM-DD",...]}, ...]
    
    戻り値:
      vehicle_schedules = {
         "V1": [ (start,end or None), (start,end or None), ... (日数分)],
         "V2": [...],
         ...
      }
      
    各車両・各日に対応する開始/終了時間範囲(分)をリストで返す。
    Noneの場合、その日はその車両は稼働不可。
    """
    start_date = datetime.datetime.strptime(date_range["start_date"], "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(date_range["end_date"], "%Y-%m-%d").date()

    day_count = (end_date - start_date).days + 1
    vehicle_schedules = {}

    for v in vehicles:
        v_id = v["id"]
        off_days = set(v.get("off_days", []))
        daily_ends = []
        for i in range(day_count):
            current_date = start_date + datetime.timedelta(days=i)
            current_str = current_date.strftime("%Y-%m-%d")

            # 休日チェック
            if current_str in holidays:
                daily_ends.append(None)
                continue

            # 車両オフ日チェック
            if current_str in off_days:
                daily_ends.append(None)
                continue

            # 曜日取得
            weekday_name = current_date.strftime("%A")
            if weekday_name not in weekday_time_windows:
                # 定義がない曜日は訪問不可日とする
                daily_ends.append(None)
                continue

            tw = weekday_time_windows[weekday_name]
            if len(tw) != 2:
                # 曜日ウィンドウ定義が不正ならその日なし
                daily_ends.append(None)
                continue

            start_str, end_str = tw
            if start_str == end_str and start_str == "00:00":
                # 実質休業日扱い
                daily_ends.append(None)
                continue

            start_min = parse_time_to_minutes(start_str)
            end_min = parse_time_to_minutes(end_str)
            daily_ends.append((start_min, end_min))

        vehicle_schedules[v_id] = daily_ends

    return vehicle_schedules
    
def datetime_to_minutes(base_datetime, target_datetime):
    """
    base_datetimeを起点(0分)として、target_datetimeがそこから何分後かを返す。
    """
    diff = target_datetime - base_datetime
    return int(diff.total_seconds() // 60)  # 分単位に変換

def generate_daily_windows(start_date, end_date):
    """
    start_dateの日付の8:00を0分として、それ以降end_dateまでの各平日8:00～19:00を時間ウィンドウ(分)で返す。
    戻り値: [(day_start_min, day_end_min), ...]
    
    ここでは、2024/12/12 8:00を起点とし、  
    2024/12/12～2024/12/18 の範囲で、  
    平日: 8:00～19:00 → (start_min, end_min)
    土日: ウィンドウなし
    
    ※今回は簡易化のため、実際の日数範囲に依存せず、  
    指定期間を日ごとにイテレートし、平日ならウィンドウを追加する実装とする。
    """
    # 起点日時はstart_dateの8:00
    base_datetime = datetime.datetime(start_date.year, start_date.month, start_date.day, 8, 0)
    daily_windows = []

    day_count = (end_date - start_date).days + 1
    for i in range(day_count):
        current_date = start_date + datetime.timedelta(days=i)
        # 土日チェック
        if current_date.weekday() < 5:  # 月曜=0, 金曜=4が平日
            # 当日8:00の分数
            day_start = datetime.datetime(current_date.year, current_date.month, current_date.day, 8, 0)
            day_end   = datetime.datetime(current_date.year, current_date.month, current_date.day, 19, 0)
            
            start_min = datetime_to_minutes(base_datetime, day_start)
            end_min = datetime_to_minutes(base_datetime, day_end)
            daily_windows.append((start_min, end_min))
        else:
            # 土日は追加しない
            daily_windows.append(None)
    
    return daily_windows

def generate_node_time_windows(daily_windows):
    """
    各ターゲット・車両に割り当てる時間ウィンドウを生成する。
    平日は daily_windows[i] = (start_min, end_min)が有効、
    土日は None となっている。
    
    ここでは、すべてのターゲットが平日の営業時間内であればいつでも訪問可能と仮定し、
    全平日のウィンドウをまとめて、単一の広いウィンドウとして与えることも可能。
    あるいは日ごとに別車両としてモデリングするなら、日ごとに別のウィンドウを割り当てる。
    
    本例では単純化のため、全平日のウィンドウをユニオンして返す例を示す。
    
    戻り値： (global_start, global_end) 
    → 全平日の最も早い開始時間と最も遅い終了時間を求める
    """
    valid_windows = [w for w in daily_windows if w is not None]
    if not valid_windows:
        return None
    global_start = min(w[0] for w in valid_windows)
    global_end = max(w[1] for w in valid_windows)
    return (global_start, global_end)
