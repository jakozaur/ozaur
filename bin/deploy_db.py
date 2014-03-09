from os.path import expanduser
import boto
import boto.rds2
import boto.vpc
import sys
import os
import requests

CREDENTIALS_PATH = expanduser("~/.elasticbeanstalk/aws_credential_file")

boto.config.load_credential_file(CREDENTIALS_PATH)

rds = boto.rds2.connect_to_region("us-west-2")
result = rds.describe_db_instances()
instances = result["DescribeDBInstancesResponse"]["DescribeDBInstancesResult"]["DBInstances"]

if len(instances) == 0:
  print "No RDS instances... quiting"
  sys.exit(-1)

if len(instances) > 1:
  print "More than one RDS instances"
  print "TODO: implement selection"
  sys.exit(-1)

instance = instances[0]

safe_url = "postgresql://%s:%%s@%s:%s/%s" % (
    instance["MasterUsername"],
    instance["Endpoint"]["Address"],
    instance["Endpoint"]["Port"],
    instance["DBName"]) 
db_security_groups = [group["VpcSecurityGroupId"] for group in instance["VpcSecurityGroups"]]
assert len(db_security_groups) == 1, "I would like to see just one group"

print "Found db url", safe_url 
db_pass = filter(lambda x: x[0].endswith("rdsmasterpassword"), boto.config.items("Credentials"))
assert len(db_pass) == 1, "Expect one db password"

url = safe_url % (db_pass[0][1])

os.environ["OZAUR_DB_URL"] = url

vpc = boto.vpc.connect_to_region("us-west-2")

print "Allowing us to talk to DB"
group_id = db_security_groups[0]
args = {
  "group_id": db_security_groups[0],
  "ip_protocol": "tcp",
  "cidr_ip": requests.get("http://ip.42.pl/raw").text + "/32",
  "to_port": instance["Endpoint"]["Port"],
  "from_port": instance["Endpoint"]["Port"],
    }
response = vpc.authorize_security_group(**args)
assert response, "Can't authorize RDS to talk with me"

import database
print "Creating DB schema"
database.create_schema()

print "Removing us from being able to talk to DB"
response = vpc.revoke_security_group(**args)
assert response, "Can't revoke RDS to talk with me"


