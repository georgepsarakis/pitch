import click

from pitch.runner.bootstrap import bootstrap
from pitch.plugins.utils import list_plugins, loader
from pitch.cli.logger import logger


@click.group()
@click.version_option()
def cli():
    pass


@cli.command(help='Run a sequence file.')
@click.option('-P', '--processes', type=int,
              help='Number of processes', default=1)
@click.option('-R', '--request-plugins',
              multiple=True,
              help='Additional request plugins (in Python import notation)')
@click.option('-S', '--response-plugins',
              multiple=True,
              help='Additional response plugins (in Python import notation)')
@click.argument('sequence_file',
                type=click.Path(exists=True, dir_okay=False, readable=True))
def run(processes, request_plugins, response_plugins, sequence_file):
    logger.info('Loading file: {}'.format(sequence_file))
    bootstrap(
        processes=processes,
        request_plugins=request_plugins,
        response_plugins=response_plugins,
        sequence_file=sequence_file,
        logger=logger
    )


@cli.group(help='View available plugins.')
def plugins():
    pass


@plugins.command(name='list', help='Display available plugins and exit.')
@click.option('-R', '--request-plugins',
              multiple=True,
              help='Additional request plugins (in Python import notation)')
@click.option('-S', '--response-plugins',
              multiple=True,
              help='Additional response plugins (in Python import notation)')
def list_(request_plugins, response_plugins):
    loader(request_plugins, response_plugins)
    for plugin_type, phase_plugins in list_plugins().items():
        click.echo()
        click.secho(plugin_type.upper(), bold=True)
        click.echo('-' * len(plugin_type))
        for name, plugin_details in sorted(phase_plugins.items()):
            signature = []
            for argument in plugin_details['arguments']:
                signature.append(argument['name'])
                if 'default' in argument:
                    signature[-1] += '={}'.format(argument['default'])
            click.secho('{}({})'.format(name, ', '.join(signature)),
                        bold=True)
            click.echo(2 * ' ', nl=False)
            click.echo(plugin_details['docstring'].strip('.'))
            click.echo()


if __name__ == "__main__":
    cli()
