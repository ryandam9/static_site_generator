# --------------------------------------------------------------------------------------
# Script - md_to_html.py
#    - Converts given markdown files to HTML
#    - Formats the HTML page created by Dart markdown command
#    - Creates a YYYY/MM/DD directory structure
#    - Creates an index.html file with links to all the HTML files
#    - Copies the images to the YYYY/MM/DD directory structure
#
# --------------------------------------------------------------------------------------
import argparse
import datetime
import fnmatch
import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import date

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: [@ %(filename)s:%(lineno)d] ==> %(message)s",
)
logger = logging.getLogger(__name__)

MARKDOWN_FILES_LIST = "md_files.yml"
CHECKSUM_FILE = ".checksums.txt"

# List of files to be excluded from index.html page.
EXCLUSION_LIST = [
    "policy.html",
    "index_template.html",
    "graph_viz.html",
]


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
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta
        name="description"
        content="{title}"
        />
        <meta name="keywords" content="Cloud Computing" />
        <link rel="shortcut icon" type="image/png" href="{domain}/images/logo.png">
        <title>{title}</title>

        <link rel="stylesheet" href="{domain}/css/prism.css" />
        <link rel="stylesheet" href="{domain}/css/style.css" />

        <link
        rel="stylesheet"
        media="screen and (max-width: 1024px)"
        href="{domain}/css/mobile.css"
        />

        <script src="{domain}/js/prism.js"></script>
    </head>

    <body>
        <!-- Navbar -->
        <nav id="main-nav">
        <div class="container">
            <!-- Menu -->
            <div class="logo">Ravi</div>

            <ul>
            <li><a href="#">Home</a></li>
            <li>
                <a href="https://github.com/ryandam9" target="_blank">Projects</a>
            </li>
            <li><a class="current" href="{domain}/blog.html" target="_blank">Blog</a></li>
            <li><a href="{domain}/about.html" target="_blank">About</a></li>
            <li>
                <a href="https://github.com/ryandam9" target="_blank">GitHub</a>
            </li>
            </ul>
        </div>
        </nav>

        <section>
        <div class="content-section">
            <div class="container-1">
    """


def get_html_tail(domain: str) -> str:
    """
    Prepares the HTML tail section

    :param domain: Domain name
    :return: HTML tail section
    """
    return f"""
        </div>

        <!-- Table of contents -->
        <div class="container-2">
          <aside>
            <div id="toc-container"></div>
          </aside>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer id="main-footer">
      <div class="container">
        <div class="footer-container">
          <div>Generated using <a href="https://github.com/ryandam9/static_site_generator">Static Site Generator</a></div>
        </div>
      </div>
    </footer>

    <script src="{domain}/js/app.js"></script>
  </body>
</html>
    """


def read_yaml_file():
    """
    Reads the YAML file and returns the contents as a dictionary
    """
    try:
        with open(MARKDOWN_FILES_LIST, "r") as file:
            yaml_file = yaml.safe_load(file)

        logger.info(f"YAML File read: {MARKDOWN_FILES_LIST}")
        return yaml_file
    except Exception as err:
        logger.error(f"Error reading {MARKDOWN_FILES_LIST} file - {err}")
        sys.exit(1)


def copy_images_to_target_dir(
    markdown_dir: str, html_contents: str, target_dir: str
) -> int:
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

    count = 0

    if matches:
        for image_path in matches:
            image_path = image_path[0] if image_path[0] else image_path[1]

            # Ignore the paths that have "img"
            if "http:" in image_path:
                continue

            image_path = image_path.replace("../", "")
            image_path = image_path.replace("./", "")
            image_abs_path = os.path.abspath(os.path.join(markdown_dir, image_path))

            try:
                shutil.copy(image_abs_path, target_dir)
                logger.info(f"Image File {image_abs_path} copied to {target_dir}")
                count += 1
            except Exception as err:
                logger.error(f"Error copying image file {image_path} - {err}")
                logger.error(f"Markdown file directory: {markdown_dir}")
                logger.error(f"Target directory: {target_dir}")
                logger.error("Image files identified in the markdown file:", matches)
                logger.error("html, contents:", html_contents)
                sys.exit(1)

    return count


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
        logger.error("Unable to convert markdown to HTML: ", str(err))
        logger.error(
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

    # Read the .checksums.txt file
    # It holds the checksum of the markdown file. It is used to determine if the
    # markdown file has changed.
    try:
        with open(f"{CHECKSUM_FILE}", "r") as file:
            for line in file:
                markdown_file, checksum = line.strip().split("~")
                checksums[markdown_file] = checksum
    except Exception as err:
        logger.error(f"Error reading {CHECKSUM_FILE} file - {err}")

    # Loop through the markdown files & convert them to HTML
    for index, entry in enumerate(yaml_contents["markdown_files"]):
        markdown_file_path = entry["file"]
        markdown_dir = os.path.dirname(markdown_file_path)
        markdown_file_name = os.path.basename(markdown_file_path)

        if not os.path.exists(markdown_file_path):
            logger.error(f"Markdown file {markdown_file_path} does not exist.")
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
            logger.info(f"{index + 1:<3} - [NOT CHANGED] - {markdown_file_path}")
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
        creation_date = "1900/01/01"

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

        logger.info(f"{index + 1} - HTML File written to {html_file}")
        logger.info("-" * 100)

    # Write the checksums to a file
    try:
        with open(f"{CHECKSUM_FILE}", "w") as file:
            for markdown_file, checksum in checksums.items():
                file.write(f"{markdown_file}~{checksum}\n")
    except Exception as err:
        logger.error(f"Error writing {CHECKSUM_FILE} file - {err}")

    logger.info("\nAll markdown files processed.")
    logger.info(f"\nChecksums written to {CHECKSUM_FILE} file.")


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
        logger.error(f"Error converting string to date - {entry}")
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

    logger.info("\nAll html files:")
    for x in html_files:
        logger.info(x)

    logger.info("\nGoing to create index.html file")
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

    index_page_template = "./blog_template.html"

    with open(index_page_template, "r") as file:
        template = file.read()

    index_page_content = template.replace("[[links]]", html_list)
    index_page = os.path.join(INDEX_PAGE_DIR, "blog.html")

    # Delete if exists
    if os.path.exists(index_page):
        os.remove(index_page)

    with open(index_page, "w") as file:
        file.write(index_page_content)

    logger.info(f"Blog page written to {index_page}")


def create_site_map():
    """
    Creates a sitemap.txt file
    :return: None
    """
    logger.info("\nInside [create_site_map]")

    sitemap_file_location = os.path.join(INDEX_PAGE_DIR, "sitemap.txt")
    sitemap_file = open(sitemap_file_location, "w")
    html_files = collect_all_html_files()

    for entry in html_files:
        entry = entry.replace(TARGET_DIR, f"{DOMAIN_WITH_PORT}/blog")
        sitemap_file.write(entry + "\n")

    sitemap_file.close()
    logger.info(f"Sitemap file created - {sitemap_file_location}")


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

    logger.info("\nMD5 Checksums:")
    for filename, md5 in checksums.items():
        logger.info(f"{md5} {filename}")

    return checksums


def main():
    yaml_contents = read_yaml_file()
    convert_markdown_to_html_wrapper(yaml_contents)
    prepare_index_page()
    create_site_map()


# --------------------------------------------------------------------------------------------------#
# Main section                                                                                      #
# --------------------------------------------------------------------------------------------------#
parser = argparse.ArgumentParser()

parser.add_argument(
    "--index_page_dir",
    help="Index page directory [Location where generated HTML files will be placed]",
    type=str,
)

parser.add_argument(
    "--domain",
    help="Domain name [E.g. ryandam.net, localhost].",
    type=str,
)

args = parser.parse_args()

# Print the help message
if not vars(args):
    parser.print_help()

INDEX_PAGE_DIR = args.index_page_dir
DOMAIN = args.domain

# Target directory
if INDEX_PAGE_DIR is not None:
    TARGET_DIR = os.path.join(INDEX_PAGE_DIR, "blog")
else:
    logger.error("ERROR: Index page directory is not specified.")
    logger.error(
        "       Please specify the index page directory using the --index_page_dir argument."
    )
    sys.exit(1)

if DOMAIN is None:
    logger.error(
        "ERROR: Domain is needed. For localhost, pass localhost as the domain."
    )
    logger.error("       Please specify domain name using --domain argument.")
    sys.exit(1)

# Normally, websites are hosted on port 80. We don't need to specify the port number in the URL.
if "localhost" not in DOMAIN:
    DOMAIN_WITH_PORT = f"https://{DOMAIN}"
else:
    DOMAIN_WITH_PORT = f"http://{DOMAIN}:8000"

if __name__ == "__main__":
    main()
