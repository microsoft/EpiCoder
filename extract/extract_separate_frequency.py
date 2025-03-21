from utils.tree import keep_keys,remove_frequency,calculate_all_frequency,check_frequency_file
import json

if __name__ == "__main__":
    # pruned_feature_file with frequency
    original_features_file = 'output/extract/TheStack_V2/Python_clustered/prompt12/statistics/extract_0-10_frequency_depth3_dict3_top50.json'
    # output feature
    full_tree_file = original_features_file.replace(".json","_fea.json")
    # output frequency
    full_frequency_file = original_features_file.replace(".json","_fre.json")
    
    language="Python"

    keep_features_lang={
        "Python":['workflow', 'functionality','resource usage','computation operation',
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques',"programming language","implementation style","security","error handling",
                                        "logging","data structures","implementation logic","scenario"],
        "Csharp":['workflow', 'functionality','resource usage','computation operation',"graphics rendering",
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques',"programming language","implementation style","security","error handling",
                                        "logging","data structures","implementation logic"],
        "C":['workflow', 'functionality','resource usage','computation operation',
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques',"programming language","implementation style","security","error handling",
                                        "logging","data structures","implementation logic","scenario"],
        "C++":['workflow', 'functionality','resource usage','computation operation',
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques',"programming language","implementation style","security","error handling",
                                        "logging","data structures","implementation logic","scenario"],
        "Java":['workflow', 'functionality','resource usage','computation operation',
                                        'user interaction','data processing','file operation','dependency relations',
                                        'algorithm','advanced techniques',"programming language","implementation style","security","error handling",
                                        "logging","data structures","implementation logic","scenario"],
    }
    keep_features=keep_features_lang[language]


    with open(original_features_file, 'r') as f:
        original_features = json.load(f)
    
    original_features=keep_keys(original_features,keep_features)

    full_tree=remove_frequency(original_features)
    
    with open(full_tree_file, 'w') as f:
        json.dump(full_tree,f,indent=4)

    full_frequencies = calculate_all_frequency(original_features)
    with open(full_frequency_file, 'w') as f:
        json.dump(full_frequencies,f,indent=4)

    check_frequency_file(full_frequency_file)