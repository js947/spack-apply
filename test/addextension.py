import sys, yaml

try:
    with open(sys.argv[1], "r") as f:
        config = yaml.load(f)
except IOError:
    config = {}

print(config)

if 'config' not in config:
    config['config'] = {}
if 'extensions' not in config['config']:
    config['config']['extensions'] = []
config['config']['extensions'] += [sys.argv[2]]

print(config)

with open(sys.argv[1], "w") as f:
    yaml.dump(config, f)