import base64
from concurrent.futures import ThreadPoolExecutor
import os
import queue
import sys
import itertools
import json
from pathlib import Path
import time
import requests
import hashlib
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from os.path import join, exists, getsize

LANG_EXT = {
    "python": "py",
    "python3": "py",
    "c": "c",
    "cpp": "cpp",
    "java": "java",
    "javascript": "js",
    "kotlin": "kt",
    "csharp": "cs",
    "rust": "rs",
    "swift": "swift",
    "golang": "go",
    "typescript": "ts",
    "scala": "sc",
    "dart": "dart",
    "php": "php",
    "ruby": "rb",
    "racket": "rkt",
}

class LcClient:
    def __init__(self, contest: str, ques_num: int, use_cache: bool = True) -> None:
        self.contest = contest
        self.ques_num = ques_num
        self.out_path = join(f"{contest}_Q{ques_num}")
        self.api_base = f"https://leetcode.com/contest/api"
        self.api_base_base = {
            "US": f"https://leetcode.com/api",
            "CN": f"https://leetcode.cn/api"
        }
        self.contest_base = f"{self.api_base}/ranking/{contest}"

        Path(self.out_path).mkdir(exist_ok=True, parents=True)
        self._driver_queue: queue.Queue = queue.Queue(8)
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        self.use_cache = use_cache

        # MySQL Connection Setup
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="DBMS@2560",
            database="leetcode_scraper"
        )
        self.cursor = self.db.cursor()

    def json_request(self, url):
        cache_dir = join("tmp", "cache2")
        Path(cache_dir).mkdir(exist_ok=True, parents=True)
        cache_file = join(cache_dir, hashlib.md5(url.encode('utf-8')).hexdigest() + ".json")
        
        if self.use_cache and exists(cache_file):
            with open(cache_file, encoding="utf8") as f:
                return json.load(f)

        try:
            driver = self._driver_queue.get_nowait()
        except queue.Empty:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

        delay = 0.5
        for attempt in itertools.count(1):
            try:
                print("Fetching url:", url)
                driver.get(url)
                content = driver.find_element(By.TAG_NAME, 'pre').text
                resp = json.loads(content)
                break
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                time.sleep(delay)
                delay *= 2
        
        # Recycle browser
        self._driver_queue.put_nowait(driver)

        time.sleep(0.1)
        with open(cache_file, 'w', encoding="utf8") as f:
            json.dump(resp, f, indent=4)
        
        return resp
    
    def fetch_contest_info(self):
        return self.json_request(f"{self.api_base}/info/{self.contest}")

    def fetch_submissions(self, pages: list[int]):
        Path(join(self.out_path, "submissions")).mkdir(exist_ok=True)

        for page in pages:
            data = self.json_request(f"{self.contest_base}/?pagination={page}&region=global")
            question_id = str(data["questions"][self.ques_num-1]["question_id"])

            submission_futures = []

            for user, submissions in zip(data["total_rank"], data["submissions"]):
                if question_id not in submissions:
                    submission_futures.append(None)
                    continue
                cont_subm = submissions[question_id]
                api_base = self.api_base_base.get(cont_subm['data_region'], self.api_base_base['US'])
                submission_futures.append(
                    self.thread_pool.submit(self.json_request, f"{api_base}/submissions/{cont_subm['submission_id']}/")
                )
            
            for user, submissions, submission_future in zip(data["total_rank"], data["submissions"], submission_futures):
                if submission_future is None:
                    continue
                cont_subm = submissions[question_id]
                submission = submission_future.result()
                # count=0
                if 'lang' not in submission:
                    print(f"❌ Missing 'lang' key in submission: {submission}")
                    # count+=1
                    print(submission)  # Print the full submission data

                    continue  # Skip this submission to prevent errors
                # print(count)
                lang_folder = LANG_EXT.get(submission.get('lang', "").lower(), "txt")  # ✅ Safe

                # lang_folder = LANG_EXT.get(submission['lang'], "txt")
                lang_path = join(self.out_path, "submissions", lang_folder)
                Path(lang_path).mkdir(exist_ok=True, parents=True)

                uname_encoded = base64.urlsafe_b64encode(user['username'].encode('utf-8')).decode()
                filename = f"{user.get('rank', 'unknown')}_b{uname_encoded}.{lang_folder}"

                print(filename)
                subm_path = join(lang_path, filename)
                content = submission['code'].encode('utf-8')

                if not exists(subm_path) or getsize(subm_path) != len(content):
                    with open(subm_path, "wb") as f:
                        f.write(content)

                # Insert into MySQL Database
                try:
                    # Ensure contest and question exist before inserting submission
                    self.cursor.execute(
                        "INSERT IGNORE INTO contests (contest_id, title) VALUES (%s, %s)",
                        (self.contest, f"Contest {self.contest}")
                    )
                    self.cursor.execute(
                        "INSERT IGNORE INTO questions (question_id, contest_id, question_number, title, difficulty) VALUES (%s, %s, %s, %s, %s)",
                        (question_id, self.contest, self.ques_num, f"Question {self.ques_num}", "Medium")
                    )
                    self.db.commit()

                    sql = """
                        INSERT INTO submissions (submission_id, question_id, rank_position, username, question_number, filename, language)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE filename=%s, language=%s;
                    """
                    values = (
                        cont_subm['submission_id'], 
                        question_id,  # Fixed: Now correctly assigns question_id
                        user.get('rank', None),
                        user['username'], 
                        self.ques_num,  # Ensure question_number is correctly assigned
                        filename, 
                        submission['lang'], 
                        filename, 
                        submission['lang']
                    )
                    self.cursor.execute(sql, values)
                    self.db.commit()
                    print(f"✅ Inserted submission {cont_subm['submission_id']} into DB.")

                except Exception as e:
                    print(f"❌ Error inserting into DB: {str(e)}")

        # Close DB connection
        self.cursor.close()
        self.db.close()

def main():
    client = LcClient(sys.argv[1], int(sys.argv[2]))
    client.fetch_submissions(range(1, 200))
    

if __name__ == "__main__":
    main()
