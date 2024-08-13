import requests
import sys
import logging

requests.packages.urllib3.disable_warnings()

try:
    from homeassistant.components.pyscript import service
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    def service(func):
        return func

def get_all_lights(hue_bridge_ip, hue_api_key):
    log.debug("Fetching all lights")
    url = f'https://{hue_bridge_ip}/clip/v2/resource/light'
    headers = {'hue-application-key': hue_api_key}
    try:
        response = task.executor(requests.get, url, headers=headers, verify=False)
    except NameError:
        log.debug("Running outside of Home Assistant, not using task.executor")
        log.debug(url, headers)
        response = requests.get(url, headers=headers, verify=False)
    except requests.RequestException as e:
        log.error("Error fetching lights: %s", e)
        return {}

    return response.json()

def get_light_states_for_scene(hue_bridge_ip, hue_api_key, light_ids):
    all_lights_data = get_all_lights(hue_bridge_ip, hue_api_key)
    filtered_light_states = {}

    if 'data' in all_lights_data:
        for light in all_lights_data['data']:
            if light['id'] in light_ids:
                filtered_light_states[light['id']] = {
                    "on": light.get("on", {"on": False}),
                    "dimming": light.get("dimming", {"brightness": 0}),
                    "color_temperature": light.get("color_temperature", {"mirek": None}),
                    "color": light.get("color", {"xy": {"x": 0.0, "y": 0.0}}),
                    "dynamics": light.get("dynamics", {"status": "none", "speed": 0.0}),
                    "gradient": light.get("gradient", {"points": []})
                }
                log.debug("Found light with ID: %s in all lights", light['id'])

    return filtered_light_states

def update_scene(hue_bridge_ip, hue_api_key, scene_id, lights_states):
    log.debug("Creating/updating scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}

    actions = []
    for light_id, state in lights_states.items():
        action_data = {
            "on": {"on": state["on"]["on"]},
            "dimming": {"brightness": state["dimming"]["brightness"]}
        }

        if state["color_temperature"]["mirek"] is not None:
            action_data["color_temperature"] = {"mirek": state["color_temperature"]["mirek"]}
        else:
            action_data["color"] = {"xy": state["color"]["xy"]}

        if state["dynamics"]["status"] != "none":
            action_data["dynamics"] = {"duration": state["dynamics"]["speed"]}

        if state["gradient"]["points"]:
            action_data["gradient"] = {"points": state["gradient"]["points"]}

        action = {
            "target": {
                "rid": light_id,
                "rtype": "light"
            },
            "action": action_data
        }
        actions.append(action)

    data = {"type": "scene", "actions": actions}

    try:
        response = task.executor(requests.put, url, headers=headers, json=data, verify=False)
    except NameError:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.put(url, headers=headers, json=data, verify=False)
    except requests.RequestException as e:
        log.error("Error updating scene: %s", e)
        return {}

    return response.json()

def get_scene_lights(hue_bridge_ip, hue_api_key, scene_id):
    log.debug("Fetching lights in the scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}
    try:
        response = task.executor(requests.get, url, headers=headers, verify=False)
    except NameError:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.get(url, headers=headers, verify=False)
    except requests.RequestException as e:
        log.error("Error fetching scene lights: %s", e)
        return []

    scene_data = response.json()
    light_ids = []
    if 'data' in scene_data and len(scene_data['data']) > 0 and 'actions' in scene_data['data'][0]:
        for action in scene_data['data'][0]['actions']:
            if action['target']['rtype'] == 'light':
                light_ids.append(action['target']['rid'])
                log.debug("Found light with ID: %s in scene", action['target']['rid'])

    return light_ids

@service
def hue_scene_save(hue_bridge_id_or_ip, hue_api_key, hue_scene_id):
    log.debug("Hue save script started")
    if "." in hue_bridge_id_or_ip:  # when using IP
        hue_bridge_ip = hue_bridge_id_or_ip
    else:
        hue_bridge_ip = get_hue_bridge_ip(hue_bridge_id_or_ip)  # have to discover it
    scene_lights = get_scene_lights(hue_bridge_ip, hue_api_key, hue_scene_id)
    lights_states = get_light_states_for_scene(hue_bridge_ip, hue_api_key, scene_lights)
    scene_response = update_scene(hue_bridge_ip, hue_api_key, hue_scene_id, lights_states)
    log.info("Scene creation/update response: %s", scene_response)

def get_hue_bridge_ip(hue_bridge_id):
    """Get Hue bridge IP from its ID"""
    url = "https://discovery.meethue.com"
    try:
        response = task.executor(requests.get, url, verify=False)
    except NameError:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.get(url, verify=False)
    except requests.RequestException as e:
        log.error("Error discovering Hue bridge: %s", e)
        return ""

    match = [b["internalipaddress"] for b in response.json() if hue_bridge_id == b["id"]]
    if match:
        log.debug("Found bridge IP %s for bridge ID %s", match[0], hue_bridge_id)
        return match[0]
    return ""

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='To use when not integrated with Home Assistant PyScript')
    parser.add_argument('-b', '--hue_bridge_id_or_ip', required=True)
    parser.add_argument('-a', '--hue_api_key', required=True)
    parser.add_argument('-s', '--hue_scene_id', required=True)

    args = parser.parse_args()
    hue_scene_save(args.hue_bridge_id_or_ip, args.hue_api_key, args.hue_scene_id)
