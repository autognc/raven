"""
Author(s):      Carson Schubert (carson.schubert14@gmail.com)
Date Created:   03/19/2019

Classes necessary for interfacing with the data command group.
"""

import glob
import click
import os
import shutil
from pathlib import Path
from datetime import datetime
from ravenml.utils.local_cache import RMLCache
from ravenml.utils.question import cli_spinner, user_input, user_selects, user_confirms
from ravenml.utils.imageset import get_imageset_names
from ravenml.data.helpers import default_filter_and_load
from colorama import Fore

### CONSTANTS ###
# these should be used in all possible situations to protect us
# in case they change in the future
STANDARD_DIR = 'standard'
FOLD_DIR_PREFIX = 'fold_'
TEST_DIR = 'test'
METADATA_PREFIX = 'meta_'

# TODO add necessary functionality to this class as needed

class CreateInput(object):
    """Represents a dataset creation input. Contains all plugin-independent
    information necessary for training. Plugins can define their own behavior
    for getting additional information.

    """
    def __init__(self, config:dict=None, plugin_name:str=None):

        if config is None or plugin_name is None:
            raise click.exceptions.UsageError(('You must provide the --config option '
                'on `ravenml create` when using this plugin command.'))
        
        self.config = config
        
        ## Set up Local Cache
        # TODO: maybe create the subdir here?
        # currently the cache_name subdir is only created IF the plugin places files there
        self.plugin_cache = RMLCache(plugin_name)
        
        ## Set up Artifact Path
        dp = config.get('dataset_path')
        if dp is None:
            self.plugin_cache.ensure_clean_subpath('temp')
            self.plugin_cache.ensure_subpath_exists('temp')
            self.dataset_path = Path(self.plugin_cache.path / 'temp')
        else:
            dp = Path(os.path.expanduser(dp))
            # check if local path contains data
            if os.path.exists(dp) and os.path.isdir(dp) and len(os.listdir(dp)) > 0:
                if config.get('overwrite_local') or user_confirms('Local artifact storage location contains old data. Overwrite?'):
                    shutil.rmtree(dp)
                else:
                    click.echo(Fore.RED + 'Dataset creation cancelled.')
                    click.get_current_context().exit() 
            # create directory, need exist_ok since we only delete
            # if directory contains files
            # TODO: protect against paths to actual files
            os.makedirs(dp, exist_ok=True)
            self.dataset_path = dp
        
        ## Set up Imageset
        # prompt for dataset if not provided
        imageset_list = config.get('imageset')
        if imageset_list is None:
            imageset_options = cli_spinner('No imageset provided. Finding imagesets on S3...', get_imageset_names)
            imageset_list = user_selects('Choose imageset:', imageset_options, selection_type="checkbox")
        else: 
            for imageset in imageset_list:
                if imageset not in get_imageset_names():
                    hint = 'imageset name, no such imageset exists on S3'
                    raise click.exceptions.BadParameter(imageset_list, param=imageset_list, param_hint=hint)
        
        # download dataset and populate field  
        image_ids, filter_metadata, temp_dir = default_filter_and_load(imageset=imageset_list, 
                        metadata_prefix=METADATA_PREFIX,
                        filter=config.get('filter'))        
    
        ## Set up Basic Metadata
        # TODO: add environment description, git hash, etc
        self.metadata = config.get('metadata', {})
        # handle user defined metadata fields
        if not self.metadata.get('created_by'):
            self.metadata['created_by'] = user_input('Please enter your first and last name:')
        if not self.metadata.get('comments'):
            self.metadata['comments'] = user_input('Please enter descriptive comments about this training:')
        
        # handle automatic metadata fields
        self.metadata['date_started_at'] = datetime.utcnow().isoformat() + "Z"
        self.metadata['imagesets_used'] = imageset_list
        
        ## Set up fields for plugin use
        # NOTE: plugins should overwrite the architecture field to something
        # more specific/useful since it is used to name the final uploaded model
        self.metadata[plugin_name] = {'architecture': plugin_name}
        # plugins should only ACCESS the plugin_metadata attibute and add items. They should
        # NEVER assign to the attribute as it will break the reference to the overall metadata dict
        self.plugin_metadata = self.metadata[plugin_name]
        if not config.get('plugin'):
            raise click.exceptions.BadParameter(config, param=config, param_hint='config, no "plugin" field. Config was')
        else:
            self.plugin_config = config.get('plugin') 


class Dataset(object):
    """Represents a training dataset.

    Args:
        name (str): name of dataset 
        metadata (dict): metadata of dataset
        path (Path): filepath to dataset

    Attributes:
        name (str): name of the dataset 
        metadata (dict): metadata of dataset
        path (Path): filepath to dataset
    """
    def __init__(self, name: str, metadata: dict, path: Path):
        self.name = name
        self.metadata = metadata
        self.path = path
        
    def get_num_folds(self) -> int:
        """Gets the number of folds this dataset supports for 
        k-fold cross validation.

        Returns:
            int: number of folds
        """
        path = self.path / Path('dev')
        return len(glob.glob(str(path) + FOLD_DIR_PREFIX + '*'))
    