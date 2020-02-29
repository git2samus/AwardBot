#!/usr/bin/env python3
import sys, json

raw = sys.stdin.read()
encoded = json.dumps(raw)

print(encoded)
