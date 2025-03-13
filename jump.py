from collections import deque
from dataclasses import dataclass
from parser import Beatmap, HitObject

# class to store final analysis numbers
@dataclass
class JumpAnalysis:
    overall_confidence: float
    jump_density: float
    bpm_consistency: float

    long_jumps: int
    medium_jumps: int
    short_jumps: int
    max_jump_length: int
    
class JumpAnalyzer:
    beatmap: Beatmap = None

    def __init__(self, beatmap):
        self.beatmap = beatmap
    
    # distance calculation of two hit objects. 
    # returns distance if the object is a slider or a circle, and 0 if not.
    def calculate_distance(self, first: HitObject, second: HitObject):
        x1, y1 = (first.x, first.y) if first.type == 1 or first.type == 2 else (0, 0)
        x2, y2 = (second.x, second.y) if second.type == 1 or second.type == 2 else (0, 0)
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    # calculates the number of consecutive notes that are jumps and bpm variations
    def calculate_consecutive_notes(self, hit_objects: list[HitObject], expected_interval: float):
        consecutive_notes = []
        curr_jump = deque()
        bpm_variations = []
        tolerance = 0.1
        distance_threshold = 120.0

        # sliding window to compare every two consecutive hit objects
        for pair in [hit_objects[i:i+2] for i in range(len(hit_objects)-3)]:
            first, second = pair

            time_diff = second.time - first.time
            distance = self.calculate_distance(first, second)

            # if the time difference is close to the expected interval and the distance is greater than the threshold
            if (abs(time_diff - expected_interval) / expected_interval <= tolerance) and (distance >= distance_threshold):
                # we count that as a consecutive note
                curr_jump.append(time_diff)
                if len(curr_jump) > 1:
                    prev_diff = curr_jump[-2]
                    # and track the bpm variations for consecutive notes
                    bpm_variations.append(abs(time_diff - prev_diff))
            elif curr_jump:
                # if the jump is not consecutive, we add the number of notes to the list
                consecutive_notes.append(len(curr_jump))
                curr_jump.clear()
        if curr_jump:
            # if theres any remaining consecutive notes, we add them to the list
            consecutive_notes.append(len(curr_jump))

        return (consecutive_notes, bpm_variations)

    def analyze(self, bpm):
        hit_objects = self.beatmap.hitobjects

        # calculate the expected interval between jumps
        beat_length = 60.0 / bpm * 1000
        expected_jump_interval = beat_length / 2

        # calculate the number of consecutive notes and bpm variations
        (consecutive_notes, bpm_variations) = self.calculate_consecutive_notes(hit_objects, expected_jump_interval)

        # split the consecutive notes into short, medium, and long jumps
        short_jumps_amount = len([jump for jump in consecutive_notes if jump >= 4 and jump < 7])
        medium_jumps_amount = len([jump for jump in consecutive_notes if jump >= 7 and jump < 12])
        long_jumps_amount = len([jump for jump in consecutive_notes if jump >= 12])
        total_jumps_amount = short_jumps_amount + medium_jumps_amount + long_jumps_amount

        # only count jumps that are longer than 2 notes
        jump_lengths = [jump for jump in consecutive_notes if jump >= 2]

        # calculate the total number of jumps and the maximum length of a note jump sequence
        total_jump_notes, max_jump_length = (sum(jump_lengths), max(jump_lengths)) if jump_lengths else (0, 0)

        # calculate the jump density, bpm consistency, average jump length, jump variety, and long jump ratio
        jump_density = total_jump_notes / len(hit_objects)
        bpm_consistency = (sum(bpm_variations) / len(bpm_variations)) / expected_jump_interval if bpm_variations else 0
        average_jump_length = total_jump_notes / total_jumps_amount if total_jumps_amount > 0 else 0
        jump_variety = medium_jumps_amount * 2 + long_jumps_amount * 3 / max(total_jumps_amount, 1)
        long_jump_ratio = long_jumps_amount / max(total_jumps_amount, 1)

        # confidence is a weighted sum of the jump density, bpm consistency, jump variety, long jump ratio, and average jump length
        confidence = min(1, jump_density * 0.4 
                        + bpm_consistency * 0.2 
                        + jump_variety * 0.35
                        + long_jump_ratio * 0.45
                        + min(average_jump_length / 3.0, 1) * 0.3)
        
        return JumpAnalysis(
            overall_confidence=confidence,
            jump_density=jump_density,
            bpm_consistency=bpm_consistency,
            long_jumps=long_jumps_amount,
            medium_jumps=medium_jumps_amount,
            short_jumps=short_jumps_amount,
            max_jump_length=max_jump_length
        )
