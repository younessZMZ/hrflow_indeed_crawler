"""A script to index job postings to the Hrflow API."""

import os
import re
from datetime import datetime, timedelta
from json import load, dump

import requests
from dotenv import load_dotenv
from hrflow import Hrflow

load_dotenv()


API_KEY = os.environ["X-API-KEY"]
USER_EMAIL = os.environ["X-USER-EMAIL"]
JOBBOARD_URL = "https://uk.indeed.com/"
BOARD_KEY = os.environ["BOARD_KEY"]
RESUME_PATH = r"C:\Users\admin\OneDrive\Bureau\Job UK\Youness ZEMZGUI resume.pdf"
HEADERS = {
    "X-API-KEY": API_KEY,
    "X-USER-EMAIL": USER_EMAIL,
    "Content-Type": "application/json",
}

client = Hrflow(api_secret=API_KEY, api_user=USER_EMAIL)


class JobIndexer:
    """
    A class to index jobs to the Hrflow API.

    This class provides methods to load jobs from a JSON file, format them according to the Hrflow API
    requirements, and then index them to a specified board on the Hrflow platform. It also handles the extraction
    and formatting of skills from the job descriptions using the Hrflow document parsing API.

    Attributes:
        jobs_path (str): The path to the JSON file containing the jobs.
        saved_jobs_path (str): The path to the JSON file where the indexed jobs will be saved.
        jobs (list): A list to store the loaded jobs.
        jobs_to_save (list): A list to store the jobs that have been successfully indexed.

    Methods:
        load_jobs: Loads jobs from the JSON file specified in jobs_path.
        get_job_creation_date: Calculates the job creation date based on the creation_date and saved_date.
        format_salary_info: Extracts and formats the salary and job type information from the salary_info string.
        format_job: Formats a job according to the Hrflow API requirements.
        format_skills: Extracts and formats the skills from a job description text.
        index_jobs: Indexes the job to the Hrflow API.
        get_urls_saved_in_the_board: Gets the URLs of the jobs that have already been saved in the board.
        dump_saved_jobs: Saves the jobs that have been successfully indexed to a JSON file.
    """

    def __init__(self, jobs_path: str, saved_jobs_path: str) -> None:
        """
        Initialize the JobIndexer with the specified jobs_path and saved_jobs_path.

        Args:
            jobs_path (str): The path to the JSON file containing the job postings.
            saved_jobs_path (str): The path to the JSON file where the indexed jobs will be saved.
        """
        self.jobs_path = jobs_path
        self.saved_jobs_path = saved_jobs_path
        self.jobs = []
        self.jobs_to_save = []

    def load_jobs(self) -> None:
        """
        Load job postings from the JSON file specified in jobs_path.
        """
        with open(self.jobs_path, "r") as f:
            self.jobs = load(f)

    @staticmethod
    def get_job_creation_date(creation_date: str, saved_date: str) -> datetime.date:
        """
        Calculate the job creation date based on the creation_date and saved_date.

        Args:
            creation_date (str): The string representing the job creation date.
            saved_date (str): The string representing the date when the job was saved.

        Returns:
            datetime.date: The calculated job creation date.
        """
        saved_date = datetime.strptime(saved_date, "%Y-%m-%d").date()
        creation_date = creation_date.split()
        if "day" in creation_date or "days" in creation_date:
            for string in creation_date:
                if string.isnumeric():
                    return saved_date - timedelta(days=int(string))
                if "+" in string:  # Check if the string contains "+"
                    days = int(re.findall(r"\d+", string)[0])  # Extract the numeric part before the "+"
                    return saved_date - timedelta(days=days)
        elif (
            "hour" in creation_date
            or "hours" in creation_date
            or "minute" in creation_date
            or "minutes" in creation_date
        ):
            for string in creation_date:
                if string.isnumeric():
                    return saved_date
        elif "month" in creation_date or "months" in creation_date:
            for string in creation_date:
                if string.isnumeric():
                    return saved_date - timedelta(days=int(string) * 30)
        elif "year" in creation_date or "years" in creation_date:
            for string in creation_date:
                if string.isnumeric():
                    return saved_date - timedelta(days=int(string) * 365)
        else:
            raise ValueError(f"Could not parse creation date: {creation_date}")

    @staticmethod
    def format_salary_info(salary_info) -> tuple:
        """
        Extract and format the salary and job type information from the salary_info string.

        Args:
            salary_info (str): The string containing the salary and job type information.

        Returns:
            tuple: A tuple containing the formatted salary and job type information.
        """
        salary_pattern = (
            r"(\£\d+(?:,\d{3})*(?:\.\d{2})? - \£\d+(?:,\d{3})*(?:\.\d{2})? (?:a day|a week|a month|a year))"
        )
        job_type_pattern = r"(Full-time|Part-time|Internship|Apprenticeship|Contract|Temporary)"

        salary = re.search(salary_pattern, salary_info)
        job_type = re.search(job_type_pattern, salary_info)

        salary = salary.group() if salary else None
        job_type = job_type.group() if job_type else None

        return salary, job_type

    def format_job(self, job: dict) -> dict:
        """
        Format a job posting according to the Hrflow API requirements.

        Args:
            job (dict): The job posting to be formatted.

        Returns:
            dict: The formatted job posting.
        """
        compensation, employment_type = self.format_salary_info(job["salary_info"])
        tags = []
        if compensation:
            tags.append({"name": "compensation", "value": compensation})
        if employment_type:
            tags.append({"name": "employment_type", "value": employment_type})
        return {
            "name": job["name"],
            "agent_key": None,
            "reference": job["url"],
            "url": job["url"],
            "created_at": self.get_job_creation_date(job["creation_date"], job["saved_date"]).isoformat(),
            "updated_at": None,
            "summary": job["summary"],
            "location": {"text": job["location"], "lat": None, "lng": None},
            "sections": [
                {"name": "description", "title": "Description", "description": job["description"]},
            ],
            "skills": [],
            "languages": [],
            "tags": tags,
            "ranges_date": [],
            "ranges_float": [],
            "metadatas": [],
        }

    @staticmethod
    def format_skills(text: str, ents: dict) -> list:
        """
        Extract and format the skills from a job description text.

        Args:
            text (str): The job description text.
            ents (list): The entities extracted from the job description text.

        Returns:
            list: A list of dictionaries representing the formatted skills.
        """
        skills = [
            {
                "name": text[ent["start"] : ent["end"]].lower(),
                "value": None,
                "type": "hard" if ent["label"] == "skill_hard" else "soft",
            }
            for ent in ents
            if ent["label"].startswith("skill")
        ]
        return list({v["name"]: v for v in skills}.values())

    def index_jobs(self) -> None:
        """
        Index the job postings to the Hrflow API.
        """
        urls_saved = self.get_urls_saved_in_the_board()
        for job in self.jobs:
            if job["url"] in urls_saved:
                continue
            try:
                formatted_job = self.format_job(job)
                job_parsing = client.document.parsing.post(text=job["description"]).get("data")
                formatted_job["skills"] = self.format_skills(job["description"], job_parsing["ents"])
                client.job.indexing.add_json(board_key=BOARD_KEY, job_json=formatted_job)
                self.jobs_to_save.append(job)
                print("saved job", job["url"])
            except Exception as e:
                print("error", e)
                continue

    @staticmethod
    def get_urls_saved_in_the_board() -> set:
        """
        Get the URLs of the jobs that have already been saved in the board.

        This method uses the requests library to send a GET request to the Hrflow API. This is because the Hrflow client
        does not currently support a method for loading the existing jobs in a board.

        Returns:
            set: A set of URLs of the jobs that have already been saved in the board.
        """
        url = f'https://api.hrflow.ai/v1/storing/jobs?board_keys=["{BOARD_KEY}"]'
        response = requests.get(url, headers=HEADERS)
        return {e["reference"] for e in response.json()["data"]}

    def dump_saved_jobs(self) -> None:
        """
        Save the jobs that have been successfully indexed to a JSON file.
        """
        with open(self.saved_jobs_path, "a") as f:
            dump(self.jobs_to_save, f, indent=4)


if __name__ == "__main__":
    """The main script."""

    jobs_path = r"C:\Users\admin\PycharmProjects\hrflow_crawler\complete_data\all_jobs.json"
    saved_jobs_path = r"C:\Users\admin\PycharmProjects\hrflow_crawler\complete_data\all_saved_jobs.json"
    job_indexer = JobIndexer(jobs_path, saved_jobs_path)
    job_indexer.load_jobs()
    job_indexer.index_jobs()
    job_indexer.dump_saved_jobs()
