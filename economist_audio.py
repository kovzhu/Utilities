import requests
import json
import os
import datetime
import glob
import subprocess
import pyperclip  # Install with: pip install pyperclip
from bs4 import BeautifulSoup
import urllib.parse
import tqdm


class EconomistsDownload:

    def __init__(self):
        print("Initializing EconomistsDownload")
        self.url = "https://github.com/hehonghui/awesome-english-ebooks/tree/master/01_economist"
        self.issue_folders = self.get_folders()
        self.new_folders = self.get_new_folders()
        self.page_url_head = "https://github.com/"
        self.download_url_head = "https://raw.githubusercontent.com"

    def save_audio(
        self, data, folder_name, create_separate_folder=False, from_pasteboard=False
    ):
        if from_pasteboard is True:
            data = self.get_pasteboard_data()
            data_js = json.loads(data)
        data_js = data
        if create_separate_folder is True:
            folder_name = self.create_economist_folder()

        for index, article in tqdm(
            enumerate(data_js), total=len(data_js), desc="Downloading"
        ):
            title = article["article"]
            audio_url = article["url"]
            audio = requests.get(audio_url)
            path = os.path.join(folder_name, f"{index}_{title}.mp3")
            with open(path, "wb") as f:
                f.write(audio.content)
        print("All audios downloaded.")

    def save_keys_to_file(self, keys, filename="folder_keys.json"):
        """Saves a list of keys to a JSON file."""
        try:
            with open(filename, "w") as f:
                json.dump(keys, f)
            print(f"Keys saved to '{filename}' successfully.")
        except OSError as e:
            print(f"Error saving keys to '{filename}': {e}")

    def load_keys_from_file(self, filename="folder_keys.json"):
        """Loads a list of keys from a JSON file."""
        try:
            with open(filename, "r") as f:
                keys = json.load(f)
            print(f"Keys loaded from '{filename}' successfully.")
            return keys
        except FileNotFoundError:
            print(f"File '{filename}' not found. Returning empty list.")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from '{filename}'. Returning empty list.")
            return []
        except OSError as e:
            print(f"Error loading keys from '{filename}': {e}")
            return []

    def get_new_folders(self):
        """
        Gets the new folders by comparing the keys from the website with the keys from the file.
        """
        filename = "folder_keys.json"
        old_keys = self.load_keys_from_file(filename)
        new_folders = []
        current_keys = [list(item.keys())[0] for item in self.issue_folders]
        for key in current_keys:
            if key not in old_keys:
                new_folders.append(
                    {key: [item[key] for item in self.issue_folders if key in item][0]}
                )
        self.save_keys_to_file(current_keys, filename)
        return new_folders

    def get_pasteboard_data(self):
        """Retrieves data from the macOS pasteboard (clipboard)."""

        try:
            # Method 1: Using pyperclip (cross-platform, but requires installation)
            data = pyperclip.paste()
            return data

        except pyperclip.PyperclipException:
            # Method 2: Using pbpaste (macOS specific, no external dependencies)
            try:
                process = subprocess.Popen(
                    ["pbpaste"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    return stdout
                else:
                    return None  # Or raise an exception, depending on your needs
            except FileNotFoundError:
                return None  # pbpaste not found

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def create_economist_folder(self, parent_folder=None, folder_name=None):
        """Creates a folder named "Economist + date" in the current directory."""

        if folder_name is None:
            today = datetime.date.today()
            date_string = today.strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
            folder_name = f"Economist audio {date_string}"
        if parent_folder is not None:
            folder_name = os.path.join(parent_folder, folder_name)

        try:
            os.makedirs(
                folder_name, exist_ok=True
            )  # Creates the folder, no error if it exists
            print(f"Folder '{folder_name}' created successfully.")
            return folder_name  # returns the folder name
        except OSError as e:
            print(f"Error creating folder '{folder_name}': {e}")
            return None  # returns None if there is an error.

    def get_folders(self, url=None):
        """
        Gets the folders from the website.
        """
        # url = "https://github.com/hehonghui/awesome-english-ebooks/tree/master/01_economist"
        # url_head = "https://raw.githubusercontent.com"
        if url is None:
            url = self.url
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            folder_links = soup.find_all("a", class_="Link--primary")
            folder_links = set(folder_links)

            folder_info = []
            for folder in folder_links:
                # print(f"folder['href']: {folder['href']}")
                # full_url = urllib.parse.urljoin("https://github.com/", folder["href"])
                full_url = folder["href"]
                # print(full_url)
                folder_info.append({folder.text.strip(): full_url})

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return folder_info

    def download_folder(self, audio=True):

        if len(self.new_folders) == 0:
            print("No new issues of Economist")
        else:
            print(f"There are {len(self.new_folders)} new issues")

        for issue in self.new_folders:
            key = list(issue.keys())[0]
            url = issue.get(key)
            url = urllib.parse.urljoin(self.page_url_head, url)
            self.create_economist_folder(folder_name=key)
            self.download_files_from_github(url=url, save_folder=key)

            print(issue.get(key))

            # download audio files
            if audio is True:
                # files = os.listdir('/key')
                try:
                    # Use glob to find JSON files in the folder.
                    json_file_name = glob.glob(os.path.join(key, "*.json"))[0]

                    print(f"the json file {json_file_name}")
                    if json_file_name:
                        folder = self.create_economist_folder(parent_folder=key)
                        # json_file_name = os.path.join(key, json_file_name)
                        print(json_file_name)
                        try:
                            with open(json_file_name, "r") as f:
                                json_file = json.load(f)
                            # print(f"json_file:{json_file}")
                        except:
                            print("json file read failure")
                        self.save_audio(folder_name=folder, data=json_file)

                except:
                    print("audio save failed")

    def download_files_from_github(self, url, save_folder):
        """Downloads all files from a GitHub directory to a specified folder."""

        file_list = self.get_folders(url=url)

        for file_info in file_list:
            for filename, file_url in file_info.items():
                try:
                    print(file_url)
                    # file_url = urllib.parse.urljoin(self.download_url_head, file_url)
                    file_url = self.generate_download_url(file_url)
                    response = requests.get(file_url)
                    # print(file_url)
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                    file_path = os.path.join(save_folder, filename)

                    with open(file_path, "wb") as f:
                        f.write(response.content)

                    print(f"Downloaded: {filename}")

                except requests.exceptions.RequestException as e:
                    print(f"Error downloading {filename}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred downloading {filename}: {e}")

    def update(self):
        if len(self.new_folders) > 0:
            self.download_folder(audio=True)

    def generate_download_url(self, relative_link):
        # def generate_raw_url(relative_link):
        """
        Generates a raw GitHub URL from a relative link.

        Args:
            relative_link (str): The relative GitHub link.

        Returns:
            str: The corresponding raw GitHub URL.
        """
        base_url = "https://raw.githubusercontent.com"
        raw_path = relative_link.replace("blob/", "")
        # Remove the leading slash if it exists
        # if raw_path.startswith('/'):
        #     raw_path = raw_path[1:]
        full_url = urllib.parse.urljoin(base_url, raw_path)
        return full_url


if __name__ == "__main__":
    Eco = EconomistsDownload()
    Eco.update()
    # Eco.get_folders()
