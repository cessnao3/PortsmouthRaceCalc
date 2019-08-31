import yaml

with open('race_input.yaml', 'r') as f:
    data = yaml.safe_load(f)

print(data)
