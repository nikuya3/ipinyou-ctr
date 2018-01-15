from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals.joblib import dump
from sklearn.metrics import classification_report, f1_score, recall_score, precision_score
from sklearn.model_selection import GridSearchCV
from time import time
from os.path import isdir, isfile, join
import pandas as pd
from csv import writer
from os import mkdir
from util import split_data

rf_models_path = 'rf_models.csv'
train_pct = 0.8

parser = ArgumentParser(description='Fits a Random forest model onto the training dataset and outputs performance',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-t', '--trees', type=int, default=1000, help='The number of decision trees to use.')
parser.add_argument('-o', '--output', type=str, default='dump', help='Output directory to use.')
parser.add_argument('-i', '--input', type=int, default='data/ads_clean.csv', help='Path to the input dataset.')
parser.add_argument('-cv', type=bool, default=False, help='Pass if hyperparameters should be tuned via cross validation')
args = parser.parse_args()
trees = args.trees
dump_dir = args.output

if not isdir(dump_dir):
    mkdir(dump_dir)

x = pd.read_csv(args.input)
x = x.as_matrix()
x = x.astype(int)

x_tr, x_te, y_tr, y_te = split_data(x, train_pct)

class_weights = {0: 1, 1: 1000}
parameters = tuned_parameters = [{'n_estimators': [10, 100, 1000], 'max_features': ["auto", "sqrt", "log2", None]}]

if args.cv:
    clf = GridSearchCV(RandomForestClassifier(), tuned_parameters, cv=5, scoring='f1', n_jobs=-1)
    clf.fit(x_tr, y_tr)
    print(f"Best estimator: {clf.best_estimator_}, params: {clf.best_params_}, score: {clf.best_score_}")
    y_pred = clf.predict(x_te)
else:
    rf = RandomForestClassifier(n_estimators=trees, n_jobs=-1, verbose=1, class_weight=class_weights)
    rf.fit(x_tr, y_tr)
    y_pred = rf.predict(x_te)

recall = recall_score(y_te, y_pred)
precision = precision_score(y_te, y_pred)
print(classification_report(y_te, y_pred))

id = str(int(time()))
if isfile(rf_models_path):
    with open(rf_models_path, 'a') as file:
        models_writer = writer(file)
        models_writer.writerow([id, recall, precision, rf.n_estimators, rf.class_weight[0], rf.class_weight[1]])
else:
    with open(rf_models_path, 'w') as file:
        models_writer = writer(file)
        models_writer.writerow(
            ['id', 'recall', 'precision', 'n_estimators', 'class_weight_0', 'class_weight_1'])
        models_writer.writerow([id, recall, precision, rf.n_estimators, rf.class_weight[0], rf.class_weight[1]])

if not isdir(join(dump_dir, 'rf')):
    mkdir(join(dump_dir, 'rf'))

if args.cv:
    dump(clf.best_estimator_, join(dump_dir, 'rf', id))
else:
    dump(rf.best_estimator_, join(dump_dir, 'rf', id))
