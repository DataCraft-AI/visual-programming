import sys

import click
import os
import uuid

from pyworkflow import Workflow
from pyworkflow import NodeException


class Config(object):
    def __init__(self):
        self.verbose = False

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
def execute(filename):

    stdin_files = []

    if not click.get_text_stream('stdin').isatty():
        stdin_text = click.get_text_stream('stdin')

        # TODO should be done for each separate file coming from stdin, currently working for one file, but easy to build up.

        # write standard in to a new file in local filesystem
        file_name = str(uuid.uuid4())

        # TODO small issue here, might be better to upload this file to the workflow directory instead of cwd
        new_file_path = os.path.join(os.getcwd(), file_name)

        # read from std in and upload a new file in project directory
        with open(new_file_path, 'w') as f:
            f.write(stdin_text.read())

        stdin_files.append(file_name)

    if filename is None:
        click.echo('Please specify a workflow to run')
        return
    try:
        click.echo('Loading workflow file form %s' % filename)
        Workflow.execute_workflow(filename, stdin_files)
    except NodeException as ne:
        click.echo("Issues during node execution")
        click.echo(ne)
