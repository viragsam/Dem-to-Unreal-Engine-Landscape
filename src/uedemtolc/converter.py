"""
GLTF to UE Landscape Heightmap Converter

Converts GLTF mesh files (+ .bin) to 16-bit heightmaps suitable for
Unreal Engine Landscape import.
"""

import struct
import json
import base64
from pathlib import Path
from typing import Tuple
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt


class GLTFHeightmapConverter:
    """Convert GLTF mesh to UE Landscape heightmap."""

    def __init__(self, gltf_path: str, verbose: bool = True):
        self.gltf_path = Path(gltf_path)
        self.bin_path = self.gltf_path.with_suffix(".bin")
        self.verbose = verbose

        if not self.gltf_path.exists():
            raise FileNotFoundError(f"GLTF file not found: {self.gltf_path}")

        # Load GLTF JSON
        with open(self.gltf_path, "r") as f:
            self.gltf = json.load(f)

        # Load binary buffers
        self._load_buffers()

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _load_buffers(self):
        """Load binary buffer data from .bin files."""
        self.buffers = {}
        for buf_idx, buf_info in enumerate(self.gltf.get("buffers", [])):
            uri = buf_info.get("uri", "")
            byte_length = buf_info.get("byteLength", 0)

            if uri.startswith("data:"):
                # Embedded base64 data
                b64_data = uri.split(",")[1]
                self.buffers[buf_idx] = base64.b64decode(b64_data)
                self._log(f"  Buffer {buf_idx}: Embedded ({byte_length:,} bytes)")
            else:
                # External file reference
                bin_file = self.gltf_path.parent / uri
                if not bin_file.exists():
                    raise FileNotFoundError(f"Binary file not found: {bin_file}")

                with open(bin_file, "rb") as f:
                    self.buffers[buf_idx] = f.read()
                self._log(f"  Buffer {buf_idx}: {uri} ({byte_length:,} bytes)")

    def _get_accessor_data(self, accessor_idx: int) -> np.ndarray:
        """Extract vertex data from accessor."""
        accessor = self.gltf["accessors"][accessor_idx]
        buffer_view_idx = accessor.get("bufferView")
        byte_offset = accessor.get("byteOffset", 0)
        count = accessor["count"]
        component_type = accessor["componentType"]
        accessor_type = accessor["type"]

        if buffer_view_idx is None:
            raise ValueError(f"Accessor {accessor_idx} has no bufferView")

        buffer_view = self.gltf["bufferViews"][buffer_view_idx]
        buffer_idx = buffer_view["buffer"]
        buffer_data = self.buffers[buffer_idx]
        view_offset = buffer_view.get("byteOffset", 0)
        stride = buffer_view.get("byteStride", None)

        # Determine format
        if component_type == 5126:  # FLOAT
            fmt = "f"
            size = 4
        elif component_type == 5125:  # UNSIGNED_INT
            fmt = "I"
            size = 4
        else:
            raise ValueError(f"Unsupported componentType: {component_type}")

        # Determine component count
        if accessor_type == "VEC3":
            num_components = 3
        elif accessor_type == "SCALAR":
            num_components = 1
        else:
            raise ValueError(f"Unsupported accessor type: {accessor_type}")

        if stride is None:
            stride = size * num_components

        # Extract data
        data = []
        for i in range(count):
            pos_offset = view_offset + byte_offset + i * stride
            vertex = []
            for j in range(num_components):
                byte_idx = pos_offset + j * size
                val = struct.unpack(f"<{fmt}", buffer_data[byte_idx : byte_idx + size])[0]
                vertex.append(val)
            data.append(vertex)

        return np.array(data)

    def extract_positions(self) -> Tuple[np.ndarray, dict]:
        """Extract all vertex positions from GLTF meshes."""
        self._log("Extracting vertex positions from GLTF meshes...")

        all_positions = []
        bounds = {"x_min": float("inf"), "x_max": float("-inf"), "y_min": float("inf"), "y_max": float("-inf"), "z_min": float("inf"), "z_max": float("-inf")}

        mesh_count = len(self.gltf.get("meshes", []))
        for mesh_idx, mesh in enumerate(self.gltf.get("meshes", [])):
            for prim in mesh.get("primitives", []):
                if "attributes" in prim and "POSITION" in prim["attributes"]:
                    pos_accessor_idx = prim["attributes"]["POSITION"]
                    positions = self._get_accessor_data(pos_accessor_idx)
                    all_positions.append(positions)

                    # Update bounds
                    if len(positions) > 0:
                        bounds["x_min"] = min(bounds["x_min"], positions[:, 0].min())
                        bounds["x_max"] = max(bounds["x_max"], positions[:, 0].max())
                        bounds["y_min"] = min(bounds["y_min"], positions[:, 1].min())
                        bounds["y_max"] = max(bounds["y_max"], positions[:, 1].max())
                        bounds["z_min"] = min(bounds["z_min"], positions[:, 2].min())
                        bounds["z_max"] = max(bounds["z_max"], positions[:, 2].max())

            if (mesh_idx + 1) % max(1, mesh_count // 10) == 0:
                self._log(f"  Processed {mesh_idx + 1}/{mesh_count} meshes...")

        all_verts = np.vstack(all_positions)
        self._log(f"Total vertices: {len(all_verts):,}")
        self._log(f"  X: {bounds['x_min']:.2f} to {bounds['x_max']:.2f}")
        self._log(f"  Y: {bounds['y_min']:.2f} to {bounds['y_max']:.2f}")
        self._log(f"  Z: {bounds['z_min']:.2f} to {bounds['z_max']:.2f}")

        return all_verts, bounds

    def create_heightmap(self, positions: np.ndarray, bounds: dict, resolution: int = 4096) -> Tuple[np.ndarray, dict]:
        """Create 16-bit heightmap from vertex positions."""
        self._log(f"\nCreating {resolution}x{resolution} heightmap...")

        x_vals = positions[:, 0]
        y_vals = positions[:, 1]
        z_vals = positions[:, 2]

        x_min, x_max = bounds["x_min"], bounds["x_max"]
        y_min, y_max = bounds["y_min"], bounds["y_max"]
        z_min, z_max = bounds["z_min"], bounds["z_max"]

        # Create heightmap grid
        heightmap = np.zeros((resolution, resolution), dtype=np.float32)
        count_map = np.zeros((resolution, resolution), dtype=np.int32)

        # Map vertices to grid
        for i, (x, y, z) in enumerate(positions):
            grid_x = int((x - x_min) / (x_max - x_min) * (resolution - 1)) if x_max > x_min else 0
            grid_y = int((y - y_min) / (y_max - y_min) * (resolution - 1)) if y_max > y_min else 0

            grid_x = np.clip(grid_x, 0, resolution - 1)
            grid_y = np.clip(grid_y, 0, resolution - 1)

            heightmap[grid_y, grid_x] += z
            count_map[grid_y, grid_x] += 1

            if (i + 1) % max(1, len(positions) // 10) == 0:
                self._log(f"  Mapped {i + 1:,} vertices...")

        # Average overlapping pixels
        mask = count_map > 0
        heightmap[mask] /= count_map[mask]

        # Fill holes with nearest neighbor
        holes = count_map == 0
        if holes.any():
            self._log("  Filling holes...")
            indices = distance_transform_edt(holes, return_distances=False, return_indices=True)
            heightmap[holes] = heightmap[tuple(indices[:, holes])]

        # Normalize to 16-bit range
        heightmap_normalized = ((heightmap - z_min) / (z_max - z_min) * 65535).astype(np.uint16)

        metadata = {
            "resolution": resolution,
            "z_min_meters": float(z_min),
            "z_max_meters": float(z_max),
            "z_range_meters": float(z_max - z_min),
            "xy_extent": {
                "x_min": float(x_min),
                "x_max": float(x_max),
                "y_min": float(y_min),
                "y_max": float(y_max),
            },
        }

        self._log(f"  Resolution: {resolution}x{resolution}")
        self._log(f"  Height range: {heightmap_normalized.min()} - {heightmap_normalized.max()}")

        return heightmap_normalized, metadata

    def save_heightmap(self, heightmap: np.ndarray, output_prefix: str):
        """Save heightmap as RAW and PNG."""
        output_path = Path(output_prefix)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save RAW (16-bit little-endian)
        raw_file = output_path.with_suffix(".raw")
        heightmap.astype(np.uint16).tofile(raw_file)
        self._log(f"\n✓ Saved: {raw_file}")
        self._log(f"  Format: 16-bit RAW (little-endian)")
        self._log(f"  Size: {raw_file.stat().st_size / 1024 / 1024:.1f} MB")

        # Save PNG preview
        png_file = output_path.with_suffix(".png")
        img_8bit = (heightmap / 65535 * 255).astype(np.uint8)
        Image.fromarray(img_8bit).save(png_file)
        self._log(f"✓ Saved: {png_file} (preview)")

        return raw_file, png_file

    def convert(self, output_prefix: str, resolution: int = 4096) -> Tuple[Path, Path]:
        """Full conversion pipeline."""
        self._log(f"Converting {self.gltf_path.name}...")
        self._log("=" * 60)

        positions, bounds = self.extract_positions()
        heightmap, metadata = self.create_heightmap(positions, bounds, resolution)
        raw_file, png_file = self.save_heightmap(heightmap, output_prefix)

        # Save metadata
        metadata_file = Path(output_prefix).with_suffix(".json")
        import json
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        self._log(f"✓ Saved: {metadata_file}")

        self._log("=" * 60)
        self._log("Done!\n")

        return raw_file, png_file
