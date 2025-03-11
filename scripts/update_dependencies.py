#!/usr/bin/env python
"""
Script to update outdated dependencies and check for compatibility issues.
"""
import subprocess
import json
import sys

def get_outdated_packages():
    result = subprocess.run(
        ["pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def update_package(package_name):
    print(f"Updating {package_name}...")
    result = subprocess.run(
        ["pip", "install", "--upgrade", package_name],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def run_tests():
    print("Running tests to check compatibility...")
    result = subprocess.run(
        ["pytest", "tests/client-sdk/safety/"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    outdated = get_outdated_packages()
    print(f"Found {len(outdated)} outdated packages")
    
    for package in outdated:
        name = package["name"]
        current = package["version"]
        latest = package["latest_version"]
        print(f"Updating {name} from {current} to {latest}")
        
        if update_package(name):
            if run_tests():
                print(f"✅ Successfully updated {name} to {latest}")
            else:
                print(f"❌ Tests failed after updating {name}, reverting...")
                subprocess.run(["pip", "install", f"{name}=={current}"])
        else:
            print(f"❌ Failed to update {name}")
    
if __name__ == "__main__":
    main()
