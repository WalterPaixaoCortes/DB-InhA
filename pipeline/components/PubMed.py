import sys
import traceback
import datetime
import time
import os
import urllib as urllib2
import json
import xml2json
import optparse
import MySQLdb
import requests

from Bio import Entrez
from xml.etree import ElementTree

def remove_shit(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

class PubMed():
    __cfg = None
    __log = None
    __db = None
    __month_cnv = dict()
    __month_cnv['Jan'] = 1
    __month_cnv['Feb'] = 2
    __month_cnv['Mar'] = 3
    __month_cnv['Apr'] = 4
    __month_cnv['May'] = 5
    __month_cnv['Jun'] = 6
    __month_cnv['Jul'] = 7
    __month_cnv['Aug'] = 8
    __month_cnv['Sep'] = 9
    __month_cnv['Oct'] = 10
    __month_cnv['Nov'] = 11
    __month_cnv['Dec'] = 12
    __month_cnv[u'01'] = 1
    __month_cnv[u'02'] = 2
    __month_cnv[u'03'] = 3
    __month_cnv[u'04'] = 4
    __month_cnv[u'05'] = 5
    __month_cnv[u'06'] = 6
    __month_cnv[u'07'] = 7
    __month_cnv[u'08'] = 8
    __month_cnv[u'09'] = 9
    __month_cnv[u'10'] = 10
    __month_cnv[u'11'] = 11
    __month_cnv[u'12'] = 12

    def __init__(self, cfg, log, db):
            self.__cfg = cfg
            self.__log = log
            self.__db = db
            Entrez.email = cfg.EntrezEmail
            Entrez.tool = cfg.EntrezApp

    def is_pubmed_online(self):
        pmAccess = True
        self.__log.info('Testing connection to PubMed...')
        try:
            handle = Entrez.einfo()
            result = handle.read()
            tree = ElementTree.fromstring(result)

            count = 0

            for node in tree.findall('.//DbName'):
                count = count + 1

            if count > 0:
                self.__log.info('PubMed is accessible...')
            else:
                raise
        except:
            pmAccess = False
            self.__log.error(traceback.format_exc())

        return pmAccess

    def search_pubmed(self):
        try:
            handle = Entrez.esearch(db=self.__cfg.EntrezDB, term=self.__cfg.EntrezTerm, retmax=self.__cfg.EntrezRetMax)
            result = Entrez.read(handle)
        except:
            result = None
            self.__log.error(traceback.format_exc())

        return result

    def get_pubmed_article(self,item):
        article = dict()
        try:
            handle = Entrez.efetch(db=self.__cfg.EntrezDB, id=item, rettype="gb", retmode="xml")
            result = handle.read()
            json_string = json.loads(xml2json.xml2json(result,optparse.Values({"pretty": False}),0))
            #print json.dumps(json_string)

            if 'PubmedArticle' in json_string['PubmedArticleSet'].keys(): 
                if 'Abstract' in json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation'].keys():
                    article_list = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Abstract']['AbstractText']

                    if type(article_list) == list:
                        formatted_list = [x['@Label'].encode('utf-8','ignore') + '\n' + x['#text'].encode('utf-8','ignore') for x in article_list]
                        article['content'] = '\n\n'.join(formatted_list)
                    elif type(article_list) == dict:
                        article['content'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Abstract']['AbstractText']['#text'].replace(u'\xa0',u' ').encode('utf-8','ignore')
                    else:
                        article['content'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Abstract']['AbstractText'].replace(u'\xa0',u' ').encode('utf-8','ignore')

                else:
                    article['content'] = 'No abstract available.'

                if 'AuthorList' in json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article'].keys():
                    def return_name(y):
                        x = None
                        if isinstance(y,str):
                            x = y
                        else:
                            if 'LastName' in y.keys(): 
                                x = y['LastName'].encode('utf-8','ignore')
                                if 'ForeName' in y.keys():
                                    x = x + ', '.encode('utf-8') + y['ForeName'].encode('utf-8','ignore') 
                            else: 
                                x = y['CollectiveName'].encode('utf-8','ignore')
                        return x
                    article['authors'] = [ return_name(x).decode('utf-8') for x in json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['AuthorList']['Author'] ]
                else:
                    article['authors'] = ['No authors informed.']
                
                article['pmid'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['PMID']['#text'].encode('utf-8','ignore')
                
                try:
                    article['title'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['ArticleTitle']['#text'].encode('utf-8','ignore')
                except:
                    article['title'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['ArticleTitle']

                article['journal'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Journal']['Title'].encode('utf-8','ignore')
                try:
                    article['journal_issn'] = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Journal']['ISSN']['#text'].encode('utf-8','ignore')
                except:
                    article['journal_issn'] = None
                
                try:
                    article_journal_PubDate_json = json_string['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']
                except:
                    article_journal_PubDate_json = None

                if article_journal_PubDate_json:
                    if 'MedlineDate' in article_journal_PubDate_json.keys():
                        article['publication_date'] = None
                        article['publication_year'] = None
                    else:
                        dt_year = article_journal_PubDate_json['Year']
                        article['publication_year'] = dt_year
                        
                        try:
                            dt_month = article_journal_PubDate_json['Month']
                        except:
                            dt_month = 'Jan'

                        try:
                            dt_day = article_journal_PubDate_json['Day']
                        except:
                            dt_day = '1'

                        article['publication_date'] = datetime.date(int(dt_year),self.__month_cnv[dt_month],int(dt_day))
                else:
                    article['publication_date'] = None
                    article['publication_year'] = None
            else:
                article['content'] = 'No abstract available.'
                article['authors'] = 'No authors informed.'
                article['pmid'] = None
                article['title'] = 'No title.'
                article['journal'] = 'No journal.'
                article['journal_issn'] = 'No ISSN.'
                article['publication_date'] = None
                article['publication_year'] = None
        except:
            article['error'] = traceback.format_exc()

        return article

    def save_pubmed_article(self,id,article,type):
        try:
            self.__log.info('Saving Article: %s...' % id)
            if type == 'Training':
                self.__db.executeCommand(self.__cfg.sqlInsertTrainingSet,(id, article['title'], MySQLdb.escape_string(str(article['content']))))
            else:
                if 'error' in article.keys():
                    self.__log.error(article['error'])
                else:
                    self.__db.executeCommand(self.__cfg.sqlInsertLiterature % (id,
                                                                             article['title'].replace("'","''"),
                                                                             MySQLdb.escape_string(str(article['content'])),
                                                                             remove_shit(';'.join(article['authors'])).replace("'","''"),
                                                                             article['journal'],
                                                                             article['journal_issn'],
                                                                             datetime.datetime.strftime(article['publication_date'],'%Y-%m-%d') if article['publication_date'] else '2099-12-31',
                                                                             str(article['publication_year']) if article['publication_year'] else '2099'))
            self.__db.commit()
            return True
        except:
            self.__log.error(traceback.format_exc())
            self.__db.rollback()
            return False

    def get_pubmed_full_article(self,item):
        result = None
        try:
            article = self.__db.getData(self.__cfg.sqlFindFullText,(item)).fetchall()
            req = requests.get(self.__cfg.pubmedFTP + article['file'])
            #urllib2.Request(self.__cfg.pubmedFTP + article['file'])
            #f = urllib2.urlopen(req)        
            fw = open(os.path.join(self.__cfg.extractFilesFolder,item + 'tar.gz'), "wb")
            #for row in f:
            fw.write(req.content)
            #fw.close()
            result = os.path.join(self.__cfg.extractFilesFolder,item + 'tar.gz')
        except:
            pass
        return result

    def get_related_pubmed_articles(self,item):
        try:
            handle = Entrez.elink(db=self.__cfg.EntrezDB, id=item, linkname="pubmed_pubmed")
            result = Entrez.read(handle)
        except:
            result = None
            self.__log.error(traceback.format_exc())

        return result

    def retrieve_file_list(self):
        self.__log.info('Getting updated list of open access articles...')
        result = None
        try:
            #req = requests.get(self.__cfg.pubmedFTPList)
            #urllib2.Request(self.__cfg.pubmedFTPList)
            #f = urllib2.urlopen(req)
            #fw = open('file_list.csv', 'w')
            #fw.write(req.content)
            #fw.close()

            f = open('file_list.csv', 'r')
            
            if self.__cfg.FullReload:
                self.__db.executeCommand(self.__cfg.sqlTruncateFullText)
            i = 0
            for result in f:
                resultList = result.replace('\n','').split(',')
                if resultList[4] is not None:
                    self.__db.executeCommand(self.__cfg.sqlInsertFullText, (resultList[0],resultList[1],resultList[2],resultList[3],resultList[4]))
                    i += 1
                    if i == 1000:
                        i = 0
                        self.__db.commit()
                        print('.')

            self.__db.commit()

        except:
            self.__db.rollback()
            self.__log.error(traceback.format_exc())
