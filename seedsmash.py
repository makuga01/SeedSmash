#!/usr/bin/python3
print('######## SeedSmash 0.2 BETA by makuga01 ########\n')
try:
    import bencodepy, bencoding, hashlib, base64, random, requests, time, sys, os, urllib.parse, codecs
except ImportError:
    raise ImportError('Maybe installing requirements can help, try: pip install -r requirements.txt')

#decodes given hash to hex and urlencodes it
def uencode(udata):
    hexd = codecs.decode(udata, "hex")
    d = {'d':hexd}
    encoded = urllib.parse.urlencode(d)[2:]
    return encoded

#Returns urlencoded info hash from torrent file
def get_info_hash(tfile):
    objTorrentFile = open(tfile, "rb")
    decodedDict = bencoding.bdecode(objTorrentFile.read())
    info_hash = hashlib.sha1(bencoding.bencode(decodedDict[b"info"])).hexdigest()
    enc_hash = uencode(info_hash)
    return enc_hash

#Returns announce and pid in list [announce,pid]
def get_announce(tfile):
    meta = bencodepy.decode_from_file(tfile)
    url = meta[b'announce'].decode()
    ann = url.split('?')[0]
    pid = url.split('=')[1]
    return [ann, pid]

#Returns urlencoded peer_id - id of torrent I'm using utorrent 2.210 (-UT2210- can be changed to whatever you want) 8 chars + 24 random chars (0123456789abcdef)
def get_peer_id():
    chars = list('0123456789abcdef')
    p1 = ''
    for i in range(24):
        p1 += urllib.parse.quote_plus(random.choice(chars))
    peer_id = '-UT2210-'+uencode(p1)
    return peer_id

#Returns key - 8 random characters (0123456789ABCDEF)
def get_key():
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

#main function
def seed():
    if len(sys.argv) < 3:
        print('Usage:\n'+sys.argv[0]+' <time in minutes> <Max up speed in kB/s(max 10 000)>\n')
        exit(0)

    seed_time = int(sys.argv[1])*60 #Time in seconds
    print('seeding for',seed_time, 'seconds')

    upspeed = int(sys.argv[2])

    #list torrent files in current dir and select first one (temporary)
    tofiles=get_files()
    file=tofiles[0]
    print('choosing file',file)

    #Get announce and pid
    ann = get_announce(file)[0]
    pid = get_announce(file)[1]

    #peer id and port stays constant on every torrent
    peer_id = get_peer_id()
    port = random.randint(10000, 65536)

    hash = get_info_hash(file)
    key = get_key()

    #Set user agent to utorrent 2.210
    header={'user-agent':'uTorrent/2210(25534)'}

    #craft start url from given info
    start = ann+'?pid='+pid+'&info_hash='+hash+'&peer_id='+peer_id+'&port='+str(port)+'&uploaded=0&downloaded=0&left=0&corrupt=0&key='+key+'&event=started&numwant=200&compact=1&no_peer_id=1'

    #send request
    r = requests.get(start, headers=header)
    print('\nResponse from announce:')
    print(r.text, '\n')
    start = time.time()
    #generate random upload in range 0.8-1x of given up speed
    randup = round(random.uniform(0.8,1)*seed_time*upspeed*1000)

    #Craft stop url
    stop = ann+'?pid='+pid+'&info_hash='+hash+'&peer_id='+peer_id+'&port='+str(port)+'&uploaded='+str(randup)+'&downloaded=0&left=0&corrupt=0&key='+key+'&event=stopped&numwant=0&compact=1&no_peer_id=1'

    #sleep for given period of time and send request, when ctrl-c is pressed - end seeding
    try:
        print('seeding, press ctrl-c to stop')
        time.sleep(seed_time)
    except KeyboardInterrupt:
        print('\nShutting down SeedSmash')
        #calculate elapsed time from start of seeding
        elapsed_time = time.time()-start

        #adjust upload from default time to elapsed
        randup = randup * (elapsed_time / seed_time)

        #craft another stop url with changed upload
        stop = ann+'?pid='+pid+'&info_hash='+hash+'&peer_id='+peer_id+'&port='+str(port)+'&uploaded='+str(randup)+'&downloaded=0&left=0&corrupt=0&key='+key+'&event=stopped&numwant=0&compact=1&no_peer_id=1'

        #Send request
        r = requests.get(stop, headers=header)

        #print elapsed time + response from stop request + how much data was "uploaded"
        print('Response from announce:')
        print(r.text,'\n')
        print('\nUploaded', round(randup/1000), 'kB in', round(elapsed_time),'seconds')
        exit(0)
    #send stop request
    print('sending stop request, don\'t ctrl-c me now pls')
    r = requests.get(stop, headers=header)
    elapsed_time = time.time()-start
    #print elapsed time + response from stop request + how much data was "uploaded"
    print('Response from announce:')
    print(r.text,'\n')
    print('\nUploaded', round(randup/1000), 'kB in', round(elapsed_time),'seconds')

seed()
