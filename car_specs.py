#! /usr/bin/python3
import urllib.request, re, time
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np

startTime = time.time()
# define specs of interest in html terms
specs = ['<h4>Transmission</h4>', '<h4>Drive type</h4>', '<h4>Engine type</h4>', '<h4>Base engine size</h4>', '<h4>Cylinders</h4>', '<h4>Horsepower</h4>', '<h4>Horsepower RPM</h4>', '<h4>Torque</h4>', '<h4>Torque RPM</h4>', '<h4>0-60 mph</h4>', '<h4>Curb weight</h4>', '<h4>Fuel tank capacity</h4>', '<h4>Ground clearance</h4>']

# define columns in order of specs array
baseColNames = ['Make', 'Model', 'Year', 'Variant', 'Price', 'MPG City', 'MPG Highway']
colNames = [spec.replace('<h4>', '').replace('</h4>' ,'') for spec in specs ]
columns = baseColNames + colNames

# define dataframe
df = pd.DataFrame(columns = columns)

# extract car makes
url = "https://www.carspecs.us/"
html = urllib.request.urlopen(url)
soup = bs(html, 'html.parser')
a = str(soup.find_all('a'))
aNames = re.findall(r'/cars/\S+"', a)
makes = [s.replace("/cars/", "").replace('"', '') for s in aNames]


count = 1
failedRequests = []
failedParsing = []
failure = 0

for make in makes:
    stop = 0
    # extract car years
    url = "https://www.carspecs.us/cars/%s" %make
    attempts = 2
    while attempts > 0:
        try:
            html = urllib.request.urlopen(url)
            soup = bs(html, 'html.parser')
            a = str(soup.find_all('a'))
            aNames = re.findall(r'/\d+/',a)
            years = [s.replace("/", "") for s in aNames]
            break
        except:
            time.sleep(1)
            print('Error: http request for %s failed. trying again...' %url)
            failure = 1
            attempts -= 1
    if failure == 1:    
        failedRequests.append(url)
        failure = 0
        stop = 1
    for year in years:
        # extract car models
        url = "https://www.carspecs.us/cars/%s/%s" %(year, make)
        attempts = 2
        if stop == 0:
            while attempts > 0:
                try:
                    html = urllib.request.urlopen(url)
                    soup = bs(html, 'html.parser')
                    a = str(soup.find_all('a'))
                    aNames = re.findall(r'/cars/%s/%s/\S+"' %(year, make),a) 
                    models = [s.replace('/cars/%s/%s/' %(year, make), "").replace('"', "") for s in aNames]
                    break
                except:
                    time.sleep(1)
                    print('Error: http request for %s failed. trying again...' %url)
                    failure = 1
                    attempts -= 1
            if failure == 1:    
                failedRequests.append(url)
                failure = 0
                stop = 1
        for model in models:
            # extract variants
            url = "https://www.carspecs.us/cars/%s/%s/%s" %(year, make, model)
            attempts = 2
            if stop == 0:
                while attempts > 0:
                    try:
                        html = urllib.request.urlopen(url)
                        soup = bs(html, 'html.parser')
                        a = str(soup.find_all('a'))
                        aNames = re.findall(r'/cars/%s/%s/%s/\S+">' %(year, make, model),a)
                        variants = [s.replace('/cars/%s/%s/%s/' %(year, make, model), "").replace('">', "") for s in aNames]
                        break
                    except:
                        time.sleep(1)
                        print('Error: http request for %s failed. trying again...' %url)
                        failure = 1
                        attempts -= 1
                if failure == 1:    
                    failedRequests.append(url)
                    failure = 0
                    stop = 1
            for variant in variants:
                # create urls
                url = "https://www.carspecs.us/cars/%s/%s/%s/%s" %(year, make, model, variant)
                attempts = 2
                if stop == 0:
                    while attempts > 0:
                        try:
                            html = urllib.request.urlopen(url)
                            soup = bs(html, 'html.parser')
                            rLabels = soup.find_all('h4')
                            indices = np.asarray(range(0,len(rLabels)))
                            row = {}
                            row[columns[0]] = make
                            row[columns[1]] = model
                            row[columns[2]] = year
                            row[columns[3]] = soup.h1.b.next_element.next_element.strip()
                            break
                        except:
                            time.sleep(1)
                            print('Error: http request for %s failed. trying again...' %url)
                            attempts -= 1
                            failure = 1
                    if failure == 1:    
                        failedRequests.append(url)
                        failure = 0
                try:
                    price = re.search(r'\d+\S{1}\d+', soup.find(title="Based on average nation-wide prices").next_element).group().replace(',', '')
                    row[columns[4]] = price
                except:
                    pass
                try:
                    mpg = re.findall(r'\d+', soup.find(title="Based on average nation-wide prices").next_element.next_element.next_element)
                    city = mpg[0]
                    row[columns[5]] = city
                    highway = mpg[1]
                    row[columns[6]] = highway
                except:
                    pass
                for spec in specs:
                    subset = [str(s) == spec for s in rLabels]
                    dfInd = specs.index(spec) + columns.index(colNames[0])
                    if sum(subset) > 0:
                        try:
                            rLabelsInd = indices[subset]
                            if spec in [specs[0], specs[1], specs[2], specs[4]]:
                                # keep data as is
                                data = rLabels[rLabelsInd[0]].next_element.next_element.replace('\r\n', "").strip()
                                row[colNames[specs.index(spec)]] = data
                            elif spec in [specs[3], specs[5], specs[6], specs[7], specs[8], specs[9], specs[10], specs[11], specs[12]]:
                                # keep numerical value
                                rData = rLabels[rLabelsInd[0]].next_element.next_element.replace('\r\n', "").strip().replace(',', '')
                                data = re.search(r'\d+', rData).group()
                                row[colNames[specs.index(spec)]] = data
                        except:
                            print('failed parsing')
                            failedParsing.append(url)
                            pass
                row['URL'] = url
                df = df.append(row, ignore_index=True)
                if count % 10 == 0:
                    print('%s variants added' %count)
                count +=1
endTime = time.time()
runTime = endTime - startTime
print('Extraction took %s minutes' %runTime)
print('HTTP requests could not be successfully made to the following urls: \n')
print(failedRequests)
print('Specs were incorrectly parsed for variants with the following urls: \n')
print(failedParsing)
df.to_csv('specs.csv')
