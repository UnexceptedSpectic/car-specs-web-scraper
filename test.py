import unittest
from scraper import Scraper


class TestStringMethods(unittest.TestCase):

    def test_get_makes(self):
        expected_makes = ['acura', 'alfa-romeo', 'am-general', 'aston-martin', 'audi', 'bentley', 'bmw', 'bugatti', 'buick', 'cadillac', 'chevrolet', 'chrysler', 'citroen', 'daewoo', 'daihatsu', 'dodge', 'eagle', 'ferrari', 'fiat', 'fisker', 'ford', 'freightliner', 'genesis', 'geo', 'gmc', 'honda', 'hummer', 'hyundai', 'infiniti', 'international', 'isuzu', 'jaguar', 'jeep', 'kia', 'lamborghini', 'land-rover', 'lexus', 'lincoln', 'lotus', 'maserati', 'maybach', 'mazda', 'mclaren', 'mercedes-benz', 'mercury', 'mini', 'mitsubishi', 'morgan', 'nissan', 'oldsmobile', 'panoz', 'plymouth', 'pontiac', 'porsche', 'ram', 'rolls-royce', 'saab', 'saleen', 'saturn', 'scion', 'smart', 'spyker', 'subaru', 'suzuki', 'tesla', 'toyota', 'volkswagen', 'volvo']
        observed_makes = scraper.get_makes()
        self.assertTrue(all([make in expected_makes for make in observed_makes]))

    def test_get_years(self):
        expected_years = [str(i) for i in range(2022, 1995, -1)]
        observed_years = scraper.get_years(make='toyota', cutoff=1995)
        self.assertTrue(all([year in expected_years for year in observed_years]))

    def test_get_models(self):
        expected_models = ['4runner', 'avalon', 'camry', 'camry-solara', 'corolla', 'highlander', 'highlander-hybrid', 'land-cruiser', 'matrix', 'prius', 'rav4', 'sequoia', 'sienna', 'tacoma', 'tundra']
        self.assertEqual(scraper.get_models('toyota', 2006), expected_models)

    def test_get_trims(self):
        expected_trims = {'18537': 'LE - Sedan 2.4L Manual', '18538': 'LE V6 - Sedan 3.0L V6 auto', '18539': 'SE - Sedan 2.4L Manual', '18535': 'SE V6 - Sedan 3.3L V6 auto', '18540': 'Standard - Sedan 2.4L auto', '18536': 'STD 4dr Sedan 5-spd manual w/OD', '18541': 'XLE V6 - Sedan 3.0L V6 auto'}
        self.assertDictEqual(scraper.get_trims('toyota', 2006, 'camry'), expected_trims)

    def test_get_specs(self):
        expected_specs = {'passenger_doors': '4', 'transmission': '5-speed manual transmission w/OD', 'drive_type': 'Front Wheel Drive', '0-60_mph': '8.61 sec', 'horsepower': '154 hp', 'horsepower_rpm': '5,700', 'torque': '160 ft-lbs.', 'torque_rpm': '4,000', 'cylinders': '4', 'base_engine_size': '2.40 L', 'engine_type': 'Gas', 'curb_weight': '3,108 lbs.', 'fuel_tank_capacity': '18.50 gal.', 'ground_clearance': '5.50 in.', 'current_price': 3127, 'city_mpg': 24, 'highway_mpg': 33}
        self.assertDictEqual(scraper.get_specs(2006, 'toyota', 'camry', '18537'), expected_specs)


if __name__ == '__main__':
    scraper = Scraper()
    unittest.main()
