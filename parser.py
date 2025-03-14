from dataclasses import dataclass
import requests
import io

@dataclass
class HitObject:
    x: int
    y: int
    time: int
    type: int
    hitsound: int
    extras: int = None
    slidertype: int = None

@dataclass
class Beatmap:
    metadata: dict
    difficulty: dict
    timingpoints: list[dict]
    hitobjects: list[HitObject]

# Function to parse beatmap from file
def parse_beatmap(beatmapid: str):
    url = f"https://osu.ppy.sh/osu/{beatmapid}"
    response = requests.get(url)
    r_file = io.StringIO(response.text)
    osu = r_file.readlines()
    out = {}
    sliders = ['C','L','P','B']

    def get_line(phrase):
        for num, line in enumerate(osu, 0):
            if phrase in line:
                return num

    out = Beatmap(
        metadata={},
        difficulty={},
        timingpoints=[],
        hitobjects=[]
    )

    # line numbers of every category
    events_line = get_line('[Events]')
    metadata_line = get_line('[Metadata]')
    difficulty_line = get_line('[Difficulty]')
    events_line = get_line('[Events]')
    timing_line = get_line('[TimingPoints]')
    hit_line = get_line('[HitObjects]')

    if not any([metadata_line, difficulty_line, events_line, timing_line, hit_line]):
        return None

    metadata_list = osu[metadata_line:difficulty_line-1] if metadata_line and difficulty_line else []
    difficulty_list = osu[difficulty_line:events_line-1] if difficulty_line and events_line else []
    timingpoints_list = osu[timing_line:hit_line-1] if timing_line and hit_line else []
    hitobject_list = osu[hit_line:] if hit_line else []

    # filling informationsss
    for item in metadata_list:
        if ':' in item:
            item = item.split(':')
            out.metadata[item[0]] = item[1]

    for item in difficulty_list:
        if ':' in item:
            item = item.split(':')
            out.difficulty[item[0]] = item[1]

    for item in timingpoints_list:
        if ',' in item:
            item = item.split(',')
            point = {
            'offset':item[0],
            'millperbeat':item[1]
            }
            try:
                point['meter'] = item[2]
            except:
                'nothing'
            out.timingpoints.append(point)


    for item in hitobject_list:
        if ',' in item:
            item = item.split(',')
            point = HitObject (
                x = int(item[0]),
                y = int(item[1]),
                time = int(item[2]),
                type = int(item[3]),
                hitsound = item[4]
            )
            if len(item) > 5 and sliders not in item:
                point.extras = item[5]
            try:
                point.slidertype = item[6]
            except:
                'nothing'
            out.hitobjects.append(point)

    return out
