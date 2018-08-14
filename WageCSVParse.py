import sys
import contextlib
import csv
import re
import json
import argparse

@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()

parser = argparse.ArgumentParser(description='Process a wage file csv to return JSON formatted list of highest average job title for unique first names.')
parser.add_argument('--inputfile', '-if', default='./City_of_Seattle_Wage_Data.csv', help='Location of file to be read, defaults to City_of_Seattle_Wage_Data.csv in the current working directory.')
parser.add_argument('--outputfile', '-of', help='Optional location for an output file. If omitted, output will go to standard out.')
parser.add_argument('--strict', action='store_true')
args=parser.parse_args()

DEBUG = False

wageData = dict()

# Read Input File
with open(args.inputfile) as csvfile:
	wagesRawData = csv.reader(csvfile, delimiter=',', quotechar='"')

	# Check Header Row - also removes it from use in data set
	if(next(wagesRawData) != ['Department', 'Last Name', 'First Name', 'Job Title', 'Hourly Rate ']):
		print "Unexpected values in header row for CSV file."
		exit(1)

	# Set up Regular Expression to strip Job Titles of specific elements
	if(args.strict):
		# Strip from anywhere: comma or space followed by Sr, Sr, comma or space followed by any Roman Numeral followed by a space or dash or at the end of the string
		# Note: any less strict on Roman Numerals can lead to many capital letters getting stripped alone, though this current version might result in a "-" being removed where is possibly shouldn't be
		jobTitleStrips = re.compile('(?:((,| )?( )*(Sr))|((,| )( )*((?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3}))($|-| )))')
	else:
		# Stripping suffix-only: comma and/or space followed by "Sr" or any Roman Numeral
		jobTitleStrips = re.compile('(,| )( )*((Sr)$|((?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3}))$)')

	# Parse into First-Name as Key Dict, list of (Dept, Stripped Title, Pay) tuples
	for row in wagesRawData:
		jobTitle = row[3]
		jobTitle = jobTitle.rstrip(' ')
		if(args.strict):
			if(DEBUG):
				print "Trimming: |" + jobTitle + "|"
			valueToStrip = jobTitleStrips.search(jobTitle)
			while(valueToStrip):
				jobTitle = jobTitle[:valueToStrip.start()] + " " + jobTitle[valueToStrip.end():]
				jobTitle = jobTitle.rstrip(' ')
				valueToStrip = jobTitleStrips.search(jobTitle)
			if(DEBUG):
				print "Trimmed:  |" + jobTitle + "|"
		else:
			suffixCheck = jobTitleStrips.search(jobTitle)
			if suffixCheck:
				if(DEBUG):
					print "Trimming: |" + jobTitle + "|"
				jobTitle = jobTitle[0:suffixCheck.start()]
				if(DEBUG):
					print "Trimmed:  |" + jobTitle + "|"
		if row[2] not in wageData:
			wageData[row[2]] = [[row[0], jobTitle, row[4]]]
		else:
			wageData[row[2]].append([row[0],jobTitle,row[4]])

highestAverageWage = dict()
# Process each name for highest average wage of a given Dept+Title
for key,valueSet in wageData.items():
	if(DEBUG):
		print key
	deptAndTitleWages = dict()
	for value in valueSet:
		deptAndTitle = value[0]+value[1]
		if deptAndTitle not in deptAndTitleWages:
			deptAndTitleWages[deptAndTitle] = [[value[2], value[0], value[1]]]
		else:
			deptAndTitleWages[deptAndTitle].append([value[2], value[0], value[1]])
	currentHighestWage = 0
	currentDepartment = ""
	currentTitle = ""
	for deptAndTitle,wages in deptAndTitleWages.items():
		accumulator = 0
		for wage in wages:
			accumulator += float(wage[0])
		averageWage = float(accumulator / len(wages))
		if(DEBUG):
			print deptAndTitle + " : " + str(averageWage)
		if averageWage > currentHighestWage:
			currentHighestWage = averageWage
			currentDepartment = wage[1]
			currentTitle = wage[2]
	highestAverageWage[key]={"Department":currentDepartment, "JobTitle":currentTitle, "Average Hourly Rate":str(currentHighestWage)}

outTarget = '-'
if(args.outputfile != None):
	outTarget = args.outputfile

# Output in JSON format
with smart_open(outTarget) as jsonFile:
	json.dump(highestAverageWage,jsonFile,separators=(',', ': '),indent=2)