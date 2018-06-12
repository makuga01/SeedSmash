import bencodepy, bencoding, hashlib, base64, random, requests, time, sys, os, urllib.parse, codecs

#urlencode to some weird torrent request form
def uencode(udata):
    print('uencode')
    hexd = codecs.decode(udata, "hex")
    d = {'d':hexd}
    encoded = urllib.parse.urlencode(d)[2:]
    print(encoded)
    return encoded

#Returns info hash from torrent file, code from DanySK's torrent2magnet https://github.com/DanySK/torrent2magnet/blob/develop/torrent2magnet.py
def get_info_hash(tfile):
    objTorrentFile = open(tfile, "rb")
    decodedDict = bencoding.bdecode(objTorrentFile.read())
    info_hash = hashlib.sha1(bencoding.bencode(decodedDict[b"info"])).hexdigest()
    enc_hash = uencode(info_hash)
    print(enc_hash)
    return enc_hash

#Returns announce and pid in list [announce,pid]
def get_announce(tfile):
    print('get announce')
    meta = bencodepy.decode_from_file(tfile)
    url = meta[b'announce'].decode()
    ann = url.split('?')[0]
    pid = url.split('=')[1]
    return [ann, pid]

#Returns peer_id - id of torrent client in this case (-UT2210-) + 24 random characters (0123456789abcdef)
def get_peer_id():
    print('get peer id')
    chars = list('0123456789abcdef')
    p1 = ''
    for i in range(24):
        p1 += urllib.parse.quote_plus(random.choice(chars))
    peer_id = '-UT2210-'+uencode(p1)
    print(peer_id)
    return peer_id

#Returns key - 8 random characters (0123456789ABCDEF)
def get_key():
    print('get_key')
    key = ''
    chars = list('0123456789ABCDEF')
    for i in range(8):
        key += urllib.parse.quote_plus(random.choice(chars))
    return key

#Returns list of torrent files in current directory
def get_files():
    torrlist = []
    for file in os.listdir():
        if file.endswith('.torrent'):
            torrlist.append(file)
    return torrlist

def seed():
    header={'user-agent':'uTorrent/2210(25534)'}
    #time = sys.argv[1]*60 #Time in seconds
    #upspeed = sys.argv[2]

    tofiles=get_files()
    if len(tofiles) > 20:
        print('Max 20 torrent files!\nSelecting first 20')
        tofiles = tofiles[:20]
    file=tofiles[0]
    print('choosing file',file)

    ann = get_announce(file)[0]
    pid = get_announce(file)[1]

    #peer id and port stays constant
    peer_id = get_peer_id()
    port = random.randint(10000, 65536)
    hash = get_info_hash(file)
    key = get_key()

    start = ann+'?pid='+pid+'&info_hash='+hash+'&peer_id='+peer_id+'&port='+str(port)+'&uploaded=0&downloaded=0&left=0&corrupt=0&key='+key+'&event=started&numwant=200&compact=1&no_peer_id=1'
    print(start)
    r = requests.get(start, headers=header)
    print(r.text)
    stop = ann+'?pid='+pid+'&info_hash='+hash+'&peer_id='+peer_id+'&port='+str(port)+'&uploaded=0&downloaded=0&left=0&corrupt=0&key='+key+'&event=stopped&numwant=0&compact=1&no_peer_id=1'
    time.sleep(10)
    r = requests.get(stop, headers=header)
    print(r.text)
    # print(ann+'?'+urllib.parse.urlencode(data))
seed()
