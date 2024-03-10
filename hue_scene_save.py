import requests
requests.packages.urllib3.disable_warnings()


def update_scene(hue_bridge_ip, hue_api_key, scene_id, lights_actions):
    log.debug("Creating/updating scene with ID: %s", scene_id)
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{scene_id}'
    headers = {'hue-application-key': hue_api_key}

    data = {"type": "scene", "actions": lights_actions}
    response = task.executor(requests.put, url, headers=headers, json=data, verify=False)
   
    return response.json()

@service
def hue_scene_save(hue_bridge_ip, hue_api_key, hue_scene_id):
    log.debug("Hue save script started")

    # Fetch scene data
    url = f'https://{hue_bridge_ip}/clip/v2/resource/scene/{hue_scene_id}'
    headers = {'hue-application-key': hue_api_key}
    response = task.executor(requests.get, url, headers=headers, verify=False)
 

    scene_data = response.json()

    # Extract light states directly from the scene data
    lights_actions = []
    if 'data' in scene_data and len(scene_data['data']) > 0 and 'actions' in scene_data['data'][0]:
        for action in scene_data['data'][0]['actions']:
            if action['target']['rtype'] == 'light':
                log.debug("Found light with ID: %s in scene", action['target']['rid'])
                lights_actions.append(action)

    # Update scene with the extracted light states
    scene_response = update_scene(hue_bridge_ip, hue_api_key, hue_scene_id, lights_actions)
    log.info("Scene creation/update response: %s", scene_response)


# This only runs when using from CLI, Home Assistant uses @service with pyscript
if __name__ == "__main__":
    import argparse
    import logging
    logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description='To use when not integrated with Home Assistant PyScript')
    parser.add_argument('-b', '--hue_bridge_ip', required=True)
    parser.add_argument('-a', '--hue_api_key', required=True)
    parser.add_argument('-s', '--hue_scene_id', required=True)

    args = parser.parse_args()
    hue_scene_save(args.hue_bridge_ip, args.hue_api_key, args.hue_scene_id)