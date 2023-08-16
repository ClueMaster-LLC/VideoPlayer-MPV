import time
import os
import json
import requests
from string import Template
from apis import *
from requests.structures import CaseInsensitiveDict

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MASTER_DIRECTORY = os.path.join(os.environ.get("HOME"), "CluemasterDisplay")


class GenerateNewToken:
    def __init__(self):
        # global variables
        self.master_device_id = None

        # instance methods
        self.master_method()

    def master_method(self):
        # fetch existing device id from unique_code.json file. ** DO NOT DELETE DEVICE ID or the file itself
        # update status of CreatingNewAPIToken
        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["CreatingNewAPIToken"] = True

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)
        except:
            print("Error while updating thread info file from create_new_api_token.py")

        # reading device unique code
        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json"), "r") as unique_code_json_file:
            self.json_raw_data = json.load(unique_code_json_file)
            self.master_device_id = self.json_raw_data["Device Unique Code"]

        self.generate_new_api_token()

    def generate_new_api_token(self):
        while True:
            try:
                authentication_api_url = GENERATE_API_TOKEN_API

                headers = CaseInsensitiveDict()
                headers["Content-Type"] = "application/json"
                initial_template = Template("""{"DeviceKey": "${device_key}", "Username": "ClueMasterAPI", "Password": "8BGIJh27uBtqBTb2%t*zho!z0nS62tq2pGN%24&5PS3D"}""")
                data = initial_template.substitute(device_key=self.master_device_id)

                response = requests.post(url=authentication_api_url, headers=headers, data=data).json()
                print(">>> Console output - Generate New API Token - ", response)
                api_key = response["apiKey"]

                self.json_raw_data["apiKey"] = api_key

                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json"), "w") as unique_code_json_file:
                    json.dump(self.json_raw_data, unique_code_json_file)

                return

            except requests.exceptions.ConnectionError:
                time.sleep(3)
                pass


