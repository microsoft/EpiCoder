import os
import json
import random
import numpy as np
from typing import Dict, List
from utils.tree import remove_frequency, sample_feature_tree_with_frequency, remove_keys, keep_keys, sample_strings_from_dict
from utils.file_operation import sort_jsonl_file, jsonl2json
import concurrent.futures
import threading

lock = threading.Lock()

from call_api_local.call_api import call_gpt4
seed=42
random.seed(seed)
np.random.seed(seed)

def get_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def extract_fields_from_formatted_text(text):
    """
    Extracts fields from a formatted text.

    Parameters:
    - text (str): Multiline string containing the formatted text.

    Returns:
    - dict: A dictionary.
    """
    import re
    f_start = text.find("<f>") + len("<f>")
    f_end = text.find("</f>")
    s_start = text.find("<s>") + len("<s>")
    s_end = text.find("</s>")
    i_start = text.find("<i>") + len("<i>")
    i_end = text.find("</i>")
    t_start = text.find("<t>") + len("<t>")
    t_end = text.find("</t>")

    f_string = text[f_start:f_end].strip()
    s_string = text[s_start:s_end].strip()
    i_string = text[i_start:i_end].strip()
    t_string = text[t_start:t_end].strip()
    if -1 in [f_start,f_end,s_start,s_end,i_start,i_end,t_start,t_end]:
        s_string=""
        i_string=""
        i_string=""
        t_string=""

    data = {"selected features": f_string,
            "scenario": s_string,
            "task": t_string,
            "instruction": i_string}
    return data


def generate(features,mandatory_features,base_prompt,model='gpt-4', client_idx=None):
    prompt = base_prompt.format_map({"optional_features": str(features), "mandatory_features": str(mandatory_features)})

    output = call_gpt4(prompt,model=model,client_idx=client_idx)[0]
    return extract_fields_from_formatted_text(output)

def extract_file_name(file_path):

    file_name_with_extension = os.path.basename(file_path)
    file_name, _ = os.path.splitext(file_name_with_extension)
    return file_name

def generate_with_retry(features, mandatory_features, base_prompt, model, idx, output_path):
    try:
        result = generate(features, mandatory_features, base_prompt, model=model)
        print(f"result idx={idx}: {result}")
    except Exception as e:
        print(f"error in {idx}: {e}")
        result = generate(features, mandatory_features, base_prompt, model=model)
    result['features'] = features
    result['mandatory_features'] = mandatory_features
    result['idx'] = idx
    # result = OrderedDict([('idx', i)] + [(k, v) for k, v in result.items() if k != 'idx'])
    with lock:
        
        with open(output_path, 'a', encoding='utf-8') as f:
            json.dump(result, f)
            f.write('\n')
        print(f"save {idx}")
        if idx%100==0:
            sort_jsonl_file(output_path)

    return result


if __name__ == "__main__":

    language="Python"
    extract_prompt_idx=10
    gen_q_idx=5
    feature_file=f"output/feature_evol/TheStack_V2/Python_clustered/prompt8/gpt-4o/extract_0-10_frequency_depth3_dict3_top50_fea_extract12/seed42-step0-10_merged_fea_ori.json"
    feature_file_name=extract_file_name(feature_file)
    frequency_file=f"output/feature_evol/TheStack_V2/Python_clustered/prompt8/gpt-4o/extract_0-10_frequency_depth3_dict3_top50_fea_extract12/seed42-step0-10_merged_fea_ori_fre.json"
    conditions=[5,2,1,1]
    fix_num=2
    base_prompt_file=f"prompt/gen_question/prompt{gen_q_idx}"
    base_prompt=get_text(base_prompt_file)
    temperature=10
    output_dir=f"output/gen_question/TheStack_V2/Python_clustered/prompt{gen_q_idx}/gpt-4/fix{fix_num}/{feature_file_name}_extract{extract_prompt_idx}_fre_t{temperature}"
    print(output_dir)
    model='gpt-4o'
    fixed_features=['computation operation']
    # fixed_features=None
    begin_idx=0
    end_idx=10
    output_path=f"{output_dir}/seed{seed}-step{begin_idx}-{end_idx}.jsonl"

    result=[]
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(feature_file, 'r') as f:
        feature_tree = json.load(f)
    with open(frequency_file, 'r') as f:
        frequencies = json.load(f)

    keep_features_lang={
        "Python":['workflow','implementation style', 'functionality','resource usage','computation operation',
                                           'user interaction','data processing','file operation','dependency relations',
                                           'algorithm',"data structures"],
        "Java":['workflow','implementation style', 'functionality','resource usage','computation operation',
                                           'user interaction','data processing','file operation',
                                           'algorithm',"data structures"],
        "Csharp":['workflow','implementation style', 'functionality','resource usage','computation operation',"graphics rendering",
                                           'user interaction','data processing','file operation','dependency relations',
                                           'algorithm',"data structures"],
        "C++":['workflow','implementation style', 'functionality','resource usage','computation operation',
                                           'user interaction','data processing','file operation',
                                           'algorithm',"data structures"],
    }

    keep_features=keep_features_lang[language]
    feature_tree=keep_keys(feature_tree,keep_features)
    
    all_features = []
    all_mandatory_features = []

    for i in range(end_idx+1):
        print(i)
        features = sample_feature_tree_with_frequency(feature_tree, conditions, frequencies=frequencies, fixed_features=fixed_features, temperature=temperature)
        mandatory_features = sample_strings_from_dict(features, n=fix_num)
        if i<begin_idx:
            continue
        features["programming language"] = language

        all_features.append((features, i))
        all_mandatory_features.append((mandatory_features, i))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_with_retry, features, mandatory_features, base_prompt, model, i, output_path) for (features, i), (mandatory_features, _) in zip(all_features, all_mandatory_features)]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            future.result()
    
    sort_jsonl_file(output_path)
    jsonl2json(output_path,output_path.replace('.jsonl','.json'))
