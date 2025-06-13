# 🌍 Political Leaders Scraper

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Dependencies](https://img.shields.io/badge/dependencies-requests%2C%20bs4%2C%20lxml-orange)

A Python-based scraper that compiles a structured JSON file of political leaders for countries around the world.  
It combines data from a public REST API with Wikipedia scraping to enrich the information.

- **API Source**: [country-leaders.onrender.com](https://country-leaders.onrender.com/docs)  
- **Supplementary Info**: Wikipedia (via HTML parsing with BeautifulSoup)

---

## 📦 Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/albertopd/wikipedia-scraper.git
   cd wikipedia-scraper
   ```

2. **(Optional) Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

Run the scraper from the terminal:
```bash
python leaders_scraper.py
```

The output file `leaders.json` will be created in the current directory.

---

## 🧠 Features

- Retrieves real-time country and leader data from a public API.
- Handles cookie expiration and retries automatically.
- Scrapes the **first paragraph** of each leader’s Wikipedia page.
- Outputs a well-structured JSON file.

---

## 📄 Requirements

- Python 3.10+
- Requests
- BeautifulSoup4
- lxml (for faster HTML parsing)

See [requirements.txt](requirements.txt) for the full list.

---

## 📂 Example Output

```json
{
    "be": [
        {
            "id": "Q12978",
            "first_name": "Guy",
            "last_name": "Verhofstadt",
            "birth_date": "1953-04-11",
            "death_date": null,
            "place_of_birth": "Dendermonde",
            "wikipedia_url": "https://nl.wikipedia.org/wiki/Guy_Verhofstadt",
            "start_mandate": "1999-07-12",
            "end_mandate": "2008-03-20",
            "wikipedia_intro": "Guy Maurice Marie-Louise Verhofstadt (Dendermonde, 11 april 1953) is een Belgisch politicus voor de Open Vlaamse Liberalen en Democraten (Open Vld). Hij was premier van Belgi\u00eb van 12 juli 1999 tot 20 maart 2008 in drie regeringen. Hij be\u00ebindigde zijn actieve politieke carri\u00e8re in het Europees Parlement, waar hij van 2009 tot 2019 fractieleider van de Alliantie van Liberalen en Democraten voor Europa (ALDE) was."
        },
        ...
    ]
}
```

---

## 👤 Author

**Alberto Pérez Dávila**  
GitHub: [@albertopd](https://github.com/albertopd)