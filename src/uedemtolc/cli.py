"""cli for converting gltf to ue heightmap. just wraps the converter."""

import click
from pathlib import Path
from .converter import GLTFHeightmapConverter


@click.command()
@click.argument("gltf_file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=None,
    help="where to save the heightmap (default: same name as input)",
)
@click.option(
    "-r",
    "--resolution",
    type=int,
    default=4096,
    help="heightmap size, needs to be power of 2 (default 4096)",
)
@click.option("-q", "--quiet", is_flag=True, help="shut up about progress")
def main(gltf_file: str, output: str, resolution: int, quiet: bool):
    """converts gltf meshes to unreal engine landscape heightmaps.

    needs the .bin file in the same folder as the gltf.

    example:
        uedemtolc LunarSouthPoleBlend.gltf -o southpole -r 4096
    """
    try:
        gltf_path = Path(gltf_file)
        bin_path = gltf_path.with_suffix(".bin")

        if not bin_path.exists():
            click.echo(f"Error: can't find the .bin file: {bin_path}", err=True)
            raise click.Exit(1)

        if output is None:
            output = str(gltf_path.stem)

        if resolution < 256 or resolution > 16384:
            click.echo("Error: resolution has to be between 256 and 16384", err=True)
            raise click.Exit(1)

        if (resolution & (resolution - 1)) != 0:
            click.echo(f"Warning: {resolution} isn't a power of 2. UE likes power of 2.", err=True)

        converter = GLTFHeightmapConverter(str(gltf_path), verbose=not quiet)
        raw_file, png_file = converter.convert(output, resolution=resolution)

        click.echo(f"\n✓ done!")
        click.echo(f"  raw: {raw_file}")
        click.echo(f"  png: {png_file}")
        click.echo(f"\nwhat to do now:")
        click.echo(f"  1. open ue")
        click.echo(f"  2. make a landscape actor")
        click.echo(f"  3. import the .raw file")
        click.echo(f"  4. add materials and enable nanite")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


if __name__ == "__main__":
    main()
