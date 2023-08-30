import requests
GRAFANA_API_KEY = 'eyJrIjoiU0phSVNoSmRPcTZSOEFpT3lodTNjTnB1MUNnT0dpYWgiLCJuIjoiZGVtb19rZXkiLCJpZCI6MX0='
base_url = "http://192.168.128.50:3000"

GRAFANA_HOST = 's1monitor'
GRAFANA_PORT = "3000"

# ist_start_time = '2023-08-03 00:32:00'
# ist_end_time = '2023-08-03 10:33:00'
# ist_time_format = '%Y-%m-%d %H:%M:%S'
# start_time_utc = '2023-08-02T19:02:00Z'
# end_time_utc = '2023-08-03T05:02:00Z'
# start_time_utc = (datetime.strptime(ist_start_time, ist_time_format) - ist_offset)
# end_time_utc = (datetime.strptime(ist_end_time, ist_time_format) - ist_offset)
# start_time_utc = int(start_time_utc.timestamp() * 1000)
# end_time_utc = int(end_time_utc.timestamp() * 1000)


# ist_start_time = '2023-08-03 00:32:00'
# ist_end_time = '2023-08-03 10:33:00'

# ist_time_format = '%Y-%m-%d %H:%M:%S'
# ist_offset = timedelta(hours=5, minutes=30)  # IST offset from UTC

# start_time_utc = (datetime.strptime(ist_start_time, ist_time_format) + ist_offset).strftime('%Y-%m-%dT%H:%M:%SZ')
# end_time_utc = (datetime.strptime(ist_end_time, ist_time_format) + ist_offset).strftime('%Y-%m-%dT%H:%M:%SZ')


def get_dashboard_data(dashboard_uid):
    url = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}/api/dashboards/uid/{dashboard_uid}"

    print(url)
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
    }
    response = requests.get(url, headers=headers)
    print(response)
    if response.status_code == 200:
        dashboard_data = response.json()
        # print(dashboard_data)
        return dashboard_data
    return None


def get_panel_data(dashboard_uid, panel_id):
    dashboard_data = get_dashboard_data(dashboard_uid)
    if dashboard_data:
        panels = dashboard_data.get("dashboard", {}).get("panels", [])
        for panel in panels:
            if panel.get("id") == panel_id:
                return panel
    return None

# Fetch data from the dashboard using its ID
# dashboard_data = get_dashboard_data('0xQAxECVk')
panel_data = get_panel_data('0xQAxECVk',136)
if panel_data:
    print("Panel Data:")
    print(panel_data)
else:
    print("Failed to fetch panel data.")
