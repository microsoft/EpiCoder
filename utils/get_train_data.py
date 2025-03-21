import os
import json
import filecmp
from file_operation import jsonl2json, sort_jsonl_file

def count_successful_debugs(base_dir, begin_idx=0, end_idx=99999, max_iter=5):
    iter_success_counts = [0] * (max_iter + 1)
    only_change_test_count = 0
    total_tasks = 0
    iter_success_indices = [[] for _ in range(max_iter + 1)]

    for idx in range(begin_idx, end_idx + 1):
        task_dir = os.path.join(base_dir, str(idx))
        if os.path.isdir(task_dir):
            # total_tasks += 1
            success_iter = -1
            try:
                for iter_num in range(max_iter + 1):
                    iter_file = os.path.join(task_dir, f"test_result_iter_{iter_num}.json")
                    if os.path.exists(iter_file):
                        with open(iter_file, 'r', encoding='utf-8') as f:
                            iter_result = json.load(f)
                        if iter_num==0 and iter_result["success"] is not None:
                            total_tasks += 1
                        if iter_result["success"]==True:
                            success_iter = iter_num
                            iter_success_counts[iter_num] += 1
                            iter_success_indices[iter_num].append(idx)
                            break
                
                if success_iter == -1:
                    continue  # No success in any iteration
                if success_iter > 0:
                    # Compare initial and final successful iteration files
                    initial_files = {f for f in os.listdir(task_dir) if f.endswith('.py') and os.path.isfile(os.path.join(task_dir, f))}
                    iter_dir = os.path.join(task_dir, f"iter_{success_iter}")
                    iter_files = {f for f in os.listdir(iter_dir) if f.endswith('.py') and os.path.isfile(os.path.join(iter_dir, f))}

                    # Check if there are new files in the final iteration that were not in the initial directory
                    new_files = iter_files - initial_files
                    if new_files:
                        continue  # Skip this task if there are new files in the final iteration

                    changed_files = [f for f in initial_files if not filecmp.cmp(os.path.join(task_dir, f), os.path.join(iter_dir, f), shallow=False)]
                    if all("test" in f for f in changed_files):
                        only_change_test_count += 1
                    
            except Exception as e:
                print(f"error in {idx}: {e}")
                # raise e
    return iter_success_counts, only_change_test_count, total_tasks, iter_success_indices

def get_code_from_dir_without_test(task_dir):
    code_snippets = []
    # try:
    for file_name in os.listdir(task_dir):
        if file_name.endswith(".py") and "test" not in file_name:
            file_path = os.path.join(task_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
                if code.startswith(f"# {file_name}"):
                    code_snippets.append(f"```python\n{code}\n```")
                else:
                    code_snippets.append(f"```python\n# {file_name}\n{code}\n```")
    # except Exception as e:
    #     print(f"file_path={file_path},{e}")
    return "".join(code_snippets)

def extract_successful_code(base_dir, iter_success_indices, max_iter, instructions):
    results = []
    for iter_num in range(max_iter + 1):
        for idx in iter_success_indices[iter_num]:
            iter_dir = os.path.join(base_dir, str(idx), f"iter_{iter_num}")
            if os.path.isdir(iter_dir):
                output = get_code_from_dir_without_test(iter_dir)
                if not output:
                    continue
                print(idx)
                instruction = instructions[idx]
                results.append({"idx": idx, "instruction": instruction, "output": output})
    return results



def get_valid_indices(base_dir, begin_idx=0, end_idx=99999):
    indices=[]
    for idx in range(begin_idx, end_idx + 1):
        task_dir = os.path.join(base_dir, str(idx))
        result_iter0=os.path.join(task_dir, "test_result_iter_0.json")
        if os.path.exists(result_iter0):
            try:
                with open(result_iter0, 'r', encoding='utf-8') as f:
                    iter_result = json.load(f)
                if iter_result["success"] is not None:
                    indices.append(idx)
            except Exception as e:
                print(f"error in {idx}: {e}")
    return indices


def extract_code(base_dir, indices, instructions):
    results=[]
    iter_num=0
    for idx in indices:
        iter_dir = os.path.join(base_dir, str(idx), f"iter_{iter_num}")
        if os.path.isdir(iter_dir):
            try:
                output = get_code_from_dir_without_test(iter_dir)
                if not output:
                    continue
                # print(idx)
                instruction = instructions[idx]
                results.append({"idx": idx, "instruction": instruction, "output": output})
            except Exception as e:
                print(f"error in {iter_dir}")
    return results


def save_results_to_jsonl(results, output_jsonl):
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')
    sort_jsonl_file(output_jsonl)
    jsonl2json(output_jsonl,output_jsonl.replace(".jsonl",".json"))
    

def load_instructions(instruction_file,key='instruction'):
    instructions = {}
    with open(instruction_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                instructions[data['idx']] = data[key]
            except Exception as e:
                print(data)
                raise(e)
    with open("instruction.json", 'w', encoding='utf-8') as f:
        json.dump(instructions,f,indent=4)
    return instructions
# output/gen_code/TheStack_V2/Python_clustered_150k/prompt5_fre_complex_tneg_2
def main():

    begin_idx = 0
    end_idx = 100000
    max_iter = 5

    begin_idx = 0
    end_idx = 10
    # instruction_key="instruction"
    instruction_key="question"
    # instruction_key="task"
    base_dir = 'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10_2/code'
    instruction_file = 'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10_2/code_0_50000.jsonl'
    output_jsonl = f'output/gen_code/TheStack_V2/Python_clustered_150k/p7_function_f1_c33_dep_t10_2/successful_code_{begin_idx}_{end_idx}_09180036_{instruction_key}.jsonl'
    output_failed_jsonl=output_jsonl.replace("successful_code","failed_code")

    valid_indices=get_valid_indices(base_dir, begin_idx, end_idx)

    # Load instructions
    instructions = load_instructions(instruction_file, instruction_key)
    # print(instructions)
    # Get the successful debug information
    iter_success_counts, only_change_test_count, total_tasks, iter_success_indices = count_successful_debugs(base_dir, begin_idx, end_idx, max_iter)

    # Extract successful code
    results = extract_successful_code(base_dir, iter_success_indices, max_iter, instructions)
    results=sorted(results, key=lambda x: x["idx"])
    print(f"len(results)={len(results)}")
    # Save results to JSONL
    save_results_to_jsonl(results, output_jsonl)

    succ_indices=set(item for sublist in iter_success_indices for item in sublist)
    failed_indices=sorted(list(set(valid_indices)-succ_indices))
    print(f"len(valid_indices)={len(valid_indices)}")
    print(f"len(succ_indices)={len(succ_indices)}")
    print(f"len(failed_indices)={len(failed_indices)}")

    failed_results=sorted(extract_code(base_dir, failed_indices, instructions), key=lambda x: x["idx"])
    save_results_to_jsonl(failed_results, output_failed_jsonl)

    # Print summary
    remaining_tasks = total_tasks
    total_success=sum(iter_success_counts)
    print(f"total success:{total_success}")
    for i, count in enumerate(iter_success_counts):
        succ_rate = count / remaining_tasks
        print(f"succ_iter{i}: {count}\ttotal: {remaining_tasks}\tsucc_rate: {succ_rate:.2f}\n\n")
        remaining_tasks -= count

    print(f"Tasks with only test changes: {only_change_test_count}")
    print(f"Total tasks checked: {total_tasks}")
    # for i, indices in enumerate(iter_success_indices):
    #     print(f"Tasks that succeeded in iter{i}: {indices}")

if __name__ == '__main__':
    main()