# Job Scraping and Indexing Project

This project contains three Python scripts that are used to scrape job postings from a website, extract detailed information about each job, and index the jobs to the Hrflow API. The scripts use the Selenium and BeautifulSoup libraries for web scraping, and the Hrflow client for interacting with the Hrflow API.

## Scripts

1. `JobScraper.py`: This script scrapes job postings from a specified website. It uses Selenium to navigate the website and BeautifulSoup to parse the HTML and extract information about each job. The extracted information includes the job title, location, company, summary, and URL.

2. `JobDetailScraper.py`: This script takes the URLs of job postings scraped by the `JobScraper.py` script and visits each URL to extract more detailed information about each job. It uses Selenium to navigate to each job posting and BeautifulSoup to parse the HTML and extract the job description and salary information.

3. `JobIndexer.py`: This script takes the detailed job information scraped by the `JobDetailScraper.py` script and indexes it to the Hrflow API. It uses the Hrflow client to interact with the Hrflow API.

## Classes

1. `JobScraper`: This class is defined in the `JobScraper.py` script. It contains methods for navigating the website, scraping job postings, and saving the scraped information to a file.

2. `JobDetailScraper`: This class is defined in the `JobDetailScraper.py` script. It contains methods for navigating to each job posting, scraping detailed job information, and saving the scraped information to a file.

3. `JobIndexer`: This class is defined in the `JobIndexer.py` script. It contains methods for loading the scraped job information, formatting it for the Hrflow API, and indexing it to the Hrflow API.

## Usage

To use these scripts, you will need to install the required Python libraries, which include Selenium, BeautifulSoup, and the Hrflow client. You will also need to set up an account with Hrflow and obtain an API key.

### Installation

1. Install the required Python libraries by running `pip install -r requirements.txt` in your terminal.

2. Set up an account with Hrflow and obtain an API key.

3. Rename the template `.env.example` to `.env` and fill in the required information:

        - X-API-KEY=ask_e0123456789 : Your Hrflow API key.
        - X-USER-EMAIL=firstname.lastname@gmail.com : Your Hrflow user email.
        - BOARD_KEY=0123456789abc : The ID of the board you are saving the jobs to.

### Running the Scripts

Once you have installed the required libraries and set up your `.env` file, you can run the scripts in the following order:

1. Run `JobScraper.py` to scrape job postings from the website.
2. Run `JobDetailScraper.py` to scrape detailed job information.
3. Run `JobIndexer.py` to index the job information to the Hrflow API.

