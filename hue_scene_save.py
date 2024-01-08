import requests
requests.packages.urllib3.disable_warnings()

# Initialize logging

def get_scene_lights(hue_bridge_ip, hue_api_key, scene_id):
    log.debug("Fetching lights in the scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}
    response = task.executor(requests.get, url, headers=headers, verify=False)
    scene_data = response.json()

    light_ids = []
    if 'data' in scene_data and len(scene_data['data']) > 0 and 'actions' in scene_data['data'][0]:
        for action in scene_data['data'][0]['actions']:
            if action['target']['rtype'] == 'light':
                light_ids.append(action['target']['rid'])
                log.debug("Found light with ID: %s in scene", action['target']['rid'])
    return light_ids

def get_light_state(hue_bridge_ip, hue_api_key, light_id):
    log.debug("Fetching state of the light with ID: %s", light_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/light/{light_id}'
    headers = {'hue-application-key': hue_api_key}
    response = task.executor(requests.get, url, headers=headers, verify=False)
    light_data = response.json()
    log.debug("Light Data: %s is %s", light_id, light_data)

    if 'data' in light_data and len(light_data['data']) > 0:
        return light_data['data'][0]
    else:
        log.warning("No data found for light with ID: %s", light_id)
        return None

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
    response = task.executor(requests.put, url, headers=headers, json=data, verify=False)
    return response.json()


@service
def hue_scene_save(hue_bridge_ip, hue_api_key, hue_scene_id):                                                                              
    log.debug("Hue save script started")                                                                                                   
                                                                                                                                           
    scene_lights = get_scene_lights(hue_bridge_ip, hue_api_key, hue_scene_id)                                                              
    lights_states = {light_id: get_light_state(hue_bridge_ip, hue_api_key, light_id)                                                       
                     for light_id in scene_lights}                                                                                         
                                                                                                                                           
    scene_response = update_scene(hue_bridge_ip, hue_api_key, hue_scene_id, lights_states)                                                     
    log.info("Scene creation/update response: %s", scene_response) 
