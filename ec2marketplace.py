#!/usr/bin/python
#
# Copyright (c) 2013  Evgeny Gridasov (evgeny.gridasov@gmail.com)
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
import boto.ec2
import re
import string
import sys
from multiprocessing import Pool
import Queue

from BeautifulSoup import BeautifulSoup
try:
	import simplejson as json
except ImportError:
	import json

WORKERS=2

EC2_REGIONS = [
	"us-east-1",
	"us-west-1",
	"us-west-2",
	"eu-west-1",
	"ap-southeast-1",
	"ap-southeast-2",
	"ap-northeast-1",
	"sa-east-1"
]

EC2_INSTANCE_TYPES = {
	"t1.micro" : "t1micro",
	"m1.small" : "m1small",
	"m1.medium" : "m1medium",
	"m1.large" : "m1large",
	"m1.xlarge" : "m1xlarge",
	"m2.xlarge" : "m2xlarge",
	"m2.2xlarge" : "m22xlarge",
	"m2.4xlarge" : "m24xlarge",
	"c3.large" : "c3large",
	"c3.xlarge" : "c3xlarge",
	"c3.2xlarge" : "c32xlarge",
	"c3.4xlarge" : "c34xlarge",
	"c3.8xlarge" : "c38xlarge",
	"c1.medium" : "c1medium",
	"c1.xlarge" : "c1xlarge",
	"cc1.4xlarge" : "cc14xlarge",
	"cc2.8xlarge" : "cc28xlarge",
	"cg1.4xlarge" : "cg14xlarge",
	"cr1.8xlarge" : "cr18xlarge",
	"m3.xlarge" : "m3xlarge",
	"m3.2xlarge" : "m32xlarge",
	"hi1.4xlarge" : "hi14xlarge",
	"hs1.8xlarge" : "hs18xlarge",
	"g2.2xlarge" : "g22xlarge"
}

DEFAULT_CURRENCY = "USD"

PRODUCT_CACHE = {}

VERBOSE = False

def get_product_pricing(url):
	f = urllib2.urlopen(url);
	marketplace = BeautifulSoup(f.read())
	monthly = marketplace.find('span', attrs={'id':'monthly-fee-text'})
	m = 0
	if monthly:
		m = string.replace(monthly.text, "$", "")
	result = { 
			"monthly" : m,
			"regions" : {}
			}	
	
	pricecount = 0
	for region in EC2_REGIONS:
		region_result = []
		result["regions"][region] = region_result
		region_table = marketplace.find('table', {'id': (region + '-pricing-matrix')})

		if region_table:
			headers = region_table.findAll('th')
				
			for instance in EC2_INSTANCE_TYPES:
				row = region_table.find('tr', {'id' : region + "-" + EC2_INSTANCE_TYPES[instance] + "-row"})
				if row :
					price_data = {}
					region_result.append(price_data)
					values = row.findAll('td')
					if values :
						i = 0
						price_data["instance"] = instance
						for v in values:
							hdr = headers[i]['class']
							text = v.text
							match = re.search("\$([0-9]+\.[0-9]+)/hr", text)
							if match :
								price_data[hdr] = match.group(1)
							else :
								price_data[hdr] = text
							i = i + 1
							pricecount = pricecount + 1
	if pricecount == 0:
		verbose("Warning: no prices extracted from " + url)
	return result



def search_product(code):
	f = urllib2.urlopen("https://aws.amazon.com/marketplace/search/results?searchTerms=" + code)
	search = BeautifulSoup(f.read())
	div = search.find("div", {"class":"product-title"})
	if div :
		url = div.find("a")
		if url :
			return "https://aws.amazon.com" + url['href']
	return None


def prepare_product(code, image):
	url = search_product(code)
	if url :
		result = get_product_pricing(url)
		return [result, image, code]
	else :
		verbose("Could not find product " + code )
		return [None, image, code]
		
def get_ec2_marketplace_prices(filter_region=None, filter_instance_type=None):
	get_specific_region = (filter_region is not None)
	pool = Pool(processes=WORKERS)
	queue = Queue.Queue(maxsize=WORKERS)
	
	result = {
			"regions" : {}
			}
	
	for region in EC2_REGIONS:
		if get_specific_region and filter_region != region :
			continue
		if not region in result["regions"] :
			result["regions"][region] = []
		
		verbose("Connecting to " + region)
		ec2 = boto.ec2.connect_to_region(region)
		
		verbose("Getting images")
		images = ec2.get_all_images(owners=["aws-marketplace"])
		
		totalCount = len(images)
		currentImage = 1
		
		region_result = result["regions"][region]
		
		for image in images :
			verbose("Processing " + image.id + " [" + str(currentImage) + "/" + str(totalCount) + "]")
			currentImage = currentImage + 1			
			match = re.search(r".*-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-ami.*", image.location)
			if queue.full():
				process_image(queue, region, region_result, filter_instance_type)
			if match:
				code = match.group(1)
				if code in PRODUCT_CACHE:
					process_image2(region, PRODUCT_CACHE[code], image, region_result, filter_instance_type)
				else:
					queue.put(pool.apply_async(prepare_product, [code, image]))
		while not queue.empty() :
			process_image(queue, region, region_result, filter_instance_type)
			
	return result


def process_image(queue, region, region_result, filter_instance_type=None):
	records = queue.get().get()
	if records:
		product = records[0]
		image = records[1]
		code = records[2]
		PRODUCT_CACHE[code] = product
		process_image2(region, product, image, region_result, filter_instance_type)


def process_image2(region, product, image, region_result, filter_instance_type=None):
	get_specific_instance_type = (filter_instance_type is not None)
	if product:
		rp = product["regions"][region]
		for instance in rp :
			if get_specific_instance_type and instance["instance"] != filter_instance_type:
				continue
			i = {}
			for k in instance:
				i[k] = instance[k]
			i["ami"] = image.id
			i["monthly"] = product["monthly"]
			region_result.append(i)
	
	
						
def verbose(str):
	if VERBOSE:
		sys.stderr.write(str + "\n")				
		
if __name__ == "__main__":
	def none_as_string(v):
		if not v:
			return ""
		else:
			return v

	try:
		import argparse 
	except ImportError:
		print "ERROR: You are running Python < 2.7. Please use pip to install argparse:   pip install argparse"


	parser = argparse.ArgumentParser(add_help=True, description="Print out the current prices of EC2 marketplace instances")
	parser.add_argument("--filter-region", "-fr", help="Filter results to a specific region", choices=EC2_REGIONS, default=None)
	parser.add_argument("--filter-type", "-ft", help="Filter results to a specific instance type", choices=EC2_INSTANCE_TYPES, default=None)
	parser.add_argument("--verbose", "-v", help="Verbose output to stderr", action="store_true")
	parser.add_argument("--workers", "-w", help="Number of workers", default=2)
	parser.add_argument("--format", "-f", choices=["json", "table", "csv"], help="Output format", default="table")

	args = parser.parse_args()
	
	VERBOSE = args.verbose
	WORKERS = int(args.workers)
	
	verbose("Using " + str(WORKERS) + " workers")
	
	data = get_ec2_marketplace_prices(args.filter_region, args.filter_type)

	if args.format == "table":
		try:
			from prettytable import PrettyTable
		except ImportError:
			print "ERROR: Please install 'prettytable' using pip:    pip install prettytable"

	if args.format == "json":
		print json.dumps(data)
	elif args.format == "table":
		x = PrettyTable()

		try:			
			x.set_field_names(["region", "ami", "type", "monthly", "software", "ec2", "total"])
		except AttributeError:
			x.field_names = ["region", "ami", "type", "monthly", "software", "ec2", "total"]

		try:
			x.aligns[-1] = "l"
		except AttributeError:
			x.align["total"] = "l"

		for r in data["regions"]:
			for it in data["regions"][r]:
				x.add_row([r, it["ami"], it["instance"], it["monthly"], none_as_string(it["price-software"]), none_as_string(it["price-ec2"]), none_as_string(it["price-total-column"])])
		print x
	elif args.format == "csv":
		print "region,ami,type,monthly,software,ec2,total"
		for r in data["regions"]:
			for it in data["regions"][r]:
				print "%s,%s,%s,%s,%s,%s,%s" % (r, it["ami"], it["instance"], it["monthly"], none_as_string(it["price-software"]), none_as_string(it["price-ec2"]), none_as_string(it["price-total-column"]))
