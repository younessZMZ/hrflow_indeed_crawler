"""A script to scrape detailed job postings from a website."""

import time
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError, dump, load

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class JobDetailScraper:
    """
    A class to scrape job details from a website.

    Attributes:
        data_path (str): The path to the file where the jobs will be saved.
        number_to_process (int): The number of jobs to process.
        saved_jobs (dict): A dictionary of jobs that have already been saved.
        jobs (list): A list of jobs to be scraped.
        job_details (list): A list of job details that have been scraped.

    Methods:
        load_saved_jobs: Load jobs from a file.
        load_jobs: Load jobs from a file.
        load_job_details: Load job details from a file.
        scrap_job_details: Scrape details of a single job.
        scrap_all_jobs: Scrape details of all jobs.
        save_jobs_details: Save job details to a file.
    """
    def __init__(self, data_path: str, number_to_process: int) -> None:
        """
        Initialize the JobDetailScraper.

        Args:
            data_path (str): The path to the file where the jobs will be saved.
            number_to_process (int): The number of jobs to process.
        """
        self.data_path = data_path
        self.dump_path = data_path.replace(".json", "_details.json")
        self.number_to_process = number_to_process
        self.saved_jobs = {}
        self.jobs = []
        self.job_details = []
        self.load_saved_jobs()
        self.load_jobs()
        self.load_job_details()

    def load_saved_jobs(self) -> None:
        """
        Load jobs from a file. If the file does not exist or is not valid JSON, an empty dictionary is used.
        """
        try:
            with open(self.dump_path, "r") as file:
                self.saved_jobs = {job["url"]: 0 for job in load(file)}
        except (FileNotFoundError, JSONDecodeError):
            self.saved_jobs = {}

    def load_jobs(self) -> None:
        """
         Load jobs from a file. If the file does not exist or is not valid JSON, an empty list is used.
         """
        try:
            with open(self.data_path, "r") as file:
                all_jobs = {job["url"]: 0 for job in load(file)}
                for url in all_jobs:
                    if url not in self.saved_jobs:
                        self.jobs.append(url)
                    if len(self.jobs) >= self.number_to_process:
                        break
        except (FileNotFoundError, JSONDecodeError):
            self.jobs = []

    def load_job_details(self) -> None:
        """
        Load job details from a file. If the file does not exist or is not valid JSON, an empty list is used.
        """
        try:
            with open(self.dump_path, "r") as file:
                self.job_details = load(file)
        except (FileNotFoundError, JSONDecodeError):
            self.job_details = []

    def scrap_job_details(self, url: str) -> None:
        """
        Scrape details of a single job.

        Args:
            url (str): The URL of the job to scrape.
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
        options.add_argument("window-size=1200x600")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.javascript": 2,
        }
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        driver.get(url)  # Navigate to the job URL

        # Pass the HTML to BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        job_description_tag = soup.find(id="jobDescriptionText")
        job_description = job_description_tag.text if job_description_tag else ""

        salary_info_tag = soup.find(id="salaryInfoAndJobType")
        salary_info = salary_info_tag.text if salary_info_tag else ""

        self.job_details.append({"url": url, "description": job_description, "salary_info": salary_info})
        driver.quit()

    def scrap_all_jobs(self) -> None:
        """
        Scrape details of all jobs. This method uses a ThreadPoolExecutor to scrape multiple jobs concurrently.
        """
        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(self.scrap_job_details, self.jobs)

    def save_jobs_details(self) -> None:
        """
        Save job details to a file. The file is named by replacing ".json" in the data_path with "_details.json".
        """
        with open(self.dump_path, "w") as file:
            dump(self.job_details, file, indent=4)


if __name__ == "__main__":
    number_to_process = 100
    now = time.time()
    path = r"C:\Users\admin\PycharmProjects\hrflow_crawler\aggregated_data\all_jobs.json"
    job_scraper = JobDetailScraper(path, number_to_process)
    job_scraper.scrap_all_jobs()
    job_scraper.save_jobs_details()
    print("Time elapsed :", time.time() - now, "seconds")
    # 30 jobs in 36 seconds with only selenium
    # 30 jobs in 33 seconds with selenium + bs4
    # 100 jobs in 80 seconds with selenium + bs4 + multithreading
