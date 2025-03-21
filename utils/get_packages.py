import json
def get_packages_from_jsonl(jsonl_file_path,begin_idx=0,end_idx=99999999):
    packages_set = set()

    with open(jsonl_file_path, 'r', encoding='utf-8') as file:
        for i,line in enumerate(file):
            if i<begin_idx or i>end_idx:
                continue
            try:
                data = json.loads(line)
                packages = data.get("packages", [])
                for package in packages:
                    packages_set.add(package)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

    return packages_set

def save_packages_to_txt(packages_set, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for package in sorted(packages_set):
            file.write(f"{package}\n")

def main():
    jsonl_file_path = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10_test/code_27_4916.jsonl'  # Replace with your JSONL file path
    output_file_path = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10_test/requirements.txt'  # Replace with your desired output file path
    
    packages_set = get_packages_from_jsonl(jsonl_file_path)
    
    save_packages_to_txt(packages_set, output_file_path)
    
    print(f"Total packages saved to {output_file_path}")

if __name__ == '__main__':
    main()