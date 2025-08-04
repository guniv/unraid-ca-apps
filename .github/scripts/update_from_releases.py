import requests
import re
import os
from xml.sax.saxutils import escape
from datetime import date
import argparse

def get_latest_release_github(repo, github_token=None):
    """Get latest release from GitHub API"""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_latest_release_gitlab(project_id, gitlab_token=None):
    """Get latest release from GitLab API"""
    url = f"https://gitlab.com/api/v4/projects/{project_id}/releases"
    
    headers = {}
    if gitlab_token:
        headers['PRIVATE-TOKEN'] = gitlab_token
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    releases = response.json()
    
    if not releases:
        raise Exception("No releases found")
    
    # Return the latest release (first in the list)
    return releases[0]

def update_xml(xml_file, release_name, tag_name, body):
    with open(xml_file, 'r') as f:
        xml_content = f.read()

    current_date = date.today().strftime("%Y.%m.%d")
    # Use # for main header and preserve existing markdown levels in body
    # GitLab uses 'description' field instead of 'body'
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

def main(source_type, source_id, xml_file, last_tag_file):
    last_tag = ""
    if os.path.exists(last_tag_file):
        with open(last_tag_file, 'r') as f:
            last_tag = f.read().strip()
    
    # Get release based on source type
    if source_type == 'github':
        github_token = os.environ.get('GITHUB_TOKEN')
        release = get_latest_release_github(source_id, github_token)
        tag_name = release['tag_name']
        release_name = release.get('name') or tag_name
        body = release['body']
    elif source_type == 'gitlab':
        gitlab_token = os.environ.get('GITLAB_TOKEN')
        release = get_latest_release_gitlab(source_id, gitlab_token)
        tag_name = release['tag_name']
        release_name = release.get('name') or tag_name
        body = release['description']  # GitLab uses 'description' instead of 'body'
    else:
        raise ValueError(f"Unsupported source type: {source_type}")
    
    if tag_name != last_tag:
        print(f"New release detected for {source_id}: {tag_name}")
        update_xml(xml_file, release_name, tag_name, body)
        
        with open(last_tag_file, 'w') as f:
            f.write(tag_name)
            
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update XML with latest release notes from GitHub or GitLab.")
    parser.add_argument('--source-type', required=True, choices=['github', 'gitlab'], 
                        help='Source type: github or gitlab')
    parser.add_argument('--source-id', required=True, 
                        help='GitHub repo in owner/name format or GitLab project ID')
    parser.add_argument('--xml', required=True, help='XML file to update')
    parser.add_argument('--last', required=True, help='File to store last release tag')
    
    # Legacy support for existing workflows
    parser.add_argument('--repo', help='Legacy: GitHub repo in owner/name format (use --source-id instead)')
    
    args = parser.parse_args()
    
    # Handle legacy --repo argument
    if args.repo and not hasattr(args, 'source_id'):
        args.source_id = args.repo
        args.source_type = 'github'
    
    if main(args.source_type, args.source_id, args.xml, args.last):
        print("XML updated successfully")
    else:
        print("No new releases found")
