#!/bin/sh

# ----------------------------------------------------------------------------#
# assemble.sh                                                                 #
#   Assembles various components to set up ryandam.net                        #
#                                                                             #
#    echo "Usage: $0 [yes]"
#    echo "  yes: Deploy to CloudFront"
#                                                                             #
# ----------------------------------------------------------------------------#

# Domain name of the blog
if [ -z "$1" ]; then
    domain_name="localhost"
else
    domain_name="$1"
fi

# CloudFront Distribution ID
if [ -z "$2" ]; then
    cloudfront_dist_id=""
    echo "NOTE: CloudFront Distribution ID not passed. Will not deploy to CloudFront"
else
    cloudfront_dist_id="$2"
fi

WEB_SITE_NAME="ryandam.net"
WEB_SITE_LOCATION="$HOME/Desktop/${WEB_SITE_NAME}"
STYLE_NAME="blue"

# ----------------------------------------------------------------------------#
# DO NOT Delete this unless to regenerate all the HTML files from Markdown    #
# ----------------------------------------------------------------------------#
rm -rf ./.checksums.txt
touch ./.checksums.txt

# ----------------------------------------------------------------------------#
# Delete some files at the target location
# ----------------------------------------------------------------------------#
rm -rf "${WEB_SITE_LOCATION}/css/*"
rm -rf "${WEB_SITE_LOCATION}/img/*"
rm -rf "${WEB_SITE_LOCATION}/js/*"
rm -rf "${WEB_SITE_LOCATION}/fonts/*"

mkdir -p "${WEB_SITE_LOCATION}/css/index"
mkdir -p "${WEB_SITE_LOCATION}/img"
mkdir -p "${WEB_SITE_LOCATION}/js"
mkdir -p "${WEB_SITE_LOCATION}/fonts"

# ----------------------------------------------------------------------------#
# Index Page
# ----------------------------------------------------------------------------#
cp index.html "${WEB_SITE_LOCATION}"
cp styles/index_page_black/css/* "${WEB_SITE_LOCATION}/css/index"
cp styles/index_page_black/img/* "${WEB_SITE_LOCATION}/img"

# ----------------------------------------------------------------------------#
# Copy blog posts related assets to the target location
# ----------------------------------------------------------------------------#
cp -R ./styles/${STYLE_NAME}/css/* "${WEB_SITE_LOCATION}/css"
cp -R ./styles/${STYLE_NAME}/fonts/* "${WEB_SITE_LOCATION}/fonts"
cp -R ./styles/${STYLE_NAME}/img/* "${WEB_SITE_LOCATION}/img"
cp -R ./styles/${STYLE_NAME}/js/* "${WEB_SITE_LOCATION}/js"

# ----------------------------------------------------------------------------#
# Site Policy
# ----------------------------------------------------------------------------#
cp ./policy.html "${WEB_SITE_LOCATION}"

# ----------------------------------------------------------------------------#
# Generate HTML Files from Markdown
# ----------------------------------------------------------------------------#
python3 app.py --index_page_dir "${WEB_SITE_LOCATION}" --domain "${domain_name}"
rc=$?

if [ $rc -ne 0 ]; then
    echo "ERROR: Failed to generate HTML files from Markdown"
    exit 1
fi

# ----------------------------------------------------------------------------#
# Sync with S3 bucket
# Note - Rather than syncing all files, we only sync the ones we need
#        selectively.
# ----------------------------------------------------------------------------#
if [ -n "${cloudfront_dist_id}" ]; then
    aws s3 sync "${WEB_SITE_LOCATION}" s3://"${domain_name}" \
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

    # ----------------------------------------------------------------------------#
    # Invalidate CloudFront
    # NOTE: As per https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html,
    #       the paths must be quoted.
    # ----------------------------------------------------------------------------#
    aws cloudfront create-invalidation --distribution-id="${cloudfront_dist_id}" --paths "/*"
fi

exit 0
