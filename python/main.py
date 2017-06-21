import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.sparse import coo_matrix
import time 
import sys
import tensorflow as tf

import utils
from models import LR, FM, PNN1, PNN1_Fixed, PNN2, FNN, CCPM, Fast_CTR, Fast_CTR_Concat

#train_file = '../data_cretio/train.txt.yx.0.7'
#test_file = '../data_cretio/train.txt.yx.0.3'
train_file = '/Users/jwpan/Github/DL_for_Multifield_Categorical_Data/data_yahoo/ctr_20170517_0530_0.015.txt.thres10.yx'
test_file = '/Users/jwpan/Github/DL_for_Multifield_Categorical_Data/data_yahoo/ctr_20170517_0530_0.015.txt.thres10.yx'
# fm_model_file = '../data/fm.model.txt'
print "train_file: ", train_file
print "test_file: ", test_file
sys.stdout.flush()

input_dim = utils.INPUT_DIM

train_data = utils.read_data(train_file)
# train_data = utils.shuffle(train_data)
test_data = utils.read_data(test_file)

train_size = train_data[0].shape[0]
test_size = test_data[0].shape[0]
num_feas = len(utils.FIELD_SIZES)

min_round = 1
num_round = 1000
early_stop_round = 3
batch_size = 2000

field_sizes = utils.FIELD_SIZES
field_offsets = utils.FIELD_OFFSETS

print 'train_data', train_data

def train(model):
    history_score = []
    start_time = time.time()
    print 'epochs\tloss\ttrain-auc\teval-auc\ttime'
    sys.stdout.flush()
    for i in range(num_round):
        fetches = [model.optimizer, model.loss]
        if batch_size > 0:
            ls = []
            for j in range(train_size / batch_size + 1):
                X_i, y_i = utils.slice(train_data, j * batch_size, batch_size)
                _, l = model.run(fetches, X_i, y_i)
                ls.append(l)
        elif batch_size == -1:
            X_i, y_i = utils.slice(train_data)
            _, l = model.run(fetches, X_i, y_i)
            ls = [l]
        lst_train_pred = []
        lst_test_pred = []
        if batch_size > 0:
            for j in range(train_size / batch_size + 1):
                X_i, y_i = utils.slice(train_data, j * batch_size, batch_size)
                #X_i = utils.libsvm_2_coo(X_i, (len(X_i), input_dim)).tocsr()
                _train_preds = model.run(model.y_prob, X_i)
                lst_train_pred.append(_train_preds)
            for j in range(test_size / batch_size + 1):
                X_i, y_i = utils.slice(test_data, j * batch_size, batch_size)
                #X_i = utils.libsvm_2_coo(X_i, (len(X_i), input_dim)).tocsr()
                _test_preds = model.run(model.y_prob, X_i)
                lst_test_pred.append(_test_preds)
        train_preds = np.concatenate(lst_train_pred)
        test_preds = np.concatenate(lst_test_pred)
        train_score = roc_auc_score(train_data[1], train_preds)
        test_score = roc_auc_score(test_data[1], test_preds)
        print '%d\t%f\t%f\t%f\t%f' % (i, np.mean(ls), train_score, test_score, time.time() - start_time)
        sys.stdout.flush()
        history_score.append(test_score)
        if i > min_round and i > early_stop_round:
            if np.argmax(history_score) == i - early_stop_round and history_score[-1] - history_score[
                        -1 * early_stop_round] < 1e-5:
                print 'early stop\nbest iteration:\n[%d]\teval-auc: %f' % (
                    np.argmax(history_score), np.max(history_score))
                sys.stdout.flush()
                break


algo = 'fm'
print "algo", algo
sys.stdout.flush()

if algo == 'lr':
    lr_params = {
        'input_dim': input_dim,
        'opt_algo': 'gd',
        'learning_rate': 0.01,
        'l2_weight': 0,
        'random_seed': 0
    }

    model = LR(**lr_params)
elif algo == 'fm':
    fm_params = {
        'input_dim': input_dim,
        'factor_order': 10,
        'opt_algo': 'adam',
        'learning_rate': 0.0005,
        'l2_w': 0,
        'l2_v': 0,
    }

    model = FM(**fm_params)
elif algo == 'fnn':
    fnn_params = {
        'layer_sizes': [field_sizes, 1, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'gd',
        'learning_rate': 0.1,
        'layer_l2': [0, 0],
        'random_seed': 0
    }

    model = FNN(**fnn_params)
elif algo == 'ccpm':
    ccpm_params = {
        'layer_sizes': [field_sizes, 10, 5, 3],
        'layer_acts': ['tanh', 'tanh', 'none'],
        'layer_keeps': [1, 1, 1],
        'opt_algo': 'gd',
        'learning_rate': 0.1,
        'random_seed': 0
    }

    model = CCPM(**ccpm_params)
elif algo == 'pnn1':
    pnn1_params = {
        'layer_sizes': [field_sizes, 10, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'gd',
        'learning_rate': 0.1,
        'layer_l2': [0, 0],
        'kernel_l2': 0,
        'random_seed': 0
    }

    model = PNN1(**pnn1_params)
elif algo == 'fast_ctr':
    fast_ctr_params = {
        'layer_sizes': [field_sizes, 10, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'adam',
        'learning_rate': 0.001,
        'layer_l2': [0, 0],
        'kernel_l2': 0,
        'random_seed': 0
    }

    model = Fast_CTR(**fast_ctr_params)
elif algo == 'fast_ctr_concat':
    fast_ctr_concat_params = {
        'layer_sizes': [field_sizes, 10, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'gd',
        'learning_rate': 0.1,
        'layer_l2': [0, 0],
        'kernel_l2': 0,
        'random_seed': 0
    }

    model = Fast_CTR_Concat(**fast_ctr_concat_params)
elif algo == 'pnn1_fixed':
    pnn1_fixed_params = {
        'layer_sizes': [field_sizes, 10, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'gd',
        'learning_rate': 0.1,
        'layer_l2': [0, 0.1],
        'kernel_l2': 0,
        'random_seed': 0
    }

    model = PNN1_Fixed(**pnn1_fixed_params)
elif algo == 'pnn2':
    pnn2_params = {
        'layer_sizes': [field_sizes, 10, 1],
        'layer_acts': ['tanh', 'none'],
        'layer_keeps': [1, 1],
        'opt_algo': 'adam',
        'learning_rate': 0.001,
        'layer_l2': [0, 0],
        'kernel_l2': 0,
        'random_seed': 0
    }
    print 'pnn2, config:'
    print pnn2_params
    sys.stdout.flush()

    model = PNN2(**pnn2_params)

if algo in {'fnn', 'ccpm', 'pnn1', 'pnn1_fixed', 'pnn2', 'fast_ctr', 'fast_ctr_concat'}:
    train_data = utils.split_data(train_data)
    test_data = utils.split_data(test_data)

train(model)

# X_i, y_i = utils.slice(train_data, 0, 100)
# fetches = [model.tmp1, model.tmp2]
# tmp1, tmp2 = model.run(fetches, X_i, y_i)
# print tmp1.shape
# print tmp2.shape
