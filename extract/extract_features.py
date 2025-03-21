import sys
import os
from datasets import load_dataset
from call_api_local.call_api import call_gpt4
import random
import json
import concurrent.futures
import json
import os
import threading
from datetime import datetime
from utils.file_operation import jsonl2json, sort_jsonl_file



lock = threading.Lock()
random.seed(0)
def get_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def get_full_content(d):
    keys=["full_content", "instruction", "output", "prompt", "text", "code"]
    content=""
    for k in keys:
        if k in d.keys():
            content+=str(d[k])
    return content

def get_data_from_file(file_path):
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data=json.load(f)
    elif file_path.endswith('.jsonl'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line.strip()) for line in f]
    for d in data:
        d["full_content"]=get_full_content(d)
    return data

# def get_data_from_file(file_path):
#     data = []
#     with open(file_path, 'r', encoding='utf-8') as f:
#         for line in f:
#             json_line = json.loads(line.strip())
#             keys_to_keep = ["full_content"]
#             filtered_data = {key: json_line[key] for key in keys_to_keep if key in json_line}
#             data.append(filtered_data)
#     return data


def get_source_data(file_paths):
    data = []
    for file_path in file_paths:
        data.extend(get_data_from_file(file_path))
    return data


def extract_fields_from_formatted_text(text):
    """
    Extracts fields from a formatted text.

    Parameters:
    - text (str): Multiline string containing the formatted text.

    Returns:
    - dict: A dictionary where each key is a category name and the value is a list of items extracted from that category.
    """
    import re

    json_start = text.find("<begin>") + len("<begin>")
    json_end = text.find("<end>")
    json_string = text[json_start:json_end].strip()
    json_string = json_string.replace("\n", "").replace("\r", "")
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(e)
        data = {"parse_error_str": json_string}

    return data


def extract_single_feature(d, idx, base_prompt, save_path):
    try:
        code = d["full_content"]
        prompt = base_prompt.replace("{source_code}", code)
        output, response = call_gpt4(prompt, model='gpt-4')

        if idx < 10:
            print(f"prompt=\n{prompt}")
            print(f"output=\n{output}")

        extract_output = extract_fields_from_formatted_text(output)
        assert len(extract_output) > 0, f"Extract output failed. Output: {output}"

        with lock:
            partial_data = {
                "idx": idx,
                "original_code": code,
                "features": extract_output
            }
            with open(save_path, 'a', encoding='utf-8') as file:
                json.dump(partial_data, file)
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
        return partial_data
    except Exception as e:
        print(f"Error processing idx {idx}: {e}")
        return None


def extract_features(base_prompt, seed_data_paths, end_idx, output_dir='./output',begin_idx=0):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    dataset = get_source_data(seed_data_paths)
    save_path = f"{output_dir}/extract_{begin_idx}-{end_idx}.jsonl"
    ext_data = []
    print(f"end_idx={end_idx}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, d in enumerate(dataset):
            if i < begin_idx:
                continue
            if i >= end_idx:
                break
            print(f"submit{i}")
            futures.append(executor.submit(extract_single_feature, d, i, base_prompt, save_path))

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if result:
                ext_data.append(result)
    sort_jsonl_file(save_path)
    jsonl2json(save_path)


if __name__ == "__main__":
    root_dir=""
    prompt_idx=12
    prompt_file=f"{root_dir}/prompt/extract/prompt{prompt_idx}.txt"
    base_prompt=get_text(prompt_file)
    seed_data_paths=[
        'cluster/example/core_set_py0.jsonl'
    ]
    data_name='TheStack_V2/Python_clustered'
    output_dir=f'{root_dir}/output/extract/{data_name}/prompt{prompt_idx}/features'
    os.makedirs(output_dir,exist_ok=True)
    extract_features(base_prompt=base_prompt,seed_data_paths=seed_data_paths, end_idx=10,
                     output_dir=output_dir,
                     begin_idx=0)