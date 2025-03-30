import os
import shutil

def move_files(source, destination):
    """Moves all files from source directory to destination directory."""
    if not os.path.exists(destination):
        os.makedirs(destination)

    for filename in os.listdir(source):
        source_path = os.path.join(source, filename)
        destination_path = os.path.join(destination, filename)
        shutil.move(source_path, destination_path)
        print(f"Moved {filename} to {destination}")

if __name__ == "__main__":
    source_dir = "test"
    destination_dir = "tests"
    
    if os.path.exists(source_dir):
        move_files(source_dir, destination_dir)
        print("All files moved successfully.")
        # Optionally, remove the now empty 'test' directory
        if not os.listdir(source_dir):
            os.rmdir(source_dir)
            print(f"Removed empty directory: {source_dir}")
        else:
            print(f"Directory {source_dir} is not empty, not removing it.")
    else:
        print(f"Source directory '{source_dir}' does not exist.")
