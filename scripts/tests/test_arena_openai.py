#!/usr/bin/env python3
import sys
import time
import uuid
import json
import requests

BASE = 'http://localhost:8000'

def post(path, payload):
    url = f"{BASE}{path}"
    r = requests.post(url, json=payload, timeout=60)
    try:
        data = r.json()
    except Exception:
        print(f"HTTP {r.status_code} raw: {r.text[:300]}")
        raise
    return r.status_code, data

def has_openai_404(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return 'Model gpt-4o returned status 404' in text or 'Error: Model gpt-4o returned status 404' in text

def main():
    sid = str(uuid.uuid4())
    message = 'What is urban microstratification?'
    # Start battle (pre-generates responses for all models)
    code, data = post('/api/arena/start_battle', {
        'message': message,
        'session_id': sid
    })
    if code != 200 or 'battle_id' not in data:
        print('FAIL: start_battle did not return battle_id', code, data)
        return 1

    battle_id = data['battle_id']
    print(f"Battle started: {battle_id}")

    # Initial responses may be present
    for k in ('response_a', 'response_b'):
        if k in data and has_openai_404(data.get(k, '')):
            print('FAIL: Initial response contained OpenAI 404')
            return 1

    # Vote through until we see gpt-4o in model_a or model_b
    # Tournament of 4 models => up to 3 rounds
    for round_idx in range(1, 4):
        code, vote_resp = post('/api/arena/vote', {
            'battle_id': battle_id,
            'vote': 'a'
        })
        if code != 200:
            print('FAIL: vote returned non-200', code, vote_resp)
            return 1
        if not vote_resp.get('continue_battle', False):
            # Tournament complete early
            print('Tournament complete earlier than expected:', vote_resp)
            break

        model_a = vote_resp.get('model_a')
        model_b = vote_resp.get('model_b')
        ra = vote_resp.get('response_a', '')
        rb = vote_resp.get('response_b', '')
        print(f"Round {vote_resp.get('round')} matchup: {model_a} vs {model_b}")

        # If OpenAI is present, verify not 404
        if model_a == 'gpt-4o' and has_openai_404(ra):
            print('FAIL: gpt-4o response_a returned 404')
            return 1
        if model_b == 'gpt-4o' and has_openai_404(rb):
            print('FAIL: gpt-4o response_b returned 404')
            return 1

    print('PASS: Arena OpenAI round returned valid response (no 404).')
    return 0

if __name__ == '__main__':
    sys.exit(main())
