# UEDEMTOLC — GLTF to UE Landscape Heightmap Converter

Convert lunar DEM GLTF mesh files to Unreal Engine Landscape heightmaps (16-bit RAW format).

## Purpose

Converts complex mesh tiles (like lunar south pole DEMs from photogrammetry/3D modeling) into UE Landscape-compatible heightmaps for terrain visualization in Unreal Engine.

**Input:** GLTF mesh file(s) + binary data
**Output:** 16-bit RAW heightmap + PNG preview + metadata

## Setup

### Prerequisites
- Python 3.10+
- `uv` package manager ([install here](https://docs.astral.sh/uv/getting-started/installation/))

### Installation

```bash
# Clone and enter directory
git clone https://github.com/viragsam/uedemtolc.git
cd uedemtolc

# Create virtual environment and install dependencies
uv sync

# (Optional) Activate venv for manual testing
source .venv/bin/activate  # macOS/Linux
# or
.\.venv\Scripts\activate  # Windows
```

## Usage

### Basic

```bash
uv run uedemtolc path/to/LunarSouthPoleBlend.gltf
```

This creates:
- `LunarSouthPoleBlend.raw` (16-bit heightmap)
- `LunarSouthPoleBlend.png` (preview image)
- `LunarSouthPoleBlend.json` (metadata)

### With Options

```bash
uv run uedemtolc LunarSouthPoleBlend.gltf \
  -o southpole_heightmap \
  -r 4096 \
  -q
```

**Options:**
- `-o, --output PREFIX` — Output file prefix (default: input filename)
- `-r, --resolution RES` — Heightmap resolution, power of 2 (default: 4096, range: 256-16384)
- `-q, --quiet` — Suppress verbose output

### Examples

```bash
# Convert south pole DEM to 4096x4096
uv run uedemtolc Soutpole/LunarSouthPoleBlend.gltf -o outputs/southpole

# Convert Apollo 15 DEM to 8192x8192 (high detail)
uv run uedemtolc Apollo15_new/Apollo_keguyaBlend.gltf -o outputs/apollo15 -r 8192

# Batch convert (shell)
for gltf in *.gltf; do
  uv run uedemtolc "$gltf" -o outputs/"${gltf%.gltf}"
done
```

## Output Files

### `.raw` — Heightmap Data
- **Format:** 16-bit unsigned integer, little-endian, no header
- **Size:** `resolution × resolution × 2 bytes`
- **Example:** 4096×4096 = 33.55 MB
- **Import into UE:** Landscape → Import → select `.raw` file

### `.png` — Preview
- 8-bit grayscale visualization of the heightmap
- For quick visual verification before UE import

### `.json` — Metadata
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

## Unreal Engine Import

1. **Create a new Landscape actor:**
   - In editor: Place Actor → Landscape
   - Set desired XY size (match your heightmap extent)

2. **Import heightmap:**
   - Landscape Details → Import
   - Select your `.raw` file
   - Set resolution to match (e.g., 4096×4096)

3. **Configure material:**
   - Add landscape material layers (rock, shadow, etc.)
   - Apply Nanite for GPU-optimized rendering

4. **Adjust height scale:**
   - Z-scale in landscape properties
   - Recommended: 100 cm per meter (scale: 100)
   - Adjust based on your desired play scale

## Technical Details

### Conversion Pipeline

1. **Extract GLTF positions**
   - Parse GLTF JSON + binary buffer
   - Extract all mesh vertex positions (X, Y, Z)

2. **Create heightmap grid**
   - Map vertices to 2D grid (e.g., 4096×4096)
   - Average overlapping vertices
   - Interpolate holes with nearest-neighbor

3. **Normalize heights**
   - Scale Z values from raw meters to 16-bit range (0–65535)
   - Preserves relative elevation differences

4. **Export**
   - Save as binary RAW file
   - Generate PNG preview
   - Output metadata JSON

### Why 16-bit?

UE Landscapes use 16-bit heightmaps for:
- 0–65535 precision levels
- Good memory efficiency (~2 bytes per height value)
- Industry standard for game terrain

## Performance

**Typical conversion times (on modern hardware):**
- South Pole (68 meshes, ~6.4M vertices): ~30–60 seconds
- Apollo 15 (larger dataset): ~2–5 minutes

**Memory usage:** ~2–3 GB for largest datasets

## Troubleshooting

### "Binary file not found"
Ensure the `.bin` file is in the same directory as the `.gltf`:
```
Soutpole/
├── LunarSouthPoleBlend.gltf
└── LunarSouthPoleBlend.bin  ← Must exist
```

### Heightmap looks inverted/distorted
- Check Z-axis orientation in UE landscape properties
- Try flipping the heightmap if needed

### Import fails in UE
- Verify resolution is power of 2 (256, 512, 1024, 2048, 4096, 8192, etc.)
- Check `.raw` file size matches `resolution² × 2`
- Re-import heightmap in UE Landscape actor properties

### Out of memory during conversion
- Reduce resolution: `-r 2048` instead of 4096
- Process on a machine with more RAM
- Close other memory-heavy applications

## Project Structure

```
uedemtolc/
├── src/uedemtolc/
│   ├── __init__.py          # Package init
│   ├── converter.py         # Core conversion logic
│   └── cli.py               # Command-line interface
├── pyproject.toml           # uv/pip configuration
├── README.md                # This file
└── .gitignore
```

## Development

### Running tests (planned)
```bash
uv run pytest
```

### Manual testing
```bash
uv run python -c "from uedemtolc.converter import GLTFHeightmapConverter; ..."
```

### Adding features
1. Fork and create feature branch
2. Update `src/uedemtolc/` modules
3. Test with sample GLTF files
4. Submit PR

## License

MIT (update if needed)

## References

- [Unreal Engine Landscape](https://docs.unrealengine.com/en-US/BuildingWorlds/Landscape/)
- [glTF 2.0 Specification](https://www.khronos.org/gltf/)
- [GLTF Python Libraries](https://github.com/KhronosGroup/glTF)

## Author

Sam (viragsam@gmail.com)

---

**Questions?** Check the examples or open an issue on GitHub.
