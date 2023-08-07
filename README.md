# Static Blog Generator

## Overview
I always wanted to setup my blog by converting the markdown files I have and applying some styling using CSS. This repo is the code I use to generate my blog https://ryandam.net.
## Repo structure

```sh
░▒▓    ~/Desktop/static_site_generator ▓▒░ tree
```

```sh
.
├── README.md
├── app.py
├── checksums.txt
├── index_template.html
├── md_files.yml
└── styles
		...
        └── policy.html

6 directories, 22 files
```

- `app.py` - A python script that converts markdown files to HTML Pages.
- `checksums.txt` - Generated file. Each markdown file will have an entry in this file. Used to check if a markdown file has been updated since last time its html got generated.
- `index_template.html` - Template used to generate main `index.html` file.
- `md_files.yml` - A list of markdown files that will be converted to HTML.
- `policy.html` - Site policy. It is not applicable for all cases.

> Note that, actual markdown to HTML conversion happens via a package  `markdown` which is written in Dart. More details are present here - https://pub.dev/packages/markdown/install.

### Dependencies
This script depends on `markdown` package that converts markdown files to HTML. It is written in Dart. 
- Install it by following the instructions at https://pub.dev/packages/markdown/install. 
- [Dart](https://dart.dev/) needs to be installed for this.

#### Install the package

```sh
dart pub global activate markdown
```

```sh
markdown --help
```

```sh
Usage: markdown.dart [options] [file]

Parse [file] as Markdown and print resulting HTML. If [file] is omitted,
use stdin as input.

By default, CommonMark Markdown will be parsed. This can be changed with
the --extensionSet flag.

--help                          Print help text and exit
--version                       Print version and exit
--extension-set                 Specify a set of extensions

      [CommonMark] (default)    Parse like CommonMark Markdown (default)
      [GitHubFlavored]          Parse like GitHub Flavored Markdown
      [GitHubWeb]               Parse like GitHub's Markdown-enabled web input fields
      [none]                    No extensions; similar to Markdown.pl
```

Test the installation by using a sample markdown.

```sh
markdown ~/Desktop/ryandam.net/links.md > ~/Desktop/ryandam.net/web/links.html
```

#### Another option - Compiling from Source

```sh
git clone git@github.com:dart-lang/markdown.git
cd markdown

# Download dependencies
dart pub get

dart compile exe bin/markdown.dart
```

- Update `PATH` variable to point the binary.
****
## Specifying Markdown file locations

- Update `md_files.yml` file by specifying the markdown file locations.
***
## How to run

```sh
python app.py --help
```

```sh
usage: app.py [-h] [--domain DOMAIN] [--port PORT] [--index_page_dir INDEX_PAGE_DIR] [--cloudfront_dist_id CLOUDFRONT_DIST_ID]

options:
  -h, --help            show this help message and exit
  --domain DOMAIN       Domain name [E.g. https://ryandam.net, http://localhost]. Default is http://localhost
  --port PORT           Port number [Default: 8000]
  --index_page_dir INDEX_PAGE_DIR
                        Index page directory [Location where HTML files will be placed]
  --cloudfront_dist_id CLOUDFRONT_DIST_ID
                        CloudFront distribution ID [For Blogs deployed on AWS]
```
****
## Local run

```shell
python app.py --index_page_dir "/Users/rk/Desktop/ryandam.net"
```

- In this case, generated HTML files will be stored at `/Users/rk/Desktop/ryandam.net`. 
- They can be viewed locally using a web server. If python is available:
	```sh
	cd /Users/rk/Desktop/ryandam.net
	python -m http.server
	```

```sh
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
::1 - - [07/Aug/2023 14:52:39] "GET / HTTP/1.1" 304 -
::1 - - [07/Aug/2023 14:52:39] "GET /css/generic.css HTTP/1.1" 200 -
::1 - - [07/Aug/2023 14:52:39] "GET /images/logo.png HTTP/1.1" 200 -
...
```
****
## Deploying to server 
- My blog is hosted on AWS S3. 
- This script generates the html files and uploads them to S3.

```shell
python app.py --index_page_dir "/Users/rk/Desktop/ryandam.net" --domain https://ryandam.net --cloudfront_dist_id "XXXXXXXXXXX"
```

- `index_page_dir` - HTML Files will be stored here. 
- `domain` - My website domain.
- `cloudfront_dist_id` - My blog is hosted on AWS S3 using CloudFront Distribution.  
****
## Checksum file
- To avoid converting the markdown files every time the script is run, the `checksums.txt` is used. 
- It is a generated file (**It can be safely deleted**)
- This file controls whether a markdown to be converted to HTML or not (*Once a markdown file is converted to HTML, it will not be converted again unless it is updated*)
****
## Styling

- Default styling is applied by copying the required files from `styles` directory.
- For Code highlighting, https://prismjs.com/ is used.
****
## Images

- Some of the Images are generated using https://www.midjourney.com. 
- The background SVG Images are generated using https://app.haikei.app/ and https://www.shapedivider.app/.
****
## Bugs / Issues

- I have not fully tested this. 
- My approach is use and fix any issues that I face when they arise.
****
