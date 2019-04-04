# -*- coding: utf-8 -*-
"""
    Wrapper module for survey monkey api
"""
import time
import re
import traceback

import requests
import textblob

from .NPParser import NPExtractor
import nltk

# -------------------------------------------------------------------------------------------------
# Wrapper class for survey monkey api
# -------------------------------------------------------------------------------------------------
class SurveyApi():
    """
        Class to interface with survey monkey api
    """
    __client = None
    __access_token = None

    __HOST = "https://api.surveymonkey.net"
    __ENDPOINTS = {
        "get_surveys": "/v3/surveys",
        "get_survey": "/v3/surveys/%s/details",
        "get_survey_data": "/v3/surveys/%s/responses/bulk",
        "get_survey_respondents": "/v3/surveys/%s/responses",
        "get_question_details": "/v3/surveys/%s/pages/%s/questions/%s",
        "get_collector_details": "/v3/surveys/%s/collectors",
        "get_response_details": "/v3/surveys/%s/responses/%s/details"
    }
    __HEADERS = {
        "Authorization": None,
        "Content-Type": "application/json"
    }

    def __init__(self, access_token, proxy=None):
        """
            Class constructor
        """
        self.__client = requests.session()
        if proxy:
            self.__client.proxies.update(proxy)
        self.__access_token = access_token
        self.__HEADERS['Authorization'] = "bearer %s" % access_token
        self.__client.headers.update(self.__HEADERS)

    def get_from_url(self, url, param=None):
        """
            return generic json from generic url
        """
        response = self.__client.get(url, params=param)
        response_json = response.json()
        return response_json

    def get_paginated_results(self, url, page_interval, param=None):
        """
            Get all the results from all the pages of the url
            It is expected the result returned from the first url
            will have metadata to indicate what is the next page to
            be fetched.
        """
        response_page = self.get_from_url(url, param)
        raw_data = response_page['data']
        if 'next' in response_page['links']:
            while True:
                response_page = self.get_from_url(response_page['links']['next'], param)
                raw_data += response_page['data']
                if 'next' in response_page['links']:
                    time.sleep(page_interval)
                    continue
                break
        return raw_data

    def get_surveys(self, param=None):
        """
            return list of surveys
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_surveys.__name__])
        return self.get_paginated_results(uri, 2, param)

    def get_survey(self, survey_id):
        """
            return the survey details (pages, questions)
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_survey.__name__])
        uri = uri % survey_id
        return self.get_from_url(uri)

    def get_survey_data(self, survey_id):
        """
            get survey responses
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_survey_data.__name__])
        uri = uri % survey_id
        return self.get_paginated_results(uri, 2)

    def get_survey_respondents(self, survey_id):
        """
            get survey responses
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_survey_respondents.__name__])
        uri = uri % survey_id
        return self.get_paginated_results(uri, 2)

    def get_question_details(self, survey_id, page_id, question_id):
        """
            get survey question details
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_question_details.__name__])
        uri = uri % (survey_id, page_id, question_id)
        return self.get_paginated_results(uri, 2)

    def get_collector_details(self, survey_id):
        """
            get collector details
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_collector_details.__name__])
        uri = uri % (survey_id)
        return self.get_paginated_results(uri, 2)

    def get_response_details(self, survey_id, response_id):
        """
            get response details
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_response_details.__name__])
        uri = uri % (survey_id, response_id)
        return self.get_from_url(uri)
        
# -------------------------------------------------------------------------------------------------
# Methods to build the data file structures
# -------------------------------------------------------------------------------------------------
class SurveyProcessor():
    """
        Class to interface with SurveyAPI and process the survey data
    """

    PUNCTUATION = ['.', ',', ':', '-', '?', '!', '%']
    CONTRACTIONS = {
        "ain't": "am not",
        "aren't": "are not",
        "can't": "cannot",
        "can't've": "cannot have",
        "'cause": "because",
        "could've": "could have",
        "couldn't": "could not",
        "couldn't've": "could not have",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hadn't've": "had not have",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'd've": "he would have",
        "he'll": "he will",
        "he'll've": "he will have",
        "he's": "he is",
        "how'd": "how did",
        "how'd'y": "how do you",
        "how'll": "how will",
        "how's": "how is",
        "I'd": "I would",
        "I'd've": "I would have",
        "I'll": "I will",
        "I'll've": "I will have",
        "I'm": "I am",
        "I've": "I have",
        "isn't": "is not",
        "it'd": "it would",
        "it'd've": "it would have",
        "it'll": "it will",
        "it'll've": "it will have",
        "it's": "it is",
        "let's": "let us",
        "ma'am": "madam",
        "mayn't": "may not",
        "might've": "might have",
        "mightn't": "might not",
        "mightn't've": "might not have",
        "must've": "must have",
        "mustn't": "must not",
        "mustn't've": "must not have",
        "needn't": "need not",
        "needn't've": "need not have",
        "o'clock": "of the clock",
        "oughtn't": "ought not",
        "oughtn't've": "ought not have",
        "shan't": "shall not",
        "sha'n't": "shall not",
        "shan't've": "shall not have",
        "she'd": "she would",
        "she'd've": "she would have",
        "she'll": "she will",
        "she'll've": "she will have",
        "she's": "she is",
        "should've": "should have",
        "shouldn't": "should not",
        "shouldn't've": "should not have",
        "so've": "so have",
        "so's": "so is",
        "that'd": "that would",
        "that'd've": "that would have",
        "that's": "that is",
        "there'd": "there would",
        "there'd've": "there would have",
        "there's": "there is",
        "they'd": "they would",
        "they'd've": "they would have",
        "they'll": "they will",
        "they'll've": "they will have",
        "they're": "they are",
        "they've": "they have",
        "to've": "to have",
        "wasn't": "was not",
        "we'd": "we would",
        "we'd've": "we would have",
        "we'll": "we will",
        "we'll've": "we will have",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what'll've": "what will have",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "when's": "when is",
        "when've": "when have",
        "where'd": "where did",
        "where's": "where is",
        "where've": "where have",
        "who'll": "who will",
        "who'll've": "who will have",
        "who's": "who is",
        "who've": "who have",
        "why's": "why is",
        "why've": "why have",
        "will've": "will have",
        "won't": "will not",
        "won't've": "will not have",
        "would've": "would have",
        "wouldn't": "would not",
        "wouldn't've": "would not have",
        "y'all": "you all",
        "y'all'd": "you all would",
        "y'all'd've": "you all would have",
        "y'all're": "you all are",
        "y'all've": "you all have",
        "you'd": "you would",
        "you'd've": "you would have",
        "you'll": "you will",
        "you'll've": "you will have",
        "you're": "you are",
        "you've": "you have"
    }

    __api = None
    __survey_id = None
    __questions = None
    __respondents = None
    __answers = None
    __open_ended = None
    __collectors = None

    def __init__(self, survey_id, access_token, proxy=None):
        """
            Class constructor
        """
        self.__survey_id = survey_id
        self.__api = SurveyApi(access_token, proxy)

    def __return_score(self, value):
        """
            Analyze the textual answer and retrieve the value for score
        """
        return_value = 0
        regex = r"^([-+]*[\s]*[0-9]+)"

        matches = re.finditer(regex, value)

        for _, match in enumerate(matches):
            return_value = int(match.group().lstrip().rstrip().replace(" ",""))
            break
        return return_value

    def __create_question_type_list(self):
        """
            build the question type list
        """
        question_data = self.__api.get_survey(self.__survey_id)
        questions = {}
        for page in question_data['pages']:
            for question in page['questions']:
                if question['family'] not in ['presentation']:
                    questions[question['id']] = {'family': question['family'], 'choices': {}}
                    if question['family'] in ['multiple_choice', 'single_choice']:
                        for choice in question['answers']['choices']:
                            questions[question['id']]['choices'][choice['id']] = choice['text']
                    elif question['family'] == "matrix":
                        for row in question['answers']['rows']:
                            row_id = row['id']
                            questions[question['id']]['choices'][row_id] = {'text': row['text'],
                                                                            'data':{}}
                            for choice in question['answers']['choices']:
                                questions[question['id']]['choices'][row_id]['data'][choice['id']] = choice['text']
                    elif question['family'] == "open_ended" and ('subtype' in question and question['subtype'] == "multi"):
                        for row in question['answers']['rows']:
                            row_id = row['id']
                            questions[question['id']]['choices'][row_id] = {'text': row['text'],
                                                                        'data':{}}

        return questions

    def __decontract(self, phrase):
        """
            Eliminate the word contractions in the sentences
        """
        #print(phrase)
        dec_phrase = phrase #.replace("´", "'")
        for key in self.CONTRACTIONS:
            dec_phrase = dec_phrase.replace(key, self.CONTRACTIONS[key])

        return dec_phrase

    def __clean_html(self, rec):
        """
            Strip HTML tags
        """
        TAG_RE = re.compile(r'<[^>]+>')
        for key in rec:
            if rec[key] and type(rec[key]) is str:
                rec[key] = TAG_RE.sub('', rec[key]).lstrip().rstrip()

        return rec

    def __return_topics(self, question_id):
        """
            Return the list of topics for generating the padded answers
        """
        topics = []
        for question in self.__answers:
            if question['question_id'] == question_id:
                if question['topic'] != '' and question['topic'] not in topics:
                    topics.append(question['topic'])
        
        return topics

    def build_question_data(self):
        """
            build the question records
        """
        self.__questions = []
        question_data = self.__api.get_survey(self.__survey_id)
        question_label = 1
        for page in question_data['pages']:
            page_id = page['id']
            for question in page['questions']:
                if question['family'] not in ['presentation']:
                    record = {
                        "survey_id": self.__survey_id,
                        "page_id" : page_id,
                        "question_id": question['id'],
                        "question_label": 'Question ' + str(question_label),
                        "question_heading": question['headings'][0]['heading'],
                        "question_type": question['family']
                    }
                    self.__questions.append(self.__clean_html(record))
                    question_label += 1
        return self.__questions

    def build_respondent_data(self):
        """
            build respondent records
        """
        self.__respondents = []
        respondent_list = self.__api.get_survey_data(self.__survey_id)
        for respondent in respondent_list:
            record = {
                "survey_id": self.__survey_id,
                "respondent_id": respondent['id']
            }
            record['duration_seconds'] = respondent['total_time']
            record['start_date'] = respondent['date_created']
            record['end_date'] = respondent['date_modified']
            record['ip_address'] = respondent['ip_address']
            record['collector_id'] = respondent['collector_id']
            record['status'] = respondent['response_status']
            self.__respondents.append(self.__clean_html(record))

        return self.__respondents

    def build_answer_data(self):
        """
            build answer records
        """
        self.__answers = []
        questions = self.__create_question_type_list()
        raw_data = self.__api.get_survey_data(self.__survey_id)
        
        with open('raw_data.json', 'w') as fo:
            fo.write(str(raw_data))

        for answer in raw_data:
            response_id = answer['id']
            for page in answer['pages']:
                page_id = page['id']
                for question in page['questions']:
                    question_id = question['id']
                    if questions[question_id]['family'] not in ['presentation']:
                        for idx, item in enumerate(question['answers']):
                            record = {
                                "survey_id": self.__survey_id,
                                "page_id": page_id,
                                "respondent_id": response_id,
                                "question_id": question_id,
                                "question_type": questions[question_id]['family'],
                                "answer": None,
                                "topic": None,
                                "score": 0
                            }
                            if questions[question_id]['family'] == "open_ended":
                                record['answer'] = item['text']
                                if 'row_id' in item:
                                    if len(questions[question_id]['choices']) > 0:
                                        record['topic'] = questions[question_id]['choices'][item['row_id']]['text']
                                    else:
                                        if idx == 0:
                                            record['topic'] = "X"
                                        else:
                                            record['topic'] = "Y"
                                else:
                                    record['topic'] = "Open Ended"

                            elif questions[question_id]['family'] in ["multiple_choice",
                                                                    "single_choice"]:
                                if 'choice_id' not in item:
                                    record['topic'] = 'Open Ended'
                                    record['answer'] = item['text']
                                else:
                                    record['answer'] = questions[question_id]['choices'][item['choice_id']]
                                    record['score'] = self.__return_score(questions[question_id]['choices'][item['choice_id']])

                            elif questions[question_id]['family'] == "matrix":
                                if 'row_id' not in item:
                                    record['topic'] = 'Open Ended'
                                    record['answer'] = item['text']
                                    record['question_type'] = "open_ended"
                                else:
                                    record['topic'] = questions[question_id]['choices'][item['row_id']]['text']
                                    record['answer'] = questions[question_id]['choices'][item['row_id']]['data'][item['choice_id']]
                                    record['score'] = self.__return_score(questions[question_id]['choices'][item['row_id']]['data'][item['choice_id']])

                            self.__answers.append(self.__clean_html(record))

        return self.__answers

    def transpose_questions(self, key_data, use_topic=False, use_score=False):
        """
            Based on configuration, it build a list of dictionaries that contains the profile
            questions for the survey as columns
        """
        raw_data = {}
        qst_lookup = {}
        for item in self.__questions:
            if (item['page_id'] in key_data.keys() and
                    item['question_id'] in key_data[item['page_id']]):
                qst_lookup[item['question_id']] = item['question_label']

        for item in self.__answers:
            if (item['page_id'] in key_data.keys() and
                    item['question_id'] in key_data[item['page_id']] and
                    (item['question_type'] != 'open_ended' and item['topic'] != 'Open Ended')):
                if item['respondent_id'] not in raw_data:
                    raw_data[item['respondent_id']] = {}
                    if not use_topic:
                        for key in qst_lookup.keys():
                            raw_data[item['respondent_id']][qst_lookup[key]] = ''
                    
                if use_topic:
                    if item['topic'] not in raw_data[item['respondent_id']]:
                        raw_data[item['respondent_id']][item['topic']] = {}
                        for key in qst_lookup.keys():
                            if use_topic:
                                raw_data[item['respondent_id']][item['topic']][qst_lookup[key]] = 0
                            else:
                                raw_data[item['respondent_id']][qst_lookup[key]] = 0
                if use_score:
                    if use_topic:
                        raw_data[item['respondent_id']][item['topic']][qst_lookup[item['question_id']]] = item['score'] or ""
                    else:
                        raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = item['score'] or ""
                else:
                    if use_topic:
                        if item['topic'] != 'Open Ended':
                            raw_data[item['respondent_id']][item['topic']][qst_lookup[item['question_id']]] = item['answer'] or ""
                        else:
                            raw_data[item['respondent_id']]['Other'][qst_lookup[item['question_id']]] = 0
                    else:
                        if item['topic'] != 'Open Ended':
                            #raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = item['answer'] or ""
                            if len(raw_data[item['respondent_id']][qst_lookup[item['question_id']]]) == 0: 
                                raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = item['answer']
                            else:
                                raw_data[item['respondent_id']][qst_lookup[item['question_id']]] += '#' + item['answer']
                        else:
                            raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = "Other"

            elif (item['page_id'] in key_data.keys() and
                    item['question_id'] in key_data[item['page_id']] and
                    item['question_type'] == 'open_ended' and 
                    item['topic'] != "Open Ended"):
                if item['respondent_id'] not in raw_data:
                    raw_data[item['respondent_id']] = {}
                    if not use_topic:
                        for key in qst_lookup.keys():
                            raw_data[item['respondent_id']][qst_lookup[key]] = ''
                    
                if use_topic:
                    if item['topic'] not in raw_data[item['respondent_id']]:
                        raw_data[item['respondent_id']][item['topic']] = {}
                        for key in qst_lookup.keys():
                            if use_topic:
                                raw_data[item['respondent_id']][item['topic']][qst_lookup[key]] = 0
                            else:
                                raw_data[item['respondent_id']][qst_lookup[key]] = 0
                if use_score:
                    if use_topic:
                        raw_data[item['respondent_id']][item['topic']][qst_lookup[item['question_id']]] = item['score'] or ""
                    else:
                        raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = item['score'] or ""
                else:
                    if use_topic:
                        if item['topic'] != 'Open Ended':
                            raw_data[item['respondent_id']][item['topic']][qst_lookup[item['question_id']]] = item['answer'] or ""
                        else:
                            raw_data[item['respondent_id']]['Other'][qst_lookup[item['question_id']]] = item['answer'] or ""
                    else:
                        if item['topic'] != 'Open Ended':
                            raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = item['answer'] or ""
                        else:
                            raw_data[item['respondent_id']][qst_lookup[item['question_id']]] = "Other"

        return_value = []
        for key in raw_data:
            if use_topic:
                for key_topic in raw_data[key]:
                    cp_item = raw_data[key][key_topic]
                    cp_item['topic'] = key_topic
                    cp_item['respondent_id'] = key
                    cp_item['survey_id'] = self.__survey_id
                    return_value.append(cp_item)
            else:
                cp_item = raw_data[key]
                cp_item['respondent_id'] = key
                cp_item['survey_id'] = self.__survey_id
                return_value.append(cp_item)

        return return_value

    def expected_preferred(self, key_data, use_topic, use_score):
        raw_data = {}
        qst_lookup = {}
        for item in self.__questions:
            if (item['page_id'] in key_data.keys() and
                    item['question_id'] in key_data[item['page_id']]):
                qst_lookup[item['question_id']] = item['question_label']

        for item in self.__answers:
            if (item['page_id'] in key_data.keys() and
                    item['question_id'] in key_data[item['page_id']]):
                if item['respondent_id'] not in raw_data:
                    raw_data[item['respondent_id']] = {}

                if use_score:
                    raw_data[item["respondent_id"]][qst_lookup[item["question_id"]] + item['topic']] = item['score']
                else:
                    raw_data[item["respondent_id"]][qst_lookup[item["question_id"]] + item['topic']] = item['answer']


        return_value = []
        for key in raw_data:
            if use_topic:
                cp_item = raw_data[key].copy()
                cp_item['topic'] = "Expected"
                cp_item['respondent_id'] = key
                cp_item['survey_id'] = self.__survey_id
                return_value.append(cp_item)
                cp_item2 = raw_data[key].copy()
                cp_item2['topic'] = "Preferred"
                cp_item2['respondent_id'] = key
                cp_item2['survey_id'] = self.__survey_id
                return_value.append(cp_item2)
            else:
                cp_item = raw_data[key]
                cp_item['respondent_id'] = key
                cp_item['survey_id'] = self.__survey_id
                return_value.append(cp_item)

        return return_value
    
    def build_open_ended_data(self):
        """
            Build the open ended dictionary
        """
        try:
            answers = []
            line_count = 0
            for line in self.__answers:
                if line['question_type'] == 'open_ended':
                    line_count += 1

                    d_line = self.__decontract(line['answer'].lower())

                    np_extractor = NPExtractor(d_line)
                    results = np_extractor.extract()
                    for word in results:
                        if word not in self.PUNCTUATION:
                            data = {'survey_id': self.__survey_id,
                                    'page_id': line['page_id'],
                                    'respondent_id': line['respondent_id'],
                                    'question_id': line['question_id'],
                                    'question_type': line['question_type'],
                                    'answer': word
                                   }
                            answers.append(data)
        except:
            answers = None
            print(traceback.format_exc())
        return answers

    def build_sa_open_ended(self):
        """
            Build the open ended dictionary with sentiment analysis
        """
        try:
            answers = []
            line_count = 0
            for line in self.__answers:
                if line['question_type'] == 'open_ended':
                    line_count += 1

                    d_line = self.__decontract(line['answer'].lower())
                    results = textblob.TextBlob(d_line)
                    for item in results.sentences:
                        pol = item.polarity
                        sub = item.subjectivity

                        data = {'survey_id': self.__survey_id,
                                'page_id': line['page_id'],
                                'respondent_id': line['respondent_id'],
                                'question_id': line['question_id'],
                                'question_type': line['question_type'],
                                'answer': item,
                                'polarity': pol,
                                'subjectivity': sub
                            }
                        answers.append(data)

        except Exception as generic_exception:
            answers = None
        return answers

    def build_padded_answers(self):
        """
            Build padded answers
        """
        try:
            answers = []
            line_count = 0
            for line in self.__questions:
                if line['question_type'] == 'matrix':
                    topics = self.__return_topics(line['question_id'])
                    for resp in self.__respondents:
                        if len(topics) <= 0:
                            data = {'survey_id': self.__survey_id,
                                    'page_id': line['page_id'],
                                    'respondent_id': resp['respondent_id'],
                                    'question_id': line['question_id'],
                                    'question_type': line['question_type'],
                                    'answer': 0,
                                    'topic': '',
                                    'score': 0.5
                            }
                            answers.append(data)
                        else:
                            for topic in topics:
                                data = {'survey_id': self.__survey_id,
                                        'page_id': line['page_id'],
                                        'respondent_id': resp['respondent_id'],
                                        'question_id': line['question_id'],
                                        'question_type': line['question_type'],
                                        'answer': 0,
                                        'topic': '',
                                        'score': 0.5
                                }
                                answers.append(data)
                        break

        except Exception as generic_exception:
            answers = None
        return answers

    def build_collectors_data(self):
        """
            build collectors records
        """
        self.__collectors = []
        collector_list = self.__api.get_collector_details(self.__survey_id)
        for item in collector_list:
            record = {
                "survey_id": self.__survey_id,
                "collector_id": item['id'],
                "name": item['name']
            }
            self.__collectors.append(self.__clean_html(record))

        return self.__collectors

    def breakdown_multiple_answers(self, questions, raw_data):
        """Breakdown a multiple choice answers in different lines"""
        return_data = []
        mid_data = []
        for idx, item in enumerate(questions):
            for row in raw_data:
                values = row[item].split("#")
                for val in values:
                    row[item] = val
                    return_data.append(row.copy())

            raw_data = return_data.copy()
            return_data = []
            
        return raw_data