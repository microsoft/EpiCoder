import os
import shutil

def copy_filtered_dirs(src, dest, threshold=20000):
    # Ensure the destination directory exists
    os.makedirs(dest, exist_ok=True)
    
    # Iterate over all items in the source directory
    for item in os.listdir(src):
        # Construct full path for the item
        item_path = os.path.join(src, item)
        
        # Check if the item is a directory and contains an index
        if os.path.isdir(item_path):
            # Extract the numeric index from the directory name
            try:
                idx = int(''.join(filter(str.isdigit, item)))
                if idx >= threshold:
                    # Copy the directory to the destination
                    if os.path.exists(os.path.join(dest, item)):
                        print(f"Skipped {item} (index {idx} < {threshold})")
                        continue
                    shutil.copytree(item_path, os.path.join(dest, item))
                    print(f"Copied {item} to {dest}")
                else:
                    print(f"Skipped {item} (index {idx} < {threshold})")
            except ValueError:
                print(f"Skipping {item} - no numeric index found.")
        else:
            print(f"Skipping {item_path} - not a directory.")

if __name__ == "__main__":
    src_dir = "output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10/code/"
    dest_dir = "output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10_2/code/"
    
    copy_filtered_dirs(src_dir, dest_dir)
