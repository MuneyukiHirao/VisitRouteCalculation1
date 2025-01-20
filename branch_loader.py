import csv

def load_branch_info_from_csv(file_like):
    """
    CSVファイル(またはファイルライクオブジェクト)から支店情報を読み込む。
    期待するCSVカラム: ID,Lat,Lon
    想定: 1行のみの支店情報を読み込み、{'id':'Branch', 'lat':..., 'lon':...} を返す。
    複数行あれば最初の行を採用する。
    """
    reader = csv.DictReader(file_like)
    for row in reader:
        if not all(k in row for k in ('ID', 'Lat', 'Lon')):
            raise ValueError("CSVに必要なカラム(ID,Lat,Lon)が不足しています")
        
        t_id = row['ID']
        lat = float(row['Lat'])
        lon = float(row['Lon'])
        return {'id': t_id, 'lat': lat, 'lon': lon}
    
    # 行がなかった場合
    raise ValueError("Branch情報が存在しません")
