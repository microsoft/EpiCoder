import jsonlines
import json
import re
import os

input_file = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt3/test.jsonl'
output_dir = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt3/test'

os.makedirs(output_dir, exist_ok=True)

with open(input_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

print(f"len lines= {len(lines)}")


for idx, line in enumerate(lines):

    obj = json.loads(line)
    obj['idx'] = idx
    print(f"idx={idx}")

    code_match = re.search(r'```python\n(.*?)```', obj['output'], re.DOTALL)
    if code_match:
        python_code = code_match.group(1)
        
        py_file_path = os.path.join(output_dir, f'{idx}.py')
        with open(py_file_path, 'w', encoding='utf-8') as py_file:
            py_file.write(python_code)