# Cloudflare Updater
Python script to update Cloudflare DNS records when a server's IP address changes

## Installation:
Get the script and make it executable:

    git clone https://github.com/jcharman/Cloudflare-Updater
    chmod +x ./updateCloudflare.py
Copy the example config file into place:

    cp ./updateCloudflare.conf.example updateCloudflare.conf
Edit the file with values for your setup.

Run the script:

    ./updateCloudflare.py

## Usage
This script is designed to be run by cron periodically. On each run it will get the server's current IP, check it against the IP last time the script ran and update Cloudflare if necessary. If the script has not been run before it will get the current IP address from Cloudflare.

NOTE: This script WILL NOT detect manual changes to cloudflare and will only update the IP when it detects that the server's IP address has changed. To force the script to check the current IP in Cloudflare, delete the updateCloudflare.lastip file.