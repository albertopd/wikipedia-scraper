from scraper import WikipediaScraper


def main():
    scraper = WikipediaScraper()
    scraper.get_leaders_data()
    scraper.to_json_file("leaders.json")


# Only runs when this file is executed directly
if __name__ == '__main__':
    main()