# -*- coding: utf-8 -*-
"""mem-single-classifier-featureset3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Z-FvQ7pQYnB1d-i9O19q-x4TPo6RDyNF
"""

from google.colab import drive
drive.mount('/content/gdrive/')

import os
import numpy as np
import codecs
import pickle
import nltk
import pickle
from nltk.classify.maxent import MaxentClassifier, TypedMaxentFeatureEncoding, BinaryMaxentFeatureEncoding
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support as score
from sklearn.metrics import multilabel_confusion_matrix
from sklearn.metrics import classification_report

# Global variables
rawdata_path = "/content/gdrive/My Drive/ml/data/rawdata/"
data_path = "/content/gdrive/My Drive/ml/data/data/"
model_path = "/content/gdrive/My Drive/ml/model/"
labels = ['B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'O']
labels_dict = {labels[i]: i for i in range(len(labels))}
eval_labels = ['B-PER', 'I-PER', 'B-LOC', 'I-LOC', 'B-ORG', 'I-ORG']
print(labels_dict)

def remove_xml_tags(filename):
  ''' 
  Remove xml tag in file in data folder(raw data)
  Args:
    filename: The name of the data file in dataVLSP folder
  Return:
    File of the same name has removed xml tags in data folder
  Example:
    <editor>Vietlex team, 8-2016</editor>
    -DOCSTART-
    <s>				
    Đó	P	B-NP	O	O
    là	V	B-VP	O	O
    con	Nc	B-NP	O	O
  :converted into:
    Đó	P	B-NP	O	O
    là	V	B-VP	O	O
    con	Nc	B-NP	O	O

    saved in dataVLSP folder(processed data)
  '''
  f1 = open(rawdata_path + filename, 'r',encoding='utf-8')
  f2 = open(data_path + filename, 'w+',encoding='utf-8')
  for line in f1:
    line.strip()
    if(('<title>' in line) or line.startswith('<e') or line.startswith('-D') or line.startswith('<s>')):
      pass
    elif(line.startswith('</')):
      f2.write(line.replace(line,'\n'))
    else:
      f2.write(line)
  f1.close()
  f2.close()

def clean_data(path):
  ''' 
  Remove xml tags of all files in the dataVLSP folder
  Processed data saved in data
  '''
  list_files = os.listdir(path)
  for file in list_files:
    remove_xml_tags(file)

def prepare_data(path):
    ''' Create training data and testing data
        Format of data: CoNLL

        Args:
        path: path of data folder
        scale: test size
        index_attri: Represents the number of attributes and the associated attribute type
            index_attri == 1 : The number of attributes = 1 - only ner label. ex: [('Huế', 'B_LOC'), ('là', 'O'), ('thành_phố', 'O'), ('đẹp', 'O')]
            index_attri == 2.1 : The number of attributes = 2(pos-tagging label, ner label). ex: [('Đó', 'P', 'O'), ('là', 'V',  'O'), ('con', 'Nc', 'O'), ('đường', 'N', , 'O')]
            index_attri = 2.2 : The number of attributes = 2(chunking label, ner label). ex: [('Đó', 'B-NP', 'O'), ('là', 'B-VP', 'O'), ('con', 'B-NP', 'O'), ('đường', 'B-NP', 'O')]
            index_attri = 3 : The number of attributes = 3(pos-tagging label,chunking, ner label). ex: [('Đó', 'P', 'B-NP', 'O'), ('là', 'V', 'B-VP', 'O'), ('con', 'Nc', 'B-NP', 'O'), ('đường', 'N', 'B-NP', 'O')]
            if index_attri not in {1,2.1,2,2,3} index_attri = 2.1
        Return:
        train_sents, test_sents
        
        Example of format data:
        [[('Đó', 'P', 'B-NP', 'O'), ('là', 'V', 'B-VP', 'O'), ('con', 'Nc', 'B-NP', 'O'), ('đường', 'N', 'B-NP', 'O')],
        [('Đó', 'P', 'B-NP', 'O'), ('là', 'V', 'B-VP', 'O'), ('con', 'Nc', 'B-NP', 'O'), ('đường', 'N', 'B-NP', 'O')],
    '''    
    list_files = os.listdir(path)
    all_data = []
    ''' Convert data format to CoNll '''
    #training data
    c = 0;
    pos_tag = []
    chunk_tag = []
    ne_tag = []
    for file in list_files:
        with codecs.open(path + file,'r',encoding='utf8') as f:
            sentence = []
            remove = False
            for line in f:
                line = line.split()
                if len(line) > 3:
                    #label_set.append(line[3])
                    if line[3] not in labels:
                        remove = True
                    else:
                        pos_tag.append(line[1])
                        chunk_tag.append(line[2])
                    sentence.append((line[0],line[1],line[2],line[3]))
                else:
                    if len(sentence) > 0:
                        if remove == False:                            
                            all_data.append(sentence)
                        else:
                            remove = False
                        sentence = []
            f.close()

    pos_tag = set(pos_tag)
    chunk_tag = set(chunk_tag)
    return  all_data, pos_tag, chunk_tag

def shape_feature(word):
    is_lower            = 'is_lower'
    is_capital          = 'is_capital' 
    is_title            = 'is_title' 
    is_mix              = 'is_mix' 
    is_capital_period   = 'is_capital_period' 
    is_digit            = 'is_digit' 
    end_digit           = 'end_digit' 
    has_hyphen          = 'has_hyphen' 
    is_code             = 'is_code' 
    num_syllabus        = 'num_syllabus'
    is_name             = 'is_name' 

    check_code = False
    for char in word:
        if char.isdigit():
            check_code = True
            break;

    ft = {
        'bias'                : 1,
        is_lower            : word.islower(),
        is_capital          : word.isupper(),
        is_title            : word.istitle(),
        is_mix              : not(word.islower() and word.isupper()),
        is_capital_period   : (('.' in word) and word[0].isupper()),
        is_digit            : word.isdigit(),
        end_digit           : word[-1].isdigit(),
        has_hyphen          : ('-' in word),
        is_code             : check_code,
        num_syllabus        : (word.count('_') + 1),
        is_name             : word[0].isupper()
    }   
    return ft

def word_feature(sent, i, pre_state, pre_pre_state, sent_re_ft):
    word = sent[i][0]
    ft = dict()
    ### basic feature 
    # current word
    ft['w0'] = word
    # previous entity tag
    ft['s-1'] = pre_state
    ft['s-2'] = pre_pre_state
    ### basic shape feature
    ft.update(shape_feature(word))
    ### basic joint feature
    if i > 0:
        ft['w-1'] = sent[i-1][0]
    else:
        ft['w-1'] = 'BOS'
    
    if i > 1:
        ft['w-2'] = sent[i-2][0]
    else:
        ft['w-2'] = 'BOS'
    if i < len(sent)-1:
        ft['w+1'] = sent[i+1][0]
    else:
        ft['w+1'] = 'EOS'    
    if i < len(sent)-2:
        ft['w+2'] = sent[i+2][0]
    else:
        ft['w+2'] = 'EOS'
    ### regular expression type
    ft['r0'] = sent_re_ft[i]
    if i > 0:
        ft['r-1'] = sent_re_ft[i-1]
    else:
        ft['r-1'] = 'BOS'
    if i < len(sent)-1:
        ft['r+1'] = sent_re_ft[i+1]
    else:        
        ft['r+1'] = 'EOS'
    if i > 1:
        ft['r-2'] = sent_re_ft[i-2]
    else:
        ft['r-2'] = 'BOS'
    if i < len(sent)-2:
        ft['r+2'] = sent_re_ft[i+2]
    else:
        ft['r+2'] = 'EOS'
    ### extra joint feature
    ft['w0+w-1'] = ft['w0'] + ' ' + ft['w-1']
    ft['w0+w+1'] = ft['w0'] + ' ' + ft['w+1']
    ft['w0+s-1'] = ft['w0'] + ' ' + ft['s-1']
    ft['r0+r-1'] = ft['r0'] + ' ' + ft['r-1']
    ft['r0+r+1'] = ft['r0'] + ' ' + ft['r+1']
    ft['w0+r0']  = ft['w0'] + ' ' + ft['r0']
    ft['w0+r-1'] = ft['w0'] + ' ' + ft['r-1']
    ft['w0+r+1'] = ft['w0'] + ' ' + ft['r+1']
    return ft
re_adm_div      = ['ấp', 'buôn', 'bản', 'huyện', 'làng', 'miền', 'nước', 
                   'phường', 'quận', 'tỉnh', 'thành_phố', 'thị_trấn', 'thị_xã', 
                   'thôn', 'TT', 'TP', 'TX', 'TT.', 'TP.', 'TX.', 'xứ', 'xã', 
                   'xóm']
re_org          = ['báo', 'bệnh_viện', 'bệnh_xá', 'công_ty', 'công_ti', 'đài', 'đảng', 'đoàn', 'hội', 'hợp_tác_xã', 'khách_sạn', 'nhà_máy', 'nhà_xuất_bản', 'ngân_hàng', 'quỹ', 'tạp_chí', 'tập đoàn', 'thông_tấn_xã', 'tờ', 'trạm_xá', 'xí_nghiệp','ủy_ban']
re_school       = ['mẫu_giáo', 'tiểu_học', 'trung_học', 'trung_học_cơ_sở', 
                   'trung_học_phổ_thông', 'cao_đẳng', 'trung_cấp', 
                   'trung_cấp_nghề', 'đại_học']
re_street       = ['đại_lộ', 'đường', 'hẻm', 'ngách', 'ngõ', 'nhà', 'phố', 'quốc_lộ']
re_place        = ['ao', 'am', 'bến', 'bến_cảng', 'bến_phà','biển', 'cảng', 
                   'cầu', 'công_viên', 'chợ', 'chùa', 'dãy', 'đảo', 'đầm', 'đèo', 
                   'đền', 'đình', 'đồi', 'động', 'đồng_bằng', 'gềnh', 'gò', 'khu', 'hòn', 'hồ', 
                   'lăng', 'miếu', 'miền', 'nhà_ga', 'núi', 'phà', 'quần_đảo', 
                   'sân_bay', 'sông', 'suối', 'vùng']
re_office       = ['ban', 'bộ', 'chi_cục', 'cục', 'hạt', 'sở']
re_army         = ['binh_đoàn', 'đại_đội', 'đặc_khu', 'đơn_vị', 'lữ_đoàn', 'quân_đoàn', 'quân_đội', 'quân_khu','sư_đoàn', 'tiểu_đội', 'tiểu_đoàn', 'trung_đội']

def re_word(word):
    """
        Return a dict of (regexp Name, regexp Value) of a word
        :type word: string
        :param word: a word in sentence
    """

    check_code = False
    for char in word:
        if char.isdigit():
            check_code = True
            break

    re_dict = dict()
    re_dict['org'] = word.lower() in re_org
    re_dict['name'] = word[0].isupper()
    re_dict['capital'] = word.isupper()
    re_dict['adm_div'] = word.lower() in re_adm_div
    re_dict['is_school'] = word.lower() == 'trường'
    re_dict['school'] = word.lower() in re_school
    re_dict['street'] = word.lower() in re_street
    re_dict['digit'] = word.isdigit()
    re_dict['code'] = check_code
    re_dict['place'] =  word in re_place
    re_dict['office'] = word in re_office
    re_dict['army'] = word in re_army
    return re_dict 

re_type_name = [ 
    ('ofice_name_admdiv_name', ['office', 'name', 'adm_div', 'name']),
    ('school_type_name_name'     , ['is_school', 'school', 'name', 'name']),
    ('school_capital_name_name'  , ['is_school', 'capital', 'name', 'name']),
    ('org_cap_name_name'         , ['org', 'capital', 'name', 'name']),
    ('org_adm_div'          , ['capital', 'adm_div', 'name']),
    ('school_type_name'     , ['is_school', 'school', 'name']),
    ('school_capital_name'  , ['is_school', 'capital', 'name']),
    ('org_cap_name'         , ['org', 'capital', 'name']),
    ('place_name_name'           , ['place', 'name', 'name']),
    ('place_name'           , ['place', 'name']),
    ('org_name'                  , ['org', 'name', 'name']),
    ('school_name_name'          , ['school', 'name', 'name']),
    ('office_name_name'               , ['office', 'name', 'name']),
    ('street_name_name'          , ['street', 'name', 'name']),
    ('org'                  , ['org', 'name']),
    ('school_name'          , ['school', 'name']),
    ('adm_div'              , ['adm_div', 'name']),
    ('office_name'               , ['office', 'name']),
    ('street_name'          , ['street', 'name']),
    ('street_digit'         , ['street', 'digit']),
    ('street_code'          , ['street', 'code']),
    ('army_name'            , ['army', 'code']),
    ('army_name'            , ['army', 'digit']),
    ('army_name'            , ['army', 'name'])
]

def sent_re_feature(sent):
    l = len(sent)
    sent_re_ft = ['NA'] * l
    re_dict_word = [re_word(word[0]) for word in sent]
    for type_name in re_type_name:
        tl = len(type_name[1])
        for i in range(l):
            if (i + tl <= l):
                if (set(['NA']) == set([sent_re_ft[i+j] for j in range(tl)])) and (set([True]) == set([re_dict_word[i+ll][type_name[1][ll]] for ll in range(tl)])):
                    for k in range(tl):
                        sent_re_ft[i+k] = type_name[0]
    return sent_re_ft

def sent_feature_train(sent):
    sent_ft_train = list()
    sent_re_ft = sent_re_feature(sent)
    for i in range(len(sent)):
        if i < 1:
            sent_ft_train.append((word_feature(sent, i, 'BOS', 'BOS', sent_re_ft),
                                  labels_dict[sent[i][3]]))
        elif i < 2:
            sent_ft_train.append((word_feature(sent, i, sent[i-1][3], 'BOS', sent_re_ft),
                                  labels_dict[sent[i][3]]))
        else:
            sent_ft_train.append((word_feature(sent, i, sent[i-1][3], sent[i-2][3], sent_re_ft),
                                  labels_dict[sent[i][3]]))    
    return sent_ft_train

def sent_feature_test(sent, pre_state, pre_pre_state):
    sent_ft_test = list()
    sent_re_ft = sent_re_feature(sent)
    for i in range(len(sent)):
        sent_ft_test.append(word_feature(sent, i, pre_state, pre_pre_state, sent_re_ft))    
    return sent_ft_test

def viterbi_decoder(model, sent):
    sent_re_ft = sent_re_feature(sent)
    alpha = [([0] * len(labels)) for i in range(len(sent))]
    trace = np.full(shape=(len(sent), len(labels)), fill_value=-1)

    # start probability
    pdist = model.prob_classify(word_feature(sent, 0, 'BOS', 'BOS', sent_re_ft))    
    alpha[0] = [pdist.prob(l) for l in labels]
    
    for i in range(1, len(sent)):
        alpha[i] = [0] * len(labels)
        for j in range(len(labels)):
            pre_state = labels[j];
            pre_pre_state = 'BOS'
            if i > 1:
                pre_pre_state = labels[trace[i-1][j]];
            feature = word_feature(sent, i, pre_state, pre_pre_state, sent_re_ft)
            pdist = model.prob_classify(feature)                
            posterior = [pdist.prob(l) for l in labels]
            for k in range(len(labels)):
                if alpha[i][k] < (posterior[k] * alpha[i-1][j]):
                    alpha[i][k] = posterior[k] * alpha[i-1][j]
                    trace[i][k] = j
    m = alpha[-1][0]
    idx = 0
    for i in range(1, len(alpha[-1])):
        if (alpha[-1][i] > m):
            m = alpha[-1][i]
            idx = i;
    predict = list()
    for i in range(len(sent)-1, -1, -1):
        predict.append(labels[idx])
        idx = trace[i][idx]
    # print(alpha)
    return reversed(predict)

def predict_sent(model, sent):
    y_test_sent = [sent[i][3] for i in range(len(sent))]   
    y_pred_sent = viterbi_decoder(model, sent)
    return y_test_sent, y_pred_sent

def predict(model, sents):
    y_test = []
    y_pred = []
    for sent in sents:
        test, pred = predict_sent(model, sent)
        y_test.extend(test)
        y_pred.extend(pred)
    return y_test, y_pred

all_data, pos_tag, chunk_tag = prepare_data(data_path)
train_sents, test_sents = train_test_split(all_data, test_size = 0.15, random_state=42)
print("train_sents", len(train_sents))
print("test_sents", len(test_sents))

train_data = []
for sent in train_sents:
    for feature, label in sent_feature_train(sent):
        train_data.append((feature, labels[label]))     

print('train_data length', len(train_data))
print(train_data[0])

# Commented out IPython magic to ensure Python compatibility.
# %%time 
# max_iter = 10
# encoding = BinaryMaxentFeatureEncoding.train(train_data, count_cutoff=3, labels = labels, alwayson_features=True)
# model = MaxentClassifier.train(train_data, algorithm = 'iis', trace=3, encoding=encoding, max_iter=max_iter)
# # save model
# pickle.dump(model, open(model_path + "mem-single-classifier-featureset3-binaryfeature-maxiter10.model", "wb"))

# Commented out IPython magic to ensure Python compatibility.
# %%time
# # test model
# test_model = pickle.load(open(model_path + "mem-single-classifier-featureset3-binaryfeature-maxiter10.model", "rb"))
# y_test, y_pred = predict(test_model, test_sents)
# precision, recall, fscore, support = score(y_test, y_pred, labels=eval_labels)
# print('labels:    {}'.format(eval_labels))
# print('precision: {}'.format([str(round(p*100,2)) + '%' for p in precision]))
# print('recall:    {}'.format([str(round(r*100,2)) + '%' for r in recall]))
# print('fscore:    {}'.format([str(round(f*100,2)) + '%' for f in fscore]))
# print('support:   {}'.format(support))
# total_precision = metrics.precision_score(y_test, y_pred, average='weighted', labels=eval_labels)
# total_recall = metrics.recall_score(y_test, y_pred, average='weighted', labels=eval_labels)
# total_fscore = metrics.f1_score(y_test, y_pred, average='weighted', labels=eval_labels)
# print('total precision (weighted): {}'.format(str(round(total_precision*100,2)) + '%'))
# print('total recall (weighted): {}'.format(str(round(total_recall*100,2)) + '%'))
# print('total fscore (weighted): {}'.format(str(round(total_fscore*100,2)) + '%'))

test_model.show_most_informative_features()

# Commented out IPython magic to ensure Python compatibility.
# %%time 
# max_iter = 50
# encoding = BinaryMaxentFeatureEncoding.train(train_data, count_cutoff=3, labels = labels, alwayson_features=True)
# model = MaxentClassifier.train(train_data, algorithm = 'iis', trace=3, encoding=encoding, max_iter=max_iter)
# # save model
# pickle.dump(model, open(model_path + "mem-single-classifier-featureset3-binaryfeature-maxiter50.model", "wb"))

# Commented out IPython magic to ensure Python compatibility.
# %%time
# # test model
# test_model = pickle.load(open(model_path + "mem-single-classifier-featureset3-binaryfeature-maxiter50.model", "rb"))
# y_test, y_pred = predict(test_model, test_sents)
# precision, recall, fscore, support = score(y_test, y_pred, labels=eval_labels)
# print('labels:    {}'.format(eval_labels))
# print('precision: {}'.format([str(round(p*100,2)) + '%' for p in precision]))
# print('recall:    {}'.format([str(round(r*100,2)) + '%' for r in recall]))
# print('fscore:    {}'.format([str(round(f*100,2)) + '%' for f in fscore]))
# print('support:   {}'.format(support))
# total_precision = metrics.precision_score(y_test, y_pred, average='weighted', labels=eval_labels)
# total_recall = metrics.recall_score(y_test, y_pred, average='weighted', labels=eval_labels)
# total_fscore = metrics.f1_score(y_test, y_pred, average='weighted', labels=eval_labels)
# print('total precision (weighted): {}'.format(str(round(total_precision*100,2)) + '%'))
# print('total recall (weighted): {}'.format(str(round(total_recall*100,2)) + '%'))
# print('total fscore (weighted): {}'.format(str(round(total_fscore*100,2)) + '%'))

test_model.show_most_informative_features()