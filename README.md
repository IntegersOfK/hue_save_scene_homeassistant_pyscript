# Hue Save Scene for Home Assistant Pyscript
This script is designed to update a pre-existing Scene in your Philips Hue setup with the current state of the lights in that Scene. I created this script to use when the occupancy of my motion sensor detects that there is no longer motion in the room, so the current state of the lights can be saved before they are turned off. That way, when the motion is detected again, the state of the lights can return to what they were before they were turned off.

You can do this type of scene creation/saving with the native scenes directly in Home Assitant, but with Philips Hue lights it does not nessarily use the correct color/temperature, and when calling multiple lights it does not syncronize (it sends calls for each light one at a time) or it may flicker/blink when being applied. By using this script to update the lights states to a native Hue Scene (rather than that a Home Assitant "create scene" state), you're going to get a nice smooth transition back to the state the lights were in before they were turned off because it'll be managed by the Hue hub.

The script itself only updates an existing scene (create the scene to use in the Hue App and then provide the scene id) by checking the current state of the lights that are already setup in that scene, ignoring the scene's current color/brightness settings. Then it checks each light's current color and brightness and updates the scene to those current states. After it's saved, you can turn the lights off and tehn later you can call restore the scene to what it was (when you detect motion again or whatever you want to make for a trigger).

This script works with the Home Assistant custom component Pyscript and exposes hue_scene_save as a service.

## Prerequisites
- Philips Hue Bridge: You should have a Philips Hue Bridge set up in your home network. This doesn't work when you have the Hue Lights connected with Zigbee directly to Home Assistant.
- API Key: Obtain an API key (also known as a username) for your Philips Hue Bridge. Follow the instructions in the Philips Hue API v2 documentation to get your API key.
- Scene Creation: Create a scene in the Philips Hue app and include all the lights you'd like to be saved. This scene will be the one updated by the script. It can contain any lights, so you could make a new Zone called "Automation" or something if you'd like to keep it segmented from your existing rooms. For some reason I wasn't able to figure out how to get a "fresh" scene to be created with the API, so just make one in the app first so we have something to modify.
- Figure out the Scene ID. I don't know an easy way to do that other than to call the API V2 with a GET `https://{bridge}/clip/v2/resource/scene` using your API key in the header. In the future, perhaps the script can be updated to allow the selection of a scene by name instead of by V2 scene ID.
- Install Pyscript as a custom component and then put the `hue_scene_save.py` file into a folder called pyscript.
- You should now be able to call the service pyscript.hue_scene_save with the data. For example, here's how mine looks.

```
hue_bridge_ip: 10.0.0.48
hue_api_key: hF6rilCE-VOmqTq0wGFqOj5xW2HBW-1HM9i7tdCu
hue_scene_id: cfb3f77f-ff35-45b9-877c-57e5bad5c473
``` 
