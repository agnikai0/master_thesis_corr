import pickle
import tqdm
from shared.utils import check_path_throw_error
import os
import numpy as np
import json 

"""
This is a collection of functions for inital data handling. Everything what is
not related to intial stuff should be in data_processing.py
"""

def load_dataset_deepcorr_specific(path_dataset, run_ids, packet_thresholds):
    """
    This function loads the dataset from the base pickle files. The dataset is a list of flow pairs.
    The dataset is loaded from the given path_dataset. The dataset is loaded from the pickle files
    that are named according to the given run_ids and packet_thresholds. The dataset is the concatenation
    of all the datasets loaded from the pickle files. The dataset is returned as a list of flow pairs.
    Note: packet_threshold 0 stands for any size between 0 and 299
    """
    print("\nLoading dataset from base pickle files...")
        
    dataset = []
    paths_to_pickle_files_to_load = []
    
    for run_id in run_ids:
        for threshold in packet_thresholds:
            if threshold == "":
                filename = f"{run_id}_tordata.pickle"  # For files without a packet threshold
            else:
                filename = f"{run_id}_tordata{threshold}.pickle"  # For files with a packet threshold
            file_path = os.path.join(path_dataset, filename)
            if os.path.exists(file_path):
                paths_to_pickle_files_to_load.append(file_path)
            else:
                print(f"Warning: The file {filename} does not exist and will be skipped.")

    with tqdm.tqdm(total=len(paths_to_pickle_files_to_load), desc="Loading progress") as pbar:
        for path in paths_to_pickle_files_to_load:
            print("Loading", path)
            with open(path, 'rb') as file:
                dataset += pickle.load(file)
            pbar.update(1)

    print('Dataset length/Amount of true flow pairs used: ', len(dataset))
    return dataset


def load_dataset_deepcorr(path_dataset, load_all_data):  
    print("\nLoading dataset from base pickle files...")
    check_path_throw_error(path_dataset)

    runs = {
        '8872': '192.168.122.117',
        '8802': '192.168.122.117',
        '8873': '192.168.122.67',
        '8803': '192.168.122.67',
        '8874': '192.168.122.113',
        '8804': '192.168.122.113',
        '8875': '192.168.122.120',
        '8876': '192.168.122.30',
        '8877': '192.168.122.208',
        '8878': '192.168.122.58'
    }

    dataset = []

    # build all paths for better loading bar
    paths_to_pickle_files_to_load = []
    for name in runs:
        if load_all_data == False:
            paths_to_pickle_files_to_load.append(
                os.path.join(path_dataset, f"{name}_tordata300.pickle"))
        else:
            paths_to_pickle_files_to_load.extend([
                # TODO add the padding stuff from the other script (somewhere done already) and then use this. otherwise this doesent work currently
                # It contains about another 11.260 flow pairs (half of the full dataset)
                os.path.join(path_dataset, f"{name}_tordata.pickle"),
                os.path.join(path_dataset, f"{name}_tordata300.pickle"),
                os.path.join(path_dataset, f"{name}_tordata400.pickle"),
                os.path.join(path_dataset, f"{name}_tordata500.pickle")
            ])

    with tqdm.tqdm(total=len(paths_to_pickle_files_to_load),
                   desc="Loading progress") as pbar:
        for path in paths_to_pickle_files_to_load:
            with open(path, 'rb') as file:
                dataset += pickle.load(file)
            pbar.update(1)

    len_tr = len(dataset)
    print('Dataset length/Amount of true flow pairs used: ', len_tr)

    return dataset

def load_test_index_deepcorr():
    print("\nLoading testing indexes from pickle file...")
    with open('test_index300.pickle', 'rb') as file:
        test_index = pickle.load(file)[:1000]
    return test_index

def load_pregenerated_memmap_dataset(path):
    print("\nLoading pregenerated memmap dataset...")
    check_path_throw_error(path)

    # Load shapes from the JSON file
    shapes_file_path = os.path.join(path, 'memmap_shapes.json')
    with open(shapes_file_path, 'r') as f:
        shapes = json.load(f)

    labels_path = os.path.join(path, "training_labels")
    l2s_path = os.path.join(path, "training_flow_pairs")
    labels_test_path = os.path.join(path, "test_labels")
    l2s_test_path = os.path.join(path, "test_flow_pairs")

    labels = np.memmap(labels_path, dtype=np.float32, mode='r', shape=tuple(shapes["labels_train_shape"]))
    l2s = np.memmap(l2s_path, dtype=np.float32, mode='r', shape=tuple(shapes["flow_pairs_train_shape"]))
    labels_test = np.memmap(labels_test_path, dtype=np.float32, mode='r', shape=tuple(shapes["labels_test_shape"]))
    l2s_test = np.memmap(l2s_test_path, dtype=np.float32, mode='r', shape=tuple(shapes["flow_pairs_test_shape"]))

    # Count true and false labels
    true_training_pairs = np.sum(labels)
    false_training_pairs = labels.shape[0] - true_training_pairs
    true_testing_pairs = np.sum(labels_test)
    false_testing_pairs = labels_test.shape[0] - true_testing_pairs

    # Print the dataset sizes
    print("Pre-generated dataset loaded successfully! Dataset sizes:")
    print(f"TRAINING set size (true and false flow pairs total): {labels.shape[0]}")
    print(f"TRAINING set size of true flow pairs: {int(true_training_pairs)}")
    print(f"TRAINING set size of false flow pairs: {int(false_training_pairs)}")
    print(f"TESTING set size (true and false flow pairs total): {labels_test.shape[0]}")
    print(f"TESTING set size of true flow pairs: {int(true_testing_pairs)}")
    print(f"TESTING set size of false flow pairs: {int(false_testing_pairs)}")


    return l2s, labels, l2s_test, labels_test

def save_memmap_info_flow_pairs_and_labels(flow_pairs_train, labels_train, flow_pairs_test, labels_test, save_path):
    print(f"\nSaving memmap file information to {save_path}...")
    # Save shapes of the memmap arrays in a JSON file
    shapes = {
        "flow_pairs_train_shape": flow_pairs_train.shape,
        "labels_train_shape": labels_train.shape,
        "flow_pairs_test_shape": flow_pairs_test.shape,
        "labels_test_shape": labels_test.shape
    }
    shapes_file_path = os.path.join(save_path, 'memmap_shapes.json')
    with open(shapes_file_path, 'w') as f:
        json.dump(shapes, f)