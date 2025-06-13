from scraper import WikipediaScraper

try:
    scraper = WikipediaScraper()
    scraper.get_leaders_data()
    scraper.to_json_file("leaders.json")
    
except Exception as ex:
    print(f"Oops! Something went wrong! => {ex}")