import yaml
import json
import time
import os
import requests
from datetime import datetime
import re
import random
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.WARNING, force=True)  # Enable WARNING logs to console

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_scoring_rules(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_starters(conversation_files):
    import re
    starters = []
    for file_path in conversation_files:
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} does not exist.")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            valid_lines = []
            for raw in f:
                l = raw.strip()
                # Skip empty lines and 'Chat' labels
                if not l or l.startswith("Chat"):
                    continue
                # Remove common speaker or system prefixes
                l = re.sub(r'^(User|Bot|He|She|Assistant|System|AI|Human|Speaker|Agent|Customer|Client|Support|Q|A|Question|Answer|Prompt|Response|Input|Output|Message|Chatbot|Robot|Guide|Responder|Interviewer|Interviewee|Participant|Moderator|Narrator|Voice|Person|Listener|Talker|Rep|Counselor|Therapist|Doctor|Nurse|Teacher|Student|Friend|Colleague|Peer|Guest|Host|Admin|Operator|Staff|Manager|Leader|Director|Chief|Officer|Official|Representative):\s*', '', l, flags=re.IGNORECASE)
                if l:
                    valid_lines.append(l)
            if valid_lines:
                starters.append(random.choice(valid_lines))
    if not starters:
        return ["Hello!"]
    return starters

def score_response(response, partner_message, rules):
    score = 5
    word_count = len(response.split())
    if word_count < rules["length"]["min_words"]:
        score += rules["length"].get("too_short_penalty", -2)
    elif word_count > rules["length"]["max_words"]:
        score += rules["length"].get("too_long_penalty", -1)
    words = response.lower().split()
    if len(set(words)) < len(words) * rules["repetition"]["max_repeat_ratio"]:
        score += rules["repetition"].get("repeat_penalty", -1)
    contractions = rules["conversational_markers"]["contractions"]
    found = any(c.lower() in response.lower() for c in contractions)
    if found:
        score += rules["conversational_markers"].get("contraction_reward", 1)
    if '?' in response:
        score += rules["question"].get("reward", 1)
    if partner_message:
        partner_keywords = set(partner_message.lower().split())
        overlap = partner_keywords.intersection(set(words))
        if overlap:
            score += rules["on_topic"].get("keyword_overlap_reward", 1)
        else:
            score += rules["on_topic"].get("no_overlap_penalty", -1)
    if partner_message and response.strip().lower() == partner_message.strip().lower():
        score += rules["originality"].get("copy_penalty", -2)
    # Typo reward
    typo_rules = rules.get("typos", {})
    common_typos = typo_rules.get("common_typos", [])
    typo_count = sum(response.lower().count(t.lower()) for t in common_typos)
    min_t = typo_rules.get("min_typos", 0)
    max_t = typo_rules.get("max_typos", float('inf'))
    reward_per = typo_rules.get("reward_per_typo", 0)
    max_reward = typo_rules.get("max_reward", 0)
    if typo_count >= min_t:
        score += min(typo_count * reward_per, max_reward)

    # Hedging
    hedge_rules = rules.get("hedging", {})
    hedges = hedge_rules.get("phrases", [])
    hedge_count = sum(response.lower().count(h.lower()) for h in hedges)
    hedge_count = min(hedge_count, hedge_rules.get("max_count", hedge_count))
    score += hedge_count * hedge_rules.get("reward_per", 0)

    # Back-channel
    back_rules = rules.get("back_channel", {})
    bc_phrases = back_rules.get("phrases", [])
    bc_count = sum(response.lower().count(b.lower()) for b in bc_phrases)
    score += min(bc_count * back_rules.get("reward_per", 0), back_rules.get("max_reward", 0))

    # Punctuation variety
    pv_rules = rules.get("punctuation_variety", {})
    puncts = pv_rules.get("punctuations", [])
    used_puncts = set(p for p in puncts if p in response)
    if len(used_puncts) >= pv_rules.get("min_variety", 0):
        score += pv_rules.get("reward", 0)

    # Emojis (per-item rewards, capped by max_reward)
    emoji_rules = rules.get("emojis", {})
    if emoji_rules:
        total_emoji_score = 0
        for item in emoji_rules.get("items", []):
            count = response.count(item.get("emoji", ""))
            total_emoji_score += count * item.get("reward", 0)
        score += min(total_emoji_score, emoji_rules.get("max_reward", float('inf')))

    # Sentence length diversity
    sld_rules = rules.get("sentence_length_diversity", {})
    sentences = re.split(r'[.!?]+', response)
    lengths = [len(s.split()) for s in sentences if s.strip()]
    if len(lengths) > 1:
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std = variance ** 0.5
        if std >= sld_rules.get("min_std", float('inf')):
            score += sld_rules.get("reward", 0)

    # Personal pronouns
    pp_rules = rules.get("personal_pronouns", {})
    pp_words = pp_rules.get("words", [])
    pp_count = sum(response.lower().split().count(w.lower()) for w in pp_words)
    score += min(pp_count * pp_rules.get("reward_per", 0), pp_rules.get("max_reward", 0))

    # Contextual callbacks
    cc_rules = rules.get("contextual_callbacks", {})
    cc_phrases = cc_rules.get("phrases", [])
    cc_count = sum(response.lower().count(p.lower()) for p in cc_phrases)
    score += min(cc_count * cc_rules.get("reward_per", 0), cc_rules.get("max_reward", 0))

    # Empathetic markers
    em_rules = rules.get("empathetic_markers", {})
    em_count = sum(response.lower().count(p.lower()) for p in em_rules.get("phrases", []))
    score += min(em_count * em_rules.get("reward_per", 0), em_rules.get("max_reward", 0))

    # Follow-up depth (additional questions)
    fu_rules = rules.get("follow_up_questions", {})
    q_total = response.count("?")
    fu_count = max(0, q_total - 1)
    score += min(fu_count * fu_rules.get("reward_per", 0), fu_rules.get("max_reward", 0))

    # Filler-words penalty
    fw_rules = rules.get("filler_words", {})
    fw_words = fw_rules.get("words", [])
    resp_words = response.lower().split()
    fw_count = sum(resp_words.count(w.lower()) for w in fw_words)
    score += max(fw_rules.get("max_penalty", 0), fw_count * fw_rules.get("penalty_per", 0))

    # Lexical richness
    lr_rules = rules.get("lexical_richness", {})
    tokens = response.lower().split()
    if tokens and lr_rules:
        ratio = len(set(tokens)) / len(tokens)
        if ratio >= lr_rules.get("min_ratio", 1.0):
            score += lr_rules.get("reward", 0)

    # Readability hybrid: reward-only within sweet spot, skip on story markers
    read_rules = rules.get("readability", {})
    if read_rules:
        lower_resp = response.lower()
        story_markers = read_rules.get("story_markers", [])
        if not any(marker in lower_resp for marker in story_markers):
            sentences = re.split(r'[.!?]+', response)
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if lengths:
                avg_len = sum(lengths) / len(lengths)
                if read_rules.get("min_len", 0) <= avg_len <= read_rules.get("max_len", float('inf')):
                    score += read_rules.get("reward", 0)

    return score

def mutate_prompt(prompt, url, model, system_msg):
    # The system message for the mutation LLM is ONLY the mutation instructions
    mutation_instructions = (
        "You are a precise text mutation machine. Your task is to perform *exact and limited* modifications to the text provided between <INPUT> and </INPUT> tags.\n"
        "FOLLOW THESE THREE SPECIFIC MUTATION RULES PRECISELY:\n"
        "1.  **Reorder Sentences:** Arrange *all* of the original sentences in a different sequence. Every single original sentence must be present in your output, used exactly once.\n"
        "2.  **Replace One Synonym:** Find *exactly one* word in the entire text and replace it with a single, safe, and contextually appropriate synonym.\n"
        "3.  **Tweak Punctuation/Spacing:** Make *one minor adjustment* to punctuation or spacing somewhere in the text (e.g., alter a comma, period, or single space). Only one such change.\n"
        "\n" # Add a line break for visual separation
        "***CRITICAL CONSTRAINTS - DO NOT VIOLATE:***\n" # Make this stand out
        "**DO NOT** remove, add, shorten, paraphrase, summarize, or omit *ANY* part of the original text's content or sentences. All original sentences must be included, only their order is changed.\n"
        "Your output must contain the *same words* as the input, with the *only exceptions* being the one word replaced by a synonym and any minor punctuation/spacing change.\n" # Explicitly state same words except for the changes
        "The meaning of the original text must be preserved as much as possible.\n"
        "\n" # Add a line break
        "Return *ONLY* the mutated text. Absolutely no other text, explanation, or conversation. The output MUST be enclosed strictly between <OUTPUT> and </OUTPUT> tags.\n"
        "Input text is below."
    )
    full_system_msg = mutation_instructions
    user_msg = f"Mutate this: {prompt}"
    response = call_model(url, model, full_system_msg, [user_msg])
    import re
    match = re.search(r"<OUTPUT>(.*?)</OUTPUT>", response, re.S)
    mutation = match.group(1).strip() if match else response.strip()
    # Compute mutation label via diff
    matcher = SequenceMatcher(None, prompt, mutation)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            orig = prompt[i1:i2]
            new = mutation[j1:j2]
            changes.append(f"{tag}:{orig}->{new}")
    label = ";".join(changes)
    return mutation, label

def call_model(url, model, system_msg, dialog, timeout=3):
    logging.info(f"call_model start: url={url}, model={model}, dialog_len={len(dialog)}")
    messages = [{"role": "system", "content": system_msg}]
    for i, m in enumerate(dialog):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": m})
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        resp = requests.post(f"{url}/api/chat", json=payload, timeout=timeout)
        logging.info(f"call_model response status: {resp.status_code}")
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "").strip()
        logging.info(f"call_model content: {content[:200]}")
        return content if content else "(no response)"
    except Exception as e:
        logging.error(f"call_model error: {e}")
        return "(no response)"

def format_duration(sec):
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

def main():
    print(f"Starting RL training: epochs={load_config().get('epochs')}, conversations_per_epoch={load_config().get('conversations_per_epoch')}, num_dialog_turns={load_config().get('num_dialog_turns')}")
    config = load_config()
    logging.info(f"Configuration loaded: epochs={config.get('epochs')}, conversation_per_epoch={config.get('conversations_per_epoch')}, num_dialog_turns={config.get('num_dialog_turns')}")
    rules = load_scoring_rules(config["scoring_rules"])
    starters = extract_starters(config["conversation_files"])
    logging.info(f"Extracted {len(starters)} starters from conversation files")
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    population_size = config.get("conversations_per_epoch", 10)
    epochs = config.get("epochs", 100)
    turns = config.get("num_dialog_turns", 10)

    # Lineage tracking for visualization
    lineage = []
    # Losers tracking to avoid regression
    losers = []
    # Archive of evaluated system messages to avoid re-evaluation (persisted)
    evaluated_archive_path = os.path.join(logs_dir, "evaluated_archive.json")
    # Clear previous archive for a fresh start
    if os.path.exists(evaluated_archive_path):
        os.remove(evaluated_archive_path)
    evaluated_messages_archive = {}

    final_winners = []

    # Initial population: original message + 9 mutants
    best_msg = config["trainee"]["system_message"]
    population = []
    population.append({"id": "E1_C1", "msg": best_msg, "history": [], "parent": None})
    
    # Ensure mutated messages aren’t duplicates and haven’t lost already been tried (via losers list)
    for i in range(2, population_size+1):
        m, label = mutate_prompt(
            best_msg,
            config["trainee"]["url"],
            config["trainee"]["model"],
            config["trainee"]["system_message"]
        )
        if all(m != c["msg"] for c in population) and all(m != loser["msg"] for loser in losers):
            population.append({"id": f"E1_C{i}", "msg": m, "history": [label], "parent": "E1_C1"})
    lineage.append(list(population))

    # Evolutionary loop
    for epoch in range(1, epochs+1):
        # prepare epoch log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        epoch_log_path = os.path.join(logs_dir, f"{timestamp}_epoch{epoch}.txt")
        log_file = open(epoch_log_path, "w", encoding="utf-8")
        log_file.write(f"--- Epoch {epoch}/{epochs} ---\n\n")
        epoch_start = time.time()
        # Epoch output suppressed
        logging.info(f"--- Epoch {epoch}/{epochs} ---")
        candidate_scores = []
        conv_time_sum = 0
        # Evaluate each candidate
        for idx, cand in enumerate(population, start=1):
            # start per-conversation timer
            conv_start = time.time()
            cid = cand["id"]
            # log candidate header
            log_file.write(f"Candidate {cid}\n")
            log_file.write(f"History: {cand['history']}\n")
            # Check if this system message was evaluated before
            if cand["msg"] in evaluated_messages_archive:
                avg_score = evaluated_messages_archive[cand["msg"]]
                logging.info(f"[{cid}] Retrieved Avg Score from archive: {avg_score:.2f}")
                log_file.write(f"[{cid}] Retrieved Avg Score from archive: {avg_score:.2f}\n\n")
                # Ensure archived candidates show up in console too
                print(f"[{cid}] Retrieved Avg Score from archive: {avg_score:.2f}")
                candidate_scores.append((cand, avg_score))
                continue
            cid = cand["id"]
            msg = cand["msg"]
            hist = cand["history"]
            total_score = 0
            dialog = []
            # Single conversation of 'turns' exchanges
            starter = random.choice(starters)
            # Clearly announce seed for this conversation
            print()  # blank line for separation
            print(f"====== Conversation {cid} Seed ======")
            print(starter)
            print("================================")
            log_file.write(f"[{cid}] Seed line: {starter}\n")
            dialog.append(starter)
            logging.info(f"[{cid}] Starter: {starter}")
            log_file.write(f"[{cid}] Starter: {starter}\n")
            for t in range(turns):
                if t % 2 == 0:
                    # Trainee call with error handling
                    try:
                        resp = call_model(config["trainee"]["url"], config["trainee"]["model"], msg, dialog, timeout=10)
                    except Exception as e:
                        logging.error(f"[{cid}] Trainee call error: {e}")
                        log_file.write(f"[{cid}] Trainee call error: {e}\n")
                        resp = ""
                    dialog.append(resp)
                    score = score_response(resp, dialog[-2], rules)
                    total_score += score
                    print(f"[{cid}] Trainee: {resp} (Score: {score:.2f})")
                    logging.info(f"[{cid}] Trainee: {resp} (Score: {score:.2f})")
                    log_file.write(f"[{cid}] Trainee: {resp} (Score: {score:.2f})\n")
                else:
                    # Partner call with error handling
                    try:
                        presp = call_model(config["partner"]["url"], config["partner"]["model"], config["partner"]["system_message"], [dialog[-1]], timeout=10)
                    except Exception as e:
                        logging.error(f"[{cid}] Partner call error: {e}")
                        log_file.write(f"[{cid}] Partner call error: {e}\n")
                        presp = ""
                    dialog.append(presp)
                    print(f"[{cid}] Partner: {presp}")
                    logging.info(f"[{cid}] Partner: {presp}")
                    log_file.write(f"[{cid}] Partner: {presp}\n")
            avg_score = total_score / (turns//2)
            # Store the evaluated score in archive
            evaluated_messages_archive[msg] = avg_score
            logging.info(f"[{cid}] Avg Score: {avg_score:.2f}")
            log_file.write(f"[{cid}] Avg Score: {avg_score:.2f}\n")
            logging.info(f"[{cid}] Conversation Duration: {format_duration(time.time()-conv_start)}")
            log_file.write(f"[{cid}] Conversation Duration: {format_duration(time.time()-conv_start)}\n\n")
            print(f"[{cid}] Avg Score: {avg_score:.2f}")
            print(f"[{cid}] Conversation Duration: {format_duration(time.time()-conv_start)}")
            # end per-conversation timer
            conv_end = time.time()
            conv_duration = format_duration(conv_end - conv_start)
            # Update ETA calculations
            conv_time_sum += conv_end - conv_start
            convs_done = idx
            remaining_convs = population_size - convs_done
            avg_conv_time = conv_time_sum / convs_done
            epoch_eta_secs = avg_conv_time * remaining_convs
            remaining_epochs = epochs - epoch
            test_eta_secs = avg_conv_time * (remaining_convs + remaining_epochs * population_size)
            eta_epoch = format_duration(epoch_eta_secs)
            eta_test = format_duration(test_eta_secs)
            print(f"[{cid}] ETA for epoch: {eta_epoch}, ETA for test: {eta_test}")
            log_file.write(f"[{cid}] ETA epoch: {eta_epoch}, ETA test: {eta_test}\n\n")
            candidate_scores.append((cand, avg_score))

        # Select winner
        winner, win_score = max(candidate_scores, key=lambda x: x[1])
        # Record losing candidates for regression guard
        for cand, score in candidate_scores:
            if cand["id"] != winner["id"]:
                losers.append({
                    "epoch": epoch,
                    "id": cand["id"],
                    "msg": cand["msg"],
                    "history": cand["history"],
                    "parent": cand["parent"],
                    "last_mutation": cand["history"][-1] if cand["history"] else None,
                    "score": score
                })
        logging.info(f"-> Epoch {epoch} Winner: {winner['id']} Score: {win_score:.2f}")
        log_file.write(f"-> Epoch {epoch} Winner: {winner['id']} Score: {win_score:.2f}\n\n")
        print(f"-> Epoch {epoch} Winner: {winner['id']} Score: {win_score:.2f}")
        log_file.close()
        logging.info(f"Epoch {epoch} log saved to {epoch_log_path}")

        final_winners.append({
            "score": win_score,
            "mutation": winner["msg"]
        })

        # Persist artifacts after each epoch
        lineage_path = os.path.join(logs_dir, "lineage.json")
        with open(lineage_path, "w", encoding="utf-8") as lf:
            json.dump(lineage, lf, indent=2)
        logging.info(f"Lineage saved to {lineage_path}")
        losers_path = os.path.join(logs_dir, "losers.json")
        with open(losers_path, "w", encoding="utf-8") as lf2:
            json.dump(losers, lf2, indent=2)
        logging.info(f"Losers saved to {losers_path}")
        with open(evaluated_archive_path, "w", encoding="utf-8") as f:
            json.dump(evaluated_messages_archive, f, indent=2)
        logging.info(f"Evaluated archive saved to {evaluated_archive_path}")
        # Generate Graphviz DOT for current lineage
        dot_lines = ["digraph Evolution {", "  rankdir=TB;", "  node [shape=circle];"]
        for ep_idx, epoch_pop in enumerate(lineage, start=1):
            ids = [c["id"] for c in epoch_pop]
            dot_lines.append("  { rank=same; " + "; ".join(ids) + " };")
        for epoch_pop in lineage[1:]:
            for c in epoch_pop:
                if c["parent"]:
                    label = c["history"][-1].replace('"','\\"') if c["history"] else ""
                    dot_lines.append(f'  {c["parent"]} -> {c["id"]} [label="{label}",fontsize=10];')
        dot_lines.append("}")
        dot_path = os.path.join(logs_dir, "lineage.dot")
        with open(dot_path, "w", encoding="utf-8") as df:
            df.write("\n".join(dot_lines))
        logging.info(f"DOT written to {dot_path}")

        # Prepare next generation
        best_msg = winner["msg"]
        winner_hist = winner["history"]
        new_population = []
        # Winner carries forward
        new_population.append({"id": f"E{epoch+1}_C1", "msg": best_msg, "history": list(winner_hist), "parent": winner["id"]})
        
        for i in range(2, population_size+1):
            m, label = mutate_prompt(
                best_msg,
                config["trainee"]["url"],
                config["trainee"]["model"],
                config["trainee"]["system_message"]
            )
            if all(m != c["msg"] for c in new_population) and all(m != loser["msg"] for loser in losers):
                new_hist = winner_hist + [label]
                new_population.append({"id": f"E{epoch+1}_C{i}", "msg": m, "history": new_hist, "parent": f"E{epoch+1}_C1"})
        population = new_population
        lineage.append(list(population))

        epoch_end = time.time()
        # Epoch duration output suppressed
        logging.info(f"Epoch {epoch} Duration: {format_duration(epoch_end-epoch_start)}")
        # Visual separation between epochs
        print("\n" * 5, flush=True)

    if final_winners:
        best = max(final_winners, key=lambda x: x["score"])
        print("\n=== FINAL WINNING MUTATION ===")
        print("Copy the following and paste it into your config.yaml under trainee.system_message:\n")
        print(best["mutation"])
        print("\n==============================\n")
    else:
        print("No winners recorded.")

    logging.info(f"\nBest system message: {best_msg}")

if __name__ == "__main__":
    main()
