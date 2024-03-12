import requests
requests.packages.urllib3.disable_warnings()

def get_all_lights(hue_bridge_ip, hue_api_key):
    log.debug("Fetching all lights")
    url = f'https://{hue_bridge_ip}/clip/v2/resource/light'
    headers = {'hue-application-key': hue_api_key}
    response = task.executor(requests.get, url, headers=headers, verify=False)
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

@service
def hue_scene_save(hue_bridge_ip, hue_api_key, hue_scene_id):                                                                              
    log.debug("Hue save script started")                                                                                                   
                                                                                                                                           
    scene_lights = get_scene_lights(hue_bridge_ip, hue_api_key, hue_scene_id)                                                              
    lights_states = get_light_states_for_scene(hue_bridge_ip, hue_api_key, scene_lights)                                                    
                                                                                                                                           
    scene_response = update_scene(hue_bridge_ip, hue_api_key, hue_scene_id, lights_states)                                                 
    log.info("Scene creation/update response: %s", scene_response)
