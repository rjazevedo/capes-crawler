#!/usr/bin/python

# Template file header
# URL (DBLP), URL (Scholar Metrics), Sigla (DBLP), Nome (DBLP), Nome (Google Scholar), H5 (Google Scholar), MedianH5 (Google Scholar)

import argparse
import csv
import requests
import sys
import time
import BeautifulSoup
import string
import os
import codecs
import string
import unicodedata

def ReadInputFile(filename):
    answer = []
    for l in open(filename, 'rU').readlines():
        line = map(lambda x : x.decode('utf-8'), l.split(';'))
        answer.append(line)

    # with codecs.open(filename, 'rU', 'utf-8') as csvfile:
    #     dialect = csv.Sniffer().sniff(csvfile.read(), delimiters=';,')
    #     csvfile.seek(0)
    #     content = list(csv.reader(csvfile, dialect = dialect))
    #     return content, dialect

    return answer


def SaveOutputFile(filename, data):

    outFile = open(filename, 'wt')
    for line in data:
        l = string.join(map(lambda x : x.encode('utf-8'), line), ';') + '\n'
        outFile.write(l)
    outFile.close()

    # csvfile = csv.writer(codecs.open(filename, 'wt', 'utf-8'), dialect = dialect)
    # for line in data:
    #     print line[3], line[4]
    #     line[3] = codecs.encode(line[3], 'utf-8', 'ignore')
    #     line[4] = codecs.encode(line[4], 'utf-8', 'ignore')
    #     csvfile.writerow(line)
    return


def DBLPCrawler(url):
    # Receives the DBLP URL to crawl and returns the short name and full name as a tuple

    print 'Crawling DBLP:', url, '->',

    # download url content
    try:
        page = requests.get(url)
    except requests.exceptions.RequestException as e:
        print e
        return ('', '')

    # parse file
    parsed = BeautifulSoup.BeautifulSoup(page.text)

    # get the first H1 that contains the expanded name
    h1 = parsed.findAll('h1')
    if (len(h1) > 0):
        fullName = h1[0].text
    else:
        fullName = ''

    # short name is the last token of the URL
    shortName = string.upper(url.split('/')[-1])

    print shortName, '|', fullName

    return (shortName, fullName)


def GoogleScholarCrawler(url, counter):
    filename = 'gs/%05d.html' % counter
    print 'Crawling GoogleScholar:', url, filename, '...'
    fullName = ''
    h5 = medianH5 = 0

    if os.path.exists(filename):
        content = codecs.open(filename, 'rt', 'utf-8').read()
        if len(content) == 0:
            os.remove(filename)
            print '... bad cache file %s: ', fullName
        else:
            parsed = BeautifulSoup.BeautifulSoup(content)
            h3 = parsed.findAll('h3')
            if len(h3) > 0:
                fullName = h3[0].text

            div = parsed.find('div', {'id': 'gs_vn_stats'})
            if div == None:
                os.remove(filename)
                print '... bad cache file %s: ', fullName
            else:
                span = div.findAll('span')
                if len(span) > 1:
                    h5 = int(span[0].text)
                    medianH5 = int(span[1].text)

                    print '... got from cache file %s:' % filename, fullName, '| H5:', h5, '| Median H5:', medianH5
    else:
        print '... no cached value yet'

    return (fullName, unicode(h5), unicode(medianH5))


def GoogleScholarWGetLine(url, counter, sleeptime):
    if url[0:4] == 'http':
        return 'if [ ! -f gs/%05d.html ]\nthen\n  wget -O gs/%05d.html "%s"\n  sleep %d\nfi\n' % (counter, counter, url, sleeptime)
    else:
        return ''

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Update Conference Information file')
    parser.add_argument('-d', '--dblp', action='store_true', help='Fetch DBLP Canonical name')
    parser.add_argument('-g', '--googlescholar', action='store_true', help='Fetch Google Scholar H5')
    parser.add_argument('-f', '--force', action='store_true', help='Force updating all fields')
    parser.add_argument('-s', '--sleep', type=int, help='Sleep time in seconds between web queries (default: 20)')
    parser.add_argument('source', type=str, help='Source CSV file')
    parser.add_argument('destination', type=str, help='Destination CSV file')
    args = parser.parse_args()

    inputData = ReadInputFile(args.source)

    if not args.dblp and not args.googlescholar:
        print('At least one option should be selected (-d or -g). Use --help for help.')
        sys.exit(1)

    outputData = inputData
    if args.sleep != None:
        sleepTime = args.sleep
    else:
        sleepTime = 20

    if args.dblp:
        for line in outputData[1:]:
            # Columns description on top of this code
            if line[0] != '' and (line[2] == '' or line[3] == '' or args.force):
                (line[2], line[3]) = DBLPCrawler(line[0])
                time.sleep(sleepTime)

    if args.googlescholar:
        counter = 0
        outputScript = ''

        for line in outputData[1:]:
            counter += 1
            if line[1] != '' and (line[4] == '' or line[5] == '' or args.force):
                outputScript += GoogleScholarWGetLine(line[1], counter, sleepTime)

        outputfile = open('googlescholar_crawler.sh', 'wt')
        outputfile.write(outputScript)
        outputfile.close()

        counter = 0
        for line in outputData[1:]:
            counter += 1
            if line[1] != '' and (line[4] == '' or line[5] == '' or line[6] == '' or args.force):
                (line[4], line[5], line[6]) = GoogleScholarCrawler(line[1], counter)


    SaveOutputFile(args.destination, outputData)
