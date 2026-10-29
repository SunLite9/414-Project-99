"""Resumable extraction of the order-book archive pieces (_obtar/obNN.tar) into data/raw/orderbook using a byte index."""
import json, os, sys, time
RAW = sys.argv[1]; budget = float(sys.argv[2]) if len(sys.argv) > 2 else 150; t0 = time.time()
ix = json.load(open(os.path.join(RAW, '_obtar', 'ob_index.json'))); P = ix['piece_size']
def read(off, n):
    out = bytearray()
    while n:
        k, r = divmod(off, P)
        with open(os.path.join(RAW, '_obtar', f'ob{k:02d}.tar'), 'rb') as f:
            f.seek(r); b = f.read(min(n, P - r))
        out += b; off += len(b); n -= len(b)
    return bytes(out)
done = wrote = 0
for name, off, size in ix['files']:
    p = os.path.join(RAW, name)
    if os.path.exists(p) and os.path.getsize(p) == size: done += 1; continue
    if time.time() - t0 > budget: break
    b = read(off, size); open(p, 'wb').write(b); wrote += 1; done += 1
print(f'complete {done}/{len(ix["files"])}  written this run {wrote}  {time.time()-t0:.0f}s')
