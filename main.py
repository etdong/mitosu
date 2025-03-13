import os
import numpy as np
import ossapi
import ossapi.models
import parser
import csv
from dotenv import load_dotenv
from jump import JumpAnalyzer
from stream import StreamAnalyzer
from model import get_weights

class BeatmapData:
    length: int
    stars: float
    od: float
    ar: float
    cs: float
    hpd: float
    bpm: float
    jump_confidence: float
    stream_confidence: float
    playcount: int

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
api = ossapi.Ossapi(client_id, client_secret)

# gets the top 1000 most played beatmaps of the player and writes the relevant info to a csv file
player = api.user("h0mygod")

with open("data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "length", "stars", "od", "ar", "cs", "hpd", "bpm", "jump_confidence", "stream_confidence", "playcount"])
    for offset in range(0, 1000, 100):
        plays = api.user_beatmaps(player.id, type="most_played", limit=100, offset=offset)
        for play in plays:
            plays = play.count
            beatmap = play.beatmap().expand()
            parsed = parser.parse_beatmap(beatmap.id)
            # analyze the beatmap for whether it is a jump or stream map
            jump_analysis = JumpAnalyzer(parsed).analyze(beatmap.bpm)
            stream_analysis = StreamAnalyzer(parsed).analyze(beatmap.bpm)
            writer.writerow([parsed.metadata["Title"].strip(),
                            beatmap.total_length, 
                            beatmap.difficulty_rating, 
                            beatmap.accuracy, beatmap.ar, 
                            beatmap.cs, 
                            beatmap.drain, 
                            beatmap.bpm, 
                            jump_analysis.overall_confidence, 
                            stream_analysis.overall_confidence, 
                            plays])
            print(f"Processed {beatmap.id}")

# train the linear regression model on the data.csv and get the best resulting weights
w = get_weights()

# get the top N most played beatmap sets and recommend them based on the weights.
# WARNING: This will take a long time to run.
recommendations = []
n = 1000
beatmapsets = api.search_beatmapsets(sort="plays_desc").beatmapsets
for beatmapset in beatmapsets[:1000]:
    for i in beatmapset.beatmaps:
        beatmap = i.expand()
        parsed = parser.parse_beatmap(beatmap.id)
        jump_analysis = JumpAnalyzer(parsed).analyze(beatmap.bpm)
        stream_analysis = StreamAnalyzer(parsed).analyze(beatmap.bpm)
        vec = np.array([1,
                        beatmap.total_length, 
                        beatmap.difficulty_rating, 
                        beatmap.accuracy, beatmap.ar, 
                        beatmap.cs, 
                        beatmap.drain, 
                        beatmap.bpm, 
                        jump_analysis.overall_confidence, 
                        stream_analysis.overall_confidence])
        recommendations.append((np.dot(vec, w)[0], beatmap.id))

# sort the recommendations by the resulting score
reccs_sorted = sorted(recommendations, key=lambda x: x[0], reverse=True)
# print the top 10 recommendations
print(reccs_sorted[:10])
