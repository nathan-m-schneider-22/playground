import json
import os, sys


print("matchid\t name\t tag\t character\t team\t winner\ttier\trank")



for file in os.listdir("players"):

    # filename = "Antonidas#6254.json"
    data = json.load(open("players/"+file))

    for match in data:
        matchid = match['metadata']['matchid']
        
        red, blue = match['teams']['red']['rounds_won'], match['teams']['blue']['rounds_won']
        winner = "Tie"
        if blue > red: winner = "Blue"
        if red > blue: winner = "Red"
        

        for player in match['players']['all_players']:
            name, tag, character = player['name'], player['tag'],player['character'] 
            team =  player['team']
            currenttier = player['currenttier']
            rank = player['currenttier_patched']

        print(matchid, name, tag, character, team, winner, currenttier, rank, sep='\t')