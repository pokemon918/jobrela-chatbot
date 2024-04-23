import spacy
import re
import json
from spacy.matcher import Matcher
import pattern_data
import requests

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize the matcher with the spaCy vocabulary
matcher = Matcher(nlp.vocab)

def format_result_as_dict(result):
    # Remove empty, null, or None values from the result dictionary
    filtered_result = {key: value for key, value in result.items() if value not in (None, "", [], 0)}
    
    formatted_result = {}
    for key, value in filtered_result.items():
        if isinstance(value, list):
            value = ", ".join(value)
        formatted_result[key] = value
    
    return formatted_result

def capitalize_first_letters(text):
    words = text.split()
    capitalized_words = [word.capitalize() for word in words]
    capitalized_text = ' '.join(capitalized_words)
    
    return capitalized_text

def extract_params_from_query(query, source):
    doc = nlp(query)
    params = []
    for token in doc:
        for i in range(3, 0, -1):  # Check for n-gram matches where n ranges from 3 to 1
            if token.i + i <= len(doc):  # Ensure the index is within bounds
                phrase = ' '.join([t.text.lower() for t in doc[token.i:token.i+i]])
                for item in source:
                    if item.lower() == phrase[:len(item)].lower():
                        if item == "work from home":
                            item = "remote"
                        if item == "mid - level":
                            item = "medior"
                        if item == "beginner":
                            item = "novice"
                        if item.lower().endswith("programmer") or item.lower().endswith("engineer"):
                            new_item = item[:-len("programmer" if item.lower().endswith("programmer") else "engineer")] + "developer"
                            params.append(capitalize_first_letters(new_item))
                        else:
                            params.append(capitalize_first_letters(item))
    params = list(set(params))
    return params


def get_exchange_rates(base_currency='EUR'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    response = requests.get(url)
    data = response.json()
    return data['rates']

def check_budget(amount, currency):
    amount = float(amount)
    
    # Get the latest exchange rates
    exchange_rates = get_exchange_rates()
    
    # Convert amount to EUR equivalent
    if currency != 'EUR':
        amount = amount / exchange_rates[currency]
    
    # Check if amount is less than 1000 EUR
    if amount < 1000:
        return ["freelance", amount]
    else:
        return ["employ", amount]
    

def extract_budget_details(sentence):
    # Define regular expressions for extracting amount, currency, and time period
    amount_regex = r'(\d+(?:\.\d+)?)'
    currency_regex = r'(EUR|USD|CZK)'
    time_period_regex = r'(day|month)'

    # Compile the regular expressions
    amount_pattern = re.compile(amount_regex, re.IGNORECASE)
    currency_pattern = re.compile(currency_regex, re.IGNORECASE)
    time_period_pattern = re.compile(time_period_regex, re.IGNORECASE)

    # Search for matches in the sentence
    amount_match = amount_pattern.search(sentence)
    currency_match = currency_pattern.search(sentence)
    time_period_match = time_period_pattern.search(sentence)

    # Extract the matched groups
    if amount_match:
        amount = amount_match.group(1)
    else:
        amount = None

    if currency_match:
        currency = currency_match.group(1)
    else:
        currency = None

    if time_period_match:
        time_period = time_period_match.group(1)
    else:
        time_period = None

    return amount, currency, time_period


def define_patterns(): 
    # Patterns for language    
    for lang in pattern_data.language_map.keys():
        matcher.add("LANGUAGE", [[{"LOWER": lang}]])
    
    # Patterns for allocation
    matcher.add("ALLOCATION", [pattern_data.allocation_pattern])

# Call define_patterns to add patterns to the matcher
define_patterns()

def extract_job_requirements(query):
    doc = nlp(query)
    results = {
        "categories": extract_params_from_query(query, pattern_data.categories),
        "skillsets": extract_params_from_query(query, pattern_data.skillsets),
        "localities": extract_params_from_query(query, pattern_data.localities),
        "currency": None,
        "levelsExample": extract_params_from_query(query, pattern_data.levels),
        "languageIds": [],
        "employmentProjectType": False,
        "employmentProjectTypeWage": 0,
        "employmentProjectTypeSuperGrossWageCZK": 0,
        "freelanceProjectType": False,
        "freelanceProjectTypeWage": 0,
        "freelanceProjectTypeSuperGrossWageCZK": 0,
        "superGrossWageCZK": 0,
        "allocation": []
    }
    
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        rule_id = nlp.vocab.strings[match_id]
        if rule_id == "JOBCATEGORY":
            results["categories"].append(span.text)
        elif rule_id == "SKILLSET":
            results["skillsets"].append(span.text)
        elif rule_id == "LOCATION":
            results["localities"].append(span.text)
        elif rule_id == "LEVELS":
            results["levelsExample"].append(span.text.upper())
        elif rule_id == "LANGUAGE":
            language = pattern_data.language_map.get(span.text.lower()).upper()
            if language not in results["languageIds"]:
                results["languageIds"].append(language)
        elif rule_id == "ALLOCATION":
            results["allocation"] = span.text

    # Extracting job categories
    for ent in doc.ents:
        if ent.label_ == "JOBCATEGORY":
            results["categories"].append(ent.text)

    # Extracting budget and currency using regex
    budget_search = extract_budget_details(query)
    if budget_search:
        if budget_search[1]:
            budget_search_list = list(budget_search)
            budget_search_list[1] = budget_search[1].upper()
            budget_search = tuple(budget_search_list)
        results["currency"] = budget_search[1]
        if budget_search[0] is not None and budget_search[1] is not None and budget_search[2] is not None:
            if budget_search[2] == 'day':
                results["freelanceProjectType"] = True
                wage = float(budget_search[0])
                results["freelanceProjectTypeWage"] = wage
                exchange_rates = get_exchange_rates()
                results["freelanceProjectTypeSuperGrossWageCZK"] = 21 * wage * exchange_rates.get('CZK', 1)
                results["superGrossWageCZK"] =  results["freelanceProjectTypeSuperGrossWageCZK"]

            elif budget_search[2] == 'month':
                results["employmentProjectType"] = True
                wage = float(budget_search[0])
                exchange_rates = get_exchange_rates()
                results["employmentProjectTypeSuperGrossWageCZK"] = wage * exchange_rates.get('CZK', 1)
                results["employmentProjectTypeWage"] = wage / 21
                results["superGrossWageCZK"] = results["employmentProjectTypeSuperGrossWageCZK"]

        if budget_search[0] is not None and budget_search[1] is not None:  # Check if both values are not None
            budget = check_budget(budget_search[0], budget_search[1])
            if budget[0] == "freelance":
                results["freelanceProjectType"] = True
                results["freelanceProjectTypeWage"] = budget[1]
                exchange_rates = get_exchange_rates()
                results["freelanceProjectTypeSuperGrossWageCZK"] = 21 * budget[1] * exchange_rates.get('CZK', 1)
                results["superGrossWageCZK"] = results["freelanceProjectTypeSuperGrossWageCZK"]
                
            elif budget[0] == "employ":
                results["employmentProjectType"] = True
                exchange_rates = get_exchange_rates()
                results["employmentProjectTypeSuperGrossWageCZK"] = budget[1] * exchange_rates.get('CZK', 1)
                results["employmentProjectTypeWage"] = budget[1]
                results["superGrossWageCZK"] = results["employmentProjectTypeSuperGrossWageCZK"]
    
    return format_result_as_dict(results)


# queries = [
#     "Looking for Java Developer",
#     "Looking for Java Developers",
#     "Looking for Java Programmer",
#     "Looking for Java Programmers",
#     "I am looking for Java Engineer",
#     "I am looking for Java Engineers",
#     "Searching for Java Developer",
#     "Searching for Java Programmers",
#     "Seaking some Java Developer",
#     "Seaking some Java Engineer",
#     "We are looking for some Java developers",
#     "We are searching for Java programmer",
#     "I need to find Java engineer",
#     "Our company need new Java Developers",
#     "Our company is looking for Java programmer",
#     "My company need to find Java developer",
#     "In search of a Java developers"
#     "We are looking for a Java developer proficient in Java, React, and SQL, available for remote work",
#     "Seeking a Java programmer skilled in Java and React, with experience in SQL, ready to work remotely",
#     "We need a Java engineer with expertise in React or Java, capable of working in Slovakia",
#     "Looking for a Java developer with SQL knowledge, need to speak english and slovak",
#     "Seeking a Java programmers with experience in Java, React, and SQL, or other technologies is plus, ready to work remotely or from Slovakia",
#     "We are looking for a Java engineer experienced in SQL and either Java or React, available for remote work with ability to speak english",
#     "We are seeking a mid-level Java developer proficient in Java, React, and SQL, available for remote work",
#     "Looking for an experienced Java programmer skilled in Java and React, with expertise in SQL, ready to work from Slovakia or Czech Republic",
#     "Seeking a senior Java engineer experienced in Java or React, capable of working from home fulltime",
#     "Looking for a mid-level Java developers working in Java, speaking english on high level",
#     "Looking for an experienced Java programmer with Java and React working experience, available for remote work, and willing to come to the office twice a week in Slovakia",
#     "Looking for a junior Java developer with experience in Java and SQL, available for remote work from Slovakia two days a week and from the Czech Republic three days a week",
#     "Looking for Java Developers speaking english and slovak",
#     "We require a Java developer who communicates at least at a B2 English level",
#     "Searching for Java Engineer with experience in Java, React, SQL and english level B1",
#     "We are seeking a Java developer with experience in Java and React, specializing in the software domain",
#     "Seeking a Java developer experienced in both Java and React, with a focus on software solutions",
#     "Looking for a Java developer with expertise in Java or React, specializing in software",
#     "Seeking a Java developer with experience in Java, React, and SQL, with a focus on software",
#     "Searching for Medior Java Developer",
#     "Looking for Medior Java Enginner",
#     "Searching for some Medior Java Programmers",
#     "Looking for Java Programmers with minimum experience",
#     "Looking for Java Programmers with maximum experience",
#     "Searching for some Java Developers with any experience",
#     "We are looking for some expert Java Developers",
#     "Searching junior or medior Java Programer",
#     "I am searching some Java Engineers with senior experience",
#     "Looking to hire some Java Programmer, he need to be at least on Medior level experience",
#     "Looking for some profesional Java Developer",
#     "We are looking for Java Developer or React Developer",
#     "Searching for some Java Programmer who also know React",
#     "Searching either Java Engineer or React Engineer",
#     "Looking for Java Programmer that also know React",
#     "Looking to hire Java Developers or React Developers",
#     "Looking for Java Programmer that know Java or React",
#     "Searching for Java Developers that have experience in Java and React",
#     "We need a Java Engineer who knows how to work with Java and React, and also needs to know SQL or PostgreSQL.",
#     "Searching for Java Developers who knows how to work with Java and also React",
#     "Looking for Medior Java Programmer that know how to work with Java and React, and also SQL or PostgreSQL",
#     "Looking for Java Engineer that can work in Slovakia",
#     "Searching for Java developer that can work from home",
#     "We are looking for some Senior Java programmer that can work from Slovakia or Czech Republic",
#     "We're looking for Java developers who can work from Slovakia and speak slovak",
#     "Seeking Java developers who can work from the Czech Republica and speak czech and english",
#     "Looking for Java developers who can work from Slovakia or the Czech Republic and also speak either czech or slovak",
#     "We are looking for an experienced Java programmer who can work from Slovakia",
#     "Seeking an experienced Java developer who could work remotely or from Slovakia",
#     "Looking for an expert Java coder available to work from Slovakia or Czech Republic",
#     "Looking to hire an experienced Java programmer who can work remotely and can speak english",
#     "We need an junior Java programmer based in Slovakia and speaks english and slovak",
#     "Looking for a mid-level Java programmer available for remote work or from the Czech Republic",
#     "In search of a junior-level Java developer who can work from the Czech Republic and communicate in Czech",
#     "Searching for a skilled Java developer to work remotely or from Slovakia",
#     "Looking for an experienced Java coder available to work from Slovakia who can speaks english",
#     "We need an novice Java programmer based in Slovakia with posibility to work from home",
#     "Looking to hire an senior Java engineer based in Slovakia who can primarily work from home but needs to be able to come into the office once a week in Slovakia",
#     "We are in need of a mid-level Java programmer capable of work from Slovakia or the Czech Republic",
#     "We are seeking a mid-level Java programmer fluent in English, Slovak, or Czech for remote work",
#     "We are searching for a novice-level Java developer who can communicate in English and Slovak from the Slovakia",
#     "Seeking a junior-level Java programmer who can speak English and Czech really well, for remote work",
#     "We need experienced Java programmer who can speak English and Czech really well and can work 1 day from Slovakia and 4 days from Czech republic",
#     "We are looking for a junior-level Java developer who can work remotely and is available for two days in the Czech Republic",
#     "I am looking for senior Java engineers that can work remotely and once a month he can come to office in Slovakia",
#     "We're in search of a medior Java engineer capable of working remotely, he need to speak English and Slovak, and available for occasional office visits in Slovakia or the Czech Republic at least once a month",
#     "Looking for a senior Java developer who can work from Slovakia or the Czech Republic and is available for weekly office visits in Slovakia",
#     "We need an experienced Java developers who can work remotely or from Slovakia, with proficiency in English, Slovak, and is available for office visits in Slovakia two times a weak",
#     "Looking to hire a mid-level Java developer fluent in English and Slovak languages, available for remote work or office visits in Slovakia or Czech Republic once a month",
#     "We need an junior Java developer who can work remotely or from Slovakia, fluent in English or Slovak languages, and willing to visit the office in Slovakia or the Czech Republic once a month",
#     "Looking for a mid-level Java programmer based in Slovakia, fluent in English and Slovak languages, able to work remotely and visit the office in Slovakia or the Czech Republic as needed",
#     "Seeking Java developers who can work from Slovakia or the Czech Republic and speak English.",
#     "I need to find some Java engineer that can work from Slovakia 3 times a week and also from Czech Republic 2 times a week.",
#     "Looking for Senior Java Developer that speaks English.",
#     "We are searching for Java engineer who knows how to works with Java and React, and speaks English",
#     "I am looking for Java developer than can work from home and speaks English.",
#     "Looking for Java developer that can speak Slovak and also English.",
#     "Looking for Java programmers that can work from home and can speak Slovak or English.",
#     "We need a Java developers that knows how to work with Java or React and can work from home or Slovakia and also they speak english.",
#     "We are seeking an experienced Java developer who has knowledge of the Spring Framework.",
#     "Looking for a Java developer with expertise in JavaScript.",
#     "We need Java engineers who can work from Slovakia full-time.",
#     "Looking for Java developers who can work part-time from the Czech Republic and speaks czech.",
#     "I am looking for some Medior Java programmer that know how to work with Java or React, he can work either from Slovakia or Czech Republic full-time and speaks english",
#     "Looking for Senior Java Developer who can work as a standard/permanent/full-time employee with wage around 1000 euro a month",
#     "We are searching Junior Java Engineers who can work as a permanent employee with wage around 500 euro and speak english very well",
#     "I am looking for mid-level Java programmers who would work on a contract basis and his daily wage would be around 200 euros",
#     "Searching for junior Java Developers, they need to know Java and React and also speak english, the job type would be full-time with salary around 800 euros",
#     "We would like to hire a senior Java developer who can work with Java or React, and he can work from Slovakia. The salary would be around 400 euros per day",
#     "We are seeking a Java engineer with expertise in SQL for a contract position, with a daily wage of about 250 euros",
#     "Looking for a junior Java developers for a full-time position with a salary of approximately 1500 euros a month",
#     "We need a Java programmer with knowledge of Java and React for a part-time position, with a salary of 100 euros per day",
#     "We're looking for an experienced Java developer with expertise in Java, React, and SQL. He need to speak english and slovak. Salary for this job can be in range from 1000 to 2000 euro per month",
#     "Looking for a skilled Java developer with expertise in Java, React, and at least MySQL or NoSQL. Salary include contractual agreements, around 1000 euro",
#     "We are seeking an experienced Java developer working in Java, React, and either MySQL or NoSQL. The salary is  approximately 1050 euros",
#     "We are looking for skilled programmers in Java with expertise in Java, React, and at least one of MySQL or NoSQL. The salary includes contractual agreements, around 2000 euros",
#     "Seeking junior Java engineers with experience in Java, React, and MySQL. Salary could be around 1500 euros",
#     "Seeking a highly skilled Java developers with expertise in Java, React and SQL. Must be fluent in English and available for full-time remote work. Salary will be around 1000 euro",
#     "Looking for a mid-level Java engineer experienced in Java or React. This is a full-time position based in Czech Republic, offering 2000 euro",
#     "Seeking a senior Java programmer with experience in SQL and Java or React. Remote work opportunity with occasional office visits in Slovakia or Czech Republic two times a month. Salary around 2500 euro",
#     "We are hiring a Java developer skilled in Java. Must have excellent English language skills and be from Slovakia. Salary is 1000 euro",
#     "Seeking a junior Java developer with knowledge of Java, SQL, and React. This is a remote work opportunity with occasional office visits in Slovakia once a month. Entry-level salary around 1000 euro",
#     "Hiring a Java developer with expertise in cloud computing technologies, fluency in English. Remote work option available or work from office located in Slovakia with 2000 euro a month",
#     "Seeking a Java developer with expertise in healthcare systems. Skilled in Java, SQL, and React required. Full-time position based in Slovakia with the possibility of remote work. Salary around 2300 euro",
#     "Hiring a senior Java engineer specializing in marketing. Must have experience in SQL and Java or React. Full-time position based in Slovakia with salary 40000 czk",
#     "Looking for a mid-level Java programmer specializing in banking. Skilled in Java or React. Remote work with salary 30000 czk",
#     "Hiring an experienced Java engineer specializing in cybersecurity. Experienced in Java. Part-time position based in Slovakia with opportunities for remote work three times a week",
#     "Looking for a full-time senior Java programmers specializing in Internet of Things solutions. Must have experience in React, with fluency in English and Slovak. Located in Slovakia but with option to work from home. Salary around 5000 euro",
#     "Seeking a senior Java developer with expertise in public services. Skilled in Java, SQL, and React required. Full-time position based in Slovakia and Czech Republic. Salary will be 3000"
#     "I need a mid-level python developer who can work from home in Praha"
# ]


# # Open a file in write mode
# with open("query_results.txt", "w") as file:
#     for query in queries:
#         result = extract_job_requirements(query)
#         output = f"Query: {query} - Result: {result}\n"  # Add newline character for each result
#         print(output)  # Print to console
#         file.write(output)  # Write to file
