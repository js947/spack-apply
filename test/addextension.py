import sys, yaml

try:
    with open(sys.argv[1], "r") as f:
        config = yaml.load(f)
except IOError:
    config = {}

print(config)

if 'extensions' not in config:
    config['extensions'] = []

config['extensions'] += [sys.argv[2]]

print(config)

with open(sys.argv[1], "w") as f:
    yaml.dump(config, f)
