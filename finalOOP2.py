import csv
import requests
import xml.etree.ElementTree as ET
from datetime import datetime


class CSVPARSER:
    def __init__(self):
        self.article_list = []
        self.parameters_list = []

    def article_csv_parser(self, placement):
        with open(placement, 'r', encoding='utf-8') as file:
            [self.article_list.append({'article': ''.join(article)}) for article in csv.reader(file)]
        # print(self.article_list)

    def csv_with_parameters_parser(self, placement):
        with open(placement, 'r', encoding='utf-8') as file:
            [self.parameters_list.append({'article': ''.join(line[0]),
                                          'weight': ''.join(line[1]),
                                          'color': ''.join(line[2]),
                                          'event': ''.join(line[3])}) for line in list(csv.reader(file))[1:]]


class Mergers(CSVPARSER):
    def __init__(self):
        super().__init__()
        self.Finallist = []

    def merge_between_csvs(self):
        [self.Finallist.append(second_dictionary) for second_dictionary in self.parameters_list for dictionary in
         self.article_list if dictionary.get('article') == second_dictionary.get('article')]
        # print(self.Finallist)

    def merge_between_csv_and_xml(self):
        with open('test.xml', 'r', encoding='utf-8') as xmlfile:
            root = ET.parse(xmlfile).getroot()
            [dictionary.update({'title': item.find('title').text,
                                'price': item.find('{http://base.google.com/ns/1.0}price').text,
                                'category': item.find('{http://base.google.com/ns/1.0}product_type').text,
                                'cost price': int(float(item.find('{http://base.google.com/ns/1.0}price').text))
                                - int(float(item.find('{http://base.google.com/ns/1.0}delivery-cost').text)),
                                'Creation_date': datetime.date(datetime.now()),
                                'Updating_date': ''}) for item in root.find('channel').findall('item') for dictionary
             in self.Finallist if str(dictionary['article'])
             == str(item.find('{http://base.google.com/ns/1.0}gtin').text)]

        print(self.Finallist)


def xml_parser():
    with open('test.xml', 'wb') as xmlfile:
        xmlfile.write(requests.get('https://www.emma.dk/gshop.xml').content)


a = Mergers()
a.article_csv_parser('ListOfSKUForTestTask - Sheet1.csv')
a.csv_with_parameters_parser('ListOfSKU2ForTestTask - Sheet1.csv')
a.merge_between_csvs()
xml_parser()
a.merge_between_csv_and_xml()
