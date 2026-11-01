"""Minimal pure-Python reader for Keynote .iwa files (no third-party deps)."""
import os, struct, sys, glob, collections


def snappy_raw(buf):
    pos = 0
    shift = 0
    n = 0
    while True:
        b = buf[pos]; pos += 1
        n |= (b & 0x7f) << shift
        if not b & 0x80:
            break
        shift += 7
    out = bytearray()
    L = len(buf)
    while pos < L:
        tag = buf[pos]; pos += 1
        t = tag & 3
        if t == 0:
            ln = tag >> 2
            if ln >= 60:
                k = ln - 59
                ln = int.from_bytes(buf[pos:pos + k], 'little'); pos += k
            ln += 1
            out += buf[pos:pos + ln]; pos += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 7) + 4
                off = ((tag >> 5) << 8) | buf[pos]; pos += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(buf[pos:pos + 2], 'little'); pos += 2
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(buf[pos:pos + 4], 'little'); pos += 4
            for _ in range(ln):
                out.append(out[-off])
    return bytes(out)


def iwa_stream(path):
    d = open(path, 'rb').read()
    pos = 0
    out = bytearray()
    while pos < len(d):
        hdr = d[pos]
        ln = int.from_bytes(d[pos + 1:pos + 4], 'little')
        pos += 4
        if hdr != 0:
            raise ValueError('bad chunk')
        out += snappy_raw(d[pos:pos + ln])
        pos += ln
    return bytes(out)


def varint(b, p):
    r = s = 0
    while True:
        c = b[p]; p += 1
        r |= (c & 0x7f) << s
        if not c & 0x80:
            return r, p
        s += 7


def pb(b):
    """Decode a protobuf message into {field: [values]}; values are int/bytes/float32/float64 tagged."""
    f = collections.defaultdict(list)
    p = 0
    n = len(b)
    while p < n:
        k, p = varint(b, p)
        fn, wt = k >> 3, k & 7
        if fn == 0:
            raise ValueError('field 0')
        if wt == 0:
            v, p = varint(b, p)
        elif wt == 1:
            v = ('d', struct.unpack('<d', b[p:p + 8])[0]); p += 8
        elif wt == 2:
            l, p = varint(b, p)
            if p + l > n:
                raise ValueError('overrun')
            v = b[p:p + l]; p += l
        elif wt == 5:
            v = ('f', struct.unpack('<f', b[p:p + 4])[0]); p += 4
        else:
            raise ValueError('wt')
        f[fn].append(v)
    return f


def sub(v):
    try:
        return pb(v)
    except Exception:
        return None


def archives(path):
    """Yield (id, type, payload, object_refs) for every message in an .iwa."""
    s = iwa_stream(path)
    p = 0
    while p < len(s):
        l, p = varint(s, p)
        info = pb(s[p:p + l]); p += l
        aid = info[1][0]
        for mi in info.get(2, []):
            m = pb(mi)
            typ = m[1][0]
            ln = m[3][0]
            refs = m.get(5, [])
            # object_references may be packed
            orefs = []
            for r in refs:
                if isinstance(r, (bytes, bytearray)):
                    q = 0
                    while q < len(r):
                        x, q = varint(r, q); orefs.append(x)
                else:
                    orefs.append(r)
            yield aid, typ, s[p:p + ln], orefs
            p += ln


def load(root):
    objs = {}
    src = {}
    for fp in sorted(glob.glob(os.path.join(root, 'Index', '*.iwa'))):
        for aid, typ, pl, refs in archives(fp):
            objs[aid] = (typ, pl, refs)
            src[aid] = os.path.basename(fp)
    return objs, src


if __name__ == '__main__':
    objs, src = load(sys.argv[1])
    c = collections.Counter(t for t, _, _ in objs.values())
    print(len(objs), 'objects')
    for t, n in c.most_common(45):
        print(t, n)
