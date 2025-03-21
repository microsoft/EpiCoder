import openai
import json
import time
import http.client
from tqdm import tqdm
import requests
from multiprocessing import Process, Queue, current_process 
import random
import os
import re
import concurrent.futures
import threading
import logging

lock = threading.Lock()

from call_api_local.call_api import call_gpt4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


prompt_1 = '''\
Now that you are a code expert, I have provided you with the following steps to answer the question, please strictly follow the steps given below to answer the question given in the QUESTION.
Please answer the questions in each step strictly according to the input:

Step 1: Analyze the question and test cases
<your answer>
Step 2: Boundary Case Study
<your answer>
Step 3: Prerequisites
<your answer>
Step 4: Extra test cases and correctness analysis
<your answer>

During analysis, do not implement the code.

QUESTION:
{question}
'''

prompt_2 = '''\
Now that you are a code expert, I have provided you with the QUESTION and corresponding ANALYSIS to answer.
Complete the problem with awesome code logic and give a richly commented analysis in the code of your answer.
Include the necessary packages and test cases.

- QUESTION
{question}

- ANALYSIS
{analysis}

- Code implementation
Enclose the python code with ```python and ``` and enclose the file name with <file> and </file>.
For example,
<file>add.py</file>
```python
# add.py
# Code implementation here
def add(x, y):  
    return x + y  
```
- Test cases
The test code should be in a single file.
<file>test.py</file>
The following points should be noted when writing the test code:
The code will be executed directly without the ability to receive external feedback, such as user input or network messages, during execution.
If your test depends on external files, you should first generate these files in the code before running the tests. Ensure that the generated files are not too large or too numerous.
The test cases should be fully self-contained, meaning that all necessary inputs should be set within the code. Avoid any form of external input, and ensure the tests run successfully under these conditions. You can use unittest.mock.patch to simulate input if necessary.
```python
# test.py
from add import add
# Code implementation here
```
Remember to import the required packages in the code.

- File names in order and packages required. 
Answer file names and packages in json and wrap them in <json> and </json> tags, for example,
<json>{
    "file_names": ["add.py","test.py"],
    "packages": ["package1", "package2"]
}</json>
Please give the name of a package that can be installed using "pip install", such as "scikit-learn" instead of "sklearn".
Packages that do not need to be installed should not be given, such as "json".
'''


import json
import time
import requests
import ast
import openai

## openai==0.28.0


def extract_content(solution):
    packages, file_names, file_names_0, code_blocks = [], [], [], []

    # Extract JSON content
    json_match = re.search(r'<json>(.*?)</json>', solution, re.DOTALL)
    if json_match:
        try:
            content = json_match.group(1)
            data = json.loads(content)
            packages = data.get("packages", [])
            file_names_0 = data.get("file_names", [])
        except Exception as e:
            logging.error(e)
    
    # Extract file names and code blocks
    code_matches = re.findall(r'<file>(.*?)</file>\s*```python(.*?)```', solution, re.DOTALL)
    for file_name, code in code_matches:
        file_names.append(file_name.strip())
        code_blocks.append(code.strip())
    if len(file_names) != len(file_names_0):
        logging.error(f"file name mismatch\n{file_names}\n{file_names_0}")

    return packages, file_names, code_blocks

def make_request(
    message: str,
    question: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    model='gpt-4o',
    client_idx=None
):
    analysis = call_gpt4(message,model=model)[0]
    twice_input = prompt_2.replace("{question}",question).replace("{analysis}",analysis)
    solution = call_gpt4(twice_input,model=model,client_idx=client_idx)[0]
    logging.info(f"prompt={message}\nanalysis={analysis}\n\ntwice_input={twice_input}\n\nsolution={solution}\n\n")

    packages, file_names, code_blocks = extract_content(solution)
    
    return analysis, solution, packages, file_names, code_blocks


def save_code_files(save_dir, idx, file_names, code_blocks):
    try:
        for file_name, code in zip(file_names, code_blocks):
            file_path = f"{save_dir}/code/{idx}/{file_name}"
            file_dir = os.path.dirname(file_path)
            
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            
            with open(file_path, 'w', encoding='utf-8') as code_file:
                code_file.write(code)
        
        logging.info(f"Code files for task {idx} have been saved")
    except Exception as e:
        logging.error(f"save error {e}")

def get_question(item):
    # return item['task']
    return f"{item['instruction']} The detailed requirements are as follows: {item['task']}"

def process_single_task(task, idx, save_dir, save_path, model='gpt-4o', client_idx=None):
    try:
        question=get_question(task)
        input = prompt_1.format(question=question)
        analysis, solution, packages, file_names, code_blocks = make_request(input, question, model=model, client_idx=client_idx)
        content = {
            "idx": idx,
            "instruction": task['instruction'],
            "task": task['task'],
            "question": question,
            "analysis": analysis,
            "output": solution,
            "packages": packages,
            "file_names": file_names
        }

        code_dir = f"{save_dir}/code/{idx}"
        if os.path.exists(code_dir):
            return None

        with lock:
            with open(save_path, 'a+', encoding='utf-8') as file:
                json.dump(content, file)
                file.write('\n')

        
        
        if idx % 100 == 0:
            with lock:
                with open(save_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()

                data = [json.loads(line) for line in lines]
                sorted_data = sorted(data, key=lambda x: x['idx'])

                with open(save_path, 'w', encoding='utf-8') as file:
                    for entry in sorted_data:
                        json.dump(entry, file)
                        file.write('\n')


        save_code_files(save_dir, idx, file_names, code_blocks)
        return content

    except Exception as e:
        logging.error(f"error in idx {idx}:{e}")
        return None


def process_tasks(tasks, save_dir, begin_idx=0,end_idx=99999,model='gpt-4o',client_idx=None):
    save_path=f"{save_dir}/code_{begin_idx}_{end_idx}.jsonl"

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i, task in enumerate(tasks):
            if i < begin_idx:
                continue
            if i > end_idx:
                break
            logging.info(f"submit task {i}")
            futures.append(executor.submit(process_single_task, task, i, save_dir, save_path, model, client_idx))

        for future in concurrent.futures.as_completed(futures):
            future.result()  



def main():
    save_dir='output/gen_code/TheStack_V2/Python_clustered_150k/prompt5_fre_complex_tneg'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    json_file_path = 'output/gen_question/TheStack_V2/Python_clustered_150k/prompt5/gpt-4/fix2/seed42-step0-10_merged_fea_ori_extract10_fre_t10/seed42-step0-10.json'

    with open(json_file_path, 'r', encoding='utf-8') as file:
        sourcelist = json.load(file)
    sourcelist=sourcelist
    
    begin_idx=0
    end_idx=10

    process_tasks(sourcelist, save_dir, begin_idx=begin_idx, end_idx=end_idx, model="gpt-4o")

    logging.info("All tasks have been processed and written to file.")

if __name__ == '__main__':
    main()
