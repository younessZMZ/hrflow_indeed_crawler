""" A script to scrape job postings from Indeed.com. """

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from glob import glob
from json import JSONDecodeError, dump, load
from os.path import join

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.support.ui import WebDriverWait

WEBSITE = "https://uk.indeed.com/"


class Colors:
    """Class to hold color codes for console output."""
    WARNING = "\033[93m"
    ENDC = "\033[0m"


class JobScraper:
    """
    A class to scrape job postings from a website.

    Attributes:
        driver: A Selenium WebDriver instance.
        jobs: A dictionary to hold job postings.
        data_path: A string representing the path to save job postings.
        website: A string representing the website to scrape.

    Methods:
        load_jobs: Load jobs from a file.
        navigate_to_site: Navigate to the website.
        accept_cookies: Accept cookies on the website.
        enter_job_title: Enter a job title in the search box.
        close_popup: Close any pop-up on the website.
        scrap_jobs: Scrape job postings from the website.
        scrap_job: Scrape a single job posting.
        quit: Quit the WebDriver.
        save_jobs_to_file: Save job postings to a file.
    """

    def __init__(self, data_path: str, website: str) -> None:
        """
        Initialize the JobScraper.

        Args:
            data_path (str): The path to the file where the jobs will be saved.
            website (str): The website to scrape.
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
        self.driver = webdriver.Chrome(options=options)
        self.jobs = {}
        self.data_path = data_path
        self.website = website
        self.load_jobs()

    def load_jobs(self) -> None:
        """
        Load jobs from a file. If the file does not exist or is not valid JSON, an empty dictionary is used.
        """
        try:
            with open(self.data_path, "r") as file:
                jobs_list = load(file)
                self.jobs = {job["url"]: job for job in jobs_list}
        except (FileNotFoundError, JSONDecodeError):
            self.jobs = {}

    def navigate_to_site(self, url: str = None) -> None:
        """
        Navigate to the website. If no URL is provided, the website attribute is used.

        Args:
            url (str, optional): The URL to navigate to. If no URL is provided, the website attribute is used.
        """
        if url is None:
            url = self.website
        self.driver.get(url)

    def accept_cookies(self) -> None:
        """
        Accept cookies on the website. If the cookies acceptance button is not found, the method continues without accepting cookies.
        """
        try:
            WebDriverWait(self.driver, 3).until(exp_cond.presence_of_element_located((By.CLASS_NAME, "ot-sdk-row")))
            accept_all_button = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
            accept_all_button.click()
        except TimeoutException:
            print("Could not find cookies acceptance button, continuing without accepting cookies.")

    def enter_job_title(self, job_title: str) -> None:
        """
        Enter a job title in the search box and submit the form.

        Args:
            job_title (str): The job title to search for.
        """
        search_box = self.driver.find_element(By.ID, "text-input-what")
        search_box.send_keys(job_title)
        search_box.submit()

    def close_popup(self) -> None:
        """
        Close any pop-up on the website. If the pop-up is not found, the method continues without closing the pop-up.
        """
        try:
            WebDriverWait(self.driver, 3).until(
                exp_cond.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            resignation_close_button = self.driver.find_element(
                By.ID, "passport-modal-overlay-social-onetap-modal-close-button"
            )
            resignation_close_button.click()
        except (NoSuchElementException, TimeoutException):
            pass

    def close_popup2(self) -> None:
        """
        Close any pop-up on the website. If the pop-up is not found, the method continues without closing the pop-up.
        """
        try:
            WebDriverWait(self.driver, 3).until(
                exp_cond.presence_of_element_located((By.CLASS_NAME, "icl-CloseButton"))
            )
            close_button = self.driver.find_element(By.CLASS_NAME, "icl-CloseButton")
            close_button.click()
        except (NoSuchElementException, TimeoutException):
            pass

    def scrap_jobs(self, word: str, already_scraped_urls: dict) -> None:
        """
        Scrape job postings from the website. The method continues until no more pages are found.

        Args:
            word (str): The job title to search for.
            already_scraped_urls (dict): A dict with the URLs that have already been scraped in the keys.
        """
        number_of_jobs = 0
        pop_up_closed = False
        try:
            while True:
                WebDriverWait(self.driver, 3).until(
                    exp_cond.presence_of_element_located((By.ID, "mosaic-provider-jobcards"))
                )
                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                job_postings = soup.find_all(class_="resultWithShelf")
                with ThreadPoolExecutor(max_workers=15) as executor:
                    job_infos = executor.map(self.scrap_job, job_postings)
                    for job_info in job_infos:
                        if job_info and job_info["url"] not in already_scraped_urls:
                            self.jobs[job_info["url"]] = job_info

                number_of_jobs += len(job_postings)
                if number_of_jobs % 90 == 0:
                    self.save_jobs_to_file()

                try:
                    next_button = self.driver.find_element(By.XPATH, '//a[@data-testid="pagination-page-next"]')
                    self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                    next_button.click()
                except NoSuchElementException:
                    print("No more pages")
                    break
                if not pop_up_closed:
                    self.close_popup2()
                    pop_up_closed = True
                print("Number of jobs found :", number_of_jobs)
        except Exception:
            print("No more pages")

        print(f"{Colors.WARNING}The final number of jobs found for {word}: {number_of_jobs}{Colors.ENDC}")

    def scrap_job(self, job) -> dict | None:
        """
        Scrape a single job posting. If the job has already been scraped, the method returns None.

        Args:
            job (bs4.element.Tag): The job posting to scrape.

        Returns:
            dict: The scraped job information.
        """
        job_url = f"{self.website[:-1]}{job.find('a')['href']}"

        if job_url in self.jobs:
            return  # Skip this job if it has already been scraped

        try:
            _, posted_time = job.find(class_="date").text.split("\n")
        except ValueError:
            posted_time = job.find(class_="date").text
        except AttributeError:
            posted_time = ""

        job_info = {
            "name": job.find(class_="jobTitle").text,
            "company": job.find(class_="companyName").text,
            "location": job.find(class_="companyLocation").text,
            "url": job_url,
            "summary": job.find(class_="job-snippet").text,
            "creation_date": posted_time,
            "saved_date": date.today().isoformat(),
        }

        return job_info  # Add the job to the dictionary of jobs

    def scrap_website(self, searched_job: str, already_saved_jobs: dict) -> None:
        """
        Navigate to the website, accept cookies, enter the job title, close the popup, scrape jobs, and save them to a file.

        Args:
            searched_job (str): The job title to search for.
            already_saved_jobs (dict): A dictionary of jobs that have already been saved.
        """
        self.navigate_to_site()
        self.accept_cookies()
        self.enter_job_title(searched_job)
        self.close_popup()
        self.scrap_jobs(searched_job, already_saved_jobs)
        self.save_jobs_to_file()

    def quit(self) -> None:
        """
        Quit the webdriver.
        """
        self.driver.quit()

    def save_jobs_to_file(self) -> None:
        """
        Save job postings to a file.
        """
        jobs_list = list(self.jobs.values())
        with open(self.data_path, "w") as file:
            dump(jobs_list, file, indent=4)

    @staticmethod
    def get_jobs(data_path: str) -> dict:
        """
        Load jobs from all JSON files in the data directory.

        Args:
            data_path (str): The path to the directory containing the JSON files.

        Returns:
            dict: The loaded jobs.
        """
        json_paths = glob(join(data_path, "*.json"))
        jobs = {}
        for path in json_paths:
            with open(path, "r") as file:
                jobs.update({job["url"]: 0 for job in load(file)})
        return jobs


if __name__ == "__main__":
    saved_jobs = JobScraper.get_jobs(r"C:\Users\admin\PycharmProjects\hrflow_crawler\data")
    professions_path = r"C:\Users\admin\PycharmProjects\hrflow_crawler\data\professions.txt"
    with open(professions_path, "r") as file:
        professions = file.read().split("\n")

    for word in professions:
        now = time.time()
        profession_path = rf"C:\Users\admin\PycharmProjects\hrflow_crawler\data\{word.lower()}.json"
        job_scraper = JobScraper(profession_path, WEBSITE)
        job_scraper.scrap_website(word, saved_jobs)
        saved_jobs.update({k: 0 for k, v in job_scraper.jobs.items()})
        job_scraper.quit()
        print(f"Time elapsed for {word}:", time.time() - now, "seconds")
