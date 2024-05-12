import requests
try:
    from homeassistant.components.pyscript import service
except ImportError:
    def service(func):
        return func
requests.packages.urllib3.disable_warnings()

def get_all_lights(hue_bridge_ip, hue_api_key):
    log.debug("Fetching all lights")
    url = f'https://{hue_bridge_ip}/clip/v2/resource/light'
    headers = {'hue-application-key': hue_api_key}
    try:
        response = task.executor(requests.get, url, headers=headers, verify=False)
    except NameError as e:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.get(url, headers=headers, verify=False)
    lights_data = response.json()
    return lights_data

def get_light_states_for_scene(hue_bridge_ip, hue_api_key, light_ids):
    all_lights_data = get_all_lights(hue_bridge_ip, hue_api_key)
    filtered_light_states = {}

    if 'data' in all_lights_data:
        for light in all_lights_data['data']:
            if light['id'] in light_ids:
                filtered_light_states[light['id']] = light
                log.debug("Found light with ID: %s in all lights", light['id'])

    return filtered_light_states

def update_scene(hue_bridge_ip, hue_api_key, scene_id, lights_states):
    log.debug("Creating/updating scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}

    actions = []
    for light_id, state in lights_states.items():
        # Prepare the action with relevant data
        action_data = {
            "on": {"on": state.get("on", {}).get("on", False)},
            "dimming": {"brightness": state.get("dimming", {}).get("brightness", 0)}
        }

        # Add color if xy coordinates are present
        if 'xy' in state.get("color", {}):
            action_data["color"] = {"xy": state["color"]["xy"]}

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
    except NameError as e:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.put(url, headers=headers, json=data, verify=False)

    return response.json()

def get_scene_lights(hue_bridge_ip, hue_api_key, scene_id):
    log.debug("Fetching lights in the scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}
    try:
        response = task.executor(requests.get, url, headers=headers, verify=False)
    except NameError as e:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.get(url, headers=headers, verify=False)
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
    if "." in hue_bridge_id_or_ip: # when using IP
        hue_bridge_ip = hue_bridge_id_or_ip
    else:
        hue_bridge_ip = get_hue_bridge_ip(hue_bridge_id_or_ip) # have to discover it
    scene_lights = get_scene_lights(hue_bridge_ip, hue_api_key, hue_scene_id)
    lights_states = get_light_states_for_scene(hue_bridge_ip, hue_api_key, scene_lights)
    scene_response = update_scene(hue_bridge_ip, hue_api_key, hue_scene_id, lights_states)
    log.info("Scene creation/update response: %s", scene_response)

def get_hue_bridge_ip(hue_bridge_id):
    """Since IP addresses are usually dynamic, the bridge id is a better selector in general, but the
    endpoint to check where it is can go down. TODO: Do discovery with mDNS too and cache it somewhere."
    """

    url = "https://discovery.meethue.com"
    try:
        response = task.executor(requests.get, url, verify=False)
    except NameError as e:
        log.debug("Running outside of Home Assistant, not using task.executor")
        response = requests.get(url)
    match = [b["internalipaddress"] for b in response.json() if hue_bridge_id == b["id"]]
    if len(match):
        log.debug("Found bridge IP " + str(match) + " for bridge ID + " + hue_bridge_id)
        return match[0]


if __name__ == "__main__":
    # Use the main function when invoked from regular python cli, otherwise home assistant uses pyscript @service
    import argparse
    import logging
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description='To use when not integrated with Home Assistant PyScript')
    parser.add_argument('-b', '--hue_bridge_id_or_ip', required=True)
    parser.add_argument('-a', '--hue_api_key', required=True)
    parser.add_argument('-s', '--hue_scene_id', required=True)

    args = parser.parse_args()
    hue_scene_save(args.hue_bridge_id_or_ip, args.hue_api_key, args.hue_scene_id)
