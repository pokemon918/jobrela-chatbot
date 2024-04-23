import requests
from extracting_parameters import extract_job_requirements


def get_job_data(query):
    query = extract_job_requirements(query)
    url = "https://www.jobrela.com/api/professional/getAvailableAnonymousProfessionals?page=0&size=12&direction=DESC&sortBy=superGrossWageCZK"
    skillsets = query.get("skillsets")
    if not skillsets:
        skillsets = []
    else:
        skillsets = [skillsets]

    localities = query.get("localities")
    if not localities:
        localities = []
    else:
        localities = [localities]
    
    categories = query.get("categories")
    if not categories:
        categories = []
    else:
        categories = [categories]

    levelsExample = query.get("levelsExample")
    if not levelsExample:
        levelsExample = []
    else:
        levelsExample = [levelsExample]

    languageIds = query.get("languageIds")
    if not languageIds:
        languageIds = []
    else:
        languageIds = [languageIds]

    
    payload = {
        "skillsets": skillsets,
        "skillSetAdvanceOption": {
            "allRequiredSkillSets": [],
            "onlyOneRequiredSkillSets": [
                []
            ]
        },
        "localities": localities,
        "categories": categories,
        "specialities": [],
        "levelsExample": levelsExample,
        "languageIds": languageIds,
        "availabilityOption": None,
        "allocations": [],
        "currency": query.get("currency", None),
        "allLanguagesRequired": False,
        "allSkillsetsRequired": False,
        "allCategoriesRequired": False,
        "employmentProjectTypeWage": query.get("employmentProjectTypeWage", 0),
        "employmentProjectType": query.get("employmentProjectType", False),
        "freelanceProjectTypeWage": query.get("freelanceProjectTypeWage", 0),
        "freelanceProjectType": query.get("freelanceProjectType", False)
    }
    print(payload)
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to retrieve data. Status code: {response.status_code}"}



query = "I need java engineers less than 300EUR/day"
print(get_job_data(query))