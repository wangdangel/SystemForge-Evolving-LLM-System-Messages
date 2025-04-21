import logging
logging.getLogger().setLevel(logging.WARNING)
from train_rl import load_config, mutate_prompt
import os
import json

if __name__ == "__main__":
    # Load configuration
    config = load_config()
    prompt = config["trainee"]["system_message"]
    url = config["trainee"]["url"]
    model = config["trainee"]["model"]
    system_msg = config["trainee"]["system_message"]

    # Generate nine distinct prompt variations, skipping duplicates and previous losers
    losers_file = os.path.join("logs", "losers.json")
    if os.path.exists(losers_file):
        with open(losers_file, "r", encoding="utf-8") as lf:
            previous = json.load(lf)
        previous_msgs = {d.get("msg", "") for d in previous}
    else:
        previous_msgs = set()

    # Generate a single prompt variant for testing
    mutated_prompt, _ = mutate_prompt(prompt, url, model, system_msg)
    print(mutated_prompt)
    # End of test script
