import requests
import base64
import re

GRAFANA_API_KEY = 'eyJrIjoiU0phSVNoSmRPcTZSOEFpT3lodTNjTnB1MUNnT0dpYWgiLCJuIjoiZGVtb19rZXkiLCJpZCI6MX0='
GRAFANA_HOST = 's1monitor'
GRAFANA_PORT = '3000'

def get_dashboard_data(dashboard_uid):
    url = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}/api/dashboards/uid/{dashboard_uid}"
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dashboard_data = response.json()
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

def save_panel_as_image(dashboard_uid, panel_id, filename):
    panel_data = get_panel_data(dashboard_uid, panel_id)
    if panel_data:
        
        panel_json = panel_data.get("gridPos", {})
        panel_base64 = base64.b64encode(str(panel_json).encode("utf-8"))
        url = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}/api/snapshots"
        headers = {
            "Authorization": f"Bearer {GRAFANA_API_KEY}",
            "Content-Type": "application/json",
        }
        # data = {
        #     "dashboard": {
        #         "id": dashboard_uid,
        #         "panels": [
        #             {"gridPos": panel_json}
        #         ]
        #     },
        #     "expires": 0,
        # }

        # data = {
        #     "dashboard": {
        #         "id": dashboard_uid,
        #         "panels": [panel_data]  # Pass the panel_data directly to the "panels" field
        #     },
        #     "expires": 0,
        # }

        data = {
        "dashboard": {
            "uid": dashboard_uid
        },
        "panelId": panel_id,
        "expires": 0,  # Optional: Set the expiration time for the snapshot (e.g., "2h" for 2 hours)
    }


        response = requests.post(url, headers=headers, json=data)
        try:
            if response.status_code == 200:
                snapshot_url = response.json().get("url", "")
                print(snapshot_url)
                image_response = requests.get(snapshot_url)
                print(image_response)
                if image_response.status_code == 200:
                    with open(filename, "wb") as f:
                        # print(image_response.content)
                        f.write(image_response.content)
                    print(f"Panel saved as image: {filename}")
                else:
                    print(f"Failed to fetch panel image: {image_response.status_code} - {image_response.text}")
            else:
                print(f"Failed to generate snapshot: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching snapshot image: {e}")  
    else:
        print("Failed to fetch panel data.")

# Example usage: Save Panel with ID 136 in Dashboard with UID '0xQAxECVk' as an image
save_panel_as_image('0xQAxECVk', 136, "panel_image.png")
