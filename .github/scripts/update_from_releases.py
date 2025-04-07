import requests
import re
import os
from xml.sax.saxutils import escape

REPO_A = "guniv/CoolerControl-Docker"  # Your source repo
LAST_TAG_FILE = ".last_release"

def get_latest_release():
    url = f"https://api.github.com/repos/{REPO_A}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def update_xml(tag_name, body):
    with open('CoolerControl.xml', 'r') as f:
        xml_content = f.read()

    new_entry = f"### {tag_name}\n{escape(body)}"
    
    # Find existing Changes section or create new one
    changes_pattern = re.compile(r'<Changes>(.*?)</Changes>', re.DOTALL)
    match = changes_pattern.search(xml_content)
    
    if match:
        updated_changes = f"{new_entry}\n\n{match.group(1)}"
        new_xml = xml_content.replace(match.group(0), f"<Changes>{updated_changes}</Changes>")
    else:
        new_xml = xml_content.replace('</Container>', f'  <Changes>{new_entry}</Changes>\n</Container>')
    
    with open('CoolerControl.xml', 'w') as f:
        f.write(new_xml)

def main():
    # Get stored last processed tag
    last_tag = ""
    if os.path.exists(LAST_TAG_FILE):
        with open(LAST_TAG_FILE, 'r') as f:
            last_tag = f.read().strip()
    
    # Get latest release from Repo A
    release = get_latest_release()
    
    if release['tag_name'] != last_tag:
        print(f"New release detected: {release['tag_name']}")
        update_xml(release['tag_name'], release['body'])
        
        # Update last processed tag
        with open(LAST_TAG_FILE, 'w') as f:
            f.write(release['tag_name'])
            
        return True
    return False

if __name__ == "__main__":
    if main():
        print("XML updated successfully")
    else:
        print("No new releases found")
