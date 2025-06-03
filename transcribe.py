import os, time, requests
from typing import Optional, Tuple, List, Dict
import json
import datetime

ASSEMBLYAI_API_KEY =  "99f9b50b0d284376be230b63eb720e0c"
BASE_URL            = "https://api.assemblyai.com"
HEADERS             = {"authorization": ASSEMBLYAI_API_KEY}

def transcribe(
    *,
    file_path: Optional[str] = None,
    file_url: Optional[str] = None,
    speech_model: str = "slam-1",
    speaker_labels: bool = True,
    poll_interval: int = 3,
) -> Tuple[str, List[Dict]]:
    """
    Uploads (if needed), kicks off transcription, polls until complete,
    and returns (full_text, utterances).
    """

    if not (file_path or file_url):
        raise ValueError("Provide either file_path or file_url.")

    # 1️⃣  Make sure we have a URL for the audio
    if file_path:
        with open(file_path, "rb") as f:
            up = requests.post(f"{BASE_URL}/v2/upload", headers=HEADERS, data=f)
        up.raise_for_status()
        audio_url = up.json()["upload_url"]
    else:
        audio_url = file_url

    # 2️⃣  Start the transcription job
    job = requests.post(
        f"{BASE_URL}/v2/transcript",
        headers=HEADERS,
        json={
            "audio_url":     audio_url,
            "speech_model":  speech_model,
            "speaker_labels": speaker_labels,
        },
    )
    job.raise_for_status()
    transcript_id = job.json()["id"]

    # 3️⃣  Poll for completion
    poll_endpoint = f"{BASE_URL}/v2/transcript/{transcript_id}"
    while True:
        result = requests.get(poll_endpoint, headers=HEADERS).json()

        if result["status"] == "completed":
            return result["text"], result.get("utterances", [])

        if result["status"] == "error":
            raise RuntimeError(f"Transcription failed: {result['error']}")

        time.sleep(poll_interval)



def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.sss format"""
    return str(datetime.timedelta(seconds=round(seconds, 3)))

if __name__ == "__main__":
    text, utter = transcribe(file_path="debate.mp3")

    print("\nFull transcript:\n")
    print(text)

    print("\nSpeaker breakdown:\n")

    # Create formatted JSON output
    output = {"utterances": []}
    for u in utter:
        formatted = {
            "speaker": f"Speaker {u['speaker']}",
            "start_time": format_timestamp(u['start'] / 1000),  # ms → sec
            "text": u['text'].strip()
        }
        output["utterances"].append(formatted)
        print(f"{formatted['speaker']} ({formatted['start_time']}): {formatted['text']}")

    # Save to JSON file
    with open("formatted_transcript.json", "w") as f:
        json.dump(output, f, indent=4)

    print("\nFormatted transcript saved to 'formatted_transcript.json'")

