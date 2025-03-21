import json
from utils.tree import merge_dicts, keep_keys, get_new_node_frequencies, merge_frequencies, recursive_deduplicate

def merge_expanded_features(json_data, raise_e=False):
    merged_features = {}

    for item in json_data:
        expanded_feature = item.get("expanded feature", {})
        
        if "parse_error_str" in expanded_feature:
            continue
        
        merged_features = merge_dicts(merged_features, expanded_feature, raise_e=raise_e)
    
    return merged_features

def merge_expanded_frequencies(json_data, frequencies, raise_e=False):
    print(f"in merge_expanded_frequencies len(json_data)={len(json_data)} ")
    for i, item in enumerate(json_data):
        print(f"item={item}")
        expanded_feature = item.get("expanded feature", {}) 
        original_feature = item.get("features", {})

        if "parse_error_str" in expanded_feature:
            print("skip")
            continue
        # print(f"original_feature={original_feature}")
        # print(f"expanded_feature={expanded_feature}")
        new_node_frequencies=get_new_node_frequencies(original_feature,expanded_feature, frequencies)
        print(f"len(new_node_frequencies)={len(new_node_frequencies)}")
        print(f"len(frequencies)={len(frequencies)}")
        print(f"i={i}")
        frequencies=merge_frequencies(full_frequencies=frequencies,new_node_frequencies=new_node_frequencies)
    return frequencies



def merge(language, original_feature_file, original_frequency_file, evol_file, merged_feature_file, updated_feature_file, updated_frequency_file):
    
    keep_features_lang={
        "Python":["programming language", "implementation style",'workflow', 'functionality','resource usage',
                                            'computation operation','security',"error handling","logging","data structures",
                                            "implementation logic",
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques'],
        "Csharp":["programming language", "implementation style",'workflow', 'functionality','resource usage',
                                            'computation operation',"graphics rendering",'security',"error handling","logging","data structures",
                                            "implementation logic",
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques'],
        "C++":["programming language", "implementation style",'workflow', 'functionality','resource usage',
                                            'computation operation','security',"error handling","logging","data structures",
                                            "implementation logic",
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques'],
        "Java":["programming language", "implementation style",'workflow', 'functionality','resource usage',
                                            'computation operation','security',"error handling","logging","data structures",
                                            "implementation logic",
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques'],
    }

    keep_features=keep_features_lang[language]


    with open(evol_file, 'r') as file:
        evol_data = json.load(file)

    merged_features = merge_expanded_features(evol_data,raise_e=True)
    
    merged_features=keep_keys(merged_features,keep_features)

    merged_features=recursive_deduplicate(merged_features)

    with open(merged_feature_file, 'w') as file:
        json.dump(merged_features,file,indent=4)


    with open(original_feature_file, 'r') as file:
        original_feature = json.load(file)

    merged_features=merge_dicts(original_feature,merged_features)


    merged_features=keep_keys(merged_features,keep_features)

    with open(updated_feature_file, 'w') as file:
        json.dump(merged_features,file,indent=4)

    full_tree=original_feature

    with open(original_frequency_file, 'r') as f:
        full_frequencies = json.load(f)
    
    full_frequencies = merge_expanded_frequencies(json_data=evol_data,frequencies=full_frequencies)

    with open(updated_frequency_file, 'w') as file:
        json.dump(full_frequencies,file,indent=4)


if __name__ == "__main__":

    language="Python"
    # iter0
    original_feature_file=f'output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50_fea.json'
    original_frequency_file = f'output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50_fre.json'
    evol_file=f'output/feature_evol/TheStack_V2/Python_clustered/prompt8/gpt-4o/extract_0-10_frequency_depth3_dict3_top50_fea_extract12/seed42-step0-10.json'
    merged_feature_file=evol_file.replace('.json','_merged_fea.json')
    updated_feature_file=evol_file.replace('.json','_merged_fea_ori.json')
    updated_frequency_file=evol_file.replace('.json','_merged_fea_ori_fre.json')
    merge(language, original_feature_file, original_frequency_file, evol_file, merged_feature_file, updated_feature_file, updated_frequency_file)
