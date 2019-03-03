import click
import raven.train.options

@click.group(help='TensorFlow Semantic Segmentation.')
@click.pass_context
@raven.train.options.kfold_opt
def tf_semantic(ctx, kfold):
    pass
    
@tf_semantic.command()
@click.pass_context
def print(ctx):
    click.echo('Test semantic print')
