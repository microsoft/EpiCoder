import json
import random
import numpy as np
import os

def remove_keys(d, keys_to_remove):
    for key in keys_to_remove:
        d.pop(key, None)
    return d

def keep_keys(d, keys_to_keep):
    return {key: d[key] for key in keys_to_keep if key in d}


def remove_frequency(frequency_tree):
    def traverse_and_remove(tree):
        if isinstance(tree, dict):
            result_tree = {}
            for key, value in tree.items():
                if isinstance(value, int):
                    result_tree[key] = []
                elif isinstance(value, dict):
                    if all(isinstance(v, int) for v in value.values()):
                        result_tree[key] = list(value.keys())
                    else:
                        result_tree[key] = traverse_and_remove(value)
            return result_tree
        return tree

    return traverse_and_remove(frequency_tree)

def sample_feature_tree(feature_tree, conditions, fixed_features = None):

    def sample_subtree(tree, conditions, depth):
        if not isinstance(tree, (dict, list)) or depth > len(conditions):
            return tree

        num_samples = conditions[depth - 1] if depth - 1 < len(conditions) else len(tree)

        if isinstance(tree, dict):

            if fixed_features is not None and depth==1:
                fixed_keys = [key for key in fixed_features if key in tree]
                remaining_keys = [key for key in tree.keys() if key not in fixed_keys]
                num_samples -= len(fixed_keys)
                sampled_keys = fixed_keys + random.sample(remaining_keys, min(num_samples, len(remaining_keys)))
            else:
                sampled_keys = random.sample(list(tree.keys()), min(num_samples, len(tree)))
            sampled_tree = {}
            for key in sampled_keys:
                sampled_tree[key] = sample_subtree(tree[key], conditions, depth + 1)
        elif isinstance(tree, list):
            sampled_items = random.sample(tree, min(num_samples, len(tree)))
            sampled_tree = [sample_subtree(item, conditions, depth + 1) for item in sampled_items]

        return sampled_tree

    return sample_subtree(feature_tree, conditions, 1)



def count_descendant(fre_file, descendant_file, overwrite=False):
    print(f"counting")
    if os.path.exists(descendant_file) and not overwrite:
        with open(descendant_file, 'r') as f:
            count = json.load(f)
        return count

    with open(fre_file, 'r') as f:
        frequency = json.load(f)
    all_keys = frequency.keys()
    
    descendant_count = {}
    
    for key in all_keys:
        count = sum(1 for k in all_keys if k.startswith(key))
        descendant_count[key] = {'descendant_count': count}
    
    with open(descendant_file, 'w') as outfile:
        json.dump(descendant_count, outfile, indent=4)
    print(f"end")
    return descendant_count

def generate_all_keys(tree):
    def traverse_and_collect_keys(node, path):
        keys = []
        if isinstance(node, dict):

            for key, value in node.items():
                new_path = f"{path}---{key}" if path else key
                keys.append(new_path)  
                keys.extend(traverse_and_collect_keys(value, new_path)) 
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, str):
                    list_path = f"{path}---{item}"
                    keys.append(list_path)
                else:
                    keys.extend(traverse_and_collect_keys(item, path))
        elif isinstance(node, str):
            keys.append(f"{path}---{node}")
        return keys


    all_keys = traverse_and_collect_keys(tree, "")
    return all_keys



def get_all_strings(data):
    strings = []

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list) and len(value)==0:
                strings.append(key)
            else:
                strings.extend(get_all_strings(value))
    
    elif isinstance(data, list):
        if len(data)==0:
            raise Exception("error in get all strings")
        for item in data:
            strings.extend(get_all_strings(item))
    
    elif isinstance(data, str):
        strings.append(data)
    
    return strings

def sample_strings_from_dict(data, n=2):
    all_strings = get_all_strings(data)
    try:
        r= random.sample(all_strings, n)
    except Exception as e:
        print(f"Data={data}")
        print(e)
        raise e
    return r

def smooth_probs(probs, temperature=1.0):
    """
    Apply softmax with temperature to smooth the given probability distribution.
    
    Args:
    probs (list or np.array): List or array of probabilities to be smoothed.
    temperature (float): Temperature parameter to control the smoothness. Default is 1.0.
                         Higher values result in smoother distributions.
    
    Returns:
    np.array: Smoothed probability distribution.
    """
    if abs(temperature) >= 100:
        return np.ones_like(probs) / len(probs)

    probs = np.array(probs)

    logits = np.log(probs + 1e-9) / temperature 
    
    exp_logits = np.exp(logits)
    smooth_probs = exp_logits / np.sum(exp_logits)
    
    return smooth_probs



def count_descendant(fre_file, descendant_file):
    print(f"counting")
    if os.path.exists(descendant_file):
        with open(descendant_file, 'r') as f:
            count = json.load(f)
        return count

    with open(fre_file, 'r') as f:
        frequency = json.load(f)
    all_keys = frequency.keys()
    
    descendant_count = {}
    
    for key in all_keys:
        count = sum(1 for k in all_keys if k.startswith(key))
        descendant_count[key] = {'descendant_count': count}
    
    with open(descendant_file, 'w') as outfile:
        json.dump(descendant_count, outfile, indent=4)
    print(f"end")
    return descendant_count

def upweight_probs(features, probs, frequencies, upweight_factor=1):
    matching_indices = [i for i, feature in enumerate(features) if isinstance(feature, str) and frequencies.get(feature, {}).get("upweight", False)]
    N = len(matching_indices)
    
    if N > 0:
        for i in matching_indices:
            probs[i] += upweight_factor / N
    
    total_prob = sum(probs)
    upweighted_probs = [prob / total_prob for prob in probs]
    
    return upweighted_probs

def sample_feature_tree_with_frequency(feature_tree, conditions, frequencies, fixed_features=None, temperature=1, frequency_key="frequency", smooth_only_first=False, upweight=False, upweight_factor=1):
    def sample_subtree(tree, conditions, depth, path):
        if isinstance(temperature, list):
            cur_t=temperature[depth]
        else:
            cur_t=temperature

        if not isinstance(tree, (dict, list)) or depth > len(conditions):
            return tree
        if len(tree)==0:
                return []
        num_samples = conditions[depth - 1] if depth - 1 < len(conditions) else len(tree)

        if isinstance(tree, dict):
            if fixed_features is not None and depth == 1:
                fixed_keys = [key for key in fixed_features if key in tree]
                remaining_keys = [key for key in tree.keys() if key not in fixed_keys]
                num_samples -= len(fixed_keys)
                remaining_frequencies = [
                    frequencies.get(f"{path}---{key}" if path else key, {frequency_key: 1})[frequency_key]
                    for key in remaining_keys
                ]

                probs0=np.array(remaining_frequencies) / sum(remaining_frequencies)
                if depth==1 or not smooth_only_first:
                    probs=smooth_probs(probs0,temperature=cur_t)
                else:
                    probs=probs0 

                if upweight:
                    probs = upweight_probs(remaining_keys, probs, frequencies, upweight_factor)

                sampled_keys = fixed_keys + list(np.random.choice(
                    remaining_keys, 
                    size=min(num_samples, len(remaining_keys)), 
                    replace=False, 
                    p=probs
                ))
            else:
                keys = list(tree.keys())
                key_paths = [f"{path}---{key}" if path else key for key in keys]
                key_frequencies = [
                    frequencies.get(key_path, {frequency_key: 1})[frequency_key]
                    for key_path in key_paths
                ]
                probs0=np.array(key_frequencies) / sum(key_frequencies)
                if depth==1 or not smooth_only_first:
                    probs=smooth_probs(probs0,temperature=cur_t)
                else:
                    probs=probs0 

                if upweight:
                    probs = upweight_probs(keys, probs, frequencies, upweight_factor)

                sampled_keys = list(np.random.choice(
                    keys, 
                    size=min(num_samples, len(keys)), 
                    replace=False, 
                    p=probs
                ))
            sampled_tree = {}
            for key in sampled_keys:
                sampled_tree[key] = sample_subtree(tree[key], conditions, depth + 1, f"{path}---{key}" if path else key)
        elif isinstance(tree, list):
            if len(tree)==0:
                return []
            item_paths = [f"{path}---{item}" for item in tree]

            item_frequencies = [
                frequencies.get(item_path, {frequency_key: 1})[frequency_key]
                for item_path in item_paths
            ]

            probs0=np.array(item_frequencies) / sum(item_frequencies)
            if depth==1 or not smooth_only_first:
                probs=smooth_probs(probs0,temperature=cur_t)
            else:
                probs=probs0 

            if upweight:
                probs = upweight_probs(tree, probs, frequencies, upweight_factor)

            sampled_items = list(np.random.choice(
                tree, 
                size=min(num_samples, len(tree)), 
                replace=False, 
                p=probs
            ))

            sampled_tree = [sample_subtree(item, conditions, depth + 1, path) for item in sampled_items]
        return sampled_tree

    return sample_subtree(feature_tree, conditions, 1, "")

def recursive_deduplicate(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = recursive_deduplicate(value)
    elif isinstance(data, list):

        seen = set()
        result = []
        for item in data:
            item = recursive_deduplicate(item)
            if isinstance(item, list) or isinstance(item, dict):

                result.append(item)
            else:

                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result
    return data 

def merge_dicts(dict1, dict2, raise_e=False):
    def check_list(list_str):
        if isinstance(list_str, list):

            list_str=[s for s in list_str if isinstance(s, str)]
            return list_str
        return list_str
    try:
        merged_dict = dict1.copy() 
        for key, value in dict2.items():
            if key in merged_dict:
                value=check_list(value)
                merged_dict[key]=check_list(merged_dict[key])
                if isinstance(merged_dict[key], dict) and isinstance(value, dict):
                    merged_dict[key] = merge_dicts(merged_dict[key], value)
                elif isinstance(merged_dict[key], list) and isinstance(value, list):

                    merged_dict[key].extend(value)
                    merged_dict[key] = list(set(merged_dict[key]))
                elif isinstance(merged_dict[key], list) and isinstance(value, dict):
                    for item in merged_dict[key]:
                        if item not in value:
                            value[item] = []
                    merged_dict[key] = value
                elif isinstance(merged_dict[key], dict) and isinstance(value, list):
                    try:
                        for item in value:
                            if item not in merged_dict[key]:
                                merged_dict[key][item] = []
                    except Exception as e1:
                        print(e1)
                else:
                    raise ValueError(f"Unsupported types at key: {key}")
            else:
                merged_dict[key] = value
    except Exception as e:
        print(f"Exception occurred while merging dict1:\n\nwith dict2: {dict2}")
        if raise_e:
            raise e
    return merged_dict

def merge_frequencies(full_frequencies, new_node_frequencies):
    def update_avg_sub_frequency(path):
        parent_path = '---'.join(path.split('---')[:-1])
        siblings = [key for key in full_frequencies if key.startswith(parent_path + '---')]
        if siblings:
            avg_sub_frequency = sum(full_frequencies[sibling]['frequency'] for sibling in siblings) / len(siblings)
            if parent_path in full_frequencies:
                full_frequencies[parent_path]['avg_sub_frequency'] = avg_sub_frequency

    for key, value in new_node_frequencies.items():
        if key in full_frequencies:
            full_frequencies[key]['his_frequencies'].append(value['frequency'])
            full_frequencies[key]['frequency'] = sum(full_frequencies[key]['his_frequencies']) / len(full_frequencies[key]['his_frequencies'])
        else:
            full_frequencies[key] = value
        update_avg_sub_frequency(key)

    return full_frequencies
    

def calculate_all_frequency(frequency_tree):
    def traverse_and_calculate(tree, path):
        if isinstance(tree, dict):
            total_frequency = 0
            sub_frequencies = []
            for key, value in tree.items():
                new_path = f"{path}---{key}" if path else key
                if new_path not in all_frequencies:
                    all_frequencies[new_path] = {
                        'frequency': 0,
                        'his_frequencies': [],
                        'avg_sub_frequency': 1
                    }
                if isinstance(value, int):
                    all_frequencies[new_path]['frequency'] = value
                    all_frequencies[new_path]['his_frequencies'].append(value)
                    total_frequency += value
                    sub_frequencies.append(value)
                else:
                    subtree_frequency = traverse_and_calculate(value, new_path)
                    all_frequencies[new_path]['frequency'] = subtree_frequency
                    all_frequencies[new_path]['his_frequencies'].append(subtree_frequency)
                    total_frequency += subtree_frequency
                    sub_frequencies.append(subtree_frequency)
            avg_sub_frequency = sum(sub_frequencies) / len(sub_frequencies) if sub_frequencies else 1
            if path:
                all_frequencies[path]['avg_sub_frequency'] = avg_sub_frequency
            return total_frequency
        return 0

    all_frequencies = {}
    traverse_and_calculate(frequency_tree, "")
    return all_frequencies

def extract_sub_tree_frequencies(sub_tree, full_frequencies):
    def traverse_and_extract(tree, path):
        if isinstance(tree, dict):
            for key, value in tree.items():
                new_path = f"{path}---{key}" if path else key
                if new_path in full_frequencies:
                    sub_tree_frequencies[new_path] = full_frequencies[new_path]
                    traverse_and_extract(value, new_path)
        elif isinstance(tree, list):
            for item in tree:
                new_path = f"{path}---{item}" if path else item
                if new_path in full_frequencies:
                    sub_tree_frequencies[new_path] = full_frequencies[new_path]

    sub_tree_frequencies = {}
    traverse_and_extract(sub_tree, "")
    return sub_tree_frequencies

def get_new_node_frequencies(t1, t2, full_frequencies):
    new_node_frequencies = {}
    t1_frequencies = extract_sub_tree_frequencies(t1, full_frequencies)

    def calculate_new_node_frequency(node_path):
        parent_path = '---'.join(node_path.split('---')[:-1])
        siblings = [key for key in t1_frequencies if key.startswith(parent_path + '---') and key != node_path]
        if len(siblings) ==0:
            if parent_path in full_frequencies:
                parent_avg_sub_frequency = full_frequencies[parent_path]['avg_sub_frequency']
            else:
                parent_avg_sub_frequency = 1
            new_frequency = {
                'frequency': parent_avg_sub_frequency,
                'his_frequencies': [parent_avg_sub_frequency],
                'avg_sub_frequency': 1
            }
        else:
            avg_sibling_frequency = sum(t1_frequencies[sibling]['frequency'] for sibling in siblings) / len(siblings)
            new_frequency = {
                'frequency': avg_sibling_frequency,
                'his_frequencies': [avg_sibling_frequency],
                'avg_sub_frequency': 1
            }
        return new_frequency
    
    def traverse_and_find_new_nodes(tree, path, depth=1):
        if isinstance(tree, dict):
            for key, value in tree.items():
                new_path = f"{path}---{key}" if path else key
                if new_path not in t1_frequencies and depth>1:
                    new_node_frequencies[new_path] = calculate_new_node_frequency(new_path)
                traverse_and_find_new_nodes(value, new_path,depth=depth+1)
        elif isinstance(tree, list):
            for item in tree:
                new_path = f"{path}---{item}" if path else item
                if new_path not in t1_frequencies and depth>1:
                    new_node_frequencies[new_path] = calculate_new_node_frequency(new_path)

    traverse_and_find_new_nodes(t2, "")

    return new_node_frequencies

def replace_zeros_with_ones(data):
    """
    Recursively replace all values of 0 in 'frequency' and 'his_frequencies' with 1.
    """
    if isinstance(data, dict):
        if "frequency" in data and data["frequency"] == 0:
            data["frequency"] = 1
        if "his_frequencies" in data and isinstance(data["his_frequencies"], list):
            data["his_frequencies"] = [1 if freq == 0 else freq for freq in data["his_frequencies"]]
        for key, value in data.items():
            replace_zeros_with_ones(value)
    elif isinstance(data, list):
        for item in data:
            replace_zeros_with_ones(item)

def check_frequency_file(file_path):
    """
    Load the frequency file, check for 'frequency' and 'his_frequencies' equal to 0,
    replace them with 1, and save the modified file.
    """

    with open(file_path, 'r') as f:
        data = json.load(f)

    replace_zeros_with_ones(data)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
