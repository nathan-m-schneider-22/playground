import requests
import json
import time



def main():
    username = "Antonidas"
    tag = "6254"

    player_queue = json.load(open("queue.json"))
    player_queue.append((username,tag))

    seen_players = json.load(open("seen.json"))
    player_queue = [p for p in player_queue if not p in seen_players]


    while len(player_queue) > 0:

        player, tag = player_queue.pop(0)
        if str((player,tag)) in seen_players: continue

        print(player,tag)
        seen_players.append(str((player,tag)))

        data = get_data(player,tag)
        if data == None: continue
        
        with open("players/%s#%s.json" % (player,tag), "w") as outfile:
            outfile.write(json.dumps(data))

        with open("queue.json", "w") as outfile:
            outfile.write(json.dumps(player_queue))
        with open("seen.json", "w") as outfile:
            outfile.write(json.dumps(seen_players))

        players = get_players(data)
        
        for player in players:
            if not str(player) in seen_players and not str(player) in player_queue:
                player_queue.append(player)



        

def get_players(data):
    players = []
    for game in data:
        for player in game["players"]["all_players"]:
            name = player['name']
            tag = player['tag']

            players.append((name,tag))

    return players


def get_data(player, tag):

    for _ in range(3):
        
        try:
            url = "https://api.henrikdev.xyz/valorant/v3/matches/na/%s/%s?filter=competitive"
            r = requests.get(url % (player,tag))

            data = r.json()['data']
            return data
        except Exception as Err:
            print(r.json)
            print(Err)
            time.sleep(10)



if __name__ == "__main__":
    main()