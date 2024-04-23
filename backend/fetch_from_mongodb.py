from pymongo import MongoClient
from bson.json_util import dumps
from extracting_parameters import extract_job_requirements

def fetch_data(criteria):
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")

    # Select the collection
    db = client.chatbot
    collection = db.chatbot

    # Define search criteria
    query = {}

    # Map criteria keys to MongoDB field names
    field_mapping = {
        "categories": "categories",
        "skillsets": "skillsets",
        "localities": "localities",
        "languages": "languageIds.name",
        "levels": "level",
        "freelanceProjectType":"freelanceProjectType",
        "employmentProjectType":"employmentProjectType",
        "superGrossWageCZK": "superGrossWageCZK",
        "currency": "currency"
    }

    for key, value in criteria.items():
        if key in field_mapping:
            # Use MongoDB field name based on field mapping
            field_name = field_mapping[key]
            if isinstance(value, list):
                # For lists, use $in operator
                query[field_name] = {"$in": value}
            else:
                # For single values, use equality
                query[field_name] = value  

    # Define conditions for wages
    wage_conditions = []
    freelance_wage = criteria.get("superGrossWageCZK", 0.0)
    print(freelance_wage)
    wage_conditions.append({"superGrossWageCZK": {"$lte": freelance_wage}})
    sort_criteria = [("superGrossWageCZK", -1)]
    
    results = collection.find(query).sort(sort_criteria).limit(10)

    # Extract emails from the results
    emails = [result.get("email") for result in results if "email" in result]

    # Return the emails as JSON
    return dumps(emails)

def query_and_fetch(query):
    job_requirements = extract_job_requirements(query)
    search_criteria = {
        "categories": job_requirements.get("categories", []),
        "skillsets": job_requirements.get("skillsets", []),
        "localities": job_requirements.get("localities", []),
        "languages": job_requirements.get("languages", []),
        "allocations": [job_requirements.get("allocation")] if job_requirements.get("allocation") else [],
        "levels": job_requirements.get("levelsExample", []),
        "currency": job_requirements.get("currency",[]),
        "freelanceProjectType": job_requirements.get("freelanceProjectType", False),
        "freelanceProjectTypeWage": job_requirements.get("freelanceProjectTypeWage", 0.0),
        "freelanceProjectTypeSuperGrossWageCZK": job_requirements.get("freelanceProjectTypeSuperGrossWageCZK", 0.0),
        "employmentProjectType": job_requirements.get("employmentProjectType", False),
        "employmentProjectTypeWage": job_requirements.get("employmentProjectTypeWage", 0.0),
        "employmentProjectTypeSuperGrossWageCZK": job_requirements.get("employmentProjectTypeSuperGrossWageCZK", 0.0),
        "superGrossWageCZK": job_requirements.get("superGrossWageCZK", 0.0)
    }
    

    search_criteria = {key: value for key, value in search_criteria.items() if value}
    if not search_criteria:
        return []
    result_emails = fetch_data(search_criteria)
    return result_emails



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
#     "Our company is looking for Java programer",
#     "My company need to find Java developer",
#     "In search of a Java developers"
# ]

# for query in queries:
#     result = query_and_fetch(query)
#     print(f"Query: {query} - Result: {result}")

query = "I need a python developer who can speek english and Spanish with 7000CZK"
print(query_and_fetch(query))