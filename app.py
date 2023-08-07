# --------------------------------------------------------------------------------------
# Script - md_to_html.py
#    - Converts given markdown files to HTML
#    - Formats the HTML page created by Dart markdown command
#    - Creates a YYYY/MM/DD directory structure
#    - Creates an index.html file with links to all the HTML files
#    - Copies the images to the YYYY/MM/DD directory structure
#    - Copies the files to AWS S3
#    - Refreshes the CloudFront distribution
#
# Usage:
# python md_to_html.py [-h] [--domain DOMAIN] [--port PORT] [--index_page_dir INDEX_PAGE_DIR]
# --------------------------------------------------------------------------------------
import argparse
import datetime
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import date

import yaml

MARKDOWN_FILES_LIST = "md_files.yml"

# List of files to be excluded from index.html page.
EXCLUSION_LIST = [
    "policy.html",
    "index_template.html",
    "graph_viz.html",
]

BLOG_DOMAIN = "ryandam.net"


def prepare_html_head(domain: str, title: str) -> str:
    """
    Prepares the HTML head section

    The html produced by Dart markdown command does not have Head section. It is needed to
    add the CSS and JS files. This function adds the head section to the HTML file.

    It adds Google fonts api link for fonts. It also adds prism.css to support code highlighting.
    Custom styling is provided by generic.css.

    :param domain: Domain name
    :param title: Title of the page

    :return: HTML head section
    """
    return f"""
    <!doctype html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
            content="width=device-width, user-scalable=no, initial-scale=1.0, 
            maximum-scale=1.0, 
            minimum-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <link rel="shortcut icon" type="image/png" href="{domain}/images/logo.png">
        <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto|Jetbrains Mono|Crimson Text|Corben|Roboto Condensed">
        <link rel="stylesheet" href="{domain}/css/prism.css">
        <link rel="stylesheet" href="{domain}/css/generic.css">
        <title>{title}</title>
    </head>

    <body>
        <article>
        <div class="content">
    """


def get_html_tail(domain: str) -> str:
    """
    Prepares the HTML tail section

    :param domain: Domain name
    :return: HTML tail section
    """
    return f"""
    </div>
    </article>
    <div class="my-footer"></div>
    <script src="{domain}/js/prism.js"></script>
    """


def read_yaml_file():
    """
    Reads the YAML file and returns the contents as a dictionary
    """
    try:
        with open(MARKDOWN_FILES_LIST, "r") as file:
            yaml_file = yaml.safe_load(file)

        print(f"YAML File read: {MARKDOWN_FILES_LIST}")
        return yaml_file
    except Exception as err:
        print(f"Error reading {MARKDOWN_FILES_LIST} file - {err}")
        sys.exit(1)


def copy_images_to_target_dir(
    markdown_dir: str, html_contents: str, target_dir: str
) -> None:
    """
    Copies any Images used in Markdown file to the target directory where html file is present.
    """
    # <img src="(.*?)": This part of the pattern matches an <img> tag with a src attribute and
    #                   captures the URL of the image.
    #                   The (.*?) captures any characters (non-greedy) between the double quotes of the src attribute.
    #
    # <source\s+src="(.*?\.mp4)"\s+type="video/mp4">:
    #                   This part of the pattern matches a <source> tag with a src attribute ending in .mp4
    #                   and a type attribute set to "video/mp4".
    #
    #                   The (.*?\.mp4) captures the URL of the video file, and the \s+ matches one or more
    #                   whitespace characters.
    pattern = r'<img src="(.*?)"|<source\s+src="(.*?\.mp4)"\s+type="video/mp4">'

    # Find all image file paths using regex
    matches = re.findall(pattern, html_contents)

    if matches:
        for image_path in matches:
            image_path = image_path[0] if image_path[0] else image_path[1]
            image_path = image_path.replace("../", "")
            image_path = image_path.replace("./", "")
            image_abs_path = os.path.abspath(os.path.join(markdown_dir, image_path))

            try:
                shutil.copy(image_abs_path, target_dir)
                print(f"Image File {image_abs_path} copied to {target_dir}")
            except Exception as err:
                print(f"Error copying image file {image_path} - {err}")
                sys.exit(1)


def convert_markdown_to_html(markdown_file_path: str) -> str:
    """
    Converts the given markdown file to HTML

    :param markdown_file_path: Path to the markdown file
    :return: HTML content
    """
    markdown_file_name = os.path.basename(markdown_file_path)

    # HTML Page title
    # Remove the .md extension from the file name
    # Remove any special characters from the file name including numbers
    title = markdown_file_name.replace(".md", "")
    title = re.sub("[^A-Za-z-]+", "", title)
    title = title.strip().lstrip("-").replace("-", " ").capitalize()

    # Convert to HTML
    try:
        result = subprocess.run(
            ["markdown", "--extension-set", "GitHubFlavored", markdown_file_path],
            capture_output=True,
            text=True,
        )
    except Exception as err:
        print("Unable to convert markdown to HTML: ", str(err))
        print(
            f"Tried to execute this command: [markdown --extension-set GitHubFlavored {markdown_file_path}"
        )
        sys.exit(1)

    # Capture HTML content
    html_data = result.stdout

    # Combine the HTML content with the HTML Head and Tail
    final_html_contents = (
        prepare_html_head(DOMAIN_WITH_PORT, title)
        + html_data
        + get_html_tail(DOMAIN_WITH_PORT)
    )

    return final_html_contents


def convert_markdown_to_html_wrapper(yaml_contents: dict[str, str]) -> None:
    """
    :return:
    """
    checksums = dict()

    # Read the checksums.txt file
    # It holds the checksum of the markdown file. It is used to determine if the
    # markdown file has changed.
    try:
        with open("checksums.txt", "r") as file:
            for line in file:
                markdown_file, checksum = line.strip().split("~")
                checksums[markdown_file] = checksum
    except Exception as err:
        print(f"Error reading checksums.txt file - {err}")
        print("This can happen if this is the first & it is fine!")

    # Loop through the markdown files & convert them to HTML
    for index, entry in enumerate(yaml_contents["markdown_files"]):
        markdown_file_path = entry["file"]
        markdown_dir = os.path.dirname(markdown_file_path)
        markdown_file_name = os.path.basename(markdown_file_path)

        if not os.path.exists(markdown_file_path):
            print(f"Markdown file {markdown_file_path} does not exist.")
            continue

        # Get MD5 Checksum
        # If the MD5 checksum is the same as the previous run, then skip the file.
        # This indicates that the file has not changed.
        current_md5_checksum = get_md5_checksum(markdown_file_path)

        if markdown_file_path in checksums:
            previous_md5_checksum = checksums[markdown_file_path]
        else:
            previous_md5_checksum = None

        if current_md5_checksum == previous_md5_checksum:
            print(f"{index + 1:<3} - [NOT CHANGED] - {markdown_file_path}")
            continue
        else:
            checksums[markdown_file_path] = current_md5_checksum

        html_contents = convert_markdown_to_html(markdown_file_path)

        # Capture creation date from the HTML
        # Expected format sample: <li>Created - 2021/01/01</li>
        pattern = r"<li>Created - (\d{4}/\d{2}/\d{2})</li>"
        match = re.search(pattern, html_contents)

        today = date.today()
        creation_date = today.strftime("%Y/%m/%d")

        if match:
            creation_date = match.group(1)

        year, month, day = creation_date.split("/")

        # Create a YYYY / MM / DD directory structure
        directory_path = os.path.join(TARGET_DIR, year, month, day)
        os.makedirs(directory_path, exist_ok=True)

        # Each HTML Page will have its own directory
        # As it needs assets like Images.
        page_directory = os.path.join(
            directory_path, markdown_file_name.replace(".md", "").lower()
        )

        if os.path.exists(page_directory):
            shutil.rmtree(page_directory)

        os.mkdir(page_directory)

        # HTML File name
        html_file = os.path.join(page_directory, "index.html")

        copy_images_to_target_dir(markdown_dir, html_contents, page_directory)

        # Change Image paths
        # Any images for a given blog post will be in the same directory as the html
        # file.
        html_contents = html_contents.replace('src="./images/', 'src="')

        with open(html_file, "w") as file:
            file.write(html_contents)

        print(f"{index + 1} - HTML File written to {html_file}")
        print("-" * 100)

    # Write the checksums to a file
    try:
        with open("checksums.txt", "w") as file:
            for markdown_file, checksum in checksums.items():
                file.write(f"{markdown_file}~{checksum}\n")
    except Exception as err:
        print(f"Error writing checksums.txt file - {err}")

    print("\nAll markdown files processed.")
    print("\nChecksums written to checksums.txt file.")


def get_md5_checksum(file: str) -> str:
    """
    Returns the MD5 checksum of a file

    :param file:
    :return: MD5 Checksum
    """
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def convert_string_to_date(entry: str) -> datetime.date:
    """
    Converts a date string to a date object
    :param entry:
    :return:
    """
    try:
        year, month, day = (
            int(entry.split("/")[-5]),
            int(entry.split("/")[-4]),
            int(entry.split("/")[-3]),
        )

        return datetime.date(year, month, day)
    except ValueError:
        print(f"Error converting string to date - {entry}")
        return datetime.date(1900, 1, 1)


def collect_all_html_files() -> list[str]:
    """
    Collect all the HTML files

    :return: List of HTML files
    """
    html_files = []

    for root, _, filenames in os.walk(TARGET_DIR):
        for filename in fnmatch.filter(filenames, "*.html"):
            file_path = os.path.join(root, filename)
            file_should_be_excluded = False

            # Exclude the main index.html file
            if file_path.endswith(f"{TARGET_DIR}/index.html"):
                continue

            # Exclusions
            for exclusion in EXCLUSION_LIST:
                if file_path.endswith(exclusion):
                    file_should_be_excluded = True
                    break

            if file_should_be_excluded:
                continue

            html_files.append(file_path)

    # Sort the list based on creation date
    html_files.sort(
        key=lambda html_file_path: convert_string_to_date(html_file_path), reverse=True
    )

    return html_files


def prepare_index_page() -> None:
    """
    Collects all the HTML files from the target directory and prepares the index.html
    file. Writes the HTML file to the target directory.

    :return: none
    """
    # Collect all the HTML files
    html_files = collect_all_html_files()

    print("\nAll html files:")
    for x in html_files:
        print(x)

    print("\nGoing to create index.html file")
    html_list = "<ul>"

    # This step prepares a list of HTML <li> elements
    for entry in html_files:
        # Replace the directory path with the domain name
        # When we click on the link, it should point to the blog post rather than
        # the local file.
        entry = entry.replace(TARGET_DIR, f"{DOMAIN_WITH_PORT}/blog")

        post_date = (
            entry.split("/")[-5]
            + "-"
            + entry.split("/")[-4]
            + "-"
            + entry.split("/")[-3]
        )

        html_list_label = str(entry.split("/")[-2])
        label = html_list_label.replace("-", " ")
        web_url = entry

        pattern = r"^[\d\W_]+"
        label = re.sub(pattern, "", label)
        label = post_date + " - " + label.capitalize()

        li_template = f"""
            <li><a href="{web_url}" target="_blank">{label}</a></li>
            """

        html_list += li_template

    html_list += "</ul>"

    index_page_template = "./index_template.html"

    with open(index_page_template, "r") as file:
        template = file.read()

    index_page_content = template.replace("[[links]]", html_list)
    index_page = os.path.join(INDEX_PAGE_DIR, "index.html")

    # Delete if exists
    if os.path.exists(index_page):
        os.remove(index_page)

    with open(index_page, "w") as file:
        file.write(index_page_content)

    print(f"\nIndex page written to {index_page}")


def create_site_map():
    """
    Creates a sitemap.txt file
    :return: None
    """
    print("\nInside [create_site_map]")

    sitemap_file_location = os.path.join(INDEX_PAGE_DIR, "sitemap.txt")
    sitemap_file = open(sitemap_file_location, "w")
    html_files = collect_all_html_files()

    for entry in html_files:
        entry = entry.replace(TARGET_DIR, f"{DOMAIN_WITH_PORT}/blog")
        sitemap_file.write(entry + "\n")

    sitemap_file.close()
    print(f"Sitemap file created - {sitemap_file_location}")


def store_md5_checksums():
    """
    Calculates MD5 checksums for all the files in the target directory.
    :return:
    """
    checksums = {}

    for root, _, filenames in os.walk(TARGET_DIR):
        for filename in fnmatch.filter(filenames, "*.html"):
            file_path = os.path.join(root, filename)
            md5_checksum = get_md5_checksum(file_path)

            file_directory = file_path.split("/")[-2]
            checksums[file_directory] = md5_checksum

    print("\nMD5 Checksums:")
    for filename, md5 in checksums.items():
        print(f"{md5} {filename}")

    return checksums


def sync_with_s3_bucket() -> None:
    """
    Syncs the target directory with the S3 bucket

    NOTE: Rather than syncing the entire directory, we are only syncing
          specific files. Each file type should be included in the list below.

    :return: None
    """
    sync_cmd = f"""
    aws s3 sync {INDEX_PAGE_DIR} s3://{BLOG_DOMAIN} \
        --exclude '*' \
        --include '*.html' \
        --include '*.js' \
        --include '*.css' \
        --include '*.png' \
        --include '*.jpg' \
        --include '*.JPG' \
        --include '*.jpeg' \
        --include '*.svg' \
        --include '*.ttf' \
        --include '*.txt' \
        --include '*.mp4' \
        --include '*.gif'
    """
    result = subprocess.run(sync_cmd, shell=True, capture_output=True, text=True)

    # Check the result
    if result.returncode == 0:
        output = result.stdout
        print(output)
    else:
        error = result.stderr
        print(error)
        sys.exit(1)


def refresh_cloudfront() -> None:
    """
    Refresh the CloudFront distribution
    """
    # As per https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html,
    # the paths must be quoted.
    cmd = f'aws cloudfront create-invalidation --distribution-id={CLOUD_FRONT_DISTRIBUTION_ID} --paths "/*"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # Check the result
    if result.returncode == 0:
        output = result.stdout
        print(output)
    else:
        error = result.stderr
        print(error)
        sys.exit(1)


def apply_styling(theme: str) -> None:
    """
    Applies styling to the HTML files
    """
    style_dir = f"./styles/{theme}"

    # Copy the files only if they don't exist in the target directory.
    if not os.path.exists(f"{INDEX_PAGE_DIR}/css"):
        subprocess.run(
            f"cp -R {style_dir}/css {INDEX_PAGE_DIR}",
            shell=True,
            capture_output=True,
            text=True,
        )
        print("css/ directory copied!")

    if not os.path.exists(f"{INDEX_PAGE_DIR}/fonts"):
        subprocess.run(
            f"cp -R {style_dir}/fonts {INDEX_PAGE_DIR}",
            shell=True,
            capture_output=True,
            text=True,
        )
        print("fonts/ directory copied!")

    if not os.path.exists(f"{INDEX_PAGE_DIR}/images"):
        subprocess.run(
            f"cp -R {style_dir}/images {INDEX_PAGE_DIR}",
            shell=True,
            capture_output=True,
            text=True,
        )
        print("images/ directory copied!")

    if not os.path.exists(f"{INDEX_PAGE_DIR}/js"):
        subprocess.run(
            f"cp -R {style_dir}/js {INDEX_PAGE_DIR}",
            shell=True,
            capture_output=True,
            text=True,
        )
        print("js/ directory copied!")

    if not os.path.exists(f"{INDEX_PAGE_DIR}/policy.html"):
        subprocess.run(
            f"cp -R {style_dir}/policy.html {INDEX_PAGE_DIR}",
            shell=True,
            capture_output=True,
            text=True,
        )

    print(f"\nStyling applied to HTML files using {style_dir}\n")


def main():
    yaml_contents = read_yaml_file()
    convert_markdown_to_html_wrapper(yaml_contents)
    prepare_index_page()
    create_site_map()
    apply_styling("serious_earth")

    if CLOUD_FRONT_DISTRIBUTION_ID is not None:
        sync_with_s3_bucket()
        refresh_cloudfront()


# --------------------------------------------------------------------------------------------------#
# Main section                                                                                      #
# --------------------------------------------------------------------------------------------------#
parser = argparse.ArgumentParser()
parser.add_argument(
    "--domain",
    help="Domain name [E.g. https://ryandam.net, http://localhost]. Default is http://localhost",
    type=str,
)
parser.add_argument("--port", help="Port number [Default: 8000]", type=str)
parser.add_argument(
    "--index_page_dir",
    help="Index page directory [Location where HTML files will be placed]",
    type=str,
)
parser.add_argument(
    "--cloudfront_dist_id",
    help="CloudFront distribution ID [For Blogs deployed on AWS]",
    type=str,
)

args = parser.parse_args()

# Print the help message
if not vars(args):
    parser.print_help()

DOMAIN = args.domain
PORT = args.port
INDEX_PAGE_DIR = args.index_page_dir

if DOMAIN is None:
    DOMAIN = "http://localhost"

if PORT is None:
    PORT = "8000"

DOMAIN_WITH_PORT = f"{DOMAIN}:{PORT}"

# Normally, websites are hosted on port 80. We don't need to specify the port number in the URL.
if "localhost" not in DOMAIN:
    DOMAIN_WITH_PORT = f"{DOMAIN}"

# Target directory
if INDEX_PAGE_DIR is not None:
    TARGET_DIR = os.path.join(INDEX_PAGE_DIR, "blog")
else:
    print("ERROR: Index page directory is not specified.")
    print(
        "       Please specify the index page directory using the --index_page_dir argument."
    )
    sys.exit(1)

# CloudFront distribution ID
# If this is not specified, then the website will not be synced with the S3 bucket.
CLOUD_FRONT_DISTRIBUTION_ID = args.cloudfront_dist_id

if __name__ == "__main__":
    main()
