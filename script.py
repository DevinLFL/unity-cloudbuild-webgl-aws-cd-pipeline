import requests
import json
import tinys3
import zipfile
import StringIO
import os

def conditionalBuildTarget(targetName):
    def decorator(function):
        def wrapper(*args, **kwargs):
            if args[0]["body-json"]["buildTargetName"] != targetName:
        	    return "Skipping deploy"
            else:
                return function(*args, **kwargs)
        return wrapper
    return decorator


@conditionalBuildTarget(os.environ.get('BUILD_TARGET_TO_DEPLOY', 'HandsOnMedical'))
def lambda_handler(event, context):
	conn = tinys3.Connection(
	    os.environ['S3_ACCESS_KEY'], os.environ['S3_SECRET_KEY'])
	tokenId = "Basic " + os.environ['UNITY_API_KEY']
	s3bucket = os.environ['S3_BUCKET_NAME']
	print event

	buildLink = event["body-json"]["links"]["api_self"]["href"]

	authPayload = {"Authorization": tokenId}
	buildData = requests.get(
	    "https://build-api.cloud.unity3d.com" + buildLink, headers=authPayload)
	primaryLink = json.loads(buildData.text)["links"]["download_primary"]["href"]
	print primaryLink
	results = requests.get(primaryLink)
	zip = zipfile.ZipFile(StringIO.StringIO(results.content))
	zip.extractall("/tmp/")

	dirName = os.listdir("/tmp/")[0]
	print dirName
	baseDir = "/tmp/" + dirName

	f = open(baseDir + "/index.html", 'rb')
	conn.upload('index.html', f, s3bucket)

	files = os.listdir(baseDir + "/Build")
	for filename in files:
		f = open(baseDir + "/Build/" + filename, 'rb')
		conn.upload("Build/" + filename, f, s3bucket)
	files = os.listdir(baseDir + "/TemplateData")
	for filename in files:
		f = open(baseDir + "/TemplateData/" + filename, 'rb')
		conn.upload("TemplateData/" + filename, f, s3bucket)

	return event["body-json"]["buildTargetName"]
