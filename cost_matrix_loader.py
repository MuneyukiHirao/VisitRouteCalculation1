from distance_loader import get_travel_time

def generate_cost_matrix(branch, targets, use_google_api=False, google_api_key=None):
    n = len(targets)
    matrix = [[0]*(n+1) for _ in range(n+1)]
    
    for i in range(n+1):
        for j in range(n+1):
            if i == j:
                matrix[i][j] = 0
            else:
                if i == 0:
                    lat_i, lon_i = branch['lat'], branch['lon']
                else:
                    lat_i, lon_i = targets[i-1]['lat'], targets[i-1]['lon']
                
                if j == 0:
                    lat_j, lon_j = branch['lat'], branch['lon']
                else:
                    lat_j, lon_j = targets[j-1]['lat'], targets[j-1]['lon']
                
                t = get_travel_time(lat_i, lon_i, lat_j, lon_j, use_google_api=use_google_api, google_api_key=google_api_key)
                matrix[i][j] = t
    
    return matrix
