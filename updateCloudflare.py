#!/usr/bin/python

try:
    import requests
    import json
    import tempfile
    import tldextract
    import os
except ModuleNotFoundError:
    print("Missing module, see requirements.txt")
    exit(1)

def getZone(email, apiKey, host):
    listZones = requests.get(f"https://api.cloudflare.com/client/v4/zones/", 
         headers={"X-Auth-Email": f"{email}","X-Auth-Key": f"{apiKey}","Content-Type": "application/json"}).json()

    if listZones["success"] != True:
        print("Could not get Zone ID from Cloudflare. Errors were: " + str(listZones["errors"]))
        exit(1)

    # Extract the root domain from the full host.
    extractedHost = tldextract.extract(host)
    domain = (extractedHost.domain + "." + extractedHost.suffix)

    for zone in listZones["result"]:
        if zone["name"] == domain:
            return zone["id"]
    
    print("Could not find a Zone ID for the specified domain.")
    exit(1)
        
def storeIP(ip):
    # Store the given IP in the lastip file.
    file = open(scriptDir + 'updateCloudflare.lastip', 'w+')
    file.write(ip)

def checkCloudflare(zone, email, apiKey, host):
    # Get all the records in the zone.
    allRecords = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone}/dns_records", 
         headers={"X-Auth-Email": f"{email}","X-Auth-Key": f"{apiKey}","Content-Type": "application/json"}).json()

    # Search for the defined zone in the list and get it's IP.
    for currentRecord in allRecords["result"]:
        if currentRecord["name"] == host:
            recordIP = currentRecord["content"]
            print(f"IP of {host} is " + recordIP)
            return(recordIP)

def updateCloudflare(zone, email, apiKey, host, ip):
    # Get all records for the given zone.
    allRecords = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone}/dns_records", 
        headers={"X-Auth-Email": f"{email}","X-Auth-Key": f"{apiKey}","Content-Type": "application/json"}).json()

    # Find the record for the domain we want to work on.
    for currentRecord in allRecords["result"]:
        if currentRecord["name"] == host:
            recordID = currentRecord["id"]
            print(f"ID for {host} is " + recordID)

    # Update our record with the new IP.
    result = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone}/dns_records/" + recordID, 
        headers={"X-Auth-Email": f"{email}","X-Auth-Key": f"{apiKey}","Content-Type": "application/json"}, 
        data='{"content":"%s"}' % ip).json()

    # Check if Cloudflare returned any errors.
    if result["success"] == True:
        print("Cloudflare was successfully updated")
    else:
        print("Updating failed, errors were: " + str(result["errors"]))

print(
    '''
    ------------------------------
    Cloudflare updater
    www.jakecharman.co.uk
    ------------------------------
    '''
)

# Get the directory of the script.
scriptDir = os.path.dirname(os.path.realpath(__file__)) + "/"

# Read in parameters from the config file.
try:
    configFile = open(scriptDir + "updateCloudflare.conf", "r")
except FileNotFoundError:
    print("Configuration file does not exist.")
    exit(1)

configLines = configFile.readlines()
for line in configLines:
    if line[0] == "#":
        continue
    # Remove any spaces from the line then split it to an array on the = sign.
    splitLn = line.replace(" ", "").strip().split('#')[0].split("=")

    # Pull in the known config lines.
    if (splitLn[0] == "email"):
        authEmail = splitLn[1]
    elif (splitLn[0] == "apiKey"):
        apiKey = splitLn[1]
    elif (splitLn[0] == "host"):
        hostToUpdate = splitLn[1]
    else:
        # Error out on an unknown config line.
        print("Unknown config: " + splitLn[0])
        exit(1)

# Get the Zone ID for the given hostname.
zoneID = getZone(authEmail, apiKey, hostToUpdate)

# Open the temp file.
try:
    file = open(scriptDir + 'updateCloudflare.lastip', 'r')
    lastip = file.read()
except FileNotFoundError:
    lastip = ""

if lastip == "":
    storedIP = False
    print("No stored IP... checking Cloudflare API")
    cloudflareIP = checkCloudflare(zoneID, authEmail, apiKey, hostToUpdate)
else:
    storedIP = lastip
    print("Stored IP is " + lastip)

# Get our external IP
ip = requests.get('https://api.ipify.org').text
print("Our current IP is " + ip)
if storedIP:    
    if ip == storedIP:
        print("IP has not changed since last run... Exiting")
        exit(0)
    else: 
        print("IP has changed since last run... Updating Cloudflare")
        storeIP(ip)
        updateCloudflare(zoneID, authEmail, apiKey, hostToUpdate, ip)
else:
    storeIP(ip)
    if ip == cloudflareIP:
        print("Cloudflare matches our current IP... Exiting")
        exit(0)
    else:
        print("Cloudflare IP does not match our current IP... Updating Cloudflare.")
        updateCloudflare(zoneID, authEmail, apiKey, hostToUpdate, ip)