from dataclasses import dataclass

@dataclass
class StreamAnalysis:
    overall_confidence: float
    stream_density: float
    bpm_consistency: float

    short_streams: int
    medium_streams: int
    long_streams: int
    max_stream_length: int

class StreamAnalyzer:
    beatmap = None

    def __init__(self, beatmap):
        self.beatmap = beatmap
    
    # calculates the number of consecutive notes that are in a stream sequence and bpm variations
    def calculate_consecutive_notes(self, hit_objects, expected_interval):
        consecutive_notes = []
        curr_stream = []
        bpm_variations = []
        tolerance = 0.1

        # sliding window to compare every two consecutive hit objects
        for pair in [hit_objects[i:i+2] for i in range(len(hit_objects)-3)]:
            first, second = pair

            time_diff = second.time - first.time

            # we only care about whether the time difference is close to the expected interval
            if (abs(time_diff - expected_interval) / expected_interval <= tolerance):
                # if it is, we count it as part of the current stream
                curr_stream.append(time_diff)
                if len(curr_stream) > 1:
                    prev_diff = curr_stream[-2]
                    # and track the bpm variations for consecutive notes
                    bpm_variations.append(abs(time_diff - prev_diff))
            elif curr_stream:
                # if the note is not consecutive, we add the number of notes in tracked stream to the list
                consecutive_notes.append(len(curr_stream))
                curr_stream.clear()
        if curr_stream:
            # if theres any remaining consecutive notes, we add them to the list
            consecutive_notes.append(len(curr_stream))

        return (consecutive_notes, bpm_variations)
    
    def analyze(self, bpm):
        hit_objects = self.beatmap.hitobjects

        # calculate the expected interval between notes
        beat_length = 60.0 / bpm * 1000
        expected_stream_interval = beat_length / 4

        # calculate the number of streams of different lengths
        (consecutive_notes, bpm_variations) = self.calculate_consecutive_notes(hit_objects, expected_stream_interval)

        # split the consecutive notes into short, medium, and long streams
        short_streams_amount = len([stream for stream in consecutive_notes if stream >= 6 and stream < 10])
        medium_streams_amount = len([stream for stream in consecutive_notes if stream >= 10 and stream < 20])
        long_streams_amount = len([stream for stream in consecutive_notes if stream >= 20])
        total_streams_amount = short_streams_amount + medium_streams_amount + long_streams_amount

        # only count streams that are longer than 6 notes, otherwise they'd be bursts
        streams_lengths = [stream for stream in consecutive_notes if stream >= 6]

        # calculate the total number of notes in streams and the maximum length of a note stream sequence
        total_stream_notes, max_stream_length = (sum(streams_lengths), max(streams_lengths)) if streams_lengths else (0, 0)

        # calculate the stream density, bpm consistency, average stream length, stream variety, and long stream
        stream_density = total_stream_notes / len(hit_objects)
        bpm_consistency = (sum(bpm_variations) / len(bpm_variations)) / expected_stream_interval if bpm_variations else 0
        average_stream_length = total_stream_notes / total_streams_amount if total_streams_amount > 0 else 0
        stream_variety = medium_streams_amount * 2 + long_streams_amount * 3 / max(total_streams_amount, 1)
        long_stream_ratio = long_streams_amount / max(total_streams_amount, 1)

        # confidence is a weighted sum of the stream density, bpm consistency, stream variety, long stream ratio, and average stream length
        confidence = min(1, stream_density * 0.3
                        + bpm_consistency * 0.2
                        + stream_variety * 0.2
                        + long_stream_ratio * 0.2
                        + min(average_stream_length / 5.0, 1) * 0.2)

        return StreamAnalysis(
            overall_confidence=confidence,
            stream_density=stream_density,
            bpm_consistency=bpm_consistency,
            short_streams=short_streams_amount,
            medium_streams=medium_streams_amount,
            long_streams=long_streams_amount,
            max_stream_length=max_stream_length
        )
    