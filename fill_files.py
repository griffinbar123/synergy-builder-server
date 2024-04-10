import asyncio
from enum import Enum
import os
import numpy as np
import requests
import json
import pandas as pd
import time
import sys
import threading
import random

NUMBER_OF_ENTRIES_PER_TIER = 840
GAMES_PER_PLAYER = 40

dev_api_key = "RGAPI-b12dbd36-709e-4f4e-9333-97ddf99e3963"

class Tier(Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    EMERALD = 5
    DIAMOND = 6
    # ALANA = "ALANA"

summoners_in_tiers = {Tier.IRON : [], Tier.BRONZE : [], Tier.SILVER : [], Tier.GOLD : [], Tier.PLATINUM : [], Tier.EMERALD : [], Tier.DIAMOND : []}

matches = {Tier.IRON : [], Tier.BRONZE : [], Tier.SILVER : [], Tier.GOLD : [], Tier.PLATINUM : [], Tier.EMERALD : [], Tier.DIAMOND : []}

def print_list(l):
    for i in l:
        print(i)

def loopWhileStatus(data, queue):
    while 'status' in data and data["status"]["status_code"] == 429:
        seconds_to_wait = 118
        if random.random() < 0.2:
            print(f"\nWaiting: ", end="")
        for i in range(seconds_to_wait):
            time.sleep(1)
        data = json.loads(requests.get(queue).text)
        if 'status' in data:
            if random.random() < 0.2:
                print(data)
        else:
            print("")
            print(f"Continuing... ")
        sys.stdout.flush()
    return data

def getPuuidFromSummonerId(summonerId):
    #get riot id
    riot_query = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/{summonerId}?api_key={dev_api_key}"
    data = json.loads(requests.get(riot_query).content)
    data = loopWhileStatus(data, riot_query)
    # print(data)
    return data['puuid']

def print_to_csv(file, titles, rows):
    f = open(file, "w")
    header = ""
    for title in titles:
        header += title + ","
    header = header[:-1] + "\n"
    f.write(header)
    for row in rows:
        row_str = ""
        for c in row:
            row_str += c + ","
        row_str = row_str[:-1] + "\n"
        f.write(row_str)

leftOffTier = Tier.IRON
leftOffValue = 0

def resumeWhereLeft(file):
    global leftOffTier
    global leftOffValue
    leftOffTier = Tier.IRON
    leftOffValue = 0
    f = open(file, "r")
    if len(f.read()) == 0:
        f.close()
        print(f"resume where left - File: {file} - leftOffTier: {leftOffTier.name} - leftOffValue: {leftOffValue}")
        return 
    df = pd.read_csv(file)
    tiers = df.loc[:, "tier"].to_list()
    print(len(tiers))
    num = len(tiers) // NUMBER_OF_ENTRIES_PER_TIER
    if num == 0:
        leftOffTier =Tier.IRON
    elif num == 1:
        leftOffTier =Tier.BRONZE
    elif num == 2:
        leftOffTier =Tier.SILVER
    elif num == 3:
        leftOffTier =Tier.GOLD
    elif num == 4:
        leftOffTier =Tier.PLATINUM
    elif num == 5:
        leftOffTier =Tier.EMERALD
    elif num == 6:
        leftOffTier =Tier.DIAMOND
    if(file == "puuids.csv"):
        leftOffValue = len(tiers) % NUMBER_OF_ENTRIES_PER_TIER
    elif file == "match_ids.csv":
        leftOffValue = len(tiers) // GAMES_PER_PLAYER
    else: 
        leftOffValue = len(tiers)
    print(f"resume where left - File: {file} - leftOffTier: {leftOffTier.name} - leftOffValue: {leftOffValue}")

def get_summoners():
    # print_to_csv("puuids.csv", ["puuids", "tier"], puuidrows)
    resumeWhereLeft("puuids.csv")
    if leftOffValue == 0 and leftOffTier.value == 0:
        f = open("puuids.csv", "w")
        f.write("puuids,tier\n")
        f.close()
    for tier in Tier:
        if tier.value < leftOffTier.value:
            continue
        for i in range(1, 5):
            if (leftOffValue // (NUMBER_OF_ENTRIES_PER_TIER//4)) >= i:
                continue
            div = "I"*i
            if div == "IIII":
                div = "IV"
            entries = f"https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier.name}/{div}?page=1&api_key={dev_api_key}"
            # data = json.loads(requests.get(entries).content)
            data = json.loads(requests.get(entries).text)
            data = loopWhileStatus(data, entries)
            if(type(data) == list):
                j = 1
                print(f"Number of entries in {tier.name} {div}: {len(data)}\nGetting Entry:", end="")
                f = open("puuids.csv", "a")
                for index, entry in enumerate(data[:NUMBER_OF_ENTRIES_PER_TIER//4]):
                    if tier.value == leftOffTier.value and ((i-1)*(NUMBER_OF_ENTRIES_PER_TIER//4)) + index < leftOffValue:
                        continue
                    print("", end=" ")
                    if(len(summoners_in_tiers[tier]) < NUMBER_OF_ENTRIES_PER_TIER): 
                        print(f"{index}, ", end="")
                        sys.stdout.flush()
                        # print(entry)
                        puuid = getPuuidFromSummonerId(entry['summonerId'])
                        summoners_in_tiers[tier].append(puuid)
                        j+=1
                        
                        f.write(f"{puuid},{tier.name}\n")
                print("\n")
                f.close()
        print_list(summoners_in_tiers[tier])

def get_match_ids(puuids, tiers):
    matches = []
    resumeWhereLeft("match_ids.csv")
    if leftOffValue == 0 and leftOffTier.value == 0:
        f = open("match_ids.csv", "w")
        f.write("match_ids,tier\n")
        f.close()

    i = 0
    print(f"Number Of Users: {len(puuids)}\nGetting Match_ids For User: ", end="")
    for puuid, tier in zip(puuids, tiers):
        if i < (leftOffTier.value * NUMBER_OF_ENTRIES_PER_TIER + leftOffValue):
            i += 1
            continue
        print(f"{i, }", end="")
        sys.stdout.flush()
        match_q = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={GAMES_PER_PLAYER}&api_key={dev_api_key}"
        data = json.loads(requests.get(match_q).text)
        data = loopWhileStatus(data, match_q)
        f = open("match_ids.csv", "a")
        # print(data)
        for match in data:
            # print(match, tier)
            matches.append([match, tier])
            f.write(f"{match},{tier}\n")
        f.close()
        i += 1
    print("\n")

    
            
    # print_to_csv("match_ids.csv", ["match_ids", "tier"], matches)

def load_summoners(reload = False):
    if reload:
        get_summoners()
        return pd.read_csv('puuids.csv')
    return pd.read_csv('puuids.csv')

    
def load_match_ids(puuids, tiers, reload = False):
    if reload:
        get_match_ids(puuids, tiers)
        return pd.read_csv('match_ids.csv')
    return pd.read_csv('match_ids.csv')

filter_obj ={"assists" : 0,
# "totalAlliedJungleMinionsKilled" : 0,
"damagePerMinute" : 0,
"effectiveHealAndShielding" : 0,
# "totalEnemyJungleMinionsKilled" : 0,
"championId" : 0,
"championName" : 0,
"detectorWardsPlaced" : 0,
"dragonKills" : 0,
"goldEarned" : 0,
"individualPosition" : 0,
"kills" : 0,
"magicDamageDealtToChampions" : 0,
"physicalDamageDealtToChampions" : 0,
"physicalDamageTaken" : 0,
"magicDamageTaken" : 0,
"timeCCingOthers" : 0,
"totalDamageDealtToChampions" : 0,
"totalDamageShieldedOnTeammates" : 0,
"totalDamageTaken" : 0,
"totalHeal" : 0,
"visionScore" : 0,
"deaths" : 0,
"teamPosition": 0,
"win" : 0}


def simplify_match_data(match):
    if "status" in match:
        print(match)
        return match
    nmatch = {}

    metadata = {}
    metadata["matchId"] = match["metadata"]["matchId"]
    # metadata["participants"] = match["metadata"]["participants"]
    nmatch["metadata"] = metadata

    info = {}
    info['gameDuration'] = match["info"]["gameDuration"]

    participants = []
    for participant in match["info"]["participants"]:
        t_participant = {}
        if "assists" in participant:
            t_participant["assists"] = participant["assists"]
        if "challenges" in participant:
            if "damagePerMinute" in participant["challenges"]:
                t_participant["damagePerMinute"] = participant["challenges"]["damagePerMinute"]
            if "effectiveHealAndShielding" in participant["challenges"]:
                t_participant["effectiveHealAndShielding"] = participant["challenges"]["effectiveHealAndShielding"]
        if "championId" in participant:
            t_participant["championId"] = participant["championId"]
        if "championName" in participant:
            t_participant["championName"] = participant["championName"]
        if "detectorWardsPlaced" in participant:
            t_participant["detectorWardsPlaced"] = participant["detectorWardsPlaced"]
        if "dragonKills" in participant:
            t_participant["dragonKills"] = participant["dragonKills"]
        if "goldEarned" in participant:
            t_participant["goldEarned"] = participant["goldEarned"]
        if "individualPosition" in participant:
            t_participant["individualPosition"] = participant["individualPosition"]
        if "teamPosition" in participant:
            t_participant["teamPosition"] = participant["teamPosition"]
        if "kills" in participant:
            t_participant["kills"] = participant["kills"]
        if "deaths" in participant:
            t_participant["deaths"] = participant["deaths"]
        if "magicDamageDealtToChampions" in participant:
            t_participant["magicDamageDealtToChampions"] = participant["magicDamageDealtToChampions"]
        if "physicalDamageDealtToChampions" in participant:
            t_participant["physicalDamageDealtToChampions"] = participant["physicalDamageDealtToChampions"]
        if "physicalDamageTaken" in participant:
            t_participant["physicalDamageTaken"] = participant["physicalDamageTaken"]
        if "magicDamageTaken" in participant:
            t_participant["magicDamageTaken"] = participant["magicDamageTaken"]
        if "timeCCingOthers" in participant:
            t_participant["timeCCingOthers"] = participant["timeCCingOthers"]
        if "totalDamageDealtToChampions" in participant:
            t_participant["totalDamageDealtToChampions"] = participant["totalDamageDealtToChampions"]
        if "totalDamageShieldedOnTeammates" in participant:
            t_participant["totalDamageShieldedOnTeammates"] = participant["totalDamageShieldedOnTeammates"]
        if "totalDamageTaken" in participant:
            t_participant["totalDamageTaken"] = participant["totalDamageTaken"]
        # if "totalAlliedJungleMinionsKilled" in participant:
        #     t_participant["totalAlliedJungleMinionsKilled"] = participant["totalAlliedJungleMinionsKilled"]
        # if "totalEnemyJungleMinionsKilled" in participant:
        #     t_participant["totalEnemyJungleMinionsKilled"] = participant["totalEnemyJungleMinionsKilled"]  
        if "totalHeal" in participant:
            t_participant["totalHeal"] = participant["totalHeal"]
        if "visionScore" in participant:
            t_participant["visionScore"] = participant["visionScore"]
        if "win" in participant:
            t_participant["win"] = participant["win"]



        participants.append(t_participant)
    
    info["participants"] = participants
    nmatch["info"] = info
    return nmatch

def checkIfChecked(matches, match_id):
    for m in matches:
        if m["match:"]["metadata"]["matchId"] == match_id:
            return True
    return False

def get_matches_for_type(match_ids, tier, tt= False):
    fi = "./matches/" + tier + ".json"
    f = open(fi, "r")
    starting = 0
    matches = []
    if len(f.read()) != 0:
        df = pd.read_json(fi)
        starting = df.loc[0, "numberOfMatches"]
        matches = df.loc[:, "matches"].tolist()
    
    print(f"Starting Matches In {tier}: {starting}")
    # print(matches)
    j = 0
    print(f"Number Of Matches In {tier}: {len(match_ids)}\nGetting Match: ", end="")
    for match_id in match_ids:
        if j < starting or checkIfChecked(matches, match_id):
            j+=1
            continue
        if j % 20 == 0:
            print(f"{tier}: {len(matches) },", end="")
            sys.stdout.flush()
        match_q = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={dev_api_key}"
        data = simplify_match_data(json.loads(requests.get(match_q).text))
        # data = json.dumps(data)
        # print(str(data))
        data = simplify_match_data(loopWhileStatus(data, match_q))
        if "metadata" in data:
            matches.append({"tier": tier, "match:":data})
        j+=1
        if j % 10 == 0:
            with open(fi, "w") as outfile:
                outfile.write(json.dumps({"numberOfMatches": len(matches),"matches":matches}, indent=4))

    with open(fi, "w") as outfile:
            outfile.write(json.dumps({"numberOfMatches": len(matches),"matches":matches}, indent=4))

def get_matches(match_ids, tiers, tt = False):
    i = []
    b = []
    s = []
    g = []
    p = []
    e = []
    d = []
    for match_id, tier in zip(match_ids, tiers):
        if tier == "IRON":
            i.append(match_id)
        elif tier == "BRONZE":
            b.append(match_id)
        elif tier == "SILVER":
            s.append(match_id)
        elif tier == "GOLD":
            g.append(match_id)
        elif tier == "PLATINUM":
            p.append(match_id)
        elif tier == "EMERALD":
            e.append(match_id)
        elif tier == "DIAMOND":
            d.append(match_id)
    t1 = threading.Thread(target=get_matches_for_type, args=(i, "IRON"))
    t2 = threading.Thread(target=get_matches_for_type, args=(b, "BRONZE"))
    t3 = threading.Thread(target=get_matches_for_type, args=(s, "SILVER"))
    t4 = threading.Thread(target=get_matches_for_type, args=(g, "GOLD"))
    t5 = threading.Thread(target=get_matches_for_type, args=(p, "PLATINUM"))
    t6 = threading.Thread(target=get_matches_for_type, args=(e, "EMERALD"))
    t7 = threading.Thread(target=get_matches_for_type, args=(d, "DIAMOND"))

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
 
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    t7.join()
    
def assemble_match_arrs(tiers):
    fi = "./matches/"
    if tiers == None:
        fi = "../../matches/"
    arr = []
    iron = pd.read_json(fi + "IRON" + '.json').loc[:, "matches"].to_list()
    bronze = pd.read_json(fi + "BRONZE" + '.json').loc[:, "matches"].to_list()
    silver = pd.read_json(fi + "SILVER" + '.json').loc[:, "matches"].to_list()
    gold = pd.read_json(fi + "GOLD" + '.json').loc[:, "matches"].to_list()
    platinum = pd.read_json(fi + "PLATINUM" + '.json').loc[:, "matches"].to_list()
    emerald = pd.read_json(fi + "EMERALD" + '.json').loc[:, "matches"].to_list()
    diamond = pd.read_json(fi + "DIAMOND" + '.json').loc[:, "matches"].to_list()
    arr.extend(iron)
    arr.extend(bronze)
    arr.extend(silver)
    arr.extend(gold)
    arr.extend(platinum)
    arr.extend(emerald)
    arr.extend(diamond)
    return arr


def load_matches(match_ids, tiers, reload = False):
    if reload:
        get_matches(match_ids, tiers)
        return assemble_match_arrs(tiers)
    return assemble_match_arrs(tiers)

def filterDuplicates(data, tiers):
    pids = len(data)
    new_p = []
    new_t = []
    for i in range(pids):
        a = True
        for j in range(i+1, pids-1):
            if data[i] == data[j]:
                a = False
        if a:
            new_p.append(data[i])
            new_t.append(tiers[i])
    return new_p, new_t



def addMatch(match, tier):
    info = match["info"]
    participants = info["participants"]
    for participant in participants:
        name = participant["championName"]
        path = "./synergy_builder/backend/champions/" + name + ".json"
        champFile = open(path, "r")
        champJson = json.loads(champFile.read())
        champFile.close()

        pos = ""
        if ("teamPosition" not in participant or not (participant["teamPosition"] == "TOP" or participant["teamPosition"] == "MIDDLE" or participant["teamPosition"] == "JUNGLE" or participant["teamPosition"] == "BOTTOM" or participant["teamPosition"] == "UTILITY")) and ("individualPosition" not in participant or not (participant["individualPosition"] == "TOP" or participant["individualPosition"] == "MIDDLE" or participant["individualPosition"] == "JUNGLE" or participant["individualPosition"] == "BOTTOM" or participant["individualPosition"] == "UTILITY")):
            continue
        elif not ("teamPosition" not in participant or not (participant["teamPosition"] == "TOP" or participant["teamPosition"] == "MIDDLE" or participant["teamPosition"] == "JUNGLE" or participant["teamPosition"] == "BOTTOM" or participant["teamPosition"] == "UTILITY")):
            pos = participant["teamPosition"]
            freq = champJson["gamestats"][tier]["frequency_" + participant["teamPosition"]] + 1
            champJson["gamestats"][tier]["frequency_" + participant["teamPosition"]] = freq
        else:
            pos = participant["individualPosition"]
            freq = champJson["gamestats"][tier]["frequency_" + participant["individualPosition"]] + 1
            champJson["gamestats"][tier]["frequency_" + participant["individualPosition"]] = freq


        total = champJson["gamestats"][tier]["gamesrecorded"] + 1
        champJson["gamestats"][tier]["gamesrecorded"] = total

        total_wins_by_pos = champJson["gamestats"][tier]["total_wins_" + pos] + participant["win"]
        champJson["gamestats"][tier]["total_wins_" + pos] = total_wins_by_pos

        for key in participant:
            if key in filter_obj and key != "championName" and key != "championId" :
                if "total_" + key in champJson["gamestats"][tier] or key == "individualPosition" or key == "teamPosition":
                    if key != "individualPosition" and key != "teamPosition":
                        champJson["gamestats"][tier]["total_" + key] = champJson["gamestats"][tier]["total_" + key] + participant[key]
                else:
                    champJson["gamestats"][tier]["total_" + key] = participant[key]
        champFile = open(path, "w")
        champFile.write(json.dumps(champJson, indent = 4))
        champFile.close()
        # print(champJson)

def averageMatches():
    for filename in os.listdir("./synergy_builder/backend/champions"):
        f = os.path.join("./synergy_builder/backend/champions", filename)
        # checking if it is a file
        if os.path.isfile(f):
            c = open(f, 'r')
            js = json.loads(c.read())
            c.close()
            for tier in Tier:
                total = 0
                tos = js["gamestats"][str(tier.name)].copy()
                for key in tos:
                    if key == "gamesrecorded":
                        total = tos[key]
                        continue
                    if total == 0:
                        continue
                    if key[:len("frequency")] == "frequency":
                        js["gamestats"][str(tier.name)]["average_" + key] = js["gamestats"][str(tier.name)][key] / total
                        continue
                    if key[:len("total_wins_")] == "total_wins_" and js["gamestats"][str(tier.name)]["frequency_"+key[len("total_wins_"):]] != 0:
                        js["gamestats"][str(tier.name)]["average_" + key[len("total_"):]] = js["gamestats"][str(tier.name)][key] / js["gamestats"][str(tier.name)]["frequency_"+key[len("total_wins_"):]]
                        continue
                    if type(tos[key]) != str:
                        js["gamestats"][str(tier.name)]["average_" + key[len("total_"):]] = js["gamestats"][str(tier.name)][key] / total
            d = open('./synergy_builder/backend/champions/' + filename, 'w')
            d.write(json.dumps(js, indent = 4))
            d.close()

def clearChamps():
    for filename in os.listdir("./synergy_builder/backend/champions"):
        f = os.path.join("./synergy_builder/backend/champions", filename)
        # checking if it is a file
        if os.path.isfile(f):
            c = open(f, 'r')
            js = json.loads(c.read())
            c.close()
            js["gamestats"] = {
        "IRON" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        },
        "BRONZE" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0          
        },
        "SILVER" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        },
        "GOLD" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        },
        "PLATINUM" :{
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        },
        "EMERALD" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        },
        "DIAMOND" : {
            "gamesrecorded" : 0,
            "frequency_TOP" : 0,
            "frequency_JUNGLE" : 0,    
            "frequency_MIDDLE" : 0,
            "frequency_BOTTOM" : 0,
            "frequency_UTILITY" : 0,
            "total_wins_TOP" : 0,
            "total_wins_JUNGLE" : 0,
            "total_wins_MIDDLE" : 0,
            "total_wins_BOTTOM" : 0,
            "total_wins_UTILITY" : 0
        }
    }
            d = open('./synergy_builder/backend/champions/' + filename, 'w')
            d.write(json.dumps(js, indent = 4))
            d.close()




def getRawChampionData(name):
    file = "./champions/" + name + ".json"

    champFile = open(file, "r")
    champJson = json.loads(champFile.read())
    champFile.close()

    # print(pandas.read_json(path_or_buf = file))

    return champJson

def flatten(data, sub):
    for key in data[sub]:
        data[key] = data[sub][key]
    del data[sub]

# def checkIfTagInArray(data, tag):
#     return data["tags"].count(tag)

def getCleanChampionData(name, tier):
    data = getRawChampionData(name)
    tier = tier.upper()

    #flatten stats
    del data["name"]
    del data["id"]
    del data["key"]
    del data["partype"]
    flatten(data, "info")
    flatten(data, "stats")
    for k in data["gamestats"][tier]:
        data[k] = data["gamestats"][tier][k]
    del data["gamestats"]

    data["Tank"] = data["tags"].count("Tank")
    data["Fighter"] = data["tags"].count("Fighter")
    data["Assassin"] = data["tags"].count("Assassin")
    data["Mage"] = data["tags"].count("Mage")
    data["Support"] = data["tags"].count("Support")
    data["Marksman"] = data["tags"].count("Marksman")

    del data["tags"]

    while True:
        for k in data:
            if k[:len("total_")] == "total_" or k[:len("frequency_")] == "frequency_":
                del data[k]
                break
        b = True
        for k in data:
            if k[:len("total_")] == "total_" or k[:len("frequency_")] == "frequency_":
                b = False
                break
        if b:
            break
    
    del data["gamesrecorded"]

    return data




def getJsonForMatch(match_id, tier):

    m = load_matches(None, None)

    jsm = None

    for m1 in m:
        if m1["tier"] == tier and m1["match:"]["metadata"]["matchId"] == match_id:
            jsm = m1
            break
    return jsm

def getColumnHeaders(jsm):
    arr = ["tier"]
    for index, p in enumerate(jsm["match:"]["info"]["participants"]):
        base_n = "participant_" + str(index + 1) + "_"
        champ = p["championName"]
        clean_p = getCleanChampionData(champ, jsm["tier"])
        for k in clean_p:
            arr.append(base_n + k)
    return arr


def flattenParticpants(jsm):
    for index, p in enumerate(jsm["participants"]):
        base_n = "participant_" + str(index + 1) + "_"
        champ = p["championName"]
        clean_p = getCleanChampionData(champ, jsm["tier"])
        for k in clean_p:
            jsm[base_n + k] = clean_p[k]

def matchToBetterObject(jsm):
    if jsm == None or jsm["match:"] == None or jsm["match:"]["info"] == None or jsm["match:"]["info"]["participants"] == None or len(jsm["match:"]["info"]["participants"]) != 10:
        return None

    win = int(jsm["match:"]["info"]["participants"][0]["win"])

    del jsm["match:"]["metadata"]
    jsm["participants"] = jsm["match:"]["info"]["participants"]
    del jsm["match:"]
    flattenParticpants(jsm)
    del jsm["participants"]
    # return jsm["participant_1_"]
    # print(jsm)
    return win

def loadDataAndTargetsToCSV():
    arr = []
    m = load_matches(None, None)
    columns = None
    print(f"Total Matches: {len(m)}")
    print("Loading Match: ", end="")
    for index, m1 in enumerate(m):
        # if index == 1:
        #     break
        if columns is None:
            columns = getColumnHeaders(m1)
        if index % 10500 == 0:
            print(f"{index}, ", end="")
            sys.stdout.flush()
        
        n1 = matchToBetterObject(m1)
        # print(m1)
        m1["win"] = n1
        if type(n1) != None:
            arr.append(m1.copy())
    columns.append("win")
    print(f"\n\n{len(arr)}, {len(columns)}")
    df = pd.DataFrame(columns = columns, data = arr, index = np.arange(len(arr)))
    df.to_csv("../../final_data.csv")

def output_match(t, participants):
    jsm = {"tier": t}
    for index, p1 in enumerate(participants):
        # sys.stdout.flush()
        base_n = "participant_" + str(index + 1) + "_"
        clean_p = getCleanChampionData(p1, t)
        for k in clean_p:
            jsm[base_n + k] = clean_p[k]
    j = json.dumps(jsm, indent = 4)
    print(j)
    sys.stdout.flush()



if len(sys.argv) == 12:
    tier = sys.argv[1]
    p = [sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8],sys.argv[9],sys.argv[10], sys.argv[11]]
    if tier != None and len(p) == 10:
        output_match(tier, p)

