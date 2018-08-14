from django.shortcuts import render, redirect
from .forms import UploadFileForm
from django.core.files.storage import FileSystemStorage
import csv
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from .models import Parameters
import ftplib


# Create your views here.
class CSVParser:
    def __init__(self):
        self.article_list = []
        self.parameters_list = []

    # Nothing unusual, just 2 functions for handling csv files
    # list comprehension was chosen because that is more shorter and faster
    def article_csv_parser(self, placement):
        with open(placement, 'r', encoding='utf-8') as file:
            [self.article_list.append({'article': ''.join(article)}) for article in csv.reader(file)]

    def csv_with_parameters_parser(self, placement):
        with open(placement, 'r', encoding='utf-8') as file:
            [self.parameters_list.append({'article': ''.join(line[0]),
                                          'gross_weight': ''.join(line[1]),
                                          'color': ''.join(line[2]),
                                          'event': ''.join(line[3]),
                                          'creation_date': datetime.date(datetime.now()),
                                          'update_date': datetime.date(datetime.now())}) for line in
             list(csv.reader(file))[1:]]


class Mergers(CSVParser):
    def __init__(self):
        super().__init__()
        self.merged_list = []

    def merge_between_csvs(self):
        [self.merged_list.append(second_dictionary) for second_dictionary in self.parameters_list for dictionary in
         self.article_list if dictionary.get('article') == second_dictionary.get('article')]

    def merge_between_csv_and_xml(self, filename):
        with open(filename, 'r', encoding='utf-8') as xmlfile:
            root = ET.parse(xmlfile).getroot()
            googledir = '{http://base.google.com/ns/1.0}'
            [dictionary.update({'title': item.find('title').text,
                                'price': item.find('%sprice' % googledir).text,
                                'category': item.find('%sproduct_type' % googledir).text,
                                'cost_price': int(float(item.find('%sprice' % googledir).text))
                                              - int(float(item.find('%sdelivery-cost' % googledir).text))}) for item
             in root.find('channel').findall('item') for dictionary
             in self.merged_list if str(dictionary['article'])
             == str(item.find('%sgtin' % googledir).text)]


def xml_parser(filename):
    with open(filename, 'wb') as xmlfile:
        xmlfile.write(requests.get('https://www.emma.dk/gshop.xml').content)


def databasequerys(finallist):
    # check on the availability in data base and if is available, updating it
    # exception handling, since not every record is full because given xml has 10 nonexistent articles
    for item in finallist:
        # Terrible exceptions because can't to import exceptions from "filesender.models.DoesNotExist"
        try:
            try:
                Parameters.objects.get(article='{article}'.format(**item))
                param = Parameters.objects.all().update(title='{title}'.format(**item),
                                                        price='{price}'.format(**item),
                                                        article='{article}'.format(**item),
                                                        gross_weight='{gross_weight}'.format(**item),
                                                        update_date='{update_date}'.format(**item),
                                                        cost_price='{cost_price}'.format(**item),
                                                        category='{category}'.format(**item))
                param.save()
            except:
                Parameters.objects.get(article='{article}'.format(**item))
                param = Parameters.objects.all().update(article='{article}'.format(**item),
                                                        gross_weight='{gross_weight}'.format(**item),
                                                        update_date='{update_date}'.format(**item),
                                                        cost_price='{cost_price}'.format(**item))
                param.save()
        except:
            try:
                param = Parameters(article='{article}'.format(**item),
                                   title='{title}'.format(**item),
                                   price='{price}'.format(**item),
                                   gross_weight='{gross_weight}'.format(**item),
                                   creation_date='{creation_date}'.format(**item),
                                   update_date='{update_date}'.format(**item),
                                   cost_price='{cost_price}'.format(**item),
                                   category='{category}'.format(**item))
                param.save()
            except KeyError:
                param = Parameters(article='{article}'.format(**item),
                                   gross_weight='{gross_weight}'.format(**item),
                                   creation_date='{creation_date}'.format(**item),
                                   update_date='{update_date}'.format(**item), )
                param.save()


# ftp-sender with a possibility of adding address, login and password from server
def ftpsender(url, login, password, file):
    ftp = ftplib.FTP(url)
    ftp.login(login, password)
    with open(file, 'r') as ftpfile:
        ftp.storlines('STOR ' + 'ftpxml.xml', ftpfile)


def templateview(request):
    form = UploadFileForm()
    return render(request, 'main.html', {'form': form})


def uploader_first_task(request):
    # first of all was decided to process files from django cache memory, but then, when right methods for processing
    # csv files wasn't found, was chosen way to saving files to MEDIA with deleting after all
    csvfile1 = request.FILES['file']
    csvfile2 = request.FILES['file2']
    fs = FileSystemStorage()
    fs.save(csvfile1.name, csvfile1)
    fs.save(csvfile2.name, csvfile2)
    # Just creating instance of class and running all mechanism one by one
    main_instance = Mergers()
    main_instance.article_csv_parser('media/' + csvfile1.name)
    main_instance.csv_with_parameters_parser('media/' + csvfile2.name)
    main_instance.merge_between_csvs()
    xml_parser('test.xml')
    main_instance.merge_between_csv_and_xml('test.xml')
    os.remove('media/' + csvfile1.name)
    os.remove('media/' + csvfile2.name)
    # Adding/Updating DB records
    databasequerys(main_instance.merged_list)


def uploader_second_task(request):
    # Raw query cuz that's more easiest way for me to inspect on price difference
    prices = Parameters.objects.raw(
        'SELECT article, title FROM filesgetter_parameters WHERE price-cost_price<price*0.05 AND price-cost_price>0 '
        'OR cost_price-price<price*0.05 AND cost_price-price>0')

    # creating xml report with items who has price difference in 5%
    prices_root = ET.Element('root')
    items = ET.SubElement(prices_root, 'items')
    for i in prices:
        ET.SubElement(items, 'item').text = i.article
    tree = ET.ElementTree(prices_root)
    tree.write('ftpxml.xml')

    # grouping by date and category
    grouped_by_date_and_category = Parameters.objects.raw(
        'SELECT article, creation_date, category, COUNT(title) as count FROM filesgetter_parameters '
        'GROUP BY creation_date, category')
    grouped_by_date = Parameters.objects.raw(
        'SELECT article, creation_date, category, COUNT(title) as count FROM filesgetter_parameters '
        'GROUP BY creation_date')
    # Method for decoding Scandinavian characters was not found
    grouped_root = ET.Element('root')
    for record_date in grouped_by_date:
        date = ET.SubElement(grouped_root, str(record_date.creation_date))
        for record_category in grouped_by_date_and_category:
            ET.SubElement(date, str(record_category.category)).text = str(record_category.count)
    groupedtree = ET.ElementTree(grouped_root)
    groupedtree.write('groupedxml.xml')

    # sending data to a chosen by user server(not tested)
    ftpsender(request.POST.get('ftpurl'), request.POST.get('ftplogin'), request.POST.get('ftppassword'),
              'ftpxml.xml')
    ftpsender(request.POST.get('ftpurl'), request.POST.get('ftplogin'), request.POST.get('ftppassword'),
              'groupedxml.xml')


def uploader(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploader_first_task(request)
            uploader_second_task(request)

            return redirect('/filesgetter/2')
