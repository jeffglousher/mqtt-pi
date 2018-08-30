import os
import binascii
import yaml
import paho.mqtt.client as mqtt



# Update the mqtt state topic
def update_state(value, topic):
    print("State change triggered: %s -> %s" % (topic, value))

    client.publish(topic, value, retain=True)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected with result code: %s" % mqtt.connack_string(rc))
    for config in CONFIG['doors']:
        command_topic = config['command_topic']
        print "Listening for commands on %s" % command_topic
        client.subscribe(command_topic)

# Execute the specified command for a door
def execute_command(door, command):
    print "Executing command %s for door %s" % (command, door.id)
    if command == "OPEN" and door.state == 'closed':
        door.open()
    elif command == "CLOSE" and door.state == 'open':
        door.close()
    elif command == "STOP":
        door.stop()
    else:
        print "Invalid command: %s" % command

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.yaml'), 'r') as ymlfile:
    CONFIG = yaml.load(ymlfile)

### SETUP MQTT ###
user = CONFIG['mqtt']['user']
password = CONFIG['mqtt']['password']
host = CONFIG['mqtt']['host']
port = int(CONFIG['mqtt']['port'])

client = mqtt.Client(client_id="MQTTGarageDoor_" + binascii.b2a_hex(os.urandom(6)), clean_session=True, userdata=None, protocol=3)

client.on_connect = on_connect

client.username_pw_set(user, password=password)
client.connect(host, port, 60)
### SETUP END ###

### MAIN LOOP ###
if __name__ == "__main__":
    # Create door objects and create callback functions
    for doorCfg in CONFIG['doors']:
        command_topic = doorCfg['command_topic']
        state_topic = doorCfg['state_topic']


        door = GarageDoor(doorCfg)

        # Callback per door that passes a reference to the door
        def on_message(client, userdata, msg, door=door):
            execute_command(door, str(msg.payload))

        # Callback per door that passes the doors state topic
        def on_state_change(value, topic=state_topic):
            update_state(value, topic)

        client.message_callback_add(command_topic, on_message)

        # You can add additional listeners here and they will all be executed when the door state changes
        door.onStateChange.addHandler(on_state_change)

        # Publish initial door state
        client.publish(state_topic, door.state, retain=True)

    # Main loop
    client.loop_forever()