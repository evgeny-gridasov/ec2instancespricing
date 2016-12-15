#!/usr/bin/python
#
# Copyright (c) 2012 Eran Sandler (eran@sandler.co.il),  http://eran.sandler.co.il,  http://forecastcloudy.net
# Portions Copyright (c) 2014 Evgeny Gridasov (evgeny.gridasov@gmail.com), http://egreex.com, https://awsreport.egreex.com
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
import argparse
import urllib2
import re
try:
	import simplejson as json
except ImportError:
	import json

EC2_REGIONS = [
	"us-east-1",
	"us-east-2",
	"us-gov-west-1",
	"us-west-1",
	"us-west-2",
	"ca-central-1",
	"eu-west-1",
	"eu-west-2",
	"eu-central-1",
	"ap-south-1",
	"ap-southeast-1",
	"ap-southeast-2",
	"ap-northeast-1",
	"ap-northeast-2",
	"sa-east-1"
]

EC2_INSTANCE_TYPES = [
	"t1.micro",
	"t2.micro",
	"t2.small",
	"t2.medium",
	"t2.large",
	"m1.small",
	"m1.medium",
	"m1.large",
	"m1.xlarge",
	"m2.xlarge",
	"m2.2xlarge",
	"m2.4xlarge",
	"c3.large",
	"c3.xlarge",
	"c3.2xlarge",
	"c3.4xlarge",
	"c3.8xlarge",
	"c4.large",
	"c4.xlarge",
	"c4.2xlarge",
	"c4.4xlarge",
	"c4.8xlarge",
	"c1.medium",
	"c1.xlarge",
	"cc1.4xlarge",
	"cc2.8xlarge",
	"cg1.4xlarge",
	"cr1.8xlarge",
	"m3.medium",
	"m3.large",
	"m3.xlarge",
	"m3.2xlarge",
	"m4.large",
	"m4.xlarge",
	"m4.2xlarge",
	"m4.4xlarge",
	"m4.10xlarge",
	"m4.16xlarge",
	"hi1.4xlarge",
	"hs1.8xlarge",
        "p2.xlarge",
        "p2.8xlarge",
        "p2.16xlarge",
	"g2.2xlarge",
	"g2.8xlarge",
	"i2.xlarge",
	"i2.2xlarge",
	"i2.4xlarge",
	"i2.8xlarge",
	"r3.large",
	"r3.xlarge",
	"r3.2xlarge",
	"r3.4xlarge",
	"r3.8xlarge",
	"d2.xlarge",
	"d2.2xlarge",
	"d2.4xlarge",
	"d2.8xlarge"
]

EC2_OS_TYPES = [
	"linux",       # api platform name = "linux"
	"mswin",       # api platform name = "windows"
	"rhel",        # api platform name = ""
	"sles",        # api platform name = ""
	"mswinSQL",    # api platform name = "windows"
	"mswinSQLWeb", # api platform name = "windows"
	"mswinSQLEnt", # api platform name = "windows"
]

JSON_NAME_TO_EC2_REGIONS_API = {
	"us-east" : "us-east-1",
	"us-east-1" : "us-east-1",
	"us-east-2" : "us-east-2",
	"us-west" : "us-west-1",
	"us-west-1" : "us-west-1",
	"us-gov-west-1" : "us-gov-west-1",
	"us-west-2" : "us-west-2",
	"ca-central-1" : "ca-central-1",
	"eu-ireland" : "eu-west-1",
	"eu-west-1" : "eu-west-1",
	"eu-west-2" : "eu-west-2",
	"eu-frankfurt" : "eu-central-1",
	"eu-central-1" : "eu-central-1",
	"apac-sin" : "ap-southeast-1",
	"ap-south-1" : "ap-south-1",
	"ap-southeast-1" : "ap-southeast-1",
	"ap-southeast-2" : "ap-southeast-2",
	"apac-syd" : "ap-southeast-2",
	"apac-tokyo" : "ap-northeast-1",
	"ap-northeast-1" : "ap-northeast-1",
	"ap-northeast-2" : "ap-northeast-2",
	"sa-east-1" : "sa-east-1"
}

INSTANCES_ON_DEMAND_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js"
INSTANCES_ON_DEMAND_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/rhel-od.min.js"
INSTANCES_ON_DEMAND_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/sles-od.min.js"
INSTANCES_ON_DEMAND_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswin-od.min.js"
INSTANCES_ON_DEMAND_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQL-od.min.js"
INSTANCES_ON_DEMAND_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQLWeb-od.min.js"
INSTANCES_ON_DEMAND_WINSQLENT_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQLEnterprise-od.min.js"

INSTANCES_OLD_ON_DEMAND_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/linux-od.min.js"
INSTANCES_OLD_ON_DEMAND_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/rhel-od.min.js"
INSTANCES_OLD_ON_DEMAND_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/sles-od.min.js"
INSTANCES_OLD_ON_DEMAND_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/mswin-od.min.js"
INSTANCES_OLD_ON_DEMAND_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/mswinSQL-od.min.js"
INSTANCES_OLD_ON_DEMAND_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/mswinSQLWeb-od.min.js"
INSTANCES_OLD_ON_DEMAND_WINSQLENT_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/mswinSQLEnterprise-od.min.js"

INSTANCES_RESERVED_LIGHT_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/linux-ri-light.min.js"
INSTANCES_RESERVED_LIGHT_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/rhel-ri-light.min.js"
INSTANCES_RESERVED_LIGHT_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/sles-ri-light.min.js"
INSTANCES_RESERVED_LIGHT_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswin-ri-light.min.js"
INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQL-ri-light.min.js"
INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQLWeb-ri-light.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/linux-ri-medium.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/rhel-ri-medium.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/sles-ri-medium.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswin-ri-medium.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQL-ri-medium.min.js"
INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQLWeb-ri-medium.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/linux-ri-heavy.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/rhel-ri-heavy.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/sles-ri-heavy.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswin-ri-heavy.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQL-ri-heavy.min.js"
INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/mswinSQLWeb-ri-heavy.min.js"
INSTANCES_SPOT_URL = "http://spot-price.s3.amazonaws.com/spot.js"

INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_linux.min.js"
INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_redhatlinux.min.js"
INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_suselinux.min.js"
INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_mswin.min.js"
INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_mswinsqlstd.min.js"
INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/light_mswinsqlweb.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_linux.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_redhatlinux.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_suselinux.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_mswin.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_mswinsqlstd.min.js"
INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/medium_mswinsqlweb.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_linux.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_redhatlinux.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_SLES_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_suselinux.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_mswin.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_mswinsqlstd.min.js"
INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/previous-generation/heavy_mswinsqlweb.min.js"

INSTANCES_RESERVED_V2_LINUX_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/linux-unix-shared.min.js"
INSTANCES_RESERVED_V2_RHEL_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/red-hat-enterprise-linux-shared.min.js"
INSTANCES_RESERVED_V2_SUSE_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/suse-linux-shared.min.js"
INSTANCES_RESERVED_V2_WINDOWS_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/windows-shared.min.js"
INSTANCES_RESERVED_V2_WINSQL_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/windows-with-sql-server-standard-shared.min.js"
INSTANCES_RESERVED_V2_WINSQLWEB_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/windows-with-sql-server-web-shared.min.js"
INSTANCES_RESERVED_V2_WINSQLENT_URL = "http://a0.awsstatic.com/pricing/1/ec2/ri-v2/windows-with-sql-server-enterprise-shared.min.js"

INSTANCES_ONDEMAND_OS_TYPE_BY_URL = {
	INSTANCES_ON_DEMAND_LINUX_URL : "linux",
	INSTANCES_ON_DEMAND_RHEL_URL : "rhel",
	INSTANCES_ON_DEMAND_SLES_URL : "sles",
	INSTANCES_ON_DEMAND_WINDOWS_URL : "mswin",
	INSTANCES_ON_DEMAND_WINSQL_URL : "mswinSQL",
	INSTANCES_ON_DEMAND_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_ON_DEMAND_WINSQLENT_URL : "mswinSQLEnt",

	INSTANCES_OLD_ON_DEMAND_LINUX_URL : "linux",
	INSTANCES_OLD_ON_DEMAND_RHEL_URL : "rhel",
	INSTANCES_OLD_ON_DEMAND_SLES_URL : "sles",
	INSTANCES_OLD_ON_DEMAND_WINDOWS_URL : "mswin",
	INSTANCES_OLD_ON_DEMAND_WINSQL_URL : "mswinSQL",
	INSTANCES_OLD_ON_DEMAND_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_OLD_ON_DEMAND_WINSQLENT_URL : "mswinSQLEnt",
}

INSTANCES_RESERVED_OS_TYPE_BY_URL = {
	INSTANCES_RESERVED_LIGHT_RESERVATION_LINUX_URL : "linux",
	INSTANCES_RESERVED_LIGHT_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_RESERVED_LIGHT_RESERVATION_SLES_URL : "sles",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_LINUX_URL : "linux",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_SLES_URL : "sles",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_RESERVED_HEAVY_RESERVATION_LINUX_URL : "linux",
	INSTANCES_RESERVED_HEAVY_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_RESERVED_HEAVY_RESERVATION_SLES_URL : "sles",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_LINUX_URL : "linux",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_SLES_URL : "sles",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_LINUX_URL : "linux",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_SLES_URL : "sles",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_LINUX_URL : "linux",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_RHEL_URL : "rhel",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_SLES_URL : "sles",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINDOWS_URL :  "mswin",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQL_URL : "mswinSQL",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL : "mswinSQLWeb",
	
	INSTANCES_RESERVED_V2_LINUX_URL : "linux",
	INSTANCES_RESERVED_V2_RHEL_URL : "rhel",
	INSTANCES_RESERVED_V2_SUSE_URL : "suse",
	INSTANCES_RESERVED_V2_WINDOWS_URL : "mswin",
	INSTANCES_RESERVED_V2_WINSQL_URL : "mswinSQL",
	INSTANCES_RESERVED_V2_WINSQLWEB_URL : "mswinSQLWeb",
	INSTANCES_RESERVED_V2_WINSQLENT_URL : "mswinSQLEnt"

}

INSTANCES_RESERVED_RESERVATION_TYPE_BY_URL = {
	INSTANCES_RESERVED_LIGHT_RESERVATION_LINUX_URL : "light",
	INSTANCES_RESERVED_LIGHT_RESERVATION_RHEL_URL : "light",
	INSTANCES_RESERVED_LIGHT_RESERVATION_SLES_URL : "light",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINDOWS_URL : "light",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQL_URL : "light",
	INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL : "light",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_LINUX_URL : "medium",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_RHEL_URL : "medium",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_SLES_URL : "medium",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL : "medium",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQL_URL : "medium",
	INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL : "medium",	
	INSTANCES_RESERVED_HEAVY_RESERVATION_LINUX_URL : "heavy",
	INSTANCES_RESERVED_HEAVY_RESERVATION_RHEL_URL : "heavy",
	INSTANCES_RESERVED_HEAVY_RESERVATION_SLES_URL : "heavy",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINDOWS_URL : "heavy",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQL_URL : "heavy",
	INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL : "heavy",
	
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_LINUX_URL : "light",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_RHEL_URL : "light",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_SLES_URL : "light",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINDOWS_URL : "light",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQL_URL : "light",
	INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL : "light",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_LINUX_URL : "medium",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_RHEL_URL : "medium",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_SLES_URL : "medium",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL : "medium",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQL_URL : "medium",
	INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL : "medium",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_LINUX_URL : "heavy",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_RHEL_URL : "heavy",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_SLES_URL : "heavy",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINDOWS_URL : "heavy",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQL_URL : "heavy",
	INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL : "heavy",
	
}

DEFAULT_CURRENCY = "USD"

def _load_data(url):
	f = urllib2.urlopen(url).read()
	# remove comments
	f = re.sub("/\\*[^\x00]+\\*/", "", f, 0, re.M)
	# quote field names
	f = re.sub("([a-zA-Z0-9]+):", "\"\\1\":", f)
	# lf in the end
	f = re.sub(";", "\n", f)
	# null values -> None
	f = re.sub("null", "None", f);
	def callback(json):
		return json
	data = eval(f, {"__builtins__" : None}, {"callback" : callback} )
	return data

def get_ec2_reserved_instances_prices(filter_region=None, filter_instance_type=None, filter_os_type=None):
	""" Get EC2 reserved instances prices. Results can be filtered by region """

	get_specific_region = (filter_region is not None)
	get_specific_instance_type = (filter_instance_type is not None)
	get_specific_os_type = (filter_os_type is not None)

	currency = DEFAULT_CURRENCY

	urls = [
		INSTANCES_RESERVED_LIGHT_RESERVATION_LINUX_URL,
		INSTANCES_RESERVED_LIGHT_RESERVATION_RHEL_URL,
		INSTANCES_RESERVED_LIGHT_RESERVATION_SLES_URL,
		INSTANCES_RESERVED_LIGHT_RESERVATION_WINDOWS_URL,
		INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQL_URL,
		INSTANCES_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_LINUX_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_RHEL_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_SLES_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQL_URL,
		INSTANCES_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_LINUX_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_RHEL_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_SLES_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_WINDOWS_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQL_URL,
		INSTANCES_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL,
		
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_LINUX_URL,
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_RHEL_URL,
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_SLES_URL,
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINDOWS_URL,
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQL_URL,
		INSTANCES_OLD_RESERVED_LIGHT_RESERVATION_WINSQLWEB_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_LINUX_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_RHEL_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_SLES_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINDOWS_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQL_URL,
		INSTANCES_OLD_RESERVED_MEDIUM_RESERVATION_WINSQLWEB_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_LINUX_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_RHEL_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_SLES_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINDOWS_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQL_URL,
		INSTANCES_OLD_RESERVED_HEAVY_RESERVATION_WINSQLWEB_URL,
		
		INSTANCES_RESERVED_V2_LINUX_URL,
		INSTANCES_RESERVED_V2_RHEL_URL,
		INSTANCES_RESERVED_V2_SUSE_URL,
		INSTANCES_RESERVED_V2_WINDOWS_URL,
		INSTANCES_RESERVED_V2_WINSQL_URL,
		INSTANCES_RESERVED_V2_WINSQLWEB_URL,
		INSTANCES_RESERVED_V2_WINSQLENT_URL,
	]

	result_regions = []
	result_regions_index = {}
	result = {
		"config" : {
			"currency" : currency,
		},
		"regions" : result_regions
	}

	for u in urls:
		os_type = INSTANCES_RESERVED_OS_TYPE_BY_URL[u]
		if get_specific_os_type and os_type != filter_os_type:
			continue
		reservation_type = ""
		if u in INSTANCES_RESERVED_RESERVATION_TYPE_BY_URL:
			reservation_type = INSTANCES_RESERVED_RESERVATION_TYPE_BY_URL[u]
		data = _load_data(u)
		if "config" in data and data["config"] and "regions" in data["config"] and data["config"]["regions"]:
			for r in data["config"]["regions"]:
				if "region" in r and r["region"]:
					region_name = JSON_NAME_TO_EC2_REGIONS_API[r["region"]]
					if get_specific_region and filter_region != region_name:
						continue

					if region_name in result_regions_index:
						instance_types = result_regions_index[region_name]["instanceTypes"]
					else:
						instance_types = []
						result_regions.append({
							"region" : region_name,
							"instanceTypes" : instance_types
						})
						result_regions_index[region_name] = result_regions[-1]
						
					if "instanceTypes" in r:
						for it in r["instanceTypes"]:
							# old reserved instances
							if "sizes" in it:
								for s in it["sizes"]:
									_type = re.sub("[^a-z0-9.]*", "", s["size"])
	
									prices = {
										"1year" : {
											"hourly" : None,
											"upfront" : None
										},
										"3year" : {
											"hourly" : None,
											"upfront" : None
										}
									}
	
									if get_specific_instance_type and _type != filter_instance_type:
										continue
	
									for price_data in s["valueColumns"]:
										price = None
										try:
											price = float(price_data["prices"][currency])
										except ValueError:
											price = None
	
										if price_data["name"] == "yrTerm1":
											prices["1year"]["upfront"] = price
										elif price_data["name"] == "yrTerm1Hourly":
											prices["1year"]["hourly"] = price
										elif price_data["name"] == "yrTerm3":
											prices["3year"]["upfront"] = price
										elif price_data["name"] == "yrTerm3Hourly":
											prices["3year"]["hourly"] = price
									if prices["1year"]["upfront"] != None or prices["1year"]["hourly"] != None or prices["3year"]["upfront"] != None or prices["3year"]["hourly"] != None:
										instance_types.append({
											"type" : _type,
											"os" : os_type,
											"reservation" : reservation_type,
											"prices" : prices
										})
	
											
							# new reserved instances
							if "type" in it and "terms" in it:
								_type = it["type"]
								if get_specific_instance_type and _type != filter_instance_type:
										continue
								for term in it["terms"]:
									for purchaseOpt in term["purchaseOptions"]:
										upfront = ""
										hourly = ""
										prices = {}
										for price_data in purchaseOpt["valueColumns"]:
											if price_data["name"] == "upfront":
												upfront = (price_data["prices"]["USD"]).replace(",", "")
											if price_data["name"] == "monthlyStar":
												hourly = float(str.replace(price_data["prices"]["USD"],",","")) * 12 / 365 / 24 
										if term["term"] == "yrTerm1Standard":
											prices["1year"] = {"upfront" :  upfront, "hourly" : hourly}
										if term["term"] == "yrTerm3Standard":
											prices["3year"] = {"upfront" :  upfront, "hourly" : hourly}
										if term["term"] == "yrTerm3Convertible":
											prices["c3year"] = {"upfront" :  upfront, "hourly" : hourly}
										instance_types.append({
													"type" : _type,
													"os" : os_type,
													"reservation" : purchaseOpt["purchaseOption"],
													"prices" : prices
												})

	return result

def get_ec2_ondemand_instances_prices(filter_region=None, filter_instance_type=None, filter_os_type=None, pricing_type="ondemand"):
	""" Get EC2 on-demand or spot instances prices. Results can be filtered by region """

	get_specific_region = (filter_region is not None)
	get_specific_instance_type = (filter_instance_type is not None)
	get_specific_os_type = (filter_os_type is not None)

	currency = DEFAULT_CURRENCY
	
	if pricing_type == "ondemand":
		urls = [
			INSTANCES_ON_DEMAND_LINUX_URL,
			INSTANCES_ON_DEMAND_RHEL_URL,
			INSTANCES_ON_DEMAND_SLES_URL,
			INSTANCES_ON_DEMAND_WINDOWS_URL,
			INSTANCES_ON_DEMAND_WINSQL_URL,
			INSTANCES_ON_DEMAND_WINSQLWEB_URL,
			INSTANCES_ON_DEMAND_WINSQLENT_URL,
	
			INSTANCES_OLD_ON_DEMAND_LINUX_URL,
			INSTANCES_OLD_ON_DEMAND_RHEL_URL,
			INSTANCES_OLD_ON_DEMAND_SLES_URL,
			INSTANCES_OLD_ON_DEMAND_WINDOWS_URL,
			INSTANCES_OLD_ON_DEMAND_WINSQL_URL,
			INSTANCES_OLD_ON_DEMAND_WINSQLWEB_URL,
			INSTANCES_OLD_ON_DEMAND_WINSQLENT_URL
		]
	elif pricing_type == "spot":
		urls = [ INSTANCES_SPOT_URL ]
	else:
		raise ValueError("get_ec2_ondemand_instances_prices: pricing_type argument must be 'ondemand' or 'spot'")

	result_regions = []
	result = {
		"config" : {
			"currency" : currency,
			"unit" : "perhr"
		},
		"regions" : result_regions
	}

	for u in urls:
		os_type = None
		if pricing_type == "ondemand":
			os_type = INSTANCES_ONDEMAND_OS_TYPE_BY_URL[u]			
			if get_specific_os_type and os_type != filter_os_type:
				continue
				
		data = _load_data(u)
		if "config" in data and data["config"] and "regions" in data["config"] and data["config"]["regions"]:
			for r in data["config"]["regions"]:
				if "region" in r and r["region"]:
					region_name = JSON_NAME_TO_EC2_REGIONS_API[r["region"]]

					if get_specific_region and filter_region != region_name:
						continue
	
					instance_types = []
					if "instanceTypes" in r:
						for it in r["instanceTypes"]:
							if "sizes" in it:
								for s in it["sizes"]:
									_type = re.sub("[^a-z0-9.]*", "", s["size"])
	
									for price_data in s["valueColumns"]:
										price = None
										os_type_report = None
										
										if pricing_type == "spot":
											os_type_report = price_data["name"]
											if get_specific_os_type and os_type_report != filter_os_type:
												continue
										else:
											os_type_report = os_type
											
										try:
											price = float(price_data["prices"][currency])
										except ValueError:
											price = None
										except TypeError:
											price = None
	
										if get_specific_instance_type and _type != filter_instance_type:
											continue
	
										instance_types.append({
											"type" : _type,
											"os" : os_type_report,
											"price" : price
										})
	
						result_regions.append({
							"region" : region_name,
							"instanceTypes" : instance_types
						})
	
	return result


if __name__ == "__main__":
	def none_as_string(v):
		if v == 0:
			return "0"
		if not v:
			return ""
		else:
			return v

	try:
		import argparse 
	except ImportError:
		print "ERROR: You are running Python < 2.7. Please use pip to install argparse:   pip install argparse"


	parser = argparse.ArgumentParser(add_help=True, description="Print out the current prices of EC2 instances")
	parser.add_argument("--type", "-t", help="Show ondemand, reserved, or spot instances", choices=["ondemand", "reserved", "spot"], required=True)
	parser.add_argument("--filter-region", "-fr", help="Filter results to a specific region", choices=EC2_REGIONS, default=None)
	parser.add_argument("--filter-type", "-ft", help="Filter results to a specific instance type", choices=EC2_INSTANCE_TYPES, default=None)
	parser.add_argument("--filter-os-type", "-fo", help="Filter results to a specific os type", choices=EC2_OS_TYPES, default=None)
	parser.add_argument("--format", "-f", choices=["json", "table", "csv"], help="Output format", default="table")

	args = parser.parse_args()

	if args.format == "table":
		try:
			from prettytable import PrettyTable
		except ImportError:
			print "ERROR: Please install 'prettytable' using pip:    pip install prettytable"

	data = None
	if args.type == "ondemand" or args.type == "spot":
		data = get_ec2_ondemand_instances_prices(args.filter_region, args.filter_type, args.filter_os_type, args.type)
	elif args.type == "reserved":
		data = get_ec2_reserved_instances_prices(args.filter_region, args.filter_type, args.filter_os_type)

	if args.format == "json":
		print json.dumps(data)
	elif args.format == "table":
		x = PrettyTable()

		if args.type == "ondemand" or args.type == "spot":
			try:			
				x.set_field_names(["region", "type", "os", "price"])
			except AttributeError:
				x.field_names = ["region", "type", "os", "price"]

			try:
				x.aligns[-1] = "l"
			except AttributeError:
				x.align["price"] = "l"

			for r in data["regions"]:
				region_name = r["region"]
				for it in r["instanceTypes"]:
					x.add_row([region_name, it["type"], it["os"], none_as_string(it["price"])])
		elif args.type == "reserved":
			try:
				x.set_field_names(["region", "type", "os", "reservation", "term", "price", "upfront"])
			except AttributeError:
				x.field_names = ["region", "type", "os", "reservation", "term", "price", "upfront"]

			try:
				x.aligns[-1] = "l"
				x.aligns[-2] = "l"
			except AttributeError:
				x.align["price"] = "l"
				x.align["upfront"] = "l"
			
			for r in data["regions"]:
				region_name = r["region"]
				for it in r["instanceTypes"]:
					for term in it["prices"]:
						x.add_row([region_name, it["type"], it["os"], it["reservation"], term, none_as_string(it["prices"][term]["hourly"]), none_as_string(it["prices"][term]["upfront"])])

		print x
	elif args.format == "csv":
		if args.type == "ondemand" or args.type == "spot":
			print "region,type,os,price"
			for r in data["regions"]:
				region_name = r["region"]
				for it in r["instanceTypes"]:
					print "%s,%s,%s,%s" % (region_name, it["type"], it["os"], none_as_string(it["price"]))
		elif args.type == "reserved":
			print "region,type,os,reservation,term,price,upfront"
			for r in data["regions"]:
				region_name = r["region"]
				for it in r["instanceTypes"]:
					for term in it["prices"]:
						print "%s,%s,%s,%s,%s,%s,%s" % (region_name, it["type"], it["os"], it["reservation"], term, none_as_string(it["prices"][term]["hourly"]), none_as_string(it["prices"][term]["upfront"]))
