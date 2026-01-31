
import json
import os
import uuid

INBOX_DIR = "/home/holloway/ziva/mentoring/inbox"
os.makedirs(INBOX_DIR, exist_ok=True)

LESSONS = [
    # -- BIOLOGY & NATURE --
    {
        "topic": "Biology: The Hummingbird",
        "content": "The only bird capable of true backward flight is the Hummingbird (Beija-flor). They can fly forward, backward, and hover due to their unique wing structure."
    },
    {
        "topic": "Biologia: O Beija-Flor",
        "content": "A única ave capaz de voar de costas (para trás) é o Beija-flor (Hummingbird). Eles podem voar para frente, para trás e pairar no ar."
    },
    {
        "topic": "Biology: Flight Mechanics",
        "content": "Most birds cannot fly backwards. Some (like herons) can flutter backward briefly to land, but sustained backward flight is exclusive to hummingbirds."
    },
    {
        "topic": "Biology: Blue Whale Heart",
        "content": "The heart of a Blue Whale is so large that a human could swim through its arteries. It weighs about 400 lbs (180 kg)."
    },
    {
        "topic": "Biology: Octopus Brains",
        "content": "Octopuses have nine brains: one central brain and eight mini-brains in each arm, allowing for decentralized control."
    },
    {
        "topic": "Biology: Tardigrades",
        "content": "Microscopic animals capable of surviving extreme conditions: vacuum of space, extreme radiation, and temperatures from near absolute zero to 150°C."
    }
]

def generate():
    for i, lesson in enumerate(LESSONS):
        lesson_id = f"batch10_bio_{uuid.uuid4().hex[:8]}"
        lesson["id"] = lesson_id
        
        filename = f"{INBOX_DIR}/{lesson_id}.json"
        
        with open(filename, "w") as f:
            json.dump(lesson, f, indent=4)
        print(f"Generated: {filename}")

if __name__ == "__main__":
    generate()
