import requests
GRAFANA_API_KEY = 'eyJrIjoiU0phSVNoSmRPcTZSOEFpT3lodTNjTnB1MUNnT0dpYWgiLCJuIjoiZGVtb19rZXkiLCJpZCI6MX0='
base_url = "http://192.168.128.50:3000"

GRAFANA_HOST = 's1monitor'
GRAFANA_PORT = "3000"



def get_dashboard_id_by_name(dashboard_name):
    url = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}/api/search"
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dashboards = response.json()
        for dashboard in dashboards:
            # print(dashboard)
            if dashboard['title'] == dashboard_name:
                return dashboard
    return None

# Call the function to get the dashboard ID by its name
dashboard_name = "OsqueryLoadTest"
dashboard = get_dashboard_id_by_name(dashboard_name)
if dashboard:
    print(f"The Dashboard ID for '{dashboard_name}' is: {dashboard['id']}")
    print(dashboard)
else:
    print(f"Dashboard '{dashboard_name}' not found.")

