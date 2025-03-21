import os
import json
import random
from typing import Dict, List
import concurrent.futures
from call_api_local.call_api import call_gpt4
from utils.file_operation import sort_jsonl_file,jsonl2json
import threading
import numpy as np
from utils.tree import merge_dicts, sample_feature_tree_with_frequency, count_descendant, generate_all_keys
lock = threading.Lock()

seed=42
random.seed(seed)
np.random.seed(seed)


def get_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


t1=\
{
    "algorithm": {
        "sorting": ["quick sort", "merge sort"],
        "tree traversal": ["in-order traversal"]
    },
    "data processing": [
        "data transformation",
        "data cleaning"
    ]
}
t2=\
{
    "algorithm": {
        "sorting": {
            "quick sort": ["3-way quick sort", "dual-pivot quick sort"], 
            "merge sort": ["top-down merge sort", "bottom-up merge sort"], 
            "heap sort":[]
        },
        "tree traversal": {
            "in-order traversal": ["recursive in-order traversal", "iterative in-order traversal"],
            "pre-order traversal":[],
            "post-order traversal":[],
            "level-order traversal":[],
        }
    },
    "data processing": {
        "data transformation": [
            "string manipulation", 
            "convert to integer",
            "split string"
        ],
        "data cleaning": [
            "reset DataFrame index", 
            "drop zero columns",
            "remove duplicates"
        ]
    }
}


base_prompt = """\
Feature Tree Evolution Task:
You are provided with a feature tree represented as a nested JSON structure. Each node in this tree represents a feature or a sub-feature of a software system, with the leaves being the most specific features. Your task is to expand this feature tree both in depth and breadth.
Depth expansion means adding more specific sub-features to existing leaves.
Breadth expnasion means adding more sibling features at the current levels.

Here are some explanations of the features:
{explanations}

The input feature tree will be provided in JSON format, and your output should be a JSON structure that represents the expanded feature tree.

Output Format:
- Expanded Feature Tree: Provide the expanded feature tree as a JSON structure. Surround the json with <begin> and <end>.

Input Feature Tree Example:
{
    "algorithm": {
        "sorting": ["quick sort", "merge sort"],
        "tree traversal": ["in-order traversal"]
    },
    "data processing": [
        "data transformation",
        "data cleaning"
    ]
}

Expanded Feature Tree Example:
<begin>
{
    "algorithm": {
        "sorting": {
            "quick sort": ["3-way quick sort", "dual-pivot quick sort"], 
            "merge sort": ["top-down merge sort", "bottom-up merge sort"], 
            "heap sort":[]
        },
        "tree traversal": {
            "in-order traversal": ["recursive in-order traversal", "iterative in-order traversal"],
            "pre-order traversal":[],
            "post-order traversal":[],
            "level-order traversal":[],
        }
    },
    "data processing": {
        "data transformation": [
            "string manipulation", 
            "convert to integer",
            "split string"
        ],
        "data cleaning": [
            "reset DataFrame index", 
            "drop zero columns",
            "remove duplicates"
        ]
    }
}
<end>


Constraints:
1. For breadth expansion, add at least 2 new sibling features to each existing node.
2. For deep expansion, you need to add new sub-features to it, provided that you think the current leaf node has a more fine-grained feature.
3. Focus on generating new and innovative features that are not present in the provided examples.
Please follow the above constraints and expand the feature tree accordingly.

Input:
{features}

Output:
<begin>expanded feature tree<end>
"""



def form_feature_explanation(feature_list):
    feature_explanation = {
        "workflow": "Outline the main steps and operations the code performs.",
        "functionality": "Explain the function of the code.",
        "resource usage": "Analyze how the code utilizes system resources.",
        "computation operation": "Describe the computation operations used, including subcategories such as mathematical operations, algorithmic operations, and statistical operations.",
        "user interaction": "Describe the code related to user interaction, including subcategories such as user input, UI components, and display methods.",
        "data processing": "Describe how the data is processed, including subcategories such as data preparation, data retrieval, data transformation, and data validation.",
        "file operation": "Describe the file operations used.",
        "dependency relations": "Describe any external libraries or services the code depends on, including full library names.",
        "algorithm": "Identify the specific algorithm or method being used in the code.",
        "advanced techniques": "Specify any sophisticated algorithms or methods applied."
    }
    
    result = []
    for feature in feature_list:
        if feature in feature_explanation:
            if feature in feature_explanation:
                result.append(f"{feature}: {feature_explanation[feature]}")
    
    return "\n".join(result)



def remove_keys(d, keys_to_remove):
    for key in keys_to_remove:
        d.pop(key, None)
    return d

def keep_keys(d, keys_to_keep):
    return {key: d[key] for key in keys_to_keep if key in d}


def extract_fields_from_formatted_text(text):
    """
    Extracts fields from a formatted text.

    Parameters:
    - text (str): Multiline string containing the formatted text.

    Returns:
    - dict: A dictionary where each key is a category name and the value is a list of items extracted from that category.
    """

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


def generate(features:dict, base_prompt_file:str, model='gpt-4o'):
    explanations=form_feature_explanation(features.keys())
    base_prompt=get_text(base_prompt_file)
    prompt = base_prompt.replace("{features}", str(features))
    prompt = prompt.replace("{explanations}", str(explanations))
    output = call_gpt4(prompt,model=model)[0]
    return extract_fields_from_formatted_text(output)


def extract_file_name(file_path):
    file_name_with_extension = os.path.basename(file_path)
    file_name, _ = os.path.splitext(file_name_with_extension)
    return file_name


def evol(features, base_prompt_file, model, idx, output_path):
    result={"expanded feature": generate(features, base_prompt_file, model=model)}
    result['features']=features
    result['idx'] = idx

    with lock:
        with open(output_path, 'a', encoding='utf-8') as f:
            json.dump(result, f)
            f.write('\n')
        print(f"save {idx}")
        if idx%100==0:
            sort_jsonl_file(output_path)
    
    return result


def evol_steps(begin_idx, end_idx, language, desc_count, base_prompt_file, feature_file, conditions, output_dir, output_path, model):
    
    keep_features_lang={
        "Python":['workflow', 'functionality','resource usage','computation operation',
                                           'user interaction','data processing','file operation','dependency relations',
                                           'algorithm','advanced techniques'],
        "Csharp":['workflow', 'functionality','resource usage','data processing','computation operation',"graphics rendering",
                                           'user interaction','file operation','dependency relations',
                                           'algorithm','advanced techniques']
    }
    keep_features=keep_features_lang[language]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(feature_file, 'r') as f:
        full_features = json.load(f)
    full_features=keep_keys(full_features,keep_features)
    all_features = []

    all_keys = generate_all_keys(full_features)
    node_count = {key: 0 for key in all_keys}

    for i in range(end_idx+1):
        print(i)
        features=sample_feature_tree_with_frequency(full_features, conditions=conditions, frequencies=desc_count, frequency_key="descendant_count")

        if i<begin_idx:
            continue
        print(features)
        all_features.append((features, i))
        sampled_keys = generate_all_keys(features)
        for key in sampled_keys:
            if key in node_count:
                node_count[key] += 1

    sample_count_file=os.path.join(output_dir, f"sample_count_{begin_idx}_{end_idx}.json")
    
    with open(sample_count_file, 'w') as outfile:
        json.dump(node_count, outfile, indent=4)

    total_nodes = len(node_count)
    nodes_with_count = sum(1 for count in node_count.values() if count > 2)
    
    print(f"Total nodes: {total_nodes}")
    print(f"Nodes with count > 2: {nodes_with_count}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(evol, features, base_prompt_file, model, i, output_path) for features, i in all_features]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            future.result()
    
    sort_jsonl_file(output_path)
    jsonl2json(output_path,output_path.replace(".jsonl",".json"))


def main():
    
    extract_prompt_idx=12
    feature_evol_idx=8
    language="Python"
    # iter1
    feature_file="output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50_fea.json"
    fre_file="output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50_fre.json"
    desc_file="output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50_desc.json"
    feature_file_name=extract_file_name(feature_file)
    descendant_count=count_descendant(fre_file, desc_file)
    begin_idx=0
    end_idx=10
    conditions=[2,1,2,1]
    base_prompt_file=f"prompt/feature_evol/prompt{feature_evol_idx}"
    model='gpt-4o'
    output_dir=f"output/feature_evol/TheStack_V2/Python_clustered/prompt{feature_evol_idx}/{model}/{feature_file_name}_extract{extract_prompt_idx}"
    print(output_dir)
    output_path=f"{output_dir}/seed{seed}-step{begin_idx}-{end_idx}.jsonl"
    evol_steps(begin_idx, end_idx, language, descendant_count, base_prompt_file, feature_file, conditions, output_dir, output_path, model)


if __name__ == "__main__":
    main()