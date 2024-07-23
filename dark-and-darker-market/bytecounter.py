
import re
import scapy.all as scapy
import pickle
from keras.models import load_model
from keras import backend as K
import numpy as np
import pandas as pd
import subprocess
import sys
import win32pipe
import win32file
import time
import pywintypes

# Configurable variables
YOUR_DESIRED_IP = "35.71.175.214"  # Replace with the server IP you're interested in
YOUR_DESIRED_PORT = 20206         # Replace with the specific port number
YOUR_INTERFACE_NAME = r"\Device\NPF_{9756BD05-F46F-40E3-8D81-75B7992FB836}"      # Adjust the interface name (like 'eth0', 'wlan0') accordingly
 
def root_mean_squared_error(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true)))
 
model = load_model('model.h5', custom_objects={'root_mean_squared_error': root_mean_squared_error})
 
with open('scaler_X.pkl', 'rb') as file:
    scaler_X = pickle.load(file)
 
with open('scaler_y.pkl', 'rb') as file:
    scaler_y = pickle.load(file)
 
with open('encoder.pkl', 'rb') as file:
    encoder = pickle.load(file)
    
def packet_callback(packet):
    # Checking if the packet has the IP layer, the TCP layer, and it's from our desired IP and port
    if packet.haslayer(scapy.IP) and packet.haslayer(scapy.TCP):
        ip_src = packet[scapy.IP].src
        tcp_sport = packet[scapy.TCP].sport
        
        if ip_src == YOUR_DESIRED_IP and tcp_sport == YOUR_DESIRED_PORT:
            original_data = packet[scapy.TCP].payload
            transformed_data = transform_data(original_data)
 
            #if the data is "ping?" or "player joining" then don't print it
            #if(transformed_data != 'ping?' and transformed_data != 'player joining' and transformed_data != 'too many items'):
                #print the raw data first
                #print(f"Original Data: {bytes(original_data)}")
                #print(f"Transformed Data: {transformed_data}\n\n")
 
def transform_data(data):
    all_effects = """MaxHealthBonus,
MagicPenetration,
MagicalDamageReduction,
Will,
MagicalDamageBonus,
PhysicalDamageTrue,
MoveSpeed,
ActionSpeed,
RegularInteractionSpeed,
MoveSpeedBonus,
PhysicalDamageAdd,
MagicalHealing,
PhysicalDamageBonus,
Primitive,
Strength,
MoveSpeedAdd,
PhysicalDamageReduction,
PhysicalWeaponDamage,
MaxHealthAdd,
MagicalDamageTrue,
SpellCapacityBonus,
SpellCapacityAdd,
HeadshotReductionMod,
BuffDurationBonus,
DebuffDurationBonus,
MagicalDamageAdd,
ArmorRating,
MagicalPower,
MagicalInteractionSpeed,
MagicRegistance,
SpellCastingSpeed,
Knowledge,
Resourcefulness,
ArmorRatingAdd,
PhysicalWeaponDamageAdd,
ItemEquipSpeed,
PhysicalHealing,
ProjectileReductionMod,
PhysicalPower,
Agility,
Vigor,
MemoryCapacityBonus,
MagicalWeaponDamage,
Dexterity,
MagicalDamage,
ArmorPenetration,
MemoryCapacityAdd,
UndeadDamageMod
"""
    # Convert data payload to bytes
    byte_data = bytes(data)
 
    if(byte_data == b'\x08\x00\x00\x00\x02\x00\x00\x00'):
        byte_data = 'ping?'
        return byte_data
    
    #if the data contains "x00\x00\x00\xd9\x07\x00\x00" then its a player joining. Check the first 8 bytes
    if(byte_data[1:8] == b'\x00\x00\x00\xd9\x07\x00\x00'):
        byte_data = 'player joining'
        return byte_data
    
    #remove the first 30 bytes
    byte_data = byte_data[44:]
 
    #iterate through the bytes unitl we find a new line character, then remove before that
    for i in range(len(byte_data)):
        if(byte_data[i] == 10):
            byte_data = byte_data[i+2:]
            break
    
    #The bytes untill we reach 'x12' are the player name. Store the name in a variable, then remove the name from the data.
    player_name = ''
    for i in range(len(byte_data)):
        if(byte_data[i] == 18):
            player_name = byte_data[:i]
            byte_data = byte_data[i+2:]
            break
    
    #the next byte should be a capital letter, if its not, return "abnormal data", and print the data
    try:
        if(byte_data[0] < 65 or byte_data[0] > 90):
            print("abnormal data")
            print(byte_data)
            return "abnormal data"
    except IndexError: #if the data is too short, return "abnormal data"
        print("abnormal data")
        print(byte_data)
        return "abnormal data"
    
    #The next bytes of interest straddle an underscore. After the underscore are 4 numbers, then "\x1a". Before the underscore are a mix of capital and lowercase letters. The first letter is always capital. Isolate the bytes of interest, then remove them from the data.
    # Search for our pattern using regex
    pattern = re.compile(b'([A-Z][a-z]+)_(\d{4})\x1a')
    matches = pattern.findall(byte_data)
 
    # Check the number of matches
    if len(matches) > 1:
        return "too many items"
    elif len(matches) == 1:
        match = pattern.search(byte_data)  # Getting the match object for further operations
        bytes_of_interest = match.group(0)
        
        # Now, you mentioned saving the pattern to a variable
        saved_pattern = bytes_of_interest.decode('utf-8')
        print(f"player name: {player_name}")
        print(f"Saved Pattern: {saved_pattern}")
 
    else:
        print("Pattern not found. Data:")
        print(byte_data)
        return "pattern not found"
    
    #create a dictionary to store the next effects
    effects = {}
 
    #Get the next bytes until we reach "\x10". Use thoes bytes as the key, excluding "\x10". The value bytes will be after the "\x10" and before the next "\n". Store the key and value in the dictionary, then remove up to and including the "\n" from the data.
    # Search for the pattern using regex
    effect_pattern = re.compile(b'Effect_([A-Za-z_]+?)\x10([^\n]*?)\n')
 
    effect_match = effect_pattern.search(byte_data)
 
    #now we iterate through looking for "Effect_", and then an 'x10'. The bytes before the 'x10' are the key, and the bytes after the 'x10' and before the next "\n" are the value. Store the key and value in the dictionary, then remove up to and including the "\n" from the data. Repeat until we run out of effects.
    for effect_match in effect_pattern.finditer(byte_data):
        # Extracting the effect name and data
        effect_name = effect_match.group(1).decode('utf-8', errors='ignore')
        effect_data = effect_match.group(2)
 
        # Storing in the dictionary
        effects[effect_name] = effect_data
 
    for effect_name, effect_data in list(effects.items()):  # Using list to ensure safe iteration
        # if effect data is b'', then set it to 10
        if effect_data == b'':
            effects[effect_name] = 10
            continue
 
        if effect_name != "MoveSpeed":
            effects[effect_name] = effect_data[0]
        else:
            effects[effect_name] = 256 - effect_data[0]
 
        print(f"Effect Name: {effect_name}")
        print(f"Effect Data: {effects[effect_name]}")
 
    #Look to see if any of the effects that are here are not included in the list of all effects. If they are not, then return "abnormal data" with the missing effect name.
    for effect_name in effects.keys():
        if effect_name not in all_effects:
            print("abnormal data: missing effect")
            print(byte_data)
            return f"abnormal data, missing effect: {effect_name}"
 
 
    pattern = re.compile(b'(?<=\n)([^\n]+)\x12\x00')
    match = pattern.search(byte_data)
    largest_number = 0
    if match:
        result = match.group(1)[1:]
        print(result)
 
        # Find all numbers in the result
        numbers = re.findall(b'\d+', result)
        if numbers:
            # Convert the byte sequences to integers and find the maximum
            largest_number = max(map(int, numbers))
            print("Largest number:", largest_number)
        else:
            print("No numbers found.")
            return "no numbers found"
    else:
        print("No match found.")
        return "no match found"
 
    if(largest_number > 5000000):
        largest_number = 0
 
 
    # Convert all_effects into a list of effect names
    all_effects_list = [effect.strip() for effect in all_effects.split(',')]
 
    # Construct the INSERT statement
    columns = ", ".join(all_effects_list)
    placeholders = ", ".join([f":{effect}" for effect in all_effects_list])
    sql = f'''
    INSERT INTO players (time, playername, name, price, {columns})
    VALUES (datetime('now'), :player_name, :saved_pattern, :largest_number, {placeholders})
    '''
 
    # Construct the dictionary of values to insert, with defaults set to None
    values = {effect: None for effect in all_effects_list}
    values.update({
        'player_name': player_name.decode('utf-8', errors='ignore'),
        'saved_pattern': saved_pattern
    })
 
    # If we found numbers in the result, we use the largest number as the price
    if 'numbers' in locals() and numbers:
        values['largest_number'] = largest_number
    else:
        values['largest_number'] = None
 
    if(values['largest_number'] < 15):
        return "abnormal data: price too low"
 
    # Update the dictionary with the actual values from effects
    for effect_name, effect_data in effects.items():
        values[effect_name] = effect_data
 
    #prepare the data for the model
    data = pd.DataFrame(values, index=[0])
    #print the columns
 
    # 1. Remove unnecessary columns
    data = data.drop(columns=['player_name', 'largest_number'])
 
    # 2. Handle missing values
    data = data.fillna(0)
 
    #move the 'saved_pattern' column to the front
    saved_pattern = data['saved_pattern']
    data.drop(labels=['saved_pattern'], axis=1,inplace = True)
 
    data.insert(0, 'saved_pattern', saved_pattern)
 
    #rename the 'saved_pattern' column to 'name'
    data.rename(columns={'saved_pattern': 'name'}, inplace=True)
 
 
    # One-hot encoding for 'name' column
    try:
        names_encoded = encoder.transform(data[['name']])
    except ValueError:
        print("abnormal data: name not found")
        print(byte_data)
        return "abnormal data: name not found"
 
    names_encoded_df = pd.DataFrame(names_encoded, columns=encoder.get_feature_names(['name']))
    # Combine with original data
 
    data_encoded = pd.concat([data.drop('name', axis=1), names_encoded_df], axis=1)
 
    #print ALL the columns (for debugging). Need to do it in list form to print all of them
 
    #order the columns by alphabetical order
    data_encoded = data_encoded.reindex(sorted(data_encoded.columns), axis=1)
 
 
    X_scaled = scaler_X.transform(data_encoded)
 
    # Predict the price
    prediction = model.predict(X_scaled)
    prediction = scaler_y.inverse_transform(prediction)
 
    # Print the prediction
    print(f"Predicted price: {prediction}")
 
    if(int(values['largest_number']) <= 100 and prediction >= 550):
            #send the player, item name and prediction to a new terminal window
            send_to_pipe(f"{values['player_name']}, {values['saved_pattern']}, {prediction}, {values['largest_number']}")
 
    return byte_data
 
def main():
    global all_effects
    try:
        scapy.sniff(iface=YOUR_INTERFACE_NAME, prn=packet_callback, filter="tcp", store=0)
    except KeyboardInterrupt:
        pass
        
    print("\nExiting gracefully...")
 
def send_to_pipe(data):
    pipe_name = r'\\.\pipe\TestPipe'
 
    try:
        pipe = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None)
        win32file.WriteFile(pipe, data.encode())
        win32file.CloseHandle(pipe)
    except pywintypes.error as e:
        print(f"Failed to send: {e}")  
 
if __name__ == "__main__":
    main()