import json
from collections import defaultdict
import os

def update_feature_frequency(freq_dict, feature, current_depth, max_depth):
    if current_depth > max_depth:
        return
    
    if isinstance(feature, list):
        for item in feature:
            update_feature_frequency(freq_dict, item, current_depth + 1, max_depth)
    elif isinstance(feature, dict):
        for key, value in feature.items():
            if not isinstance(freq_dict[key], defaultdict):
                freq_dict[key] = defaultdict(int)
            update_feature_frequency(freq_dict[key], value, current_depth + 1, max_depth)
    else:
        if not isinstance(freq_dict, defaultdict):
            freq_dict[feature] += 1
        else:
            if not isinstance(freq_dict[feature], int):
                freq_dict[feature] = 0
            freq_dict[feature] += 1


def sort_feature_frequency(freq_dict):
    if isinstance(freq_dict, defaultdict):
        for key in freq_dict:
            if isinstance(freq_dict[key], defaultdict):
                freq_dict[key] = sort_feature_frequency(freq_dict[key])
        return dict(sorted(freq_dict.items(), key=custom_compare, reverse=True))
    else:
        return freq_dict

def custom_compare(item):
    key, value = item
    if isinstance(value, dict):
        return (1, )
    return (0, value)

def get_feature_frequency(input_file, output_file, max_depth):
    with open(input_file, 'r') as f:
        data = json.load(f)

    feature_frequency = defaultdict(lambda: defaultdict(int))

    skip_features = ["summary", "purpose", "issues & bugs", "potential scenario"]

    for entry in data:
        features = entry.get("features", {})
        for key, value in features.items():
            if key in skip_features:
                continue
            if key not in feature_frequency:
                feature_frequency[key] = defaultdict(int)
            update_feature_frequency(feature_frequency[key], value, 1, max_depth)

    sorted_feature_frequency = sort_feature_frequency(feature_frequency)

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, 'w') as f:
        json.dump(feature_frequency, f, indent=4)

def prune_to_top_n(freq_dict, n, dict_min_size=5):
    if isinstance(freq_dict, dict):
        for key in list(freq_dict.keys()):
            if isinstance(freq_dict[key], dict):
                if len(freq_dict[key])<dict_min_size:
                    freq_dict[key]=len(freq_dict[key])
                freq_dict[key] = prune_to_top_n(freq_dict[key], n)
        sorted_items = dict(sorted(freq_dict.items(), key=custom_compare, reverse=True)[:n])
        return sorted_items
    return freq_dict

def keep_top_n(input_file, output_file, n, dict_min_size):
    with open(input_file, 'r') as f:
        data = json.load(f)

    pruned_data = {}
    for key in data:
        pruned_data[key] = prune_to_top_n(data[key], n, dict_min_size=dict_min_size)

    with open(output_file, 'w') as f:
        json.dump(pruned_data, f, indent=4)


if __name__ == "__main__":
    input_file = 'output/extract/TheStack_V2/Python_clustered/prompt12/features/extract_0-10.json'

    if input_file.endswith("jsonl"):
        jsonl2json(input_file, input_file.replace('.jsonl','.json'))
        input_file=input_file.replace('.jsonl','.json')
    output_file = input_file.replace(".json","_frequency.json").replace("features","statistics")
    max_depth = 3
    n=50
    dict_min_size=3
    pruned_output_file = input_file.replace(".json",f"_frequency_depth{max_depth}_dict{dict_min_size}_top{n}.json").replace("features","statistics")
    get_feature_frequency(input_file, output_file, max_depth)
    keep_top_n(output_file, pruned_output_file, n=n, dict_min_size=dict_min_size)