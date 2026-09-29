"""Command-line interface for GLTF to UE Landscape conversion."""

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
    help="Output prefix for heightmap files (default: same as input)",
)
@click.option(
    "-r",
    "--resolution",
    type=int,
    default=4096,
    help="Heightmap resolution (power of 2, default: 4096)",
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress verbose output")
def main(gltf_file: str, output: str, resolution: int, quiet: bool):
    """
    Convert lunar DEM GLTF meshes to Unreal Engine Landscape heightmaps.

    GLTF_FILE: Path to GLTF file (+ accompanying .bin file must exist)

    Example:
        uedemtolc LunarSouthPoleBlend.gltf -o southpole_heightmap -r 4096
    """
    try:
        gltf_path = Path(gltf_file)
        bin_path = gltf_path.with_suffix(".bin")

        if not bin_path.exists():
            click.echo(f"Error: Binary file not found: {bin_path}", err=True)
            raise click.Exit(1)

        # Set output path
        if output is None:
            output = str(gltf_path.stem)

        # Validate resolution
        if resolution < 256 or resolution > 16384:
            click.echo("Error: Resolution must be between 256 and 16384", err=True)
            raise click.Exit(1)

        # Check power of 2
        if (resolution & (resolution - 1)) != 0:
            click.echo(f"Warning: {resolution} is not a power of 2. UE works best with power-of-2 resolutions.", err=True)

        # Run conversion
        converter = GLTFHeightmapConverter(str(gltf_path), verbose=not quiet)
        raw_file, png_file = converter.convert(output, resolution=resolution)

        click.echo(f"\n✓ Conversion complete!")
        click.echo(f"  RAW: {raw_file}")
        click.echo(f"  PNG: {png_file}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Open your UE project")
        click.echo(f"  2. Create a new Landscape actor")
        click.echo(f"  3. Import heightmap: {raw_file.name}")
        click.echo(f"  4. Set material layers and enable Nanite")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


if __name__ == "__main__":
    main()
