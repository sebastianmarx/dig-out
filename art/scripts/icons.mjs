// Shared by the standalone icon build and the complete art postprocessor.
import { copyFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

export async function writeIcons(artDir, outDir, icons) {
  const source = path.resolve(artDir, icons.source);
  const publicDir = path.dirname(outDir);
  const iconDir = path.join(outDir, "icons");
  await mkdir(iconDir, { recursive: true });
  const written = [];
  for (const size of icons.sizes) {
    const dest = path.join(iconDir, `icon-${size}.png`);
    await sharp(source, { density: 384 }).resize(size, size).png({ compressionLevel: 9 }).toFile(dest);
    written.push(dest);
  }
  const svg = path.join(publicDir, "icon.svg");
  await copyFile(source, svg);
  written.push(svg);

  // ICO supports PNG entries; include native sizes for older browsers/bookmarks.
  const sizes = [16, 32, 48];
  const images = await Promise.all(sizes.map((size) => sharp(source, { density: 384 }).resize(size, size).png().toBuffer()));
  const header = Buffer.alloc(6 + sizes.length * 16);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(sizes.length, 4);
  let offset = header.length;
  images.forEach((png, i) => {
    const entry = 6 + i * 16;
    header[entry] = sizes[i];
    header[entry + 1] = sizes[i];
    header.writeUInt16LE(1, entry + 4);
    header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(png.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += png.length;
  });
  const ico = path.join(publicDir, "favicon.ico");
  await writeFile(ico, Buffer.concat([header, ...images]));
  written.push(ico);
  return written;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { readFile } = await import("node:fs/promises");
  const { default: YAML } = await import("yaml");
  const artDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const manifest = YAML.parse(await readFile(path.join(artDir, "manifest.yaml"), "utf8"));
  const files = await writeIcons(artDir, path.resolve(artDir, manifest.output), manifest.icons);
  console.log(`Generated ${files.length} icon assets.`);
}
