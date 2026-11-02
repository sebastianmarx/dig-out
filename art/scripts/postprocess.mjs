// Turns raw Blender renders (art/renders/*.png) into web assets according to art/manifest.yaml:
// WebP in @1x/@2x/@3x per group, PNG app icons, and a size-budget check.
//
// Usage (from art/):  npm run postprocess

import { copyFile, mkdir, readdir, readFile, rm, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import YAML from "yaml";
import { writeIcons } from "./icons.mjs";

const artDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const rendersDir = path.join(artDir, "renders");
const manifest = YAML.parse(await readFile(path.join(artDir, "manifest.yaml"), "utf8"));
const outDir = path.resolve(artDir, manifest.output);

await rm(outDir, { recursive: true, force: true });
const groups = manifest.groups.map((g) => ({ ...g, regex: new RegExp(g.pattern) }));
const written = [];

for (const file of (await readdir(rendersDir)).sort()) {
  const group = groups.find((g) => g.regex.test(file));
  if (!group) continue;
  const src = path.join(rendersDir, file);
  const { width: srcWidth } = await sharp(src).metadata();
  const id = file.replace(/\.png$/, "");
  await mkdir(path.join(outDir, group.dir), { recursive: true });
  for (const scale of [1, 2, 3]) {
    const width = group.width * scale;
    if (width > srcWidth) break; // never upscale
    const dest = path.join(outDir, group.dir, `${id}@${scale}x.webp`);
    await sharp(src).resize({ width }).webp({ quality: manifest.quality, alphaQuality: 90 }).toFile(dest);
    written.push(dest);
  }
}

for (const { from, to } of manifest.copy ?? []) {
  const dest = path.join(outDir, to);
  await mkdir(path.dirname(dest), { recursive: true });
  await copyFile(path.join(rendersDir, from), dest);
  written.push(dest);
}

written.push(...await writeIcons(artDir, outDir, manifest.icons));

let total = 0;
for (const file of written) total += (await stat(file)).size;
const totalKb = Math.round(total / 1024);
console.log(`${written.length} files, ${totalKb} KB (budget ${manifest.budget_kb} KB) -> ${outDir}`);
if (totalKb > manifest.budget_kb) {
  console.error("Asset budget exceeded");
  process.exit(1);
}
