import json

with open('project.json', 'r', encoding='utf-8') as reader:
        projects = json.load(reader)

print(len(projects))