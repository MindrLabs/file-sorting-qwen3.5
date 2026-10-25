import json
rows = json.load(open('results.json'))
print(rows['tokens_per_sec'])
