#!/bin/sh

# ----------------------------------------------------------------------------#
# assemble.sh                                                                 #
#   Assembles various components to set up ryandam.net                        #
#                                                                             #
#    echo "Usage: $0 [yes]"
#    echo "  yes: Deploy to CloudFront"
#                                                                             #
# ----------------------------------------------------------------------------#

deploy_to_cloud="$1"

# If not passed, default to false
if [ -z "$deploy_to_cloud" ]; then
    deploy_to_cloud="false"
    echo "NOTE: Not Deploying to Cloud. If you want, pass a flag 'yes'"
fi

WEB_SITE_NAME="ryandam.net"
WEB_SITE_LOCATION="$HOME/Desktop/${WEB_SITE_NAME}"
STYLE_NAME="blue"

# ----------------------------------------------------------------------------#
# DO NOT Delete this unless to regenerate all the HTML files from Markdown    #
# ----------------------------------------------------------------------------#
# rm ./checksums.txt

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

if [ "$deploy_to_cloud" = "true" ]; then
    python3 app.py \
        --index_page_dir "${WEB_SITE_LOCATION}" \
        --domain https://ryandam.net \
        --cloudfront_dist_id "E3T6GHYM5S5H1J"
else
    python3 app.py \
        --index_page_dir "${WEB_SITE_LOCATION}"
fi

exit 0
