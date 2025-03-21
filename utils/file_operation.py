import json

def jsonl2json(jsonl_file_path,json_file_path=None):
    data = []
    with open(jsonl_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    if json_file_path is None:
        json_file_path = jsonl_file_path.replace(".jsonl",".json")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def sort_jsonl_file(file_path, sort_key="idx"):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        data = [json.loads(line) for line in lines]
        
        sorted_data = sorted(data, key=lambda x: x[sort_key])
        
        with open(file_path, 'w', encoding='utf-8') as file:
            for entry in sorted_data:
                json.dump(entry, file)
                file.write('\n')
        print(f"File {file_path} sorted successfully by key '{sort_key}'")
    except Exception as e:
        print(f"Error sorting file {file_path}: {e}")

if __name__ == "__main__":
    
    jsonl_file_path = 'output/feature_evol/TheStack_V2/Csharp_clustered/prompt5/gpt-4/extract_0-24000_frequency_top_50_fea_extract11/seed42-step0-9000.jsonl'
    sort_jsonl_file(jsonl_file_path)
    json_file_path = jsonl_file_path.replace(".jsonl",".json")
    jsonl2json(jsonl_file_path,json_file_path)