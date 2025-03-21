import os

from openai import AzureOpenAI

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

import time

import re

from datetime import datetime

from azure.keyvault.secrets import SecretClient   # pip install azure-keyvault-secrets

import logging

import hmac

import hashlib

import time

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_secret():

    key_vault_url = "https://code-model.vault.azure.net/"

    # Create a DefaultAzureCredential object for authentication

    credential = DefaultAzureCredential(additionally_allowed_tenants=["*"])

    # Create a SecretClient object to interact with Key Vault

    client = SecretClient(vault_url=key_vault_url, credential=credential)

    # Replace with your secret name

    secret_name = "gh-gpt4o-endpoint-secret"

    # Retrieve the secret

    retrieved_secret = client.get_secret(secret_name)

    return retrieved_secret.value

secret = get_secret().encode("utf-8")


def call_gh_endpoint(messages, model="gpt-4o", n=1, max_retry=500):

    hmac_key = secret # replace with secret key

    current = str(int(time.time()))

    hmac_value = hmac.new(hmac_key, current.encode('utf8'), hashlib.sha256).hexdigest()

    request_hmac = f'{current}.{hmac_value}'

    endpoint = "https://api.githubcopilot.com/chat/completions"

    headers = {

        "Content-Type": "application/json",

        "Accept": "application/json",

        "Copilot-Integration-Id": "code-specific-models-eval",

        "Request-HMAC": request_hmac,

    }

    body = {

        "model": model,

        "messages": messages,

        "temperature": 0.7,
        
        "top_p": 0.95
    }

    res = ['error'] * n

    for i in range(max_retry):

        try:

            response = requests.post(endpoint, json=body, headers=headers)

            if response.status_code == 200:

                choices = response.json()["choices"]

                res = [choice["message"]["content"] for choice in choices]

                if res[0] is None and i==0:

                    logging.warning(f"none error:\nmessages={messages}\nresponse={response}")

                    continue

                return res[0], response.json()


        except Exception as e:

            # Get the current system time

            current_time = datetime.now()       

            logging.info(">" * 5, f"current time {current_time}")

            logging.error(">" * 5, f"LLMs error `{e}`")
            if response.status_code == 429:

                logging.warning("too many requests sent. Will sleep 5secs.")

                time.sleep(3)

                continue

            else:

                logging.warning(f"request error: {response.status_code}, {response.text}")

                if "prompt token limit exceeded" in response.text:

                    return "prompt too long", "prompt too long"

                if response.status_code == 422:

                    return "error", "Unprocessable Entity"

            if "repetitive patterns" in str(e):

                messages[-1]['content']=shorten_repeated_substrings(messages[-1]['content'])

            # print(">>",f"response.text: {response}")

            time.sleep(3 * (2 ** (i + 1)))

            res = ['error'] * n

            if str(e) in ["'content'"]:

                break

    logging.error("failed to call gh endpoint")

    return 'error', str(response)


model2deployment={

    "gpt-4":"tscience-uks-gpt4-1106",

    "gpt-4o":"tscience-uks-gpt-4o"

}

token_provider = get_bearer_token_provider(

    DefaultAzureCredential(managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID")),

    "https://cognitiveservices.azure.com/.default")

client = AzureOpenAI(

    azure_endpoint="https://aims-oai-research-inference-uks.openai.azure.com/",

    azure_ad_token_provider=token_provider,

    api_version="2024-05-01-preview",

)

def shorten_repeated_substrings(s: str) -> str:

    def replacer(match):

        substring = match.group(1)

        count = len(match.group(0).split(substring)) - 1

        return f"{substring}, {substring}, {substring}...{count} times"

    # Use regex to find repeated substrings separated by comma and space

    pattern = re.compile(r"((?:'\w+'|\"\w+\"|\b\w+\b))(, \1){20,}")

    return pattern.sub(replacer, s)

def call_gpt4(messages, model='gpt-4o',client_idx=None):
    if isinstance(messages, str):
        messages=messages= [{
            "role": "user",
            "content": messages,
        }]
    #return my_chat_api(messages=messages,client=client,model=model2deployment[model])
    # print(f"messages={messages}")
    return call_gh_endpoint(messages=messages)


print(
    call_gpt4(
        messages= [{
            "role": "user",
            "content": "hello",
        }],
        model='gpt-4o-mini' # or gpt-4o
    )
)