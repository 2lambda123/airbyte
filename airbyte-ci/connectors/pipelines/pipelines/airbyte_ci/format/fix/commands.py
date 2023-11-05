# Copyright (c) 2023 Airbyte, Inc., all rights reserved.

from typing import Optional

import asyncclick as click
import dagger
from pipelines.cli.click_decorators import click_ignore_unused_kwargs, click_merge_args_into_context_obj
from pipelines.cli.lazy_group import LazyGroup
from pipelines.models.contexts.click_pipeline_context import ClickPipelineContext, pass_pipeline_context


@click.group(
    cls=LazyGroup,
    help="Run code format checks and fix any failures.",
    lazy_subcommands={
        "java": "pipelines.airbyte_ci.format.fix.java.commands.java",
        "js": "pipelines.airbyte_ci.format.fix.js.commands.js",
        "license": "pipelines.airbyte_ci.format.fix.license.commands.license",
        "python": "pipelines.airbyte_ci.format.fix.python.commands.python",
    },
    invoke_without_command=True,
    chain=True,
)
@click_merge_args_into_context_obj
@pass_pipeline_context
@click_ignore_unused_kwargs
async def fix(ctx: click.Context, pipeline_ctx: ClickPipelineContext):
    """Run code format checks and fix any failures."""
    # TODO: fix this client hacking
    ctx.obj["dagger_client"] = await pipeline_ctx.get_dagger_client(pipeline_name="Format License")

    if ctx.invoked_subcommand is None:
        print("Running all formatters...")
        await ctx.invoke(fix.get_command(ctx, "java"))
        await ctx.invoke(fix.get_command(ctx, "js"))
        await ctx.invoke(fix.get_command(ctx, "license"))
        await ctx.invoke(fix.get_command(ctx, "python"))
