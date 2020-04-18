import click

from pyworkflow import Workflow
from pyworkflow import NodeException


class Config(object):
    def __init__(self):
        self.verbose = False

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--file-directory', type=click.Path())
@pass_config
def cli(config, file_directory):
    print('Unable to run file')
    config.file_directory = file_directory


@cli.command()
@pass_config
def execute(config):
    if config.file_directory is None:
        click.echo('Please specify a workflow to run')
        return
    try:
        click.echo('Loading workflow file form %s' % config.file_directory)
        Workflow.execute_workflow(config.file_directory)
    except NodeException as ne:
        click.echo("Issues during node execution")
        click.echo(ne)
