import sys

from scraper import WikipediaScraper

try:
    scraper = WikipediaScraper()
    scraper.get_leaders_data()

    if len(sys.argv) > 1 and sys.argv[1].upper() == "CSV":
        scraper.to_csv_file("leaders.csv")
    else:
        scraper.to_json_file("leaders.json")

except Exception as ex:
    print(f"Oops! Something went wrong! => {ex}")