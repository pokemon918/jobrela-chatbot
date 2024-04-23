def format_result_as_string(result):
    formatted_result = ""
    for key, value in result.items():
        if value is not None and value != "" and value != []:
            if isinstance(value, list):
                value = ", ".join(value)
            formatted_result += f"{key}: {value}, "
    return formatted_result.rstrip(", ")

