import re
import requests
import json
from bs4 import BeautifulSoup

def clean_first_paragraph(paragraph: str):
    if not str:
        return None
    
    patterns_replacements = [
        {
            "pattern": r"\/.*?ⓘ; ",
            "replacement": ""
        },
        {
            "pattern": r" \(.*?ⓘ\)",
            "replacement": ""        
        },
        { 
            "pattern": r"\(.*?ⓘ; ",
            "replacement": "("
        },
        {
            "pattern": r"\(/.*?; ",
            "replacement": "("            
        },
        { 
            "pattern": r" \[.*?ⓘ",
            "replacement": ""
        },
        { 
            "pattern": r"\[\w\]",
            "replacement": ""
        }
    ]

    cleaned_paragraph = paragraph

    for pattern_replacement in patterns_replacements:
        cleaned_paragraph = re.sub(pattern_replacement["pattern"], pattern_replacement["replacement"], cleaned_paragraph)

    return cleaned_paragraph


def get_first_paragraph(session, wikipedia_url: str):
    wiki_response = session.get(wikipedia_url)

    if wiki_response.status_code != 200:
        print(f"Error {wiki_response.status_code} while scrapping URL => {wikipedia_url}")
        print(wiki_response.content)
        return ""
   
    wiki_html = wiki_response.content

    soup = BeautifulSoup(wiki_html, 'html.parser')

    # We will only look for the first paragraph in the main content of the page 
    main_content = soup.find("div", class_ = "mw-content-ltr")

    # Some pages use different class for the main content, let's try that
    if not main_content:
        print("Didn't find mw-content-ltr, trying mw-content-rtl")
        main_content = soup.find("div", class_ = "mw-content-rtl")

    if main_content:
        # Get all the pragraphs from the main content section
        paragraphs = main_content.find_all("p")
    
    if not paragraphs:
       # As a backup, we get all the pragraphs from the page
       print("Last resource, getting all the paragraphs from the page")
       paragraphs = soup.find_all("p")
   
    if paragraphs:
        print(f"Number of paragraphs: {len(paragraphs)}")

        for paragraph in paragraphs:
            # Look for a <b> tag in the paragraph
            bold_tag = paragraph.find("b")

            # If we find the <b> tag and is not empty, then we assume that we are in the first paragraph of the main content
            if bold_tag and bold_tag.get_text().rstrip() != "":
                # Clean the content of the paragraph before returning it
                return clean_first_paragraph(paragraph.get_text().rstrip())
            
    return ""


def api_get_cookies(session, api_root_url: str, cookie_endpoint: str):
    # Get cookie from the API
    cookie_response = session.get(f"{api_root_url}/{cookie_endpoint}")

    if cookie_response.status_code != 200:
        print(f"Error {cookie_response.status_code} while callling API => {api_root_url}/{cookie_endpoint}")
        print(cookie_response.content)
        return None
    
    return cookie_response.cookies


def get_leaders(session):
    api_root_url = "https://country-leaders.onrender.com"
    cookie_endpoint = "cookie"
    countries_endpoint = "countries"
    leaders_endpoint = "leaders"

    cookies = api_get_cookies(session, api_root_url, cookie_endpoint)
    if not cookies:
        return

    # Get list of countries from the API
    countries_response = session.get(
        f"{api_root_url}/{countries_endpoint}",
        cookies = cookies
    )

    if countries_response.status_code != 200:
        print(f"Error {countries_response.status_code} while callling API => {api_root_url}/{countries_endpoint}")
        print(countries_response.content)
        return None

    countries = countries_response.json()
    print(f"Countries: {countries}")

    leaders_per_country = {}
    
    # Get list of leaders per country from the API
    for country in countries:
        print(f"Processing country: {country}")

        leaders_response = session.get(
            f"{api_root_url}/{leaders_endpoint}",
            cookies = cookies,
            params = {"country": country}
        )

        # If cookie is expired, lets get a new one and call the leaders endpoint again
        if leaders_response.status_code == 403:
            print("Expired cookie, getting new one")
            
            cookies = api_get_cookies(session, api_root_url, cookie_endpoint)

            leaders_response = session.get(
                f"{api_root_url}/{leaders_endpoint}",
                cookies = cookies,
                params = {"country": country}
            )

        if leaders_response.status_code == 200:
            leaders_per_country[country] = leaders_response.json()

            print(f"{len(leaders_per_country[country])} leaders found for country {country}")
            # For each leader, get the extra info from Wikipedia
            for leader in leaders_per_country[country]:
                print(leader["wikipedia_url"])
                leader["wikipedia_intro"] = get_first_paragraph(session, leader["wikipedia_url"])
        else:
            print(f"Error {leaders_response.status_code} while callling API => {api_root_url}/{leaders_endpoint}")
            print(leaders_response.content)
    
    return leaders_per_country


def save(leaders_dictionary, filepath):
    # Serializing json
    json_object = json.dumps(leaders_dictionary, indent=4)

    # Writing to file
    with open(filepath, "w") as outfile:
        outfile.write(json_object)


if __name__ == '__main__':
    session = requests.Session()

    leaders = get_leaders(session)
    save(leaders, "leaders.json")
