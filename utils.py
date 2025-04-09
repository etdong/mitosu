import os
import numpy as np
import ossapi
import parser

import threading

from dotenv import load_dotenv
from jump import JumpAnalyzer
from stream import StreamAnalyzer

class BeatmapData:
    length: int
    stars: float
    od: float
    ar: float
    cs: float
    hpd: float
    bpm: float
    jump: float
    stream: float
    pp: float
    acc: float

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
api = ossapi.Ossapi(client_id, client_secret)

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = f"mongodb+srv://{db_username}:{db_password}@mitosu.t6p1o.mongodb.net/?retryWrites=true&w=majority&appName=mitosu"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# gets the top 1000 most played beatmaps of the player and writes the relevant info to db
def get_player_plays_data(player: ossapi.User):
    try:
        users_col = client["users"]["osu"]
        beatmaps_col = client["beatmaps"]["osu"]
        played = []
        for offset in range(0, 1000, 100):
            plays = api.user_beatmaps(player.id, type="most_played", limit=100, offset=offset)
            for play in plays:
                beatmap = play.beatmap().expand()
                doc = beatmaps_col.find_one({"beatmap_id": beatmap.id})
                if not doc:
                    parsed = parser.parse_beatmap(beatmap.id)
                    if not parsed:
                        continue
                    # analyze the beatmap for whether it is a jump or stream map
                    jump_analysis = JumpAnalyzer(parsed).analyze(beatmap.bpm)
                    stream_analysis = StreamAnalyzer(parsed).analyze(beatmap.bpm)
                    beatmap_info = {"beatmap_id": beatmap.id,
                                    "length": beatmap.total_length, 
                                    "starts": beatmap.difficulty_rating, 
                                    "od": beatmap.accuracy, 
                                    "ar": beatmap.ar, 
                                    "cs": beatmap.cs, 
                                    "hpd": beatmap.drain, 
                                    "bpm": beatmap.bpm, 
                                    "jump": jump_analysis.overall_confidence, 
                                    "stream": stream_analysis.overall_confidence}
                    beatmaps_col.insert_one(beatmap_info)
                played.append(beatmap.id)
                print(f"Processed {beatmap.id}; {len(played)}/1000")
        users_col.update_one({"user_id": player.id}, {"$set": {"played": played}}, upsert=True)
    except Exception as e:
        print(e)

def get_player_top_plays(player: ossapi.User):
    try:
        db = client["beatmaps"]
        col = db["osu"]
        top_plays = []
        plays = api.user_scores(player.id, type="best", limit=100)
        for score in plays:
            beatmap = score.beatmap
            doc = col.find_one({"beatmap_id": beatmap.id})
            if doc:
                doc["pp"] = score.pp
                doc["acc"] = score.accuracy
                top_plays.append(doc)
            else:
                parsed = parser.parse_beatmap(beatmap.id)
                # analyze the beatmap for whether it is a jump or stream map
                jump_analysis = JumpAnalyzer(parsed).analyze(beatmap.bpm)
                stream_analysis = StreamAnalyzer(parsed).analyze(beatmap.bpm)
                beatmap_info = {"beatmap_id": beatmap.id,
                                "length": beatmap.total_length, 
                                "starts": beatmap.difficulty_rating, 
                                "od": beatmap.accuracy, 
                                "ar": beatmap.ar, 
                                "cs": beatmap.cs, 
                                "hpd": beatmap.drain, 
                                "bpm": beatmap.bpm, 
                                "jump": jump_analysis.overall_confidence, 
                                "stream": stream_analysis.overall_confidence}
                col.update_one({"beatmap_id": beatmap.id}, {"$set": beatmap_info}, upsert=True)
                beatmap_info["pp"] = score.pp
                beatmap_info["acc"] = score.accuracy
                top_plays.append(beatmap_info)
            print(f"Processed {beatmap.id}; {len(top_plays)}/100")
        return top_plays
    except Exception as e:
        print(e)

def process_beatmap_batch(beatmapsets_batch: list[ossapi.Beatmapset], page: int):
    try:
        db = client["beatmaps"]
        beatmap_col = db["osu"]
        batch = []
        print(f"START processing page {page}")
        for beatmapset in beatmapsets_batch:
            for i in beatmapset.beatmaps:
                beatmap = i.expand()
                parsed = parser.parse_beatmap(beatmap.id)
                # analyze the beatmap for whether it is a jump or stream map
                jump_analysis = JumpAnalyzer(parsed).analyze(beatmap.bpm)
                stream_analysis = StreamAnalyzer(parsed).analyze(beatmap.bpm)
                batch.append({"beatmap_id": beatmap.id,
                                "length": beatmap.total_length, 
                                "starts": beatmap.difficulty_rating, 
                                "od": beatmap.accuracy,
                                "ar": beatmap.ar, 
                                "cs": beatmap.cs, 
                                "hpd": beatmap.drain, 
                                "bpm": beatmap.bpm, 
                                "jump": jump_analysis.overall_confidence, 
                                "stream": stream_analysis.overall_confidence})
            print(f"Processed beatmapset {i}/50 on page {page}")
        beatmap_col.insert_many(batch)
        print(f"FINISH processed page {page}")
    except Exception as e:
        print(e)

def get_beatmap_data(num_pages: int):
    beatmapsets_res = api.search_beatmapsets(sort="plays_desc")
    for page in range(0, num_pages):
        if beatmapsets_res:
            beatmapsets_batch = beatmapsets_res.beatmapsets
            threading.Thread(target=process_beatmap_batch, args=(beatmapsets_batch, page)).start()
        beatmapsets_res = api.search_beatmapsets(sort="plays_desc", cursor=beatmapsets_res.cursor)

def get_training_data(user: ossapi.User):
    try:
        users_col = client["users"]["osu"]
        beatmaps_col = client["beatmaps"]["osu"]

        user_data = users_col.find_one({"user_id": user.id})
        if not user_data:
            return None

        played_ids = user_data["played"]

        played = list(beatmaps_col.find({"beatmap_id": {"$in": played_ids}}))
        played_ = np.array([[i["length"], i["starts"], i["od"], i["ar"], i["cs"], i["hpd"], i["bpm"], i["jump"], i["stream"], 1] for i in played])

        not_played = list(beatmaps_col.find({"beatmap_id": {"$nin": played_ids}}).limit(len(played_ids)))
        not_played_ = np.array([[i["length"], i["starts"], i["od"], i["ar"], i["cs"], i["hpd"], i["bpm"], i["jump"], i["stream"], 0] for i in not_played])


        samples = np.concatenate((played_, not_played_))
        np.random.shuffle(samples)
        return samples   
    except Exception as e:
        print(e)
