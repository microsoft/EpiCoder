import json
import os
import random
from call_api_local.call_api import call_gpt4

random.seed(42)

base_prompt = """\
The following are some features extracted from a large amount of code data. Please classify these features and divide them into several categories.
There is actually an inclusion relationship between these features. The coarse-grained category will contain multiple fine-grained categories. We can organize these features into a tree structure, and then we consider those closer to the root as good categories, such as running logic, function functionality. Try to find some such tree structures from these features.
Input:
{feature_data}

Please format the output as a JSON string representing a tree structure. Each node should be a dictionary, with keys as dimension names and values as either sub-dictionaries (for further classification) or lists (for features).
Note that the depth of the tree is arbitrary and can be deeper.
Also, please surround the json string with <begin> and <end>.
Here's an example format:
<begin>{
    "RootDimension": {
        "Dimension1": {
            "SubDimension1": ["feature1", "feature2"],
            "SubDimension2": ["feature3"]
        },
        "Dimension2": {
            "SubDimension3": ["feature4"],
            "SubDimension4": ["feature5", "feature6"]
        }
    }
}<end>
Output:
"""


def get_features(feature_freq_file):
    """
    Extract features from the feature frequency file.

    Parameters:
    - feature_freq_file (str): Path to the feature frequency JSON file.

    Returns:
    - list: A list of features.
    """
    with open(feature_freq_file, 'r') as f:
        feature_data = json.load(f)

    features = []
    for feature_list in feature_data.values():

        features.extend(feature_list.keys())
        
        for k in feature_list.keys():
            if isinstance(feature_list[k],dict):
                features.extend(feature_list[k].keys())

    return features


def get_tree(base_prompt, features, sample_num, step, output_dir, begin_idx=0):
    """
    Generate tree structures by sampling features and querying the model.

    Parameters:
    - base_prompt (str): The prompt template.
    - features (list): A list of features to sample from.
    - sample_num (int): Number of features to sample in each step.
    - step (int): Number of steps to perform.
    - output_dir (str): Directory to save the resulting JSON files.

    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    all_trees = []

    save_step = 10

    for i in range(step):
        sampled_features = random.sample(features, sample_num)
        if i<begin_idx:
            continue
        feature_data = "\n".join(sampled_features)
        prompt = base_prompt.replace("{feature_data}", feature_data)
        print(f"prompt={prompt}")
        response_text = call_gpt4(prompt)[0]

        json_start = response_text.find("<begin>") + len("<begin>")
        json_end = response_text.find("<end>")
        json_string = response_text[json_start:json_end].strip()

        json_string = json_string.replace("\n", "").replace("\r", "")
        try:
            tree_structure = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(e)
            print(f"Failed to decode JSON for step {i + 1}. Adding parse error string.")
            tree_structure = {"parse_error_str": json_string}
        all_trees.append({"idx": i + 1, "tree": tree_structure})

        output_file = os.path.join(output_dir, f"tree_structures_{i}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_trees[-1], f, indent=4)

    output_file = os.path.join(output_dir, "all_tree_structures.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_trees, f, indent=4)

if __name__ == "__main__":
    sample_num = 1000  
    step = 1000 
    feature_freq_file = 'output/extract/TheStack_V2/Csharp_clustered/prompt10/statistics/extract_0-24000_frequency.json'
    output_dir = f'output/extract/TheStack_V2/Csharp_clustered/prompt10/feature_tree_0_29999_n{sample_num}_step{step}'
    features = get_features(feature_freq_file)
    features=list(set(features))
    get_tree(base_prompt, features, sample_num, step, output_dir, begin_idx=0)