import sys
import os
import subprocess

# Set the repository root as the Python path
repo_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(repo_root)

def run_script(script):
    if not os.path.exists(script):
        print(f"Error: The script '{script}' does not exist.")
        return
    
    try:
        # Run the script with Python
        subprocess.run(["python3", script], check=True)
    except subprocess.CalledProcessError:
        pass
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python run.py <path_to_script>")
        sys.exit(1)

    script_path = sys.argv[1]

    run_script(script_path)

if __name__ == "__main__":
    main()