import json

def merge_jsonl_files(file_path_list, output_file):
    merged_data = []

    # Read all files in the file path list
    for file_path in file_path_list:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                merged_data.append(data)
    
    print(f"len merged_data={len(merged_data)}")
    # Write the merged data to the output file
    with open(output_file, 'w', encoding='utf-8') as out:
        for data in merged_data:
            out.write(json.dumps(data) + '\n')
    
    return merged_data
    

def sort_output(data):
    # Sort the data based on 'idx' using a stable sort
    sorted_data = sorted(data, key=lambda x: x['idx'])
    return sorted_data

def save_sorted_data(data, output_file):
    # Save the sorted data to the output file
    with open(output_file, 'w', encoding='utf-8') as out:
        for item in data:
            out.write(json.dumps(item) + '\n')



if __name__ == '__main__':
    file_path_list = [
        'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10/code_0_60000.jsonl',
        'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10/code_60001_100000.jsonl',
    ]
    
    output_file = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10/code_0_100000.jsonl'
    merged_data = merge_jsonl_files(file_path_list, output_file)
    
    # Sort the merged data
    sorted_data = sort_output(merged_data)
    
    # Save the sorted data
    save_sorted_data(sorted_data, output_file)
