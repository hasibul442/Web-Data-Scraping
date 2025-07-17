import subprocess

# Run the first script
result1 = subprocess.run(["python", "main.py"])

# Check if the first script was successful
if result1.returncode == 0:
    # If successful, run the second script
    result2 = subprocess.run(["python", "image_download.py"])
    
    if result2.returncode == 0:
        print("Both scripts executed successfully.")
    else:
        print("Script 2 failed.")
else:
    print("Script 1 failed.")