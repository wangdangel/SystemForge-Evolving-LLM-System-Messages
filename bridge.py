import sys
# Force UTF-8 encoding for all stdio to handle emojis
sys.stdin.reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import subprocess
import yaml
import random
import time
import threading
import queue

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


def load_starters(paths):
    starters = []
    for p in paths:
        with open(p, 'r', encoding='utf-8') as f:
            starters.extend([line.strip() for line in f if line.strip()])
    return starters


def main():
    config = load_config()
    # optional turns arg
    num_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    starters = load_starters(config['conversation_files'])
    initial_msg = random.choice(starters)
    # sanitize initial_msg to ASCII on Windows console
    init_safe = initial_msg.encode(sys.stdout.encoding, 'replace').decode(sys.stdout.encoding)
    print(f'Initial: {init_safe}', flush=True)

    # launch trainee and partner agents
    trainee_proc = subprocess.Popen([
        sys.executable, 'trainee_agent.py'
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    partner_proc = subprocess.Popen([
        sys.executable, 'partner_agent.py'
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    # ensure agents are terminated when done
    try:
        # thread worker to read lines
        q = queue.Queue()
        def read_worker(proc, role):
            while True:
                line = proc.stdout.readline()
                if line:
                    q.put((role, line.strip()))
                elif proc.poll() is not None:
                    q.put((role, None))
                    break
        threading.Thread(target=read_worker, args=(trainee_proc, 'trainee'), daemon=True).start()
        threading.Thread(target=read_worker, args=(partner_proc, 'partner'), daemon=True).start()

        # helper to get a message for a specific role
        def get_message(expected_role, timeout=10):
            end = time.time() + timeout
            while True:
                remaining = end - time.time()
                if remaining <= 0:
                    return (expected_role, None)
                try:
                    role, msg = q.get(timeout=remaining)
                except queue.Empty:
                    return (expected_role, None)
                if role == expected_role:
                    return (role, msg)
                # ignore other roles
                continue

        # send initial to trainee and await response
        trainee_proc.stdin.write(initial_msg + '\n')
        trainee_proc.stdin.flush()
        role, msg = get_message('trainee', timeout=10)
        if msg is None:
            print('Trainee did not respond.', flush=True)
            return
        tr_safe = msg.encode(sys.stdout.encoding, 'replace').decode(sys.stdout.encoding)
        print(f'Trainee: {tr_safe}', flush=True)

        for i in range(num_turns):
            # partner turn
            partner_proc.stdin.write(msg + '\n')
            partner_proc.stdin.flush()
            role, partner_resp = get_message('partner', timeout=10)
            if partner_resp is None:
                print('Partner did not respond.', flush=True)
                break
            pr_safe = partner_resp.encode(sys.stdout.encoding, 'replace').decode(sys.stdout.encoding)
            print(f'Partner: {pr_safe}', flush=True)

            # trainee turn
            trainee_proc.stdin.write(partner_resp + '\n')
            trainee_proc.stdin.flush()
            role, msg = get_message('trainee', timeout=10)
            if msg is None:
                print('Trainee did not respond.', flush=True)
                break
            tr_safe2 = msg.encode(sys.stdout.encoding, 'replace').decode(sys.stdout.encoding)
            print(f'Trainee: {tr_safe2}', flush=True)
    finally:
        trainee_proc.terminate()
        partner_proc.terminate()


if __name__ == '__main__':
    main()
