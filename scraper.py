import json
import re
import csv
from urllib.parse import urljoin

import requests
import requests.cookies
from bs4 import BeautifulSoup
from requests import Session


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

def api_call_with_cookie_retry(api_call):
    def wrapper(self, *args, **kwargs):
        for _ in range(2):
            try:
                return api_call(self, *args, **kwargs)
            except CookieExpiredError:
                print("Cookie expired, getting another one from the jar")
                self.refresh_cookie()
        return api_call(self, *args, **kwargs)
    return wrapper

class WikipediaScraper:
    # API base URL and endpoints
    API_BASE_URL = "https://country-leaders.onrender.com"
    COOKIE_ENDPOINT = "/cookie"
    COUNTRIES_ENDPOINT = "/countries"
    LEADERS_ENDPOINT = "/leaders"

    # API status codes
    STATUS_CODE_EXPIRED_COOKIE = 403

    def __init__(self) -> None:
        self.session = requests.Session()
        self.leaders_data = {}

    def get_leaders_data(self) -> None:
        """
        Function to retrieve and enrich leaders data for all countries.
        """
        self.refresh_cookie()

        # Get list of countries from the API
        countries = self.get_countries()
        print(f"Countries: {countries}")
        
        for country in countries:
            print(f"Processing country: {country}")

            # Get list of country leaders from the API
            self.leaders_data[country] = self.get_leaders_per_country(country)

            print(f"{len(self.leaders_data[country])} leaders found for country {country}")

            # For each leader, get the extra info from Wikipedia
            for leader in self.leaders_data[country]:
                print(f"Leader Wikipage: {leader["wikipedia_url"]}")

                leader["wikipedia_intro"] = self.get_first_wiki_paragraph(leader["wikipedia_url"])
    
    def refresh_cookie(self) -> None:
        """
        Request a new session cookie from the API.
        """
        cookie_response = self.session.get(urljoin(self.API_BASE_URL, self.COOKIE_ENDPOINT))
        cookie_response.raise_for_status()
        self.cookie = cookie_response.cookies

    @api_call_with_cookie_retry
    def get_countries(self) -> list[str]:
        """
        Retrieve a list of countries from the API, retrying on cookie expiration.

        Returns:
            list[str]: List of country codes.
        """
        countries_response = self.session.get(
            urljoin(self.API_BASE_URL, self.COUNTRIES_ENDPOINT),
            cookies = self.cookie
        )

        if countries_response.status_code == self.STATUS_CODE_EXPIRED_COOKIE:
            raise CookieExpiredError(countries_response.status_code)

        countries_response.raise_for_status()

        return countries_response.json()

    @api_call_with_cookie_retry
    def get_leaders_per_country(self, country_code: str) -> list[dict]:
        """
        Get leaders for a specified country from the API, retrying on cookie expiration.

        Args:
            country_code (str): The ISO country code.

        Returns:
            list[dict]: A list of leader records as dictionaries.
        """
        leaders_response = self.session.get(
            urljoin(self.API_BASE_URL, self.LEADERS_ENDPOINT), 
            cookies = self.cookie,
            params = {"country": country_code}
        )

        if leaders_response.status_code == self.STATUS_CODE_EXPIRED_COOKIE:
            raise CookieExpiredError(leaders_response.status_code)
        
        leaders_response.raise_for_status()

        return leaders_response.json()

    def get_first_wiki_paragraph(
            self,
            wikipedia_url: str
        ) -> str:
        """
        Extract the first relevant paragraph from a Wikipedia page.

        Args:
            wikipedia_url (str): URL of the Wikipedia page.

        Returns:
            str: The cleaned first paragraph of the main content.
        """
        wiki_response = self.session.get(wikipedia_url)
        wiki_response.raise_for_status()

        soup = BeautifulSoup(wiki_response.content, 'html.parser')

        # Try to find main content using known class names
        # First we search by classs "mw-content-ltr"
        main_content = soup.find("div", class_ = "mw-content-ltr")

        # If not found, then we search by class "mw-content-rtl"
        if not main_content:
            print("Didn't find main content by class [mw-content-ltr], searching by class [mw-content-rtl]")
            main_content = soup.find("div", class_ = "mw-content-rtl")

        if main_content:
            # Get all the pragraphs from the main content section
            paragraphs = main_content.find_all("p")
        else:
            # As fallback, we get all the pragraphs from the page
            paragraphs = soup.find_all("p")
    
        print(f"Number of paragraphs found: {len(paragraphs)}")

        for paragraph in paragraphs:
            # Look for a <b> tag in the paragraph
            bold_tag = paragraph.find("b")

            # If we find the <b> tag and is not empty, then we assume that we are in the first paragraph of the main content
            if bold_tag and bold_tag.get_text().rstrip() != "":
                # Clean the content of the paragraph before returning it
                return self.clean_paragraph(paragraph.get_text().rstrip())
                
        return ""

    def clean_paragraph(self, paragraph: str) -> str:
        """
        Clean and remove unnecessary annotations and references from a paragraph string.

        Args:
            paragraph (str): The raw paragraph text.

        Returns:
            str: Cleaned paragraph text.
        """
        if not paragraph:
            return ""
        
        patterns_replacements = [
            # Remove things like "/xyzⓘ; ", "(xyzⓘ)", "[xyzⓘ", "xyzⓘ "
            { "pattern": r"(\/.*?ⓘ; ?|\(.*?ⓘ\)|\[.*?ⓘ|.*?ⓘ )", "replacement": "" },

            # Remove other cases where there is extra information inside the parenthesis that we want to preserve
            { "pattern": r"\(\/.*?;", "replacement": "(" },
            { "pattern": r"\(.*?ⓘ;", "replacement": "(" },

            # Remove simple reference markers like [1], [a], etc.
            { "pattern": r"\[\w\]", "replacement": "" }
        ]

        cleaned_paragraph = paragraph

        for pr in patterns_replacements:
            cleaned_paragraph = re.sub(pr["pattern"], pr["replacement"], cleaned_paragraph)

        return cleaned_paragraph.strip()

    def to_json_file(self, filepath: str) -> None:
        """
        Save the leader data dictionary to a JSON file.

        Args:
            filepath (str): Path where the JSON file will be saved.
        """
        # Serializing object to JSON string
        json_object = json.dumps(self.leaders_data, indent = 4)

        # Writing serialized string to file
        with open(filepath, "w") as outfile:
            outfile.write(json_object)

        print(f"Leaders data saved to {filepath}")

    def to_csv_file(self, filepath: str) -> None:
        """
        Save the leader data dictionary to a CSV file.

        Args:
            filepath (str): Path where the CSV file will be saved.
        """
        # Flatten the data and add the country info
        rows = []
        for country, leaders in self.leaders_data.items():
            for leader in leaders:
                row = leader.copy()
                row['Country'] = country
                rows.append(row)

        # Get all the fieldnames (keys)
        fieldnames = ['Country'] + [key for key in rows[0] if key != 'Country']

        # Write to CSV
        with open('leaders.csv', mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Leaders data saved to {filepath}")