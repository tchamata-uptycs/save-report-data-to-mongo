import requests

GRAFANA_API_KEY = 'eyJrIjoiNm9QeWppVHE3dEVZajA5NEoybEp2NmRpQlNPYUU0MVoiLCJuIjoibmV3a2V5IiwiaWQiOjF9'
GRAFANA_HOST = 's1monitor'
GRAFANA_PORT = '3000'

def get_dashboard_data(dashboard_id):
    url = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}/api/dashboards/db/{dashboard_id}"
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dashboard_data = response.json()
        return dashboard_data
    return None

def get_panel_data(dashboard_id, panel_id):
    dashboard_data = get_dashboard_data(dashboard_id)
    if dashboard_data:
        print(dashboard_data)
        panels = dashboard_data.get("dashboard", {}).get("panels", [])
        for panel in panels:
            if panel.get("id") == panel_id:
                return panel
    return None

# Example usage: Fetch data from Panel with ID 136 in Dashboard with ID 339
panel_data = get_panel_data(339, 136)
if panel_data:
    print("Panel Data:")
    print(panel_data)
else:
    print("Failed to fetch panel data.")
