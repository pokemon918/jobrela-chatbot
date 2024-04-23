import json


def find_keys(data, keys):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys:
                if key == 'languageIds':
                    yield key, [lang['name'] for lang in value] if isinstance(value, list) else value
                elif key == 'specialities':
                    yield key, [{'name': spec['name'], 'description': spec['description']} for spec in value]
                else:
                    yield key, value
            elif isinstance(value, dict) or isinstance(value, list):
                for result in find_keys(value, keys):
                    yield result
    elif isinstance(data, list):
        for item in data:
            for result in find_keys(item, keys):
                yield result


def format_value(value):
    if isinstance(value, str):
        return f'{value}'
    elif isinstance(value, list):
        return f'[{", ".join(map(str, value))}]'
    elif isinstance(value, dict):
        if '$date' in value:
            return f'{value["$date"]}'  # Handle MongoDB-style dates
        else:
            return json.dumps(value)  # Convert other dictionaries to JSON string
    else:
        return str(value)
