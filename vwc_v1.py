#!/usr/bin/python
# Author: Zafar Gilani (CAM)
# Resources:
#	https://docs.python.org/2/tutorial/datastructures.html
#	https://docs.python.org/2/library/heapq.html
#	https://docs.python.org/2/library/zlib.html#module-zlib
# Purpose: Read a Hunter scan log file and group APs into virtual cells.
#          Output a JSON compatible file for virtual cells.
# Usage: python vwc_v1.py cc=0.50 oc=0.40,0.49 campaign/FullListScan.txt output.json

import sys
import os
import datetime
import zlib
import json

from difflib import SequenceMatcher

# adler32(data) & 0xffffffff generates same numeric value
# across all Python versions and platforms
#print zlib.adler32("Sahairy") & 0xffffffff

cc = sys.argv[1] # cell condition
cc = float(cc[3:])
oc = sys.argv[2] # overlap condition
#oc = float(oc[3:])
oc1 = float(oc[3:7])
oc2 = float(oc[8:])

inPath = sys.argv[3]
outPath = sys.argv[4]

lists_ap_mac = []
lists_ap_gps = []
lists_ap_olap = []

# ###########################
# ***** create_vcells() *****
# input:  raw WiFi scan longs
# output: virtual WiFi cells
def create_vcells():
	print "creating virtual WiFi cells"

	scan = "Scan#:"
	date = "Date:"

	text = ""
	timestamp = ""

	scan_mac = []
	scan_gps = []

	scnd_list = ""
	last = ""
	overlap = ""
	new_list = ""

	scan_count = 0

	with open(inPath, 'r') as fr:
		text = fr.readlines()
		#fr.close()
		#print text

	for line in text:
		if scan in line: # extract data from each scan
			scan_count = scan_count+1
			#timestamp = line[line.find(date)+6:]
		
			# ap
			#lists_ap_mac.append(str(scan_count))
			lists_ap_mac.append(scan_mac)
			scan_mac = []
		
			# gps
			#lists_ap_gps.append(str(scan_count))
			lists_ap_gps.append(scan_gps)
			scan_gps = []

			if scan_count >= 3: # start forming cells, when 3 scans are completed
				# ap
				last_ap = lists_ap_mac.pop() # last scan
				scnd_last_ap = lists_ap_mac.pop() # second last scan
				intersection_ap = list(set(scnd_last_ap) & set(last_ap)) # intersection

				# ap gps
				last_gps = lists_ap_gps.pop() # last gps of last scan
				scnd_last_gps = lists_ap_gps.pop() # last gps of second last scan
				intersection_gps = list(set(scnd_last_gps) & set(last_gps)) # intersection

				#print "---- DEBUGGING // ITERATION " + str(scan_count)
				#print last_ap
				#print scnd_last_ap
				#print intersection_ap

				# implement cell condition
				#if SequenceMatcher(None, last_ap, scnd_last_ap).ratio() >= cc: # if >= cc% overlap
				if float(len(intersection_ap)) >= cc*float(len(scnd_last_ap)): # if >= cc% overlap
					# ap
					new_list_ap = list(set(scnd_last_ap) | set(last_ap)) # union, avoid dups 
					lists_ap_mac.append(new_list_ap)

					#gps
					new_list_gps = list(set(scnd_last_gps) | set(last_gps)) # union, avoid dups
					lists_ap_gps.append(new_list_gps)
				else: # if < cc% overlap
					# ap
					lists_ap_mac.append(scnd_last_ap)
					lists_ap_mac.append(last_ap)

					# gps
					lists_ap_gps.append(scnd_last_gps)
					lists_ap_gps.append(last_gps)

				#print new_list
		else: # compile scan lists
			line_tokens = line.split("\t") # [0] is lat, [1] is lng, [4] is MAC, [5] is SSID
			scan_mac.append(line_tokens[4])
			#scan_gps.append("{" + str(line_tokens[0]) + "," + str(line_tokens[1]) + "}")
			if scan_gps: # get rid of duplicates from lists_ap_gps
				last_scan_gps = scan_gps.pop()
				new_scan_gps = "{" + str(line_tokens[0]) + "," + str(line_tokens[1]) + "}"
				if last_scan_gps == new_scan_gps:
					scan_gps.append(last_scan_gps)
				else:
					scan_gps.append(last_scan_gps)
					scan_gps.append(new_scan_gps)
			else:
				scan_gps.append("{" + str(line_tokens[0]) + "," + str(line_tokens[1]) + "}")
			#scan_mac.append(zlib.adler32(line_tokens[5]) & 0xffffffff)
		
	header = str(scan_count) + " scans grouped into " + str(len(lists_ap_mac))  + " virtual cells"
	print header

# ***** create_vcells() *****
# ###########################

# #########################
# ***** append_olap() *****
# input:  virtual WiFi cells
# output: virtual WiFi cells with overlap information (geo-coordinates)
def append_olap():
	print "appending overlaps among virtual cells"

	empty_list = []
	add_empty = 0

	for i in range(0, len(lists_ap_gps)):
		# change this outer for loop to control how many neighbouring j cells to overlap with an i cell
		#for j in range(i+1, len(lists_ap_gps)): # general case: use all j cells for overlap with i cell
		for j in range(i+1, min(i+5, len(lists_ap_gps))): # restricting to next 4 (5-1) vcells only
			#ap_mac_union = list(set(lists_ap_mac[i]) | set(lists_ap_mac[j]))
			#ap_mac_intersection = list(set(lists_ap_mac[i]) & set(lists_ap_mac[j]))
			
			#ap_gps_union = list(set(lists_ap_gps[i]) | set(lists_ap_gps[j]))
			#ap_gps_intersection = list(set(lists_ap_gps[i]) & set(lists_ap_gps[j]))
			#ap_gps_intersection = list(set(lists_ap_gps[i]) | set(lists_ap_gps[j]))

			ap_gps_intersection = []
			max_ratio = 0.0
			for c in range(0, len(lists_ap_gps[i])):
				for d in range(0, len(lists_ap_gps[j])):
					ratio = SequenceMatcher(None, lists_ap_gps[i][c], lists_ap_gps[j][d]).ratio()
					# change these if blocks to control how many GPS values to keep per cell
					if float(ratio) >= float(max_ratio): # >, >=
						max_ratio = ratio
						#if ap_gps_intersection:
						#	ap_gps_intersection.pop()
						ap_gps_intersection.append(lists_ap_gps[j][d])

			ap_gps_intersection_new = []
			for k in range(0, len(ap_gps_intersection)): # intersection_new: {vcellid, olapid, lat, lng}
				item = ap_gps_intersection.pop()
				#if float(item.split(',')[0].split('{')[1]) != float(0):
				item_new = '{' + str(i) + ',' + str(j) + ',' +\
						item.split(',')[0].split('{')[1] + ',' +\
						item.split(',')[1].split('}')[0] + '}'
				#else:
				#	item_new = '{' + str(0) + ',' + str(0) + ',' +\
				#			item.split(',')[0].split('{')[1] + ',' +\
				#			item.split(',')[1].split('}')[0] + '}'
				ap_gps_intersection_new.append(item_new)

			# ensure unique items only in ap_gps_intersection_new
			tmp_set = set(ap_gps_intersection_new)
			ap_gps_intersection_new = list(tmp_set)

			#print "---- DEBUGGING // ITERATION " + str(i) + " " + str(j)
			#print lists_ap_gps[i]
			#print lists_ap_gps[j]
			#print union
			#print intersection
	
			# implement overlap condition (range)
			#if float(len(ap_gps_intersection_new)) >= oc*float(len(lists_ap_gps[i])):
			#if float(len(ap_gps_intersection_new)) >= oc1*float(len(lists_ap_gps[i])):
			if float(SequenceMatcher(None, lists_ap_mac[i], lists_ap_mac[j]).ratio()) >= float(oc1) and float(SequenceMatcher(None, lists_ap_mac[i], lists_ap_mac[j]).ratio()) <= float(oc2):
				lists_ap_olap.append(ap_gps_intersection_new)
				add_empty = add_empty + 1

		if add_empty == 0:
			lists_ap_olap.append(empty_list)
		else:
			add_empty = 0
	#lists_ap_olap.pop(0)
	#print lists_ap_olap
# ***** append_olap() *****
# #########################

# ##################
# ***** main() *****
# main method
def main():
	if str(sys.argv[1]) == "help":
		print "python <script>.py cc=[0.0 to 1.0] oc=[m to n],[n to o] /in/path/ /out/path/"
	elif len(sys.argv) < 4:
		print "try: python <script>.py help"
	else:
		create_vcells()
		append_olap()
		
		concatenated_list = ""

		# write out in JSON format, following:
		# [
		#   {
		#     vcellid: ID,
		#     count: count of APs (MACs),
		#     apMACs: ['MAC', 'MAC'],
		#     apGPS: [
		#       { "lat": LAT, "lng": LNG },
		#       { "lat": LAT, "lng": LNG } ],
		#     olaps: [
		#       { "lat": LAT, "lng": LNG, "id": UD },
		#       { "lat": LAT, "lng": LNG, "id": ID } ]
		#   }
		# ]

		for r in range(0, len(lists_ap_mac)):
			apMACs = ""
			for c in range(0, len(lists_ap_mac[r])):
				if c == 0:
					apMACs = apMACs + "\n"

				apMACs = apMACs + "\t\"" + list(lists_ap_mac[r])[c] + "\""
				
				if c == len(lists_ap_mac[r])-1:
					apMACs = apMACs + "\n"
				else:
					apMACs = apMACs + ",\n"

			apGPSs = ""
			for c in range(0, len(lists_ap_gps[r])):
				if c == 0: # first line should be pushed down
					apGPSs = apGPSs + "\n"

				apGPSs = apGPSs + "\t" + json.dumps({\
						'lat':\
						float(str(list(lists_ap_gps[r])[c]).split(',')[0].split('{')[1]),\
						'lng':\
						float(str(list(lists_ap_gps[r])[c]).split(',')[1].split('}')[0]),\
						},\
						separators=(',',':'))

				if c == len(lists_ap_gps[r])-1: # avoid comma last line
					apGPSs = apGPSs + "\n"
				else:
					apGPSs = apGPSs + ",\n"

			apOlaps = ""
			put_comma = 0
			#if lists_ap_olap[r] != "[]":
			if lists_ap_olap[r]:
				for s in range(0, len(lists_ap_olap)):
					if s == 0:
						apOlaps = apOlaps + "\n"
					# only the first item of lists_ap_olap[s]
					for c in range(0, len(lists_ap_olap[s])):
						if str(list(lists_ap_olap[s])[c]).split(',')[0].split('{')[1] == str(r):
						#if c == 0: # first line should be pushed down
						#	apOlaps = apOlaps + "\n"

							apOlaps = apOlaps + "\t" + json.dumps({\
									'id':\
									int(str(list(lists_ap_olap[s])[c]).split(',')[1]),\
									'lat':\
									float(str(list(lists_ap_olap[s])[c]).split(',')[2]),\
									'lng':\
									float(str(list(lists_ap_olap[s])[c]).split(',')[3].split('}')[0]),\
									},\
									separators=(',',':'))
					
							apOlaps = apOlaps + ",\n"

							#if c == len(lists_ap_olap[s])-1: # avoid comma last line
							#	apOlaps = apOlaps + "\n"
							#else:
							#	apOlaps = apOlaps + ",\n"

			# couldn't solve ",\n" above (don't know why) so resolved it here
			apOlaps = apOlaps[:-2] + "\n"

			concatenated_list = concatenated_list + "{\n" +\
					"\"vcellid\":" + str(r) + ",\n" +\
					"\"count\":" + str(len(lists_ap_mac[r])) + ",\n" +\
					"\"apMACs\": [" + str(apMACs) + "],\n" +\
					"\"apGPSs\": [" + str(apGPSs) + "],\n" +\
					"\"apOlaps\": [" + str(apOlaps) + "]\n" +\
					"}"

			if r == len(lists_ap_mac)-1:
				concatenated_list = concatenated_list + "\n"
			else:
				concatenated_list = concatenated_list + ",\n"

		concatenated_list = "[\n" + concatenated_list + "]"
		#print apMACs
		#print concatenated_list

		print str(len(lists_ap_mac))
		print str(len(lists_ap_gps))
		print str(len(lists_ap_olap))

		with open(outPath, 'w') as fw:
			fw.write("{0}\n".format(concatenated_list))
# ***** main() *****
# ##################

# calling main
main()

