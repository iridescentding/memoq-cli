# -*- coding: utf-8 -*-
"""
memoQ CLI - File Commands
"""

import sys
from pathlib import Path
import click

from ..wsapi import FileManager
from ..utils import output_json, handle_api_error


@click.group()
def file():
    """File import/export commands"""
    pass


@file.command("upload")
@click.argument("project_guid")
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="File or directory path")
@click.option("--type", "-t", "file_type",
              type=click.Choice(["file", "zip", "dir"]),
              default="file", help="Import type")
@click.option("--target-lang", "-l", multiple=True, help="Target language code(s)")
@click.option("--preserve-structure/--no-preserve-structure", "-P", default=True,
              help="Preserve directory structure (for zip/dir)")
@click.option("--filter-system/--no-filter-system", default=True,
              help="Filter system files")
@click.pass_context
def file_upload(ctx, project_guid, path, file_type, target_lang, preserve_structure, filter_system):
    """Upload files to a project"""
    fm = FileManager()
    target_languages = list(target_lang) if target_lang else None

    click.echo(f"\nUpload Task")
    click.echo(f"   Path:    {path}")
    click.echo(f"   Type:    {file_type}")
    click.echo(f"   Project: {project_guid}")

    if target_languages:
        click.echo(f"   Targets: {', '.join(target_languages)}")
    click.echo()

    try:
        if file_type == "file":
            click.echo("Uploading file...")
            result = fm.upload_file(path, project_guid, target_languages)
        elif file_type == "zip":
            click.echo("Uploading ZIP...")
            result = fm.upload_zip(
                path, project_guid,
                preserve_structure=preserve_structure,
                target_languages=target_languages
            )
        elif file_type == "dir":
            click.echo("Packaging and uploading directory...")
            result = fm.upload_directory(
                path, project_guid,
                target_languages=target_languages,
                filter_system_files=filter_system
            )

        click.echo("\nDone: Upload successful!")

        if ctx.obj.get("verbose"):
            click.echo("\nDetails:")
            output_json(result)

    except FileNotFoundError as e:
        click.echo(f"\nError: File not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@file.command("download")
@click.argument("project_guid")
@click.option("--doc", "-d", "document_guid", help="Document GUID (omit for all)")
@click.option("--output", "-o", type=click.Path(), help="Output path")
@click.option("--format", "-f", "export_format",
              type=click.Choice(["target", "xliff"]),
              default="target", help="Export format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
@click.pass_context
def file_download(ctx, project_guid, document_guid, output, export_format, overwrite):
    """Download files from a project"""
    cfg = ctx.obj.get("config")
    fm = FileManager()

    if not output:
        output = getattr(cfg, 'export_path', './exports')

    click.echo(f"\nDownload Task")
    click.echo(f"   Project: {project_guid}")
    click.echo(f"   Format:  {export_format}")
    click.echo(f"   Output:  {output}")
    click.echo(f"   Document: {document_guid or 'All'}")
    click.echo()

    try:
        if document_guid:
            output_path = Path(output)

            if output_path.suffix == '':
                output_path.mkdir(parents=True, exist_ok=True)
                ext = ".xliff" if export_format == "xliff" else ".out"
                output_path = output_path / f"document{ext}"

            if output_path.exists() and not overwrite:
                if not click.confirm(f"File {output_path} exists. Overwrite?"):
                    click.echo("Cancelled")
                    return

            click.echo("Downloading...")
            result = fm.download_document(
                project_guid, document_guid, str(output_path), export_format
            )
            click.echo(f"\nDone: Downloaded to {result}")
        else:
            output_path = Path(output)
            output_path.mkdir(parents=True, exist_ok=True)

            click.echo("Downloading all documents...")
            results = fm.download_all_documents(
                project_guid, str(output_path), export_format
            )

            click.echo(f"\nDone: Downloaded {len(results)} file(s) to {output_path}")

            if ctx.obj.get("verbose"):
                click.echo("\nFiles:")
                for r in results:
                    click.echo(f"   - {r}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@file.command("import-xliff")
@click.argument("project_guid")
@click.argument("document_guid")
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="XLIFF file path")
@click.option("--confirm-level", "-c",
              type=click.Choice(["None", "Confirmed", "Reviewed", "Proofread"]),
              default="Confirmed", help="Confirmation level")
@click.pass_context
def file_import_xliff(ctx, project_guid, document_guid, path, confirm_level):
    """Import XLIFF to update a document"""
    fm = FileManager()

    click.echo(f"\nImport XLIFF")
    click.echo(f"   File:    {path}")
    click.echo(f"   Project: {project_guid}")
    click.echo(f"   Document: {document_guid}")
    click.echo(f"   Level:   {confirm_level}")
    click.echo()

    try:
        click.echo("Importing...")
        result = fm.import_xliff(path, project_guid, document_guid)
        click.echo("\nDone: XLIFF import successful!")

        if ctx.obj.get("verbose"):
            click.echo("\nDetails:")
            output_json(result)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
