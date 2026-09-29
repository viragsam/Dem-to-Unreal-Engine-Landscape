# UEDEMTOLC - GLTF to UE Landscape Converter

converts lunar DEM GLTF meshes to unreal engine landscape heightmaps. takes a mesh with like 7 million vertices and turns it into a 16-bit grayscale image UE can read.

## What This Does

takes photogrammetry meshes (or any GLTF really) and converts them to heightmaps. useful for getting lunar terrain or whatever into unreal without it being laggy garbage.

input: GLTF file + .bin file
output: .raw heightmap + .png preview so you can see what it looks like + .json with the numbers

## Getting Started

need python 3.10 or newer and `uv`. if you don't have uv, get it here: https://docs.astral.sh/uv/

```bash
git clone https://github.com/viragsam/uedemtolc.git
cd uedemtolc

uv sync

# optional: activate the venv if you want to mess with it directly. You can use

uv venv

or:
source .venv/bin/activate  # linux/mac
# or
.\.venv\Scripts\activate  # windows
```

## Using It

```bash
uv run uedemtolc path/to/LunarSouthPoleBlend.gltf
```

spits out:
- `LunarSouthPoleBlend.raw` (the actual heightmap)
- `LunarSouthPoleBlend.png` (so you can see it)
- `LunarSouthPoleBlend.json` (numbers and stuff)

with options:

```bash
uv run uedemtolc LunarSouthPoleBlend.gltf \
  -o southpole \
  -r 4096 \
  -q
```

options:
- `-o` or `--output` - where to save it. defaults to same name as input
- `-r` or `--resolution` - size of the heightmap. power of 2 preferred (4096 is good). range is 256 to 16384
- `-q` or `--quiet` - don't print all the progress stuff

examples:

```bash
# basic
uv run uedemtolc Soutpole/LunarSouthPoleBlend.gltf -o outputs/southpole

# bigger resolution for more detail
uv run uedemtolc Apollo15_new/Apollo_keguyaBlend.gltf -o outputs/apollo15 -r 8192

# batch if you have a bunch
for gltf in *.gltf; do
  uv run uedemtolc "$gltf" -o outputs/"${gltf%.gltf}"
done
```

## What You Get

`.raw` file is 16-bit unsigned integers in little-endian format. no header or anything, just raw bytes. UE reads this directly as a heightmap.

`.png` is just so you can actually see what it looks like before you import it into UE.

`.json` has all the metadata like resolution, height range in meters, xy extent, etc. useful for reference.

example metadata:
```json
{
  "resolution": 4096,
  "z_min_meters": -5147.91,
  "z_max_meters": 1876.39,
  "z_range_meters": 7024.30,
  "xy_extent": {
    "x_min": -59956.46,
    "x_max": 60002.93,
    "y_min": -60042.09,
    "y_max": 60002.58
  }
}
```

## Importing into UE

new landscape actor, place it in your level. then go to details and import the .raw file. set the resolution to match what you generated (like 4096x4096). add some materials if you want it to look less gray. enable nanite for performance.

adjust z-scale depending on your game world. like 100 is reasonable if you want 1 UE unit per meter.

## How It Works

basically does this:

1. loads the gltf json and the separate .bin file
2. pulls out all the vertex positions from every mesh
3. maps those vertices to a 2d grid
4. averages overlapping vertices and fills holes
5. scales the height values to 16-bit range (0-65535)
6. saves as raw binary

the trickier part is stitching together the 68 different mesh tiles into one coherent heightmap. fills in any gaps with nearest neighbor interpolation.

uses 16-bit because unreal does, and it's efficient enough for good detail without using tons of memory.

## Performance

south pole (68 meshes, ~6.4M vertices) takes like 30-60 seconds.
apollo 15 is bigger so more like 2-5 minutes.
uses like 2-3 GB of ram during conversion depending on resolution.

## Troubleshooting

### "Binary file not found"
the .bin file needs to be right next to the .gltf file. same directory.

### Looks weird
check the z-axis orientation. might need to flip it in UE. heightmap might be inverted depending on how your mesh was built.

### Import fails
make sure resolution is power of 2. check that .raw file size is resolution squared times 2 (like 4096 * 4096 * 2 = 33554432 bytes). try re-importing.

### Out of memory
lower the resolution with `-r 2048`. or get more ram. or close stuff.

## Code Structure

```
src/uedemtolc/
├── converter.py   - the actual conversion
├── cli.py         - command line interface
└── __init__.py
```

## References

- UE Landscape docs: https://docs.unrealengine.com/en-US/BuildingWorlds/Landscape/
- glTF spec: https://www.khronos.org/gltf/
- general gltf stuff: https://github.com/KhronosGroup/glTF

## MIT License

do whatever you want with it

---

sam (viragsam@gmail.com)
