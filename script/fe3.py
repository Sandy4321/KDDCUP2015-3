import graphlab as gl
import pandas as pd
from datetime import datetime
from csv import DictReader
from sklearn.metrics import roc_curve  
from sklearn.metrics import auc  
import numpy as np
import matplotlib.pyplot as plt
import math
import xgboost as xgb
import random
from sklearn.feature_extraction import DictVectorizer as DV
from scikits.statsmodels.tools import categorical
from datetime import date
from collections import Counter
from graphlab import feature_engineering as fe


#train.iloc[(train['event']=='problem').values,:]['source'].value_counts()


#データの読み込み
#print 'leading data'
train = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/log_train.csv')
test = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/log_test.csv')
label = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/truth_train.csv',header=None)
label.columns = ['enrollment_id','drop']
enr_train = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/enrollment_train.csv')
enr_test = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/enrollment_test.csv')
label = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/truth_train.csv',header=None)
label.columns = ['enrollment_id','drop']
#train = train.fillna(0)
#test = test.fillna(0)
f_tostr = lambda x: str(x)
#train['module_depth'] = train['module_depth'].apply(f_tostr)
#test['module_depth'] = test['module_depth'].apply(f_tostr)
#train = train.drop_duplicates(cols=[ u'username', u'course_id', u'source', u'event', u'object'])
#test = test.drop_duplicates(cols=[ u'username', u'course_id', u'source', u'event', u'object'])

train = train.drop_duplicates()
test = test.drop_duplicates()



'''
#objectの各mojuleの木構造の深さを作成
Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
Object = Object.fillna('0')
Object = Object.drop_duplicates()
Object.index = range(0,len(Object))
Object['module_depth'] = pd.DataFrame(np.zeros(len(Object)))
for i in Object.index:
    obj = Object.iloc[i,:]['module_id']
    depth = 1
    while True:
        if len(dtObject.iloc[Object['children'].str.contains(obj).values,:]) >= 1:
            #print (Object.iloc[Object['children'].str.contains(obj).values,:])
            obj = Object.iloc[Object['children'].str.contains(obj).values,:]['module_id'].values[0]
            depth += 1
        else:
            Object.loc[i,'module_depth'] = depth
            break
    print i,depth

Object.columns = [u'course_id', u'object', u'category', u'children', u'start', u'module_depth']
yy = Object[[u'object',u'module_depth']]
Object.to_csv('/Users/IkkiTanaka/Documents/KDDCup/Object_depth.csv',index=False)
train = train.merge(yy ,how='left',on='object')
test = test.merge(yy,how='left',on='object')

train.to_csv('/Users/IkkiTanaka/Documents/KDDCup/train/log_train_depth.csv',index=False)
test.to_csv('/Users/IkkiTanaka/Documents/KDDCup/test/log_test_depth.csv',index=False)
'''
len_enr_train = len(enr_train)
len_enr_test = len(enr_test)
enr_train = enr_train.reset_index().merge(label, how='inner',on='enrollment_id').sort('index').drop('index',axis=1)#ここで1つデータが落ちている

Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
Object = Object.fillna('0')
Object = Object.drop_duplicates()
Object.index = range(0,len(Object))

#Object.loc[(Object['category']=='chapter').values,['course_id']]
train['category'] = train.reset_index().merge(Object,how='left',left_on='object',right_on='module_id').sort('index')['category'].values
#train.loc[(train['category'].isnull()).values,['category']] = train.iloc[(train['category'].isnull()).values,:]['object']
train = train.fillna('0')

test['category'] = test.reset_index().merge(Object,how='left',left_on='object',right_on='module_id').sort('index')['category'].values
#test.loc[(test['category'].isnull()).values,['category']] = test.iloc[(test['category'].isnull()).values,:]['object']
#train.iloc[(train['category'].isnull()).values,:]['object'].value_counts().index
test = test.fillna('0')

'''
#Objectのproblemにtimeをつける
Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
Object = Object.fillna('0')
Object = Object.drop_duplicates()
Object.index = range(0,len(Object))
Object['chapter'] = pd.DataFrame(np.zeros(len(Object)))
for obj in Object.iloc[(Object['category']=='problem').values,:]['module_id'].values:
    if len(Object.iloc[Object['children'].str.contains(obj).values,:]['module_id']):
        a = Object.iloc[Object['children'].str.contains(obj).values,:]['module_id'].values[0]
        if len(Object.iloc[Object['children'].str.contains(a).values,:]['start']) > 0:
            a2 = Object.iloc[Object['children'].str.contains(a).values,:]['start'].values[0]
            print a2
            Object.loc[(Object['module_id']==obj).values,['start']] = a2
            a3 = Object.iloc[Object['children'].str.contains(a).values,:]['module_id'].values[0]

            if len(Object.iloc[Object['children'].str.contains(a3).values,:]['module_id']) > 0:
                a4 = Object.iloc[Object['children'].str.contains(a3).values,:]['module_id'].values[0]
                Object.loc[(Object['module_id']==obj).values,['chapter']] = a4

print Object.iloc[(Object['category']=='problem').values,:][['category','chapter','start']]
Object.to_csv('/Users/IkkiTanaka/Documents/KDDCup/object_problem_time.csv',index=False)
'''
Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object_problem_time.csv')

enr_train[['min_time','max_time','mean_time','len_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_timelen_mean.csv')
enr_test[['min_time','max_time','mean_time','len_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_timelen_mean.csv')

#そのuserが参加しているchapterのユニーク数
#10日以内に新しいproblemが始まるか
chapter_unique = train.iloc[(train['category']=='chapter').values,:][['username','object']].drop_duplicates()
#実質参加しているchapter数
chapter_unique_user = chapter_unique['username'].value_counts()
chapter_unique_user = pd.DataFrame(chapter_unique_user,columns=['chapter_unique'])
chapter_unique_user['username'] = chapter_unique_user.index
enr_train['chapter_unique'] = enr_train.merge(chapter_unique_user, on='username',how='left')['chapter_unique']

#その参加したchaperの中のproblemのstartをつけ、10日以内に新しいproblemがいくつ始まるか
aaa = chapter_unique.merge(Object.iloc[(Object['category']=='problem').values,:][['category','chapter','start']],left_on='object',right_on='chapter',how='outer')[['username','chapter','start']]
f_toordinal = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000 if x != 'null' else 0
aaa['start'] = aaa['start'].fillna('null').apply(f_toordinal)
aaa = aaa.dropna()
f_to1 = lambda x: 1 if 0<= x <= 10 else 0
def prob_in10days(x):
    #print x[0]
    #aaa = problemのstartが記述されている
    #そのusernameのchapterのproblemのstart
    t = aaa.iloc[(aaa['username']==x['username']).values,:]['start'].values
    if len(t)>0:
        t2 = t - x['max_time']#usernameのchapter
        #print 1
        return np.sum(pd.Series(t2).apply(f_to1))#１０日以内にproblemのある数
    else:
        return np.nan

#con = np.apply_along_axis(prob_in10days,1,aaa[['username','start']].values)
enr_train['prob_in10days'] = enr_train.apply(prob_in10days,axis=1)
#con = [prob_in10days(x) for x in enr_train[['username','max_time']].values]
#prob_in10days = np.vectorize(prob_in10days)
#bbb = aaa[['username','start']].values[:100]
#con = prob_in10days(bbb)
#enr_train['prob_in10days'] = con
enr_train = enr_train.fillna(0)
#aaa2 = aaa.groupby('username').sum()['prob_in10days']
#enr_train['prob_in10days'] = enr_train.merge(aaa2,on='username',how='left')['prob_in10days']
#enr_train = enr_train.fillna(0)


chapter_unique = test.iloc[(test['category']=='chapter').values,:][['username','object']].drop_duplicates()
#実質参加しているchapter数
chapter_unique_user = chapter_unique['username'].value_counts()
chapter_unique_user = pd.DataFrame(chapter_unique_user,columns=['chapter_unique'])
chapter_unique_user['username'] = chapter_unique_user.index
enr_test['chapter_unique'] = enr_test.merge(chapter_unique_user, on='username',how='left')['chapter_unique']

#そのchaperの中のproblemのstartをつける
aaa = chapter_unique.merge(Object.iloc[(Object['category']=='problem').values,:][['category','chapter','start']],left_on='object',right_on='chapter',how='outer')[['username','chapter','start']]
f_toordinal = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000 if x != 'null' else 0
aaa['start'] = aaa['start'].fillna('null').apply(f_toordinal)
aaa = aaa.dropna()

enr_test['prob_in10days'] = enr_test.apply(prob_in10days,axis=1)
enr_test = enr_test.fillna(0)



#10日以内に新しいproblemが始まるか(courseのみ考慮,上は過去参加したchapterの中だけを見ている)
f_time = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000 if x != 'null' else np.nan
chapter_time = Object.loc[(Object['category']=='problem').values,['course_id','module_id','category','start']]
chapter_time['start'] = chapter_time['start'].apply(f_time)
chapter_time = chapter_time.dropna()

def in10days_num(x):
    course = x['course_id']
    max_time = x['max_time']
    course_chapter = chapter_time.iloc[(chapter_time['course_id']==course).values,:]['start']
    if True in pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().values:
        a = pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().value_counts()[True]#10日以内にあるかず
        b = 1#ダミー変数
        #print a
        #x['course_in10days'] = a
        #print x
        #x['course_in10days_dummy'] = b
        return a
    else:
        a = 0
        b = 0
        #x['course_in10days'] = a
        #x['course_in10days_dummy'] = b
        return a

def in10days_dummy(x):
    course = x['course_id']
    max_time = x['max_time']
    course_chapter = chapter_time.iloc[(chapter_time['course_id']==course).values,:]['start']
    if True in pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().values:
        a = pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().value_counts()[True]#10日以内にあるかず
        b = 1#ダミー変数
        #print a
        #x['course_in10days'] = a
        #print x
        #x['course_in10days_dummy'] = b
        return b
    else:
        a = 0
        b = 0
        #x['course_in10days'] = a
        #x['course_in10days_dummy'] = b
        return b

#10日以内にproblemが新しく始まるかの情報
enr_train['problem_in10days'] = enr_train.apply(in10days_num,axis=1)
enr_train['problem_in10days_dummy'] = enr_train.apply(in10days_dummy,axis=1)

enr_test['problem_in10days'] = enr_test.apply(in10days_num,axis=1)
enr_test['problem_in10days_dummy'] = enr_test.apply(in10days_dummy,axis=1)




#category_label = []
#a = train['category'].value_counts()[(train['category'].value_counts()>100).values].index.values
#a2 = test['category'].value_counts()[(test['category'].value_counts()>100).values].index.values
#for i in a:
#    if i in a2:
#        category_label.append(i)
#print 'category_label: ' , len(category_label)

#train.iloc[(train['category']=='sequential').values,:].sort('enrollment_id')
#trainにdropのlabelをつける

#timeをyear, month, day, hourに変換する
f_y = lambda x: x[:4]#year
train['year'] = train['time'].apply(f_y)
test['year'] = test['time'].apply(f_y)

f_m = lambda x: x[5:7]#month
train['month'] = train['time'].apply(f_m)
test['month'] = test['time'].apply(f_m)

f_d = lambda x: x[8:10]#day
train['day'] = train['time'].apply(f_d)
test['day'] = test['time'].apply(f_d)

f_h = lambda x: x[11:13]#hour
train['hour'] = train['time'].apply(f_h)
test['hour'] = test['time'].apply(f_h)

#曜日をつける
f_w = lambda x: str(date(int(x[:4]),int(x[5:7]),int(x[8:10])).weekday())
train['weekday'] = train['time'].apply(f_w)
test['weekday'] = test['time'].apply(f_w)

del train['time']
del test['time']

#LibFFM用
#n_val = round(len(train)*0.2)
#rows = np.random.choice(train.index.values, len(train),replace=False)
#train = train.ix[rows]
#train = train.drop_duplicates()
#test = test.drop_duplicates()

#train.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_fm.csv', index=False)
#test.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_fm.csv', index=False)


#enr_trainの中のusernameとcourse_idのカウント数を各idに追加する
X = pd.concat((enr_train[[col for col in enr_train.columns if col in ["enrollment_id",'username','course_id'] ]], enr_test))
count_lk = {col: X.groupby(col).aggregate({"enrollment_id": "count"}).to_dict()["enrollment_id"] for col in X.columns}

for col in ['username','course_id']:
    enr_train[col + "_count"] = ([count_lk[col][x] for x in enr_train[col]])
    enr_test[col + "_count"] = ([count_lk[col][x] for x in enr_test[col]])

#enr_train.iloc[(enr_train['username']=='1qXC7Fjbwp66GPQc6pHLfEuO8WKozxG4').values,:]
#X['username'].value_counts()
#enr_trainにlog_trainのデータを付加する
for col in ['source','event','year','month','day','hour','weekday','category']:#'source',
    l_train_count = train.groupby(['enrollment_id',col]).aggregate({'enrollment_id':'count'}).unstack()
    l_train_count['enrollment_id']['enrollment_id'] = l_train_count['enrollment_id'].index

    col_count = l_train_count['enrollment_id']
    col_count.index = enr_train.index
    if col == 'month':
        col_count.columns = col_count.columns + '_m'
    if col == 'day':
        col_count.columns = col_count.columns + '_d'
    if col == 'hour':
        col_count.columns = col_count.columns + '_h'
    if col == 'weekday':
        col_count.columns = col_count.columns + '_w'
    if col == 'module_depth':
        col_count.columns = col_count.columns + '_md'
    if col == 'category':
        #col_count = col_count[category_label]
        col_count.columns = col_count.columns + '_cg'

    enr_train = pd.concat([enr_train,col_count],axis=1)

#log_trainでの各idの連続する数を追加する
enr_train['sum_count'] = enr_train[['server','browser']].sum(1)
enr_train = enr_train.fillna(0)

#del train['0_cg']

#enr_testにlog_testのデータを付加する
for col in ['source','event','year','month','day','hour','weekday','category']:
    l_test_count = test.groupby(['enrollment_id',col]).aggregate({'enrollment_id':'count'}).unstack()
    l_test_count['enrollment_id']['enrollment_id'] = l_test_count['enrollment_id'].index

    col_count = l_test_count['enrollment_id']
    col_count.index = enr_test.index
    if col == 'month':
        col_count.columns = col_count.columns + '_m'
    if col == 'day':
        col_count.columns = col_count.columns + '_d'
    if col == 'hour':
        col_count.columns = col_count.columns + '_h'
    if col == 'weekday':
        col_count.columns = col_count.columns + '_w'
    if col == 'module_depth':
        col_count.columns = col_count.columns + '_md'
    if col == 'category':
        #col_count = col_count[category_label]
        col_count.columns = col_count.columns + '_cg'

    enr_test = pd.concat([enr_test,col_count],axis=1)

#log_testでの各idの連続する数を追加する
enr_test['sum_count'] = enr_test[['server','browser']].sum(1)
enr_test = enr_test.fillna(0)

#del enr_train['server'],enr_train['browser']
#del enr_test['server'],enr_test['browser']

#Objectのカウント
#cnt = Counter()
#tr_te = pd.concat([train,test])
#for i in tr_te['object']:
#    cnt[i]+=1
#
#obj_count = pd.DataFrame(cnt.items(),columns=['object','object_count'])
#train = train.merge(obj_count,on='object',how='outer')
#test = test.merge(obj_count,on='object',how='inner')
#enr_train = enr_train.merge(train[['username','object_count']],on='username',how='inner')


#object.csv
#Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
#Object['module_id'].columns = ['object']
#Object.merge(enr_train, on='object', how='inner')[['category','children']]

#enr_train['problem_in10days'] = enr_train['course_in10days']
#enr_test['problem_in10days'] = enr_test['course_in10days']

#del enr_train['course_in10days'],enr_test['course_in10days']
#enr_train = enr_train.T.drop_duplicates().T
#enr_trainvalを1:2にsplit
n_val = round(len(enr_train)*0.2)
np.random.seed(19920407)
rows = np.random.choice(enr_train.index.values, len(enr_train),replace=False)

new_train = enr_train.ix[rows[n_val:]]
val_data = enr_train.ix[rows[:n_val]]
#shuffle_train = enr_train.ix[rows]
shuffle_train = enr_train

val_label = val_data['drop']

print '(new_train+val_data), shuffle_trian, enr_testが元の長さと同じか'
print 'dropデータの無いtrainの中の1つのデータが落ちたから1少ない'

print (len(new_train)+len(val_data))==len_enr_train-1, len(shuffle_train) == len_enr_train-1, len(enr_test) == len_enr_test, len(val_label) == len(val_data)

print new_train.columns
print enr_test.columns
print new_train.columns == val_data.columns
print new_train.columns == shuffle_train.columns

new_train.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/new_enr_train.csv',index=False)
val_data.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/enr_validation.csv',index=False)
shuffle_train.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/shuffle_enr_train2.csv',index=False)
enr_test.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/new_enr_test2.csv',index=False)
val_label.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/val_enr_label.csv',index=False)






dtrain = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/shuffle_enr_train.csv')
dtest = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/new_enr_test.csv')
dtrain = dtrain.sort('enrollment_id')
dtest = dtest.sort('enrollment_id')
label = dtrain['drop']

'''
yyy = dtrain.groupby('username')['drop'].sum()
yyy = pd.DataFrame(yyy)
yyy['username'] = yyy.index


dtrain = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/shuffle_enr_train.csv')
dtrain['sum_drop'] = dtrain.reset_index().merge(yyy,on='username',how='left').sort('index').drop('index',axis=1)['drop_y'].values
dtrain['sum_nondrop'] = dtrain['username_count'] - dtrain['sum_drop']
f_tonan = lambda x: 0 if x > 3 else np.nan
dtrain['sum_nondrop'] = dtrain['sum_nondrop'] - dtrain['username_count'].apply(f_tonan)
dtrain['sum_drop'] = dtrain['sum_drop'] - dtrain['username_count'].apply(f_tonan)

dtest['sum_drop'] = dtest.reset_index().merge(yyy,on='username',how='left').sort('index').drop('index',axis=1)['drop'].values
dtest['sum_nondrop'] = dtest['username_count'] - dtest['sum_drop']
dtest['sum_nondrop'] = dtest['sum_nondrop'] - dtest['username_count'].apply(f_tonan)
dtest['sum_drop'] = dtest['sum_drop'] - dtest['username_count'].apply(f_tonan)
'''
'''
train = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/log_train_depth.csv')
test = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/log_test_depth.csv')
X = pd.concat([train,test],axis=0,ignore_index=True)
obj_count = X['object'].value_counts()
obj_count = pd.DataFrame(obj_count,columns=['obj_count'])
obj_count['object'] = obj_count.index
gg = X.merge(obj_count,on='object',how='left').sort('enrollment_id')
label_ = dtrain[['enrollment_id','drop']]
ggg = gg.merge(label_,on='enrollment_id',how='left').sort('enrollment_id')
#log_trainのobjectのカウントを取りidごとの最小の値を追加
ggg2 = ggg.groupby('enrollment_id').min()['obj_count']
ggg2.index = range(0,len(ggg2))
dtrain['obj_count_min'] = ggg2[:len(dtrain)]
dtest['obj_count_min'] = ggg2[len(dtrain):].values
'''
#ggg2 = ggg.groupby('enrollment_id').max()['obj_count']
#ggg2.index = range(0,len(ggg2))
#dtrain['obj_count_max'] = ggg2[:len(dtrain)]
#dtest['obj_count_max'] = ggg2[len(dtrain):].values
#ggg.iloc[ggg['module_depth'].notnull().values,:]
#ggg2 = ggg.groupby('enrollment_id').mean()['obj_count']
#ggg2.index = range(0,len(ggg2))
#dtrain['obj_count_mean'] = ggg2[:len(dtrain)]
#dtest['obj_count_mean'] = ggg2[len(dtrain):].values

'''
#usernameの全体で見た情報を追加
xx = dtrain.groupby('username').sum()
for col in [u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki', u'2013', u'2014', u'01_m', u'02_m', u'05_m', u'06_m', u'07_m', u'08_m', u'10_m', u'11_m', u'12_m', u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d', u'00_h', u'01_h', u'02_h', u'03_h', u'04_h', u'05_h', u'06_h', u'07_h', u'08_h', u'09_h', u'10_h', u'11_h', u'12_h', u'13_h', u'14_h', u'15_h', u'16_h', u'17_h', u'18_h', u'19_h', u'20_h', u'21_h', u'22_h', u'23_h', u'0_w', u'1_w', u'2_w', u'3_w', u'4_w', u'5_w', u'6_w', u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg', u'sum_count']:
    dtrain[col+'_all_user'] = xx[col]

xx = dtest.groupby('username').sum()
for col in [u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki', u'2013', u'2014', u'01_m', u'02_m', u'05_m', u'06_m', u'07_m', u'08_m', u'10_m', u'11_m', u'12_m', u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d', u'00_h', u'01_h', u'02_h', u'03_h', u'04_h', u'05_h', u'06_h', u'07_h', u'08_h', u'09_h', u'10_h', u'11_h', u'12_h', u'13_h', u'14_h', u'15_h', u'16_h', u'17_h', u'18_h', u'19_h', u'20_h', u'21_h', u'22_h', u'23_h', u'0_w', u'1_w', u'2_w', u'3_w', u'4_w', u'5_w', u'6_w', u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg', u'sum_count']:
    dtest[col+'_all_user'] = xx[col]
'''









#クラスごとの離反率
aaa = dtrain.groupby('course_id')['drop'].sum()
aaa = pd.DataFrame(aaa,columns=['drop'])
aaa['course_id'] = aaa.index
aaa = aaa.sort('course_id')
bbb = dtrain['course_id'].value_counts()
bbb = pd.DataFrame(bbb,columns=['len'])
bbb['course_id'] = bbb.index
bbb = bbb.sort('course_id')
#aaa['drop'].values/bbb['len'].values.astype(float)
bbb['ratio_of_drop'] = aaa['drop'].values/bbb['len'].values.astype(float)

ccc = bbb[['course_id','ratio_of_drop']]
ccc['droprate_course'] = aaa['drop']#courseごとのdropout数
dtrain = dtrain.reset_index().merge(ccc,on='course_id',how='left').sort('index').drop('index',axis=1)
dtest = dtest.reset_index().merge(ccc,on='course_id',how='left').sort('index').drop('index',axis=1)
#dtrain = dtrain.sort('enrollment_id')
#dtest = dtest.sort('enrollment_id')
dtrain.index = range(0,len(dtrain))
dtest.index = range(0,len(dtest))

#username_countごとの離反率
aaa = dtrain.groupby('username_count')['drop'].sum()
aaa = pd.DataFrame(aaa,columns=['drop'])
aaa['username_count'] = aaa.index
aaa = aaa.sort('username_count')
bbb = dtrain['username_count'].value_counts()
bbb = pd.DataFrame(bbb,columns=['len'])
bbb['username_count'] = bbb.index
bbb = bbb.sort('username_count')
#aaa['drop'].values/bbb['len'].values.astype(float)
bbb['ratio_of_drop_uc'] = aaa['drop'].values/bbb['len'].values.astype(float)

ccc = bbb[['username_count','ratio_of_drop_uc']]
ccc['droprate_uc'] = aaa['drop']#username_countごとのdropout数
dtrain = dtrain.reset_index().merge(ccc,on='username_count',how='left').sort('index').drop('index',axis=1)
dtest = dtest.reset_index().merge(ccc,on='username_count',how='left').sort('index').drop('index',axis=1)
#dtrain = dtrain.sort('enrollment_id')
#dtest = dtest.sort('enrollment_id')
dtrain.index = range(0,len(dtrain))
dtest.index = range(0,len(dtest))


del dtrain['drop']

X = pd.concat([dtrain,dtest])
X.index = range(0,len(X))

#course_idのダミー変数化
b = categorical(np.array(X['course_id']), drop=True)
b = pd.DataFrame(b)

#aaa = pd.factorize(X['username'])#usernameのFactorize化
#dtrain['username'] = aaa[0][:len(dtrain)]
#dtrain[dtrain['username_count'] <= 5]['username'] = -999


#bbb = pd.factorize(X['course_id'])#course_idのFactorize化
#dtrain['course_id'] = bbb[0][:len(dtrain)]

#del dtrain['enrollment_id'],dtrain['username'],dtrain['course_id'],
dtrain = pd.concat([b[:len(dtrain)],dtrain],axis=1)
#label = dtrain['drop']
#del dtrain['drop']
#dtrain.iloc[:,39:] = dtrain.iloc[:,39:].applymap(f)#対数変換


#dtest = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/new_enr_test.csv')
#b = categorical(np.array(dtest['course_id']), drop=True)
#b = pd.DataFrame(b)
#dtest['username'] = aaa[0][len(dtrain):]

#dtest['course_id'] = bbb[0][len(dtrain):]



#del dtest['enrollment_id'],dtest['username'], dtest['course_id']

xx = b[len(dtrain):]
xx.index = range(0,len(xx))
dtest = pd.concat([xx,dtest],axis=1)
#dtest.iloc[:,39:] = dtest.iloc[:,39:].applymap(f)#対数変換



#sum_countで割って, percentageを追加する
for col in [u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki']:
    dtrain[col+'_pct'] = dtrain[col]/dtrain[u'sum_count']

for col in [u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki']:
    dtest[col+'_pct'] = dtest[col]/dtest[u'sum_count']

dtrain['sum_count_cg'] = dtrain[[u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']].sum(1)
#sum_countで割って, percentageを追加する
for col in [u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']:
    dtrain[col+'_pct'] = dtrain[col]/dtrain[u'sum_count_cg']

dtest['sum_count_cg'] = dtest[[u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']].sum(1)
#sum_countで割って, percentageを追加する
for col in [u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']:
    dtest[col+'_pct'] = dtest[col]/dtest[u'sum_count_cg']


#year, month, day, hour ,weekdayのカウントデータを1にする
f_to1 = lambda x: 1 if x >=1 else 0
label_to1 = [u'2013', u'2014', u'01_m', u'02_m', u'05_m', u'06_m', u'07_m', u'08_m', u'10_m', u'11_m', u'12_m', u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d', u'00_h', u'01_h', u'02_h', u'03_h', u'04_h', u'05_h', u'06_h', u'07_h', u'08_h', u'09_h', u'10_h', u'11_h', u'12_h', u'13_h', u'14_h', u'15_h', u'16_h', u'17_h', u'18_h', u'19_h', u'20_h', u'21_h', u'22_h', u'23_h', u'0_w', u'1_w', u'2_w', u'3_w', u'4_w', u'5_w', u'6_w']




dtrain[label_to1] = dtrain[label_to1].applymap(f_to1)
dtest[label_to1] = dtest[label_to1].applymap(f_to1)

label_to1 = [u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki']
dtrain[label_to1] = dtrain[label_to1].applymap(f_to1)
dtest[label_to1] = dtest[label_to1].applymap(f_to1)

#label_to1 = [u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']
#dtrain[label_to1] = dtrain[label_to1].applymap(f_to1)
#dtest[label_to1] = dtest[label_to1].applymap(f_to1)





#dtrain.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_NN.csv',index=False)
#dtest.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_NN.csv',index=False)
'''
#log_trainのなかの各idの最初と最後の時間を抽出
train = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/log_train.csv')
test = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/log_test.csv')

#enrollment_trainとenrollment_idを合わせるためにソート
train = train.sort('enrollment_id')
test = test.sort('enrollment_id')

f_time = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000
train_id_time = train[['enrollment_id','time']]
test_id_time = test[['enrollment_id','time']]
train_id_time['time'] = train_id_time['time'].apply(f_time)
test_id_time['time'] = test_id_time['time'].apply(f_time)

a = np.zeros(len(dtrain)*4)
a = a.reshape((len(dtrain),4))
train_time = pd.DataFrame(a,columns=['min_time','max_time','mean_time','len_time'])
train_time.columns = ['min_time','max_time','mean_time','len_time']
i = 0
a = train_id_time['enrollment_id'].drop_duplicates().values
#f_toordinal = lambda x: x.toordinal() - 735000
for id in a:
    train_time_ = train_id_time.iloc[(train_id_time['enrollment_id']==id).values,1]
    train_time.loc[i,['min_time']] = min(train_time_)
    train_time.loc[i,['max_time']] = max(train_time_)
    #train_id_time['time'] = train_id_time['time'].apply(f_toordinal)
    train_time.loc[i,['mean_time']] = np.mean(train_time_.values)
    i+=1
    if i % 1000 == 0:
        print i
train_time['len_time'] = train_time['max_time'] - train_time['min_time']

test_time = pd.DataFrame(np.zeros(len(dtest)),columns=['time'])
train_time.columns = ['min_time','max_time','mean_time','len_time']

a = np.zeros(len(dtest)*4)
a = a.reshape((len(dtest),4))
test_time = pd.DataFrame(a,columns=['min_time','max_time','mean_time','len_time'])
test_time.columns = ['min_time','max_time','mean_time','len_time']
i = 0
a = test_id_time['enrollment_id'].drop_duplicates().values
for id in a:
    test_time_ = test_id_time.iloc[(test_id_time['enrollment_id']==id).values,1]
    test_time.loc[i,['min_time']] = min(test_time_)
    test_time.loc[i,['max_time']] = max(test_time_)

    #test_id_time['time'] = test_id_time['time'].apply(f_toordinal)
    test_time.loc[i,['mean_time']] = np.mean(test_time_.values)

    i+=1
    if i % 1000 == 0:
        print i
test_time['len_time'] = test_time['max_time'] - test_time['min_time']
['min_time','max_time','mean_time','len_time']

dtrain[['min_time','max_time','mean_time','len_time']] = train_time
dtest[['min_time','max_time','mean_time','len_time']] = test_time

#train_timelenを読み込んでdtrainに付け加える
train_time.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_timelen_mean.csv',index=False)
test_time.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_timelen_mean.csv',index=False)
'''

#shuffleしてないenr_trainに追加しろ!!
dtrain[['min_time','max_time','mean_time','len_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_timelen_mean.csv')
dtest[['min_time','max_time','mean_time','len_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_timelen_mean.csv')

dtrain['max-mean']=dtrain['max_time']-dtrain['mean_time']
dtrain['mean-min']=dtrain['mean_time']-dtrain['min_time']

dtest['max-mean']=dtest['max_time']-dtest['mean_time']
dtest['mean-min']=dtest['mean_time']-dtest['min_time']

'''
log_trainのなかのmodule_idをstartとの差で表す
train = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/log_train.csv')
test = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/log_test.csv')

Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
Object = Object.fillna('0')
Object = Object.drop_duplicates()
Object.index = range(0,len(Object))

train = train.merge(Object[['module_id','start']],how='left',left_on='object',right_on='module_id')
del train['module_id']
train['start'] = train['start'].fillna('null')
f_toordinal = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000 if x != 'null' else 100000

train['time'] = train['time'].apply(f_toordinal)
test['time'] = test['time'].apply(f_toordinal)

train['start'] = train['start'].apply(f_toordinal)
train['diff_time'] = train['time'] - train['start']
f_ela = lambda x: 0 if x < -90000 else x
train['diff_time'] = train['diff_time'].apply(f_ela)

ddd = train.groupby('enrollment_id')[['start','diff_time']].mean()
ddd.index = range(0,len(ddd))
dtrain[['start','diff_time']] = ddd
#train_course = dtrain['course_id'] +1
#test_course = dtest['course_id'] +1
'''

#dtrain = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_timelen.csv')
#dtest = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_timelen.csv')

#dtrain = dtrain.iloc[:,39:]
#dtest = dtest.iloc[:,39:]

f_to0 = lambda x: -1 if x == 0 else x
#dtrain.iloc[:,:39] = dtrain.iloc[:,:39].applymap(f_to0)
#dtest.iloc[:,:39] = dtest.iloc[:,:39].applymap(f_to0)
#dtrain['time_len'] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_timelen.csv')
#dtest['time_len'] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_timelen.csv')



'''
dtrain_leaf.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/train_NN.csv',index=False)
dtest_leaf.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/test_NN.csv',index=False)
label.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/label_NN.csv',index=False)
'''

#del dtrain['object_fact'], dtest['object_fact']

#dtrain.iloc[:,39:] = dtrain.iloc[:,39:].applymap(f)#対数変換
#dtest.iloc[:,39:] = dtest.iloc[:,39:].applymap(f)#対数変換
'''
numerics = dtrain.loc[:, [ u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']]
 
# for each pair of variables, determine which mathmatical operators to use based on redundancy
for i in range(0, numerics.columns.size-1):
    for j in range(0, numerics.columns.size-1):
        col1 = str(numerics.columns.values[i])
        col2 = str(numerics.columns.values[j])
        # multiply fields together (we allow values to be squared)
        if i <= j:
            #name = col1 + "*" + col2
            #dtrain = pd.concat([dtrain, pd.Series(numerics.iloc[:,i] * numerics.iloc[:,j], name=name)], axis=1)
            name = col1 + "-" + col2
            dtrain = pd.concat([dtrain, pd.Series(numerics.iloc[:,i] - numerics.iloc[:,j], name=name)], axis=1)
        # add fields together
        #if i < j:
            #name = col1 + "+" + col2
            #dtrain = pd.concat([dtrain, pd.Series(numerics.iloc[:,i] + numerics.iloc[:,j], name=name)], axis=1)
        # divide and subtract fields from each other
        #if not i == j:
            #name = col1 + "/" + col2
            #dtrain = pd.concat([dtrain, pd.Series(numerics.iloc[:,i] / numerics.iloc[:,j], name=name)], axis=1)
            #name = col1 + "-" + col2
            #dtrain = pd.concat([dtrain, pd.Series(numerics.iloc[:,i] - numerics.iloc[:,j], name=name)], axis=1)

#numerics = dtest.loc[:, [u'username_count', u'course_id_count', u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki']]
numerics = dtest.loc[:, [ u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg']]
# for each pair of variables, determine which mathmatical operators to use based on redundancy
for i in range(0, numerics.columns.size-1):
    for j in range(0, numerics.columns.size-1):
        col1 = str(numerics.columns.values[i])
        col2 = str(numerics.columns.values[j])
        # multiply fields together (we allow values to be squared)
        if i <= j:
            #name = col1 + "*" + col2
            #dtest = pd.concat([dtest, pd.Series(numerics.iloc[:,i] * numerics.iloc[:,j], name=name)], axis=1)
            name = col1 + "-" + col2
            dtest = pd.concat([dtest, pd.Series(numerics.iloc[:,i] - numerics.iloc[:,j], name=name)], axis=1)
        # add fields together
        #if i < j:
            #name = col1 + "+" + col2
            #dtest = pd.concat([dtest, pd.Series(numerics.iloc[:,i] + numerics.iloc[:,j], name=name)], axis=1)
        # divide and subtract fields from each other
        #if not i == j:
            #name = col1 + "/" + col2
            #dtest = pd.concat([dtest, pd.Series(numerics.iloc[:,i] / numerics.iloc[:,j], name=name)], axis=1)
            #name = col1 + "-" + col2
            #dtest = pd.concat([dtest, pd.Series(numerics.iloc[:,i] - numerics.iloc[:,j], name=name)], axis=1)
'''
'''
onehot = fe.create(gl.SFrame(pd.DataFrame(train['object'])), fe.OneHotEncoder( max_categories=30))
def apply_onehot(dataset):
    if 'encoded_features' in dataset.column_names():
        # operation already completed on SFrame
        return dataset
    
    return onehot.transform(dataset)
qqq = apply_onehot(gl.SFrame(pd.DataFrame(train['object'])))
def f(x):
    try:
        return x.keys()[0]
    except:
        return 0
qqq2 = qqq.to_dataframe()
qqq2 = qqq2['encoded_features'].apply(f)
train['object'] = qqq2
qqq2 = train.groupby('enrollment_id')['object'].mean()
qqq2.index = range(0,len(qqq2))
dtrain_leaf['object_encoded'] = qqq2

#oneday = gl.SFrame(dtrain_leaf
hasher = fe.create(gl.SFrame(pd.DataFrame(dtrain['course_id'])), fe.FeatureHasher(num_bits=22))

def apply_feature_hasher(dataset):
    if 'hashed_features' in dataset.column_names():
        # feature hasher already performed
        return dataset
    return hasher.transform(dataset)
www = apply_feature_hasher(gl.SFrame(pd.DataFrame(dtrain['course_id'])))
f = lambda x: x.keys()[0]
www2 = www.to_dataframe()
www2 = www2['hashed_features'].apply(f)

dtrain['course_id'] = www2


del dtrain_leaf['start']
#2つのやまがあるのでそれぞれ分けて学習してみる
dtrain_leaf.iloc[(dtrain_leaf.loc[:,['max_time']]<350).values),:]
dtest_leaf.iloc[(dtest_leaf.loc[:,['max_time']]<350).values),:]

#dtrain_leaf['course_id'] = bbb[0][:len(dtrain)]
#dtest_leaf['course_id'] = bbb[0][len(dtrain):]
#ddd = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, u'username_count', u'course_id_count', u'browser', u'server', u'access', u'discussion', u'nagivate', u'page_close', u'problem', u'video', u'wiki', u'sum_count', u'min_time', u'max_time', u'len_time',u'01_m', u'02_m', u'05_m', u'06_m', u'07_m', u'08_m', u'10_m', u'11_m', u'12_m']


#dtrain_leaf.loc[(dtrain_leaf['min_time']>350).values,'min_time'] = dtrain_leaf.loc[(dtrain_leaf['min_time']>350).values,'min_time'] - 198
#dtrain_leaf.loc[(dtrain_leaf['max_time']>350).values,'max_time'] = dtrain_leaf.loc[(dtrain_leaf['max_time']>350).values,'max_time'] - 198
#dtrain_leaf.loc[(dtrain_leaf['mean_time']>350).values,'mean_time'] = dtrain_leaf.loc[(dtrain_leaf['mean_time']>350).values,'mean_time'] - 198
dtrain['obj_not_nan'] = dtrain[[u'1.0_md', u'2.0_md', u'3.0_md', u'5.0_md']].sum(1)
dtest['obj_not_nan'] = dtest[[u'1.0_md', u'2.0_md', u'3.0_md', u'5.0_md']].sum(1)
dtrain_leaf.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_train/NN/train_NN.csv',index=False)
dtest_leaf.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/NN/test_NN.csv',index=False)
label.to_csv('/Users/IkkiTanaka/Documents/KDDCup/fe_test/NN/label_NN.csv',index=False)
'''


using_label = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, u'username_count', u'course_id_count', u'2013', u'2014', u'01_m', u'02_m', u'05_m', u'06_m', u'07_m', u'08_m', u'10_m', u'11_m', u'12_m', u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d', u'00_h', u'01_h', u'02_h', u'03_h', u'04_h', u'05_h', u'06_h', u'07_h',u'08_h', u'09_h', u'10_h', u'11_h', u'12_h', u'13_h', u'14_h', u'15_h', u'16_h', u'17_h', u'18_h', u'19_h', u'20_h', u'21_h', u'22_h', u'23_h', u'0_w', u'1_w', u'2_w', u'3_w', u'4_w', u'5_w', u'6_w', u'0.0_md', u'1.0_md', u'2.0_md', u'3.0_md', u'5.0_md', u'0_cg', u'chapter_cg', u'combinedopenended_cg', u'problem_cg', u'sequential_cg', u'video_cg', u'sum_count', u'min_time', u'max_time', u'mean_time', u'len_time', u'max-mean', u'mean-min', u'access_pct', u'discussion_pct', u'nagivate_pct', u'page_close_pct', u'problem_pct', u'video_pct', u'wiki_pct',u'sum_count_cg', u'0_cg_pct', u'chapter_cg_pct', u'combinedopenended_cg_pct', u'problem_cg_pct', u'sequential_cg_pct', u'video_cg_pct', u'len_from_start']

dtrain['day_count'] = dtrain[[ u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d']].sum(1)

dtest['day_count'] = dtest[[ u'01_d', u'02_d', u'03_d', u'04_d', u'05_d', u'06_d', u'07_d', u'08_d', u'09_d', u'10_d', u'11_d', u'12_d', u'13_d', u'14_d', u'15_d', u'16_d', u'17_d', u'18_d', u'19_d', u'20_d', u'21_d', u'22_d', u'23_d', u'24_d', u'25_d', u'26_d', u'27_d', u'28_d', u'29_d', u'30_d', u'31_d']].sum(1)


Object = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/object.csv')
Object = Object.fillna('0')
Object = Object.drop_duplicates()
Object.index = range(0,len(Object))

#コースのstart時間
course_start = Object.loc[(Object['category']=='course').values,['course_id','start']]
f_time = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000
course_start['start'] = course_start['start'].apply(f_time)

dtrain = dtrain.reset_index().merge(course_start, on='course_id',how='left').sort('index').drop('index',axis=1)
dtrain['min-start'] = dtrain['min_time'] - dtrain['start']
dtrain['max-start'] = dtrain['max_time'] - dtrain['start']

dtest = dtest.reset_index().merge(course_start, on='course_id',how='left').sort('index').drop('index',axis=1)
dtest['min-start'] = dtest['min_time'] - dtest['start']
dtest['max-start'] = dtest['max_time'] - dtest['start']

#コースのchapter, sequentialなどの数
num_chapter = Object.groupby(['course_id','category']).count().unstack()['module_id']
num_chapter['course_id'] = num_chapter.index
dtrain['index'] = range(0,len(dtrain))
dtrain = dtrain.merge(num_chapter, on='course_id', how='left').sort('index').drop('index',axis=1)
dtrain = dtrain.fillna(0)
dtrain.index = range(0,len(dtrain))

dtest['index'] = range(0,len(dtest))
dtest = dtest.merge(num_chapter, on='course_id', how='left').sort('index').drop('index',axis=1)
dtest = dtest.fillna(0)
dtest.index = range(0,len(dtest))


#10日以内に新しいチャプターが始まるか
f_time = lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:10])).toordinal() - 735000 if x != 'null' else np.nan
chapter_time = Object.loc[(Object['category']=='chapter').values,['course_id','module_id','category','start']]
chapter_time['start'] = chapter_time['start'].apply(f_time)
chapter_time = chapter_time.dropna()

def in10days_num(x):
    course = x['course_id']
    max_time = x['max_time']
    course_chapter = chapter_time.iloc[(chapter_time['course_id']==course).values,:]['start']
    if True in pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().values:
        a = pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().value_counts()[True]#10日以内にあるかず
        b = 1#ダミー変数
        #print a
        #x['course_in10days'] = a
        #print x
        #x['course_in10days_dummy'] = b
        return a
    else:
        a = 0
        b = 0
        #x['course_in10days'] = a
        #x['course_in10days_dummy'] = b
        return a

def in10days_dummy(x):
    course = x['course_id']
    max_time = x['max_time']
    course_chapter = chapter_time.iloc[(chapter_time['course_id']==course).values,:]['start']
    if True in pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().values:
        a = pd.DataFrame([0 <= (course_chapter - max_time).values,(course_chapter - max_time).values <=10]).all().value_counts()[True]#10日以内にあるかず
        b = 1#ダミー変数
        #print a
        #x['course_in10days'] = a
        #print x
        #x['course_in10days_dummy'] = b
        return b
    else:
        a = 0
        b = 0
        #x['course_in10days'] = a
        #x['course_in10days_dummy'] = b
        return b

#10日以内にchapterが新しく始まるかの情報
#dtrain['course_in10days'] = dtrain.apply(in10days_num,axis=1)
#dtrain['course_in10days_dummy'] = dtrain.apply(in10days_dummy,axis=1)

#dtest['course_in10days'] = dtest.apply(in10days_num,axis=1)
#dtest['course_in10days_dummy'] = dtest.apply(in10days_dummy,axis=1)

'''
#その参加者が何回目の参加か
dtrain['drop'] = label
dtest.index = range(len(dtrain),len(dtrain)+len(dtest))
X = pd.concat([dtrain,dtest],ignore_index=True)
X = X.sort('min_time')
username = X['username'].drop_duplicates().values
X['past_enr'] = np.zeros(len(X))#過去の参加数
X['past_drop'] = np.zeros(len(X))#過去のdropout数
X['past_nondrop'] = np.zeros(len(X))#過去のdropout数
X['past_nondrop_rate'] = np.zeros(len(X))#過去のdropout率

new_X = pd.DataFrame()
count = 0
for i in username:
    username_data = X.loc[(X['username']==i).values,:]
    #%timeit 
    if len(username_data['drop'].values) > 1:#参加数が1回の人は欠損値とする
        a = username_data['drop']
        past_enr = range(1,len(a)+1)
        past_drop = a.cumsum()
        username_data['past_drop'] = past_drop.fillna(method='ffill')
    else:
        a = np.nan
        past_enr = 1
        past_drop = np.nan
        username_data['past_drop'] = np.nan
    username_data['past_enr'] = past_enr
    username_data['past_nondrop'] = username_data['past_enr'] - username_data['past_drop']
    username_data['past_nondrop_rate'] = username_data['past_nondrop']/username_data['past_enr']
    print username_data[['min_time','max_time','past_enr','past_drop','past_nondrop','past_nondrop_rate']]
    username_data.iloc[1:,:][['past_enr','past_drop','past_nondrop','past_nondrop_rate']] = username_data.iloc[:(len(username_data)-1),:][['past_enr','past_drop','past_nondrop','past_nondrop_rate']].values
    username_data.loc[username_data.index[0],['past_enr','past_drop','past_nondrop','past_nondrop_rate']] = [np.nan] *4
    
    new_X = pd.concat([new_X, username_data[['past_enr','past_drop','past_nondrop','past_nondrop_rate']]])
    count += 1
    if count % 1000 == 0:
        print len(username), count


past_dtrain = new_X.ix[dtrain.index]
#ss = new_X.ix[dtest.index]
#del ss['drop']
past_dtest = new_X.ix[dtest.index]
#保存
past_dtrain.to_csv('/Users/IkkiTanaka/Documents/KDDCup/train/new_train_past2.csv',index=False)
past_dtest.to_csv('/Users/IkkiTanaka/Documents/KDDCup/test/new_test_past2.csv',index=False)


dtrain = pd.concat([dtrain,past_dtrain],axis=1)
dtest = pd.concat([dtest,past_dtest],axis=1)

dtest.index = range(0,len(dtest))


dtrain = dtrain.sort_index()
dtest = dtest.sort_index()

label = dtrain['drop']
del dtrain['drop']

#X.to_csv('/Users/IkkiTanaka/Documents/KDDCup/enrollment_train_and_test.csv',index=False)
#X.groupby('username')


'''


dtrain[['past_enr','past_drop','past_nondrop','past_nondrop_rate']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/new_train_past2.csv')
dtest[['past_enr','past_drop','past_nondrop','past_nondrop_rate']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/new_test_past2.csv')

#dtrain.loc[(dtrain['past_enr']<=2).values,['past_drop','past_nondrop','past_nondrop_rate']] = np.nan
#dtest.loc[(dtest['past_enr']<=2).values,['past_drop','past_nondrop','past_nondrop_rate']] = np.nan

dtrain = dtrain.fillna(0)
dtest = dtest.fillna(0)

del dtrain['past_drop'], dtrain['past_nondrop']#, dtrain['past_nondrop_rate']
del dtest['past_drop'], dtest['past_nondrop']#, dtest['past_nondrop_rate']

'''
#そのusernameがその時点で何個のcourseに参加しているか

def count_course(time_array):
    a_min = []
    a_max = []
    for i in time_array:
        a_min.append(np.sum([1 for x in time_array if x[0] <= i[0] <= x[1]]))
        a_max.append(np.sum([1 for x in time_array if x[0] <= i[1] <= x[1]]))
    return np.vstack([a_min,a_max]).T

dtest.index = range(len(dtrain),len(dtrain)+len(dtest))
X = pd.concat([dtrain,dtest],ignore_index=True)
X = X.sort('min_time')
username = X['username'].drop_duplicates().values

new_X = pd.DataFrame()
count = 0
for i in username:
    username_data = X.loc[(X['username']==i).values,:]
    #%timeit 
    
    count_course_ = count_course(username_data[['min_time','max_time']].values)
    new_X = pd.concat([new_X, pd.DataFrame(count_course_, index=username_data.index, columns=['num_course_min','num_course_max'])])
    count += 1
    if count % 1000 == 0:
        print len(username), count


past_dtrain = new_X.ix[dtrain.index]
past_dtest = new_X.ix[dtest.index]
dtest.index = range(0,len(dtest))

dtrain = dtrain.sort_index()
dtest = dtest.sort_index()

#保存
past_dtrain.to_csv('/Users/IkkiTanaka/Documents/KDDCup/train/new_train_course_count.csv',index=False)
past_dtest.to_csv('/Users/IkkiTanaka/Documents/KDDCup/test/new_test_course_count.csv',index=False)
'''
#間違えたが精度上がった
#dtrain[['min_time','max_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/new_train_course_count.csv')
#dtest[['min_time','max_time']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/new_test_course_count.csv')

dtrain[['num_course_min','num_course_max']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/train/new_train_course_count.csv')
dtest[['num_course_min','num_course_max']] = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/test/new_test_course_count.csv')

#dtrain['num_course_min-max'] = dtrain['num_course_min'] - dtrain['num_course_max']
#dtrain['num_course_max-min'] = dtrain['num_course_max'] - dtrain['num_course_min']

#dtest['num_course_min-max'] = dtest['num_course_min'] - dtest['num_course_max']
#dtest['num_course_max-min'] = dtest['num_course_max'] - dtest['num_course_min']

#dtrain['num_course_min-max_abs'] = np.abs(dtrain['num_course_min'] - dtrain['num_course_max'])

#dtest['num_course_min-max_abs'] = np.abs(dtest['num_course_min'] - dtest['num_course_max'])


'''
#usernameをfactorize化
dtrain.loc[(dtrain['username_count']<10).values,'username'] = 'ikki'
dtest.loc[(dtest['username_count']<10).values,'username'] = 'ikki'

#a = dtrain.loc[(dtrain['username_count']>=10).values,:]
#a.iloc[(a['username']=='2oTvbzieHn2y5oozeOgSnruqE6N0BtR5').values,:]
#a2 = dtest.loc[(dtest['username_count']>=10).values,:]
#a2.iloc[(a2['username']=='2oTvbzieHn2y5oozeOgSnruqE6N0BtR5').values,:]

X = pd.concat([dtrain,dtest],ignore_index=True)
b = categorical(np.array(X['username']), drop=True)
b = pd.DataFrame(b)
dtrain = pd.concat([b[:len(dtrain)],dtrain],axis=1)
xx = b[len(dtrain):]
xx.index = range(0,len(xx))
dtest = pd.concat([xx,dtest],axis=1)
'''





del dtrain['username'],dtrain['course_id'],dtrain['enrollment_id'],
del dtest['username'], dtest['course_id'],dtest['enrollment_id'],

#学期の始まりからの時間
f_from_start = lambda x: x - 168 if x < 350 else x - 366
dtrain['len_from_start'] = dtrain['min_time'].apply(f_from_start)
dtest['len_from_start'] = dtest['min_time'].apply(f_from_start)

#学期の終わりからの時間
f_from_end = lambda x: 279 - x if x < 350 else 446 - x
dtrain['len_from_end'] = dtrain['max_time'].apply(f_from_end)
dtest['len_from_end'] = dtest['max_time'].apply(f_from_end)

#一日毎の平均log回数
dtrain['mean_stay_times'] = dtrain['sum_count']/dtrain['day_count']
dtest['mean_stay_times'] = dtest['sum_count']/dtest['day_count']

#一日毎の平均event回数
for col in [u'browser', u'server', u'access', u'discussion_x', u'nagivate', u'page_close', u'problem_x', u'video_x', u'wiki']:
    dtrain[col+'_per_day'] = dtrain[col]/dtrain[u'day_count']

for col in [u'browser', u'server', u'access', u'discussion_x', u'nagivate', u'page_close', u'problem_x', u'video_x', u'wiki']:
    dtest[col+'_per_day'] = dtest[col]/dtest[u'day_count']


#dtrain['len_from_end2'] = dtrain['min_time'].apply(f_from_end)
#dtest['len_from_end2'] = dtest['min_time'].apply(f_from_end)

#label = dtrain['drop']
#del dtrain['drop']

dtrain['2013_10'] = dtrain['10_m']
dtrain['2013_11'] = dtrain['11_m']
dtrain['2013_12'] = dtrain['12_m']
dtrain['2014_01'] = dtrain['01_m']
dtrain['2014_02'] = dtrain['02_m']
dtrain['2014_05'] = dtrain['05_m']
dtrain['2014_06'] = dtrain['06_m']
dtrain['2014_07'] = dtrain['07_m']
dtrain['2014_08'] = dtrain['08_m']

del dtrain['2013'],dtrain['2014'],dtrain['10_m'],dtrain['11_m'],dtrain['12_m'],dtrain['01_m'],dtrain['02_m'],dtrain['05_m'],dtrain['06_m'],dtrain['07_m'],dtrain['08_m']

dtest['2013_10'] = dtest['10_m']
dtest['2013_11'] = dtest['11_m']
dtest['2013_12'] = dtest['12_m']
dtest['2014_01'] = dtest['01_m']
dtest['2014_02'] = dtest['02_m']
dtest['2014_05'] = dtest['05_m']
dtest['2014_06'] = dtest['06_m']
dtest['2014_07'] = dtest['07_m']
dtest['2014_08'] = dtest['08_m']

del dtest['2013'],dtest['2014'],dtest['10_m'],dtest['11_m'],dtest['12_m'],dtest['01_m'],dtest['02_m'],dtest['05_m'],dtest['06_m'],dtest['07_m'],dtest['08_m']


dtrain.index = range(0,len(dtrain))
dtest.index = range(0,len(dtest))

'''
from sklearn.cluster import KMeans
clf = KMeans(n_clusters=50, init='k-means++', n_init=40, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=1, random_state=1992, copy_x=True, n_jobs=-1)
clf.fit(dtrain)
dtrain['kmeans50'] = clf.predict(dtrain)
dtest['kmeans50'] = clf.predict(dtest)
clf = KMeans(n_clusters=40, init='k-means++', n_init=40, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=1, random_state=1992, copy_x=True, n_jobs=-1)
clf.fit(dtrain)
dtrain['kmeans40'] = clf.predict(dtrain)
dtest['kmeans40'] = clf.predict(dtest)
clf = KMeans(n_clusters=30, init='k-means++', n_init=40, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=1, random_state=1992, copy_x=True, n_jobs=-1)
clf.fit(dtrain)
dtrain['kmeans30'] = clf.predict(dtrain)
dtest['kmeans30'] = clf.predict(dtest)
clf = KMeans(n_clusters=20, init='k-means++', n_init=40, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=1, random_state=1992, copy_x=True, n_jobs=-1)
clf.fit(dtrain)
dtrain['kmeans20'] = clf.predict(dtrain)
dtest['kmeans20'] = clf.predict(dtest)
clf = KMeans(n_clusters=10, init='k-means++', n_init=40, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=1, random_state=1992, copy_x=True, n_jobs=-1)
clf.fit(dtrain)
dtrain['kmeans10'] = clf.predict(dtrain)
dtest['kmeans10'] = clf.predict(dtest)
'''







dtrain_leaf = dtrain
dtest_leaf = dtest
print dtrain_leaf.columns == dtest_leaf.columns
aa = dtrain_leaf.columns

#dtrain_leaf.to_csv('/Users/IkkiTanaka/Documents/ikeda/ikeda_train.csv',index=False)
#dtest_leaf.to_csv('/Users/IkkiTanaka/Documents/ikeda/ikeda_test.csv',index=False)
#label.to_csv('/Users/IkkiTanaka/Documents/ikeda/ikeda_label.csv',index=False)

#f_tonan = lambda x: np.nan if x == 0 else x
#dtrain_leaf = dtrain_leaf.applymap(f_tonan)

np.random.seed(19920407)
rows = np.random.choice(dtrain_leaf.index.values, len(dtrain_leaf),replace=False)

#dtrain_leaf['drop'] = label
#d1 = dtrain_leaf.iloc[(dtrain_leaf['max_time']<350).values,:]
#d2 = dtrain_leaf.iloc[:,:-1]
#d2_label = d1['drop']
#dtrain = xgb.DMatrix(d2, label=d2_label.values)
#dtrain_leaf.iloc[(dtrain_leaf['sum_count']==1).values,:]['drop']
#dtest_leaf.iloc[(dtest_leaf['sum_count']==1).values,:]['drop']

#dtrain_leaf.loc[(dtrain_leaf['sum_count']==1).values,['past_nondrop_rate']] = 0.0
#dtest_leaf.loc[(dtest_leaf['sum_count']==1).values,['past_nondrop_rate']] = 0.0
#del dtrain_leaf['drop']


del dtrain_leaf['sum_count']
dtrain = xgb.DMatrix(dtrain_leaf, label=label)
dtest = xgb.DMatrix(dtest_leaf)


pred_name = []
num_model = 30
for i in xrange(0,num_model):
    random.seed(i*25433+23)
    param = {"objective" : "binary:logistic",#"binary:logistic",
              "eval_metric" :  'auc',
              #"eval_metric" : "ams@0.15",
              #'scale_pos_weight': 1.2, #sum_wneg/sum_wpos
              "num_class" :  1,
              "nthread" :  8,
              "bst:max_depth" :  random.randint(5,6),
              "bst:eta" :  random.uniform(.01, .05),#step_size
              "bst:gamma" : round(random.uniform(.0, 8.),1),#min_loss_reduction
              "bst:min_child_weight" : random.randint(0.,4.),
              "bst:subsample" :  round(random.uniform(.3, .9),2),#row_subsample
              "colsample_bytree" :  round(random.uniform(.4, 1.),2),#column_subsample
              "silent": 1,
              "base_score": round(random.uniform(.50, .55),2),
              #"max_delta_step": 1,
              #"scale_pos_weight": 1.6,
              }
    #if random.randint(0,1):
    #    param['scale_pos_weight'] = scale_pos_weight
    num_round = int( round(random.uniform(500, 550),0))
    #k = int(round(1+np.log2(dtrain_all_sf.num_row())))
    print param
    print num_round
    #print k
    #evallist  = [(dval, 'eval'),(dtrain_sp,'train')]
    #bst = xgb.train(param,dtrain_sp, num_round,evallist)
    #pred_prob = bst.predict( dtest )
    #print pred_prob
    watchlist  = [(dtrain,'train')]
    #bst = xgb.train(param,dtrain_sp, num_round,watchlist)

    bst=xgb.cv(param, dtrain, num_round, nfold=5, seed = 1992, show_stdv = False)
    #pred_prob = bst.predict( dtest )
    #print pred_prob
    f_ = lambda x: float(x.split('\tcv-test-auc:')[1][:8])
    bst = pd.Series(bst).apply(f_)
    num_round_ = bst.argmax() + 100#60
    cc = bst.max()
    if cc > 0.8907:
        watchlist  = [(dtrain,'train')]
        np.random.seed(19920407)
        bst = xgb.train(param,dtrain, num_round_,watchlist)
        pred_prob = bst.predict( dtest )
        sample = pd.read_csv('/Users/IkkiTanaka/Documents/KDDCup/sampleSubmission.csv',header=None)
        preds = pd.concat([sample[0],pd.DataFrame(pred_prob)],axis=1)
        pred_name.append('/Users/IkkiTanaka/Documents/KDDCup/pred/xgb/pred_all4%i_%f_%i_%i.csv' % (i,cc,num_round_, param["bst:max_depth"]))
        preds.to_csv('/Users/IkkiTanaka/Documents/KDDCup/pred/xgb/pred_all4%i_%f_%i_%i.csv' % (i,cc,num_round_, param["bst:max_depth"]) ,header=None,index=False)

Pred = pd.DataFrame(np.zeros(80362),columns=[1])[1]
for i in xrange(0,len(pred_name)):
    pred = pd.read_csv(pred_name[i], header=None)
    Pred = Pred + pred[1]
Pred = Pred/float(len(pred_name))
Pred = pd.concat([pred[0],Pred],axis=1)
Pred.to_csv('/Users/IkkiTanaka/Documents/KDDCup/pred/xgb/Pred46.csv',header=None,index=False)



