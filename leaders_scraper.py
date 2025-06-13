import json
import re
from urllib.parse import urljoin

import requests
import requests.cookies
from bs4 import BeautifulSoup
from requests import Session


# API base URL and endpoints
API_BASE_URL = "https://country-leaders.onrender.com"
COOKIE_ENDPOINT = "/cookie"
COUNTRIES_ENDPOINT = "/countries"
LEADERS_ENDPOINT = "/leaders"

# API status codes
STATUS_CODE_EXPIRED_COOKIE = 403

# API settings
API_NUM_RETRIES = 2

# Custom exceptions
class CookieExpiredError(Exception):
    """
    Exception raised when an API error occurs.
    
    Attributes:
        message (str): Description of the error.
        status_code (int, optional): HTTP status code returned by the API.
    """
    def __init__(self, status_code: int):
        self.status_code = status_code 
        super().__init__(f"Cookie expired (STATUS CODE: {status_code})")

# API calls
def api_get_cookie(session: Session) -> requests.cookies.RequestsCookieJar:
    """
    Request a session cookie from the API.

    Args:
        session (Session): The active requests session.

    Returns:
        RequestsCookieJar: The cookie jar from the API response.

    Raises:
        APIError: If the response status code is not 200.
    """
    cookie_response = session.get(urljoin(API_BASE_URL, COOKIE_ENDPOINT))
    cookie_response.raise_for_status()
    return cookie_response.cookies

def api_call_with_cookie_retry(api_call):
    """
    Decorator that retries an API call when a cookie expired error occurs.

    This decorator wraps an API call function and attempts to handle `CookieExpiredError`
    by fetching a new cookie and retrying the call. It retries up to `API_NUM_RETRIES` times.

    Parameters:
        api_call (callable): The API function to decorate. It must accept a `session` and `cookie`
                             as its first two arguments, followed by any additional arguments.

    Returns:
        callable: A wrapped function that retries the API call with a refreshed cookie if needed.

    Raises:
        The last encountered exception if all retry attempts fail.
    """
    def wrapper(session: Session, cookie, *args, **kwargs):
        
        for _ in range(API_NUM_RETRIES):
            try:
                call_response = api_call(session, cookie, *args, **kwargs)
            except CookieExpiredError as cee:
                print("Cookie expired, getting another one from the jar")
                cookie = api_get_cookie(session)
            
        return call_response

    return wrapper

@api_call_with_cookie_retry
def api_get_countries(
        session: Session,
        cookie: requests.cookies.RequestsCookieJar
    ) -> list[str]:
    """
    Retrieve a list of countries from the API, retrying on cookie expiration.

    Args:
        session (Session): The active requests session.
        cookie: The session cookie.

    Returns:
        list[str]: List of country codes.

    Raises:
        APIError: If the request fails with an unhandled status code.
    """
    countries_response = session.get(
        urljoin(API_BASE_URL, COUNTRIES_ENDPOINT),
        cookies = cookie
    )

    if countries_response.status_code == STATUS_CODE_EXPIRED_COOKIE:
        raise CookieExpiredError(countries_response.status_code)

    countries_response.raise_for_status()

    return countries_response.json()

@api_call_with_cookie_retry
def api_get_leaders(
        session: Session,
        cookie: requests.cookies.RequestsCookieJar,
        country_code: str
    ) -> list[dict]:
    """
    Get leaders for a specified country from the API, retrying on cookie expiration.

    Args:
        session (Session): The active requests session.
        cookie: The session cookie.
        country_code (str): The ISO country code.

    Returns:
        list[dict]: A list of leader records as dictionaries.

    Raises:
        APIError: If the request fails with an unhandled status code.
    """
    leaders_response = session.get(
        urljoin(API_BASE_URL, LEADERS_ENDPOINT), 
        cookies = cookie,
        params = {"country": country_code}
    )

    if leaders_response.status_code == STATUS_CODE_EXPIRED_COOKIE:
        raise CookieExpiredError(leaders_response.status_code)
    
    leaders_response.raise_for_status()

    return leaders_response.json()


def clean_first_paragraph(paragraph: str):
    """
    Clean and remove unnecessary annotations and references from a paragraph string.

    Args:
        paragraph (str): The raw paragraph text.

    Returns:
        str: Cleaned paragraph text.
    """
    if not str:
        return None
    
    patterns_replacements = [
        {"pattern": r"\/.*?ⓘ; ", "replacement": ""},
        {"pattern": r" \(.*?ⓘ\)", "replacement": ""},
        {"pattern": r"\(.*?ⓘ;", "replacement": "("},
        {"pattern": r" \[.*?ⓘ", "replacement": ""},
        {"pattern": r" .*?ⓘ ", "replacement": " "},
        {"pattern": r"\(\/.*?;", "replacement": "("},
        {"pattern": r"\[\w\]", "replacement": ""}
    ]

    cleaned_paragraph = paragraph

    for pattern_replacement in patterns_replacements:
        cleaned_paragraph = re.sub(pattern_replacement["pattern"], pattern_replacement["replacement"], cleaned_paragraph)

    return cleaned_paragraph

def get_first_paragraph_from_wikipedia(
        session: Session, 
        wikipedia_url: str
    ):
    """
    Extract the first relevant paragraph from a Wikipedia page.

    Args:
        session (Session): The requests session.
        wikipedia_url (str): URL of the Wikipedia page.

    Returns:
        str: The cleaned first paragraph of the main content.
    """
    wiki_response = session.get(wikipedia_url)
    
    wiki_response.raise_for_status()

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

def get_leaders(session: Session):
    """
    Function to retrieve and enrich leaders data for all countries.

    Args:
        session (Session): The requests session.

    Returns:
        dict[str, list[dict]]: Mapping of country codes to lists of enriched leader data.
    """
    cookie = api_get_cookie(session)

    # Get list of countries from the API
    countries = api_get_countries(session, cookie)

    print(f"Countries: {countries}")

    leaders = {}
    
    for country in countries:
        print(f"Processing country: {country}")

        # Get list of country leaders from the API
        leaders[country] = api_get_leaders(session, cookie, country)

        print(f"{len(leaders[country])} leaders found for country {country}")

        # For each leader, get the extra info from Wikipedia
        for leader in leaders[country]:
            leader_wiki_url = leader["wikipedia_url"]

            print(f"Leader Wikipage: {leader_wiki_url}")

            leader["wikipedia_intro"] = get_first_paragraph_from_wikipedia(session, leader_wiki_url)
    
    return leaders

def save(
        leaders_dictionary: dict[str, list[dict]],
        filepath: str
    ):
    """
    Save the leader data dictionary to a JSON file.

    Args:
        leaders_dictionary (dict[str, list[dict]]): Dictionary of country -> leaders list.
        filepath (str): Path where the JSON file will be saved.
    """
    # Serializing object to JSON string
    json_object = json.dumps(leaders_dictionary, indent = 4)

    # Writing serialized string to file
    with open(filepath, "w") as outfile:
        outfile.write(json_object)


def main():
    # Create a Session to be shared by all the request calls
    session = requests.Session()

    # Get list of leader per country from the API + the extra info from Wikipedia
    leaders = get_leaders(session)

    # Store the list of leaders in a JSON file
    save(leaders, "leaders.json")


# Only runs when this file is executed directly
if __name__ == '__main__':
    main()