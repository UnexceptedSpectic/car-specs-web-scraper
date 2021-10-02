#! /usr/bin/python3.8
import requests, time
from bs4 import BeautifulSoup as bs
import pandas as pd


class Scraper:

    def __init__(self):
        # Define specs to scrape. Exact site values.
        self.specs_of_interest = ['Transmission', 'Drive type', '0-60 mph', 'Drag Coefficient', 'Horsepower', 'Horsepower RPM', 'Torque', 'Torque RPM', 'Cylinders', 'Base engine size', 'Valves', 'Engine type', 'Curb weight', 'Fuel tank capacity', 'Maximum cargo capacity', 'Ground clearance', 'Passenger Doors']

        # Initialize data frame
        specs_columns = ["_".join(i.lower().split()) for i in self.specs_of_interest]
        columns = ['make', 'model', 'year', 'trim', 'city_mpg', 'highway_mpg'] + specs_columns
        self.df = pd.DataFrame(columns=columns)

        # Track progress and errors
        self.n_requests = 0
        self.request_errors = []
        self.parsing_errors = []

        # Create request session object
        self.session = requests.Session()

    def make_persistent_request(self, url, timeout=3, tries=3, retry_wait=3):
        for i in range(tries):
            try:
                res = self.session.get(url=url, verify=False, timeout=timeout)
                if res.status_code != 200:
                    print("INFO: Connection unsuccessful. Retrying after %ss." % retry_wait)
                    time.sleep(retry_wait)
                    continue
                self.n_requests += 1
                return res.text
            except:
                pass

    def get_makes(self):
        url = "https://www.carspecs.us/"
        text_content = self.make_persistent_request(url)
        if text_content:
            soup = bs(text_content, 'html.parser')
            makes_elements = soup.select("#homepage-browsemakes > div > ul > li > a")
            try:
                return [el["href"].split("/")[-1] for el in makes_elements]
            except:
                self.parsing_errors.append("makes\t%s" % url)
                return None
        else:
            self.request_errors.append(url)
            return None

    # less requests required getting years before models, given that typically for a make, n_years < n_models
    def get_years(self, make, cutoff=None):
        url = "https://www.carspecs.us/cars/%s" % make
        text_content = self.make_persistent_request(url)
        if text_content:
            soup = bs(text_content, 'html.parser')
            year_elements = soup.select('div.main-content > div > div:nth-child(1) > ul > li > a')
            try:
                years = [el["href"].split("/")[-2] for el in year_elements]
                if cutoff:
                    return [year for year in years if int(year) > cutoff]
                else:
                    return years
            except:
                self.parsing_errors.append("years\t%s" % url)
                return None
        else:
            self.request_errors.append(url)
            return None

    def get_models(self, make, year):
        url = "https://www.carspecs.us/cars/%s/%s" % (year, make)
        text_content = self.make_persistent_request(url)
        if text_content:
            soup = bs(text_content, 'html.parser')
            model_elements = soup.select('div.main-content > div > div > ul > li > a')
            try:
                return [el["href"].split("/")[-1] for el in model_elements]
            except:
                self.parsing_errors.append("models\t%s" % url)
                return None
        else:
            self.request_errors.append(url)
            return None

    def get_trims(self, make, year, model):
        url = "https://www.carspecs.us/cars/%s/%s/%s" % (year, make, model)
        text_content = self.make_persistent_request(url)
        if text_content:
            soup = bs(text_content, 'html.parser')
            trim_elements = soup.select('select > option')
            trims = {}
            try:
                for el in trim_elements:
                    trims[el["value"].split("/")[-1]] = el.string.strip()
                return trims
            except:
                self.parsing_errors.append("trims\t%s" % url)
                return None
        else:
            self.request_errors.append(url)
            return None

    def get_specs(self, year, make, model, trim_id):
        url = "https://www.carspecs.us/cars/%s/%s/%s/%s" % (year, make, model, trim_id)
        text_content = self.make_persistent_request(url)
        if text_content:
            soup = bs(text_content, 'html.parser')
            spec_divs = soup.select('div.car-details > div > div')
            spec_data = {}
            try:
                for el in spec_divs:
                    if el.h4 is None:
                        continue
                    spec = el.h4.string.strip()
                    if spec in self.specs_of_interest:
                        spec_data["_".join(spec.lower().split())] = el.text.strip().split('\n')[-1].strip()
            except Exception as e:
                self.parsing_errors.append("specs\t%s\t%s" % (url, e))

            details_div = soup.select_one('div.main-car-details')
            try:
                spec_data['current_price'] = int(details_div.span.string.strip().replace('$', '').replace(',', ''))
            except:
                spec_data['current_price'] = None
                self.parsing_errors.append("current_price\t%s" % url)
            try:
                city_highway_raw = details_div.text.strip().split('\n')[-1].strip().split('/')
                spec_data['city_mpg'] = int(city_highway_raw[0].strip().split()[0])
                spec_data['highway_mpg'] = int(city_highway_raw[1].strip().split()[0])
            except:
                spec_data['city_mpg'] = spec_data['highway_mpg'] = None
                self.parsing_errors.append("mpg\t%s" % url)

            return spec_data
        else:
            self.request_errors.append(url)
            return None

    @staticmethod
    def update_if_exists(_dict, key, update_fn):
        if _dict.get(key):
            _dict[key] = update_fn(_dict, key)

    def run(self):
        start_time = time.time()
        # Scrape data and populate data frame

        makes = self.get_makes()
        if makes is None:
            return

        for ind, make in enumerate(makes):

            print("Scraping make %s of %s" % (ind + 1, len(makes)))
            years = self.get_years(make, cutoff=2000)
            if years is None:
                continue

            for year in years:

                models = self.get_models(make, year)
                if models is None:
                    continue

                for model in models:

                    trims = self.get_trims(make, year, model)
                    if trims is None:
                        continue

                    for trim_id in trims.keys():

                        spec_data = self.get_specs(year, make, model, trim_id)
                        if self.n_requests % 10 == 0:
                            print("STATUS: made request number %s for (%s, %s, %s)" % (self.n_requests, make, year, model))
                        if spec_data is None:
                            continue
                        data_row = {"make": make, "model": model, "year": int(year), "trim": trims[trim_id]}
                        data_row = {**data_row, **spec_data}
                        # Sanitize data
                        self.update_if_exists(data_row, 'city_mpg',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.update_if_exists(data_row, 'highway_mpg',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.update_if_exists(data_row, '0-60_mph',
                                              lambda _dict, key: float(_dict.get(key).split()[0]))
                        self.update_if_exists(data_row, 'drag_coefficient',
                                              lambda _dict, key: float(_dict.get(key).split()[0]))
                        self.update_if_exists(data_row, 'horsepower',
                                              lambda _dict, key: int(_dict.get(key).split()[0].replace(',', '')))
                        self.update_if_exists(data_row, 'horsepower_rpm',
                                              lambda _dict, key: int(_dict.get(key).replace(',', '')))
                        self.update_if_exists(data_row, 'torque',
                                              lambda _dict, key: int(_dict.get(key).split()[0].replace(',', '')))
                        self.update_if_exists(data_row, 'torque_rpm',
                                              lambda _dict, key: int(_dict.get(key).replace(',', '')))
                        self.update_if_exists(data_row, 'cylinders',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.update_if_exists(data_row, 'base_engine_size',
                                              lambda _dict, key: float(_dict.get(key).split()[0]))
                        self.update_if_exists(data_row, 'valves',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.update_if_exists(data_row, 'curb_weight',
                                              lambda _dict, key: int(_dict.get(key).split()[0].replace(',', '')))
                        self.update_if_exists(data_row, 'fuel_tank_capacity',
                                              lambda _dict, key: float(_dict.get(key).split()[0]))
                        self.update_if_exists(data_row, 'maximum_cargo_capacity',
                                              lambda _dict, key: float(_dict.get(key).split()[0]))
                        self.update_if_exists(data_row, 'ground_clearance',
                                              lambda _dict, key: float(_dict.get(key).split()[0].replace(',', '')))
                        self.update_if_exists(data_row, 'passenger_doors',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.update_if_exists(data_row, 'current_price',
                                              lambda _dict, key: int(_dict.get(key)))
                        self.df = self.df.append(data_row, ignore_index=True)

        # Export data frame
        self.df.to_csv('specs.csv', index=False)

        # Save error log files
        with open('request_errors.log', 'w') as f:
            for i in self.request_errors:
                f.write(i + '\n')

        with open('parsing_errors.log', 'w') as f:
            for i in self.parsing_errors:
                f.write(i + '\n')

        # Print summary information
        print('Extraction took %s minutes' % (round((time.time() - start_time)/60, 2)))
        print('%s HTTP requests failed. See request_errors.log' % len(self.request_errors))
        print('%s parsing errors encountered. See parsing_errors.log' % len(self.parsing_errors))


if __name__ == '__main__':
    scraper = Scraper()
    scraper.run()