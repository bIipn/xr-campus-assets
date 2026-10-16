// Usage: node minify.mjs js <in> <out> | node minify.mjs css <in> <out>
import { readFileSync, writeFileSync } from 'node:fs';
import { minify } from 'terser';
import CleanCSS from 'clean-css';

const [kind, inp, out] = process.argv.slice(2);
const src = readFileSync(inp, 'utf8');

if (kind === 'js') {
  const r = await minify(src, {
    module: true,
    ecma: 2020,
    compress: { passes: 2, drop_console: false, pure_getters: false, unsafe: false },
    mangle: true,
    format: { comments: false, ascii_only: false, wrap_func_args: false }
  });
  writeFileSync(out, r.code);
  console.log('js', src.length, '->', r.code.length);
} else if (kind === 'css') {
  const r = new CleanCSS({ level: 1 }).minify(src);
  if (r.errors.length) { console.error(r.errors); process.exit(1); }
  writeFileSync(out, r.styles);
  console.log('css', src.length, '->', r.styles.length, r.warnings.length ? r.warnings : '');
}
