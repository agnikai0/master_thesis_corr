# Needed to find the other modules. Dont really like this solution.
import sys
import os
sys.path.insert(0, 
                os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, 
                os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import argparse
import time

from modules.model_training import train_model
from modules.model_validation import perform_custom_cv
from modules.config_utlis import init_model_for_training
from modules.data_handling import load_prepare_dataset, save_dataset_info
from modules.data_processing import flatten_flow_pairs_and_label
from modules.enviroment_setup import setup_environment
from modules.model_persistence import save_model
from modules.plotting import plot_multiple_roc_curves
from shared.utils import copy_file, save_plot_to_path

def verify_and_stop_if_invalid(config):
    """
    Verifies that all dataset paths in the config are valid.
    Stops script execution and prints invalid paths if any are found.
    
    Parameters:
    - config: The configuration dictionary.
    """
    invalid_paths = []
    for run_name, run_settings in config['runs'].items():
        dataset_path = run_settings.get('pregenerated_dataset_path', '')
        if not os.path.exists(dataset_path):
            invalid_paths.append(dataset_path)
    
    if invalid_paths:  # If there are any invalid paths
        print("Invalid paths found. Please correct the following paths in your configuration:")
        for path in invalid_paths:
            print(f"- {path}")
        sys.exit("Script execution stopped due to invalid paths.")
    else:
        print("All paths are valid.")

def main():
    """Train a Classifier on the dataset."""
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description='Train a Classifier on the dataset.'
    )
    parser.add_argument(
        '-c', '--config_path', type=str, required=True, 
        help='Path to the configuration file'
    )
    parser.add_argument(
        '-r', '--run_name', type=str, 
        help='Name of the run followed by date time. \
            If not set the current date and time only will be used.'
    )
    args = parser.parse_args()

    config, parent_run_folder_path = setup_environment(args)
    
    # print("\nModel type:", config['model_type'])
    # print("Selected Model Config:", 
    #       config['selected_model_configs'])

    load_dataset_into_memory = config['load_dataset_into_memory']
    
    copy_file(args.config_path, os.path.join(
        parent_run_folder_path, "used_config_train.yaml"))
    
    mean_res = []

    #todo this is a bit ugly
    run_names = []

    verify_and_stop_if_invalid(config)
    
    for run_name, run_settings in config['runs'].items():
        # Display which run this is
        print(f"\n ---------------------------------- Training run: {run_name} -----------------------------------------")
        
        run_names.append(run_name)
        
        # Create a subfolder for the run
        sub_run_folder_path = os.path.join(parent_run_folder_path, run_name)
        os.makedirs(sub_run_folder_path, exist_ok=True)

        model_type = run_settings['model_type']
        model_config_name = run_settings['model_config_name']
        pregenerated_dataset_path = run_settings['pregenerated_dataset_path']
        
        flow_pairs_train, labels_train, flow_pairs_test, labels_test = \
            load_prepare_dataset(pregenerated_dataset_path, 
                                    load_dataset_into_memory)
        
        flattened_flow_pairs_train, flattened_labels_train = \
            flatten_flow_pairs_and_label(flow_pairs_train, labels_train)
        
        model_training_parameter = (config['model_configs']
                        [model_type]
                        [model_config_name])
        
        # Model initialization
        model = init_model_for_training(model_type, 
                                        model_training_parameter)
        
        trained_model = train_model(model, 
                                    flattened_flow_pairs_train, 
                                    flattened_labels_train)        

        if(config['validation_settings']['run_validation'] == True):
            cv_mean_res = perform_custom_cv(trained_model, 
                                                flattened_flow_pairs_train, 
                                                flattened_labels_train, 
                                                cv_num=config['validation_settings']
                                                ['cross_validation']
                                                ['cv'], 
                                                run_folder_path = sub_run_folder_path)
        
            mean_res.append(cv_mean_res)

        # Save the model
        save_model(trained_model, sub_run_folder_path)

    fig_linear, fig_log = plot_multiple_roc_curves(mean_res, run_names)

    save_plot_to_path(fig=fig_linear, file_name="roc_linear_comb.png", save_path=parent_run_folder_path)
    save_plot_to_path(fig=fig_log, file_name="roc_log_comb.png", save_path=parent_run_folder_path)


    # save_model(trained_model, run_folder_path)

    # save_dataset_info(config, 
    #                   flow_pairs_train, 
    #                   labels_train, 
    #                   flow_pairs_test, 
    #                   labels_test, 
    #                   run_folder_path)

    end_time = time.time()
    # pretty output full training process time in seconds, minutes and hours
    if end_time - start_time > 3600:
        print(f"\nFull training process finished in {(end_time - start_time) / 3600} hours.")
    elif end_time - start_time > 60:
        print(f"\nFull training process finished in {(end_time - start_time) / 60} minutes.")
    else:
        print(f"\nFull training process finished in {end_time - start_time} seconds.")

    

if __name__ == "__main__":
    main()