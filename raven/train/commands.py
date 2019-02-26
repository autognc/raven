'''
Author(s):      Carson Schubert (carson.schubert14@gmail.com)
Date Created:   02/23/2019

Command group for training in raven.
'''

from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

from PyInquirer import prompt

@with_plugins(iter_entry_points('raven.plugins.train'))
@click.group()
# @click.option('-k', '--kfold', is_flag=True)
@click.pass_context
# def train(ctx, kfold):
def train(ctx):
    # ctx.ensure_object(dict)
    # ctx.obj['KFOLD'] = kfold
    pass

@train.command(help='List available training plugins.')
def list():
    for entry in iter_entry_points(group='raven.plugins.train', name=None):
        print(entry.name)
