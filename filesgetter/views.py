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

    # Ничего необычного, просто 2 обработчика получаемых csv файлов
    # list comprehension был выбран больше из-за компактности и скорости
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
    # Проверка на нахождение записи в базе, и при нахождении - обновление ее
    # Обработка исключений т.к не все записи полные ибо в выданном xml 10 несуществующих артиклев
    for item in finallist:
        # Ужастные эксепшены т.к не находит в filesender.models.DoesNotExist такого исключения
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


#  fpt-sender с возможность указания адресса, логина и пароля от сервера
def ftpsender(url, login, password, file):
    ftp = ftplib.FTP(url)
    ftp.login(login, password)
    with open(file, 'r') as ftpfile:
        ftp.storlines('STOR ' + 'ftpxml.xml', ftpfile)


def templateview(request):
    form = UploadFileForm()
    return render(request, 'main.html', {'form': form})

def uploader_first_task(request):
    # Сначала был принято решение обрабатывать файлы на лету т.е в кэше джанго, но спустя время не было найдено
    # Адекватных методов для разбора csv файла, по этому выбор пал на сохранение в MEDIA и последующем удалении
    csvfile1 = request.FILES['file']
    csvfile2 = request.FILES['file2']
    fs = FileSystemStorage()
    fs.save(csvfile1.name, csvfile1)
    fs.save(csvfile2.name, csvfile2)
    # Просто создание экземпляра класса и запуск всех механизмов по порядку
    main_instance = Mergers()
    main_instance.article_csv_parser('media/' + csvfile1.name)
    main_instance.csv_with_parameters_parser('media/' + csvfile2.name)
    main_instance.merge_between_csvs()
    xml_parser('test.xml')
    main_instance.merge_between_csv_and_xml('test.xml')
    os.remove('media/' + csvfile1.name)
    os.remove('media/' + csvfile2.name)
    # Добавление/Обновление записей в БД
    databasequerys(main_instance.merged_list)


def uploader_second_task(request):
    # Сырой запрос т.к им легче было провести проверку на разницу в ценах чем обрабатывать питоном
    prices = Parameters.objects.raw(
        'SELECT article, title FROM filesgetter_parameters WHERE price-cost_price<price*0.05 AND price-cost_price>0 OR cost_price-price<price*0.05 AND cost_price-price>0')

    # Создание отчета в формате xml
    prices_root = ET.Element('root')
    items = ET.SubElement(prices_root, 'items')
    for i in prices:
        ET.SubElement(items, 'item').text = i.article
    tree = ET.ElementTree(prices_root)
    tree.write('ftpxml.xml')

    # групировка по категориям и датам
    grouped_by_date_and_category = Parameters.objects.raw(
        'SELECT article, creation_date, category, COUNT(title) as count FROM filesgetter_parameters GROUP BY creation_date, category')
    grouped_by_date = Parameters.objects.raw(
        'SELECT article, creation_date, category, COUNT(title) as count FROM filesgetter_parameters GROUP BY creation_date')
    # Способа декодинга скандинавских символов так и не было найдено
    grouped_root = ET.Element('root')
    for record_date in grouped_by_date:
        date = ET.SubElement(grouped_root, str(record_date.creation_date))
        for record_category in grouped_by_date_and_category:
            ET.SubElement(date, str(record_category.category)).text = str(record_category.count)
    groupedtree = ET.ElementTree(grouped_root)
    groupedtree.write('groupedxml.xml')

    # Отправка данных на выбранный пользователем сервер
    #ftpsender(request.POST.get('ftpurl'), request.POST.get('ftplogin'), request.POST.get('ftppassword'),
     #         'ftpxml.xml')
    #ftpsender(request.POST.get('ftpurl'), request.POST.get('ftplogin'), request.POST.get('ftppassword'),
     #         'groupedxml.xml')


def uploader(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploader_first_task(request)
            uploader_second_task(request)


            return redirect('/filesgetter/2')
