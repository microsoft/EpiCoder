import json
save_path="output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10_2/test_results_2468_20000.jsonl"

with open(save_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

data = [json.loads(line) for line in lines]
sorted_data = sorted(data, key=lambda x: x['idx'])

with open(save_path, 'w', encoding='utf-8') as file:
    for entry in sorted_data:
        json.dump(entry, file)
        file.write('\n')