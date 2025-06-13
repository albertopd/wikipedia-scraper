from scraper import WikipediaScraper

try:
    scraper = WikipediaScraper()
    scraper.get_leaders_data()
    scraper.to_json_file("leaders.json")
    scraper.to_csv_file("leaders.csv")
except Exception as ex:
    print(f"Oops! Something went wrong! => {ex}")