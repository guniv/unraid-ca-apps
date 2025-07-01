import requests
import re
import os
from xml.sax.saxutils import escape
from datetime import date
import argparse

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def update_xml(xml_file, release_name, tag_name, body):
    with open(xml_file, 'r') as f:
        xml_content = f.read()

    current_date = date.today().strftime("%Y.%m.%d")
    # Use # for main header and preserve existing markdown levels in body
    new_entry = f"# {current_date} ({release_name})\n{escape(body)}"
    
    changes_pattern = re.compile(r'<Changes>(.*?)</Changes>', re.DOTALL)
    match = changes_pattern.search(xml_content)
    
    if match:
        updated_changes = f"{new_entry}\n\n{match.group(1)}"
        new_xml = xml_content.replace(match.group(0), f"<Changes>{updated_changes}</Changes>")
    else:
        new_xml = xml_content.replace('</Container>', f'  <Changes>{new_entry}</Changes>\n</Container>')
    
    with open(xml_file, 'w') as f:
        f.write(new_xml)

def main(repo, xml_file, last_tag_file):
    last_tag = ""
    if os.path.exists(last_tag_file):
        with open(last_tag_file, 'r') as f:
            last_tag = f.read().strip()
    
    release = get_latest_release(repo)
    tag_name = release['tag_name']
    # Use release name if available, fallback to tag name
    release_name = release.get('name') or tag_name
    
    if tag_name != last_tag:
        print(f"New release detected for {repo}: {tag_name}")
        update_xml(xml_file, release_name, tag_name, release['body'])
        
        with open(last_tag_file, 'w') as f:
            f.write(tag_name)
            
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update XML with latest GitHub release notes.")
    parser.add_argument('--repo', required=True, help='GitHub repo in owner/name format')
    parser.add_argument('--xml', required=True, help='XML file to update')
    parser.add_argument('--last', required=True, help='File to store last release tag')
    args = parser.parse_args()
    if main(args.repo, args.xml, args.last):
        print("XML updated successfully")
    else:
        print("No new releases found")
