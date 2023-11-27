# Static Blog Generator

## Overview

I always wanted to setup my blog by converting the markdown files I have and applying some styling using CSS. This repo is the code I use to generate my blog https://ryandam.net.

## Repo structure

```sh
░▒▓    ~/Desktop/static_site_generator ▓▒░ tree
```

```sh
├── README.md
├── app.py
├── assemble.sh
├── blog_template.html
├── index.html
├── md_files.yml
├── policy.html
└── styles
    ├── blue
    ├── index_page_black
    └── serious_earth
```

- `app.py` - A python script that converts markdown files to HTML Pages
- `assemble.sh` - shell script to assemble different parts. It also pushes the assets to S3 bucket and invalidates CloudFront distribution
- `blog_template.html` - Template used to generate `blog.html` file
- `index.html` - Main index page
- `md_files.yml` - A list of markdown files that will be converted to HTML
- `policy.html` - Site policy. It is not applicable for all cases.
- `styles` - A directory containing CSS styles grouped into directories.
- `.checksums.txt` - Generated file. Each markdown file will have an entry in this file. Used to check if a markdown file has been updated since last time its html got generated.

> Note that, actual markdown to HTML conversion happens via a package `markdown` which is written in Dart. More details are present here - https://pub.dev/packages/markdown/install.

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

---

## Specifying Markdown file locations

- Update `md_files.yml` file by specifying the markdown file locations.

---

## How to run

```sh
sh ./assemble.sh “ryandam.net" "CLOUDFRONT-DIST-ID"
```

- `ryandam.net` - Domain name
- `CLOUDFRONT-DIST-ID` - Actual CloudFront Distribution ID.

---

## Local run

```shell
cd static_site_generator
sh ./assemble.sh
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

---

## Checksum file

- To avoid converting the markdown files every time the script is run, the `checksums.txt` is used.
- It is a generated file (**It can be safely deleted**)
- This file controls whether a markdown to be converted to HTML or not (_Once a markdown file is converted to HTML, it will not be converted again unless it is updated_)

---

## Styling

- Default styling is applied by copying the required files from `styles` directory.
- For Code highlighting, https://prismjs.com/ is used.

---

## Images

- Some of the Images are generated using https://www.midjourney.com.
- The background SVG Images are generated using https://app.haikei.app/ and https://www.shapedivider.app/.

---

## Bugs / Issues

- I have not fully tested this.
- My approach is use and fix any issues that I face when they arise.

---
