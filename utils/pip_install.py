import subprocess

def install_packages(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    for line in lines:
        package = line.strip()
        if package:
            if "cupy" in package:
                continue
            try:
                print(f"Installing {package}...")
                subprocess.check_call([f"pip install {package}"], shell=True)
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}, skipping.")
    subprocess.check_call([f"pip install --upgrade httpx"], shell=True)
# in docker: cd /workspace/code/DataSynthesis/output/gen_code
if __name__ == "__main__":
    install_packages('/workspace/code/DataSynthesis/output/gen_code/TheStack_V2/Python_clustered/Python_src_0/prompt5_fre_t10_test/requirements.txt')
