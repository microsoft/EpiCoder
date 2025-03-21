import os

def get_large_files(root_dir, size_threshold_mb=10):
    large_files = []
    size_threshold_bytes = size_threshold_mb * 1024 * 1024
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                if os.path.getsize(file_path) > size_threshold_bytes:
                    large_files.append(file_path)
            except Exception as e:
                print(e)
    
    return large_files


def remove_files(file_list):
    for file_path in file_list:
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Successfully removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
        else:
            print(f"Skipped {file_path}: not a file")

if __name__ == "__main__":
    root_dir = 'output/gen_code/TheStack_V2/Python_clustered/Python_src_0'
    large_files = get_large_files(root_dir)

    for file in large_files:
        print(file)
