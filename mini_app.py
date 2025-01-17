from flask import Flask
import click

app = Flask(__name__)

@click.command("hello-world")
def hello():
    click.echo("Hello from CLI!")

app.cli.add_command(hello)
