import csv
from typing import List, Dict

def load_targets_from_csv(file_like) -> List[Dict]:
    """
    CSVファイル(またはファイルライクオブジェクト)からターゲット情報を読み込む。
    期待するCSVカラム: ID,Lat,Lon,StayTime
    戻り値: [{'ID': 'T1', 'Lat':10.2871, 'Lon':123.8215, 'Stay':45}, ...] のリスト
    """
    reader = csv.DictReader(file_like)
    targets = []
    for row in reader:
        # 必須カラムが揃っているか簡易チェック
        if not all(k in row for k in ('ID', 'Lat', 'Lon', 'Stay')):
            raise ValueError("CSVに必要なカラムが不足しています")
        
        t_id = row['ID']
        lat = float(row['Lat'])
        lon = float(row['Lon'])
        stay = int(row['Stay'])
        
        targets.append({
            'id': t_id,
            'lat': lat,
            'lon': lon,
            'stay': stay
        })
    return targets
