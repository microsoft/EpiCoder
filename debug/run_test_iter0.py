import os
from call_api_local.call_api import call_gpt4
import subprocess
import json
import re
import shutil
import concurrent.futures
import threading
from utils.file_operation import sort_jsonl_file
from datetime import datetime
import psutil
import time
lock = threading.Lock()

python_executable = "/root/anaconda3/envs/test/bin/python"

def extract_content(solution):
    error_analysis = ""
    file_names, code_blocks = [], []

    # Extract error analysis
    try:
        error_match = re.search(r'<error analysis>(.*?)</error analysis>', solution, re.DOTALL)
        if error_match:
            error_analysis = error_match.group(1).strip()
    

        # Extract file names and code blocks
        code_matches = re.findall(r'<file>(.*?)</file>\s*```.*?\n(.*?)```', solution, re.DOTALL)
        for file_name, code in code_matches:
            file_names.append(file_name.strip())
            code_blocks.append(code.strip())

    except Exception as e:
        print(e)

    return error_analysis, file_names, code_blocks


def make_request_to_fix_code(instruction, analysis, current_code, error_message):
    

    prompt = f'''\
Based on the given instruction, analysis, current code and error message, identify the issue and provide a corrected version of the code. Ensure the new code handles the specified errors.

Instruction:
{instruction}

Analysis:
{analysis}

Current Code:
{current_code}

Error Message:
{error_message}

Provide an analysis of the error the updated code with necessary changes.
- Error analysis
Surround the error analysis with <error analysis> and </error analysis>
<error analysis>your answer</error analysis>

- Updated code implementation with test cases
If you find that the cause of the error is the lack of external files or services, rather than code implementation errors, please modify the test file to ignore these test cases. If necessary, you can make the test file empty.
Surround the updated python code with ```python and ``` and surround the file name with <file> and </file>. Ensure the updated code's file name matches the current code's file name exactly.
For example,
<file>add.py</file>
```python
# add.py
# Code implementation here
def add(x, y):  
    return x + y
```
''' 
    print(f"make_request_to_fix_code")
    print(f"Fixing code prompt:\n{prompt}\n\n")
    updated_code_response = call_gpt4(prompt)[0]
    print(f"updated_code_response:\n{updated_code_response}")
    return updated_code_response

def make_request_to_fix_code_without_analysis(instruction, current_code, error_message):
    prompt = f'''\
Based on the given instruction, current code and error message, identify the issue and provide a corrected version of the code. Ensure the new code handles the specified errors.

Instruction:
{instruction}

Current Code:
{current_code}

Error Message:
{error_message}

Provide an analysis of the error the updated code with necessary changes.
- Error analysis
Surround the error analysis with <error analysis> and </error analysis>
<error analysis>your answer</error analysis>

- Updated code implementation with test cases
If you find that the cause of the error is the lack of external files or services, rather than code implementation errors, please modify the test file to ignore these test cases. If necessary, you can make the test file empty.
Surround the updated python code with ```python and ``` and surround the file name with <file> and </file>. Ensure the updated code's file name matches the current code's file name exactly.
For example,
<file>add.py</file>
```python
# add.py
# Code implementation here
def add(x, y):  
    return x + y
```
''' 
    print(f"Fixing code prompt:\n{prompt}\n")
    updated_code_response = call_gpt4(prompt)[0]
    print(f"Fixing code prompt:\n{prompt}\n\nupdated_code_response:\n{updated_code_response}")
    return updated_code_response

def save_code_files(base_dir, idx, file_names, code_blocks, iteration="iter_1"):
    try:
        task_dir = os.path.join(base_dir, str(idx))
        new_task_dir = os.path.join(task_dir, iteration)
        if not os.path.exists(new_task_dir):
            os.makedirs(new_task_dir, exist_ok=True)
        for file_name, code in zip(file_names, code_blocks):
            file_path = os.path.join(new_task_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as code_file:
                code_file.write(code)
                print(f"save{code} to {file_path}")
    except Exception as e:
        print(f"save error {e}")

def copy_existing_py_files(task_dir, new_task_dir="iter_1"):
    # new_task_dir = os.path.join(task_dir, iteration)
    if not os.path.exists(new_task_dir):
        os.makedirs(new_task_dir)
    for file_name in os.listdir(task_dir):
        if file_name.endswith(".py") and not os.path.isdir(os.path.join(task_dir, file_name)):
            shutil.copy(os.path.join(task_dir, file_name), os.path.join(new_task_dir, file_name))
UNSAFE_PATTERNS = [
    r'\bkill\b',
    r'\bterminate\b',
    r'\brmtree\b',
    r'\brmdir\b',
    r'\brmtree\b',
    r'rm.*?-rf'
]


def contains_unsafe_code(code):
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, code):
            return True
    return False

def get_py_code(dir):
    py_code = []
    for file_name in os.listdir(dir):
        if file_name.endswith(".py"):
            file_path = os.path.join(dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
                formatted_code = f"<file>{file_name}</file>\n```python\n{code}\n```"
                py_code.append(formatted_code)
    return "\n".join(py_code)

def monitor_process(proc, max_execution_time):
    try:
        proc.wait(timeout=max_execution_time+1)
    except subprocess.TimeoutExpired:
        print(f"Process {proc.pid} exceeded time limit of {max_execution_time} seconds, killing it.")
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):  # Terminate child processes
            child.kill()
        proc.kill()  # Terminate the parent process

def test_dir(task_dir, max_execution_time, task_idx):
    print(f"test_dir({task_dir}, {max_execution_time}, {task_idx})")

    task_result = {
        "idx": task_idx,
        "success": True,
        "errors": [],
        "test_files":[],
        "dir": f"{task_dir}"
    }
    
    all_code=get_py_code(task_dir)
    if contains_unsafe_code(all_code):
        task_result["success"] = None
        task_result["errors"].append({
            "file": None,
            "error": "unsafe code"
        })
        return task_result

    for file_name in os.listdir(task_dir):
        if "test" in file_name and file_name.endswith(".py"):
            file_path = os.path.join(task_dir, file_name)
            try:
                print(f"run {file_path}")
                proc = subprocess.Popen(
                    [python_executable, file_path], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True, 
                    cwd=task_dir
                )

                # Start a daemon thread to monitor the process
                monitor_thread = threading.Thread(target=monitor_process, args=(proc, max_execution_time))
                monitor_thread.daemon = True
                monitor_thread.start()
                print(f"run {file_path}")
                stdout, stderr = proc.communicate(timeout=max_execution_time)
                task_result["test_files"].append(f"{file_name}")
                if stderr and not stderr.strip().endswith('OK'):
                    task_result["success"] = False
                    task_result["errors"].append({
                        "file": file_name,
                        "error": stderr.strip()
                    })

            except subprocess.TimeoutExpired:
                task_result["success"] = False
                task_result["errors"].append({
                    "file": file_name,
                    "error": f"Execution timed out after {max_execution_time} seconds"
                })
            except Exception as e:
                task_result["success"] = False
                task_result["errors"].append({
                    "file": file_name,
                    "error": str(e)
                })
            # finally:
            #     # Ensure all child processes are terminated
            #     subprocess.run(['pkill', '-P', str(os.getpid())])
    return task_result


def process_single_task(idx, base_dir, analysis_data, output_jsonl, max_execution_time, begin_iter, max_iter, rewrite, instruction_field="instruction"):
    current_time = datetime.now().isoformat()
    print(f"idx={idx}:{current_time}")
    task_dir = os.path.join(base_dir, str(idx))
    if os.path.isdir(task_dir):
        iteration = begin_iter
        while iteration <= max_iter:
            print(f"iter_{iteration}")
            if iteration==0:
                new_task_dir = os.path.join(task_dir, f"iter_{iteration}")
                new_result_file_path = os.path.join(task_dir, f"test_result_iter_{iteration}.json")
                if not rewrite and os.path.exists(new_result_file_path): # skip
                    try:
                        with open(new_result_file_path, 'r', encoding='utf-8') as f:
                            iter_result = json.load(f)
                        task_result = iter_result 
                        # if iter_result["success"] is not None:
                        #     task_result={
                        #         "idx": idx,
                        #         "success": None,
                        #         "errors": ["skip"]
                        #     }
                        #     print(f"skip {idx}")
                        print(f"skip {idx}")
                    except Exception as e:
                        print(e)
                    finally:
                        iteration+=1
                        continue

                copy_existing_py_files(task_dir, new_task_dir)
                task_result = test_dir(new_task_dir, max_execution_time,idx)
                
                with open(new_result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(task_result, f, indent=4, ensure_ascii=False)
                iteration+=1
                continue

            last_task_dir = os.path.join(task_dir, f"iter_{iteration-1}")
            if not os.path.exists(last_task_dir):
                if iteration == 1:
                    copy_existing_py_files(task_dir, last_task_dir)
                else:  # 没到上一个iter就成功了
                    print(f"success before")
                    break

            last_result_file_path = os.path.join(task_dir, f"test_result_iter_{iteration-1}.json")
            # if not os.path.exists(last_result_file_path) or iteration == 1 or rewrite:
            if not os.path.exists(last_result_file_path) or rewrite:
                task_result = test_dir(last_task_dir, max_execution_time, idx)
                with open(last_result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(task_result, f, indent=4, ensure_ascii=False)
            else:  # 当last result存在时，直接用
                print(f"{last_result_file_path} exists")
                with open(last_result_file_path, 'r', encoding='utf-8') as f:
                    task_result = json.load(f)
                print(f"result={task_result}")

            new_result_file_path = os.path.join(task_dir, f"test_result_iter_{iteration}.json")
            
            if os.path.exists(new_result_file_path) and not rewrite:
                print(f"{new_result_file_path} exists")
                with open(new_result_file_path, 'r', encoding='utf-8') as f:
                    task_result = json.load(f)
                iteration += 1
                print(f"result={task_result} continue")
                continue
            
            if task_result["success"] is None: # unsafe
                print(f"result={task_result} break")
                break
            
            if not task_result["success"]:
                print(f"not success")
                analysis_entry = next((item for item in analysis_data if item["idx"] == idx), None)
                if analysis_entry:

                    instruction = analysis_entry[instruction_field]
                    error_messages = "\n".join([error["error"] for error in task_result["errors"]])
                    if iteration == 1:
                        analysis = analysis_entry["analysis"]
                        current_code = analysis_entry["output"]
                        updated_code_response = make_request_to_fix_code(instruction, analysis, current_code, error_messages)
                    else:
                        current_code = get_py_code(last_task_dir)
                        updated_code_response = make_request_to_fix_code_without_analysis(instruction, current_code, error_messages)
                    error_analysis, file_names, code_blocks = extract_content(updated_code_response)
                    
                    new_task_dir = os.path.join(task_dir, f"iter_{iteration}")
                    copy_existing_py_files(last_task_dir, new_task_dir)
                    save_code_files(base_dir, idx, file_names, code_blocks, iteration=f"iter_{iteration}")

                    task_result = test_dir(new_task_dir, max_execution_time, idx)
                    task_result["error_analysis"] = error_analysis
                    
                    new_result_file_path = os.path.join(task_dir, f"test_result_iter_{iteration}.json")
                    with open(new_result_file_path, 'w', encoding='utf-8') as f:
                        json.dump(task_result, f, indent=4, ensure_ascii=False)
            else:
                break
            iteration += 1

        with lock:
            with open(output_jsonl, 'a', encoding='utf-8') as f:
                f.write(json.dumps(task_result) + '\n')

            if idx%100==0:
                sort_jsonl_file(output_jsonl)

    else:
        print(f"{task_dir} not exists")

def run_test_files(base_dir, output_jsonl, analysis_file, max_execution_time=10, begin_idx=0, end_idx=99999, begin_iter=1, max_iter=3, rewrite=False, instruction_field="instruction"):
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_data = [json.loads(line) for line in f]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_single_task, idx, base_dir, analysis_data, output_jsonl, max_execution_time, begin_iter, max_iter, rewrite, instruction_field)
            for idx in range(begin_idx, end_idx + 1)
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result() 

def main():
    begin_idx=0
    end_idx=10
    # instruction_field="instruction"
    instruction_field="question"
    base_dir = 'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10_2/code'
    output_jsonl = f'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10_2/test_results_{begin_idx}_{end_idx}.jsonl'
    code_generation_file = 'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10/code_0_100000.jsonl'

    run_test_files(base_dir, output_jsonl, code_generation_file,begin_idx=begin_idx,end_idx=end_idx,begin_iter=0,max_iter=0,rewrite=False,instruction_field=instruction_field)

if __name__ == '__main__':
    main()

# copy generated code into another dir for backup
# run in docker, don't use nohup!!!
# after each run, use  ps aux | grep "python" | grep -v grep | awk '{print $2}' | xargs -r kill -9 to kill the remained process in docker