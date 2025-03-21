import json

def merge_json(path_list, output_file):
    merged_data = []

    for file in path_list:
        with open(file, 'r') as f:
            data = json.load(f)
            merged_data.extend(data)

    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=4)

if __name__ == "__main__":
    path_list = [
        'output/gen_question/TheStack_V2/Python_clustered/Python_src_0/prompt3/gpt-4/seed42-step0-9000_merged_fea_ori_extract10_fre_t10/seed42-step0-100000.json',
        'output/gen_question/TheStack_V2/Python_clustered/Python_src_0/prompt3/gpt-4/seed42-step0-9000_merged_fea_ori_extract10_fre_t10/seed42-step100001-200000.json'
    ]
    output_file = 'output/gen_question/TheStack_V2/Python_clustered/Python_src_0/prompt3/gpt-4/seed42-step0-9000_merged_fea_ori_extract10_fre_t10/seed42-step0-200000.json'
    merge_json(path_list, output_file)
