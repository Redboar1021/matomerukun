import json

with open("firebase_key.json", "r") as f:
    key = json.load(f)

# TOML形式用に1行のエスケープ文字列を作成
escaped = json.dumps(key)

print(escaped)
