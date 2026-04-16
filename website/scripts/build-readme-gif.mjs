import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import GIFEncoder from 'gif-encoder-2';

const root = path.resolve(process.cwd(), '..');
const srcDir = path.join(root, 'data', 'img');
const outDir = path.join(root, 'docs', 'assets', 'readme');
const outFile = path.join(outDir, 'secom-dashboard-tour.gif');

const frames = [
  'Screenshot_1.png',
  'Screenshot_2.png',
  'Screenshot_3.png',
  'Screenshot_4.png',
];

const width = 1200;
const height = 840;
const delay = 1200; // ms

function readPng(file) {
  const data = fs.readFileSync(file);
  const png = PNG.sync.read(data);
  if (png.width !== width || png.height !== height) {
    console.error(`Unexpected size for ${file}: ${png.width}x${png.height}, expected ${width}x${height}`);
    process.exit(1);
  }
  return png.data;
}

const encoder = new GIFEncoder(width, height, 'neuquant', true);
encoder.setDelay(delay);
encoder.start();

for (const frame of frames) {
  const filePath = path.join(srcDir, frame);
  console.log(`Adding frame: ${filePath}`);
  const pixels = readPng(filePath);
  encoder.addFrame(pixels);
}

encoder.finish();

const buffer = encoder.out.getData();
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outFile, buffer);
console.log(`GIF written to ${outFile}`);
