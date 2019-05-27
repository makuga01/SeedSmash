#!/usr/bin/python3
print("######## SeedSmash 0.3 BETA by makuga01 ########\n")
try:
    import bencodepy, bencoding, hashlib, base64, random, requests, time, argparse, os, urllib.parse, codecs, re
except ImportError:
    raise ImportError(
        "Maybe installing requirements can help, try: pip install -r requirements.txt"
    )


def grab(string, start, end):
    """
    shame on me for this, borrowed code from https://github.com/s0md3v/regxy amazing guy, check him out
    this functions grabs string betweed 2 given start and stop and raturns it
    eg. torrent anncounce returns something like this:
    d8:intervali7200e12:min...
    i just need to know when to contact announce again to keep seeding for longer time
    Using it like this grab('d8:intervali7200e12:min...', 'intervali', 'e12')  returns 7200 - time i need
    """
    match = re.search(r"%s[^<]*%s" % (start, end), string)
    if match:
        return match.group().split(start)[1][: -len(end)]
    else:
        return False

def hex2bytes(hex_sring):
    return codecs.decode(hex_sring, "hex")

def uencode(udata):

    """decodes given hash to hex and urlencodes it"""

    hexd = codecs.decode(udata, "hex")
    d = {"d": hexd}
    encoded = urllib.parse.urlencode(d)[2:]
    return encoded


def get_info_hash(tfile):

    """Returns urlencoded info hash from torrent file"""

    objTorrentFile = open(tfile, "rb")
    decodedDict = bencoding.bdecode(objTorrentFile.read())
    info_hash = hashlib.sha1(bencoding.bencode(decodedDict[b"info"])).hexdigest()
    # enc_hash = uencode(info_hash)
    return hex2bytes(info_hash)


def get_announce(tfile):

    """Returns announce and pid in list [announce,pid]"""

    meta = bencodepy.decode_from_file(tfile)
    url = meta[b"announce"].decode()
    ann = url.split("?")[0]
    pid = url.split("=")[1]
    return [ann, pid]


def get_peer_id():

    """Returns (bytes) peer_id - id
    of torrent I'm using utorrent 2.210 (-UT2210- can be
    changed to whatever you want) 8 chars + 24 random
    chars (0123456789abcdef)"""

    chars = list("0123456789abcdef")
    p1 = ''.join([urllib.parse.quote_plus(random.choice(chars)) for _ in range(24)])
    # for i in range(24):
    #     p1 += urllib.parse.quote_plus(random.choice(chars))
    peer_id = "-UT2210-".encode() + hex2bytes(p1)
    return peer_id


#
def get_key():

    """Returns key - 8 random characters (0123456789ABCDEF)"""

    key = ""
    chars = list("0123456789ABCDEF")
    for i in range(8):
        key += random.choice(chars)
    return key



def get_files():

    """Returns list of torrent files in current directory"""

    torrlist = []
    for file in os.listdir():
        if file.endswith(".torrent"):
            torrlist.append(file)
    return torrlist


def start_seed(torrfile):
    file = torrfile
    print(f'choosing file {file}')

    """Get announce and pid"""
    ann = get_announce(file)[0]
    pid = get_announce(file)[1]

    hash = get_info_hash(file)

    """
    craft start url from given info.
    """
    start = {
        'pid': pid,
        'info_hash': hash,
        'peer_id': peer_id,
        'port': port,
        'uploaded': 0,
        'downloaded': 0,
        'left': 0,
        'corrupt': 0,
        'key': key,
        'event': 'started',
        'numwant': 200,
        'compact': 1,
        'no_peer_id': 1
    }


    # send request
    r = requests.get(ann, params=start, headers=header)
    print(f"Response from announce: {r.text}")
    intervali = grab(r.text, "intervali", "e12")
    if intervali:
        return {"filename": torrfile, "start": time.time(), "intervali": intervali}
    else:

        return None


def stop_seed(torrfile, starttime):

    file = torrfile
    ann = get_announce(file)[0]
    pid = get_announce(file)[1]
    hash = get_info_hash(file)

    # generate random upload in range 0.8-1x of given up speed
    randup = round(random.uniform(0.8, 1) * seed_time * upspeed * 1000)

    # Craft stop url

    stop = {
        'pid': pid,
        'info_hash': hash,
        'peer_id': peer_id,
        'port': port,
        'uploaded': randup,
        'downloaded': 0,
        'left': 0,
        'corrupt': 0,
        'key': key,
        'event': 'stopped',
        'numwant': 0,
        'compact': 1,
        'no_peer_id': 1
    }

    # sleep for given period of time and send request, when ctrl-c is pressed - end seeding
    try:
        print("seeding, press ctrl-c to stop")
        time.sleep(seed_time)
    except KeyboardInterrupt:
        print("\nShutting down SeedSmash")
        # calculate elapsed time from start of seeding
        elapsed_time = time.time() - starttime

        # adjust upload from default time to elapsed
        randup = randup * (elapsed_time / seed_time)

        # craft another stop url with changed upload

        stop = {
            'pid': pid,
            'info_hash': hash,
            'peer_id': peer_id,
            'port': port,
            'uploaded': randup,
            'downloaded': 0,
            'left': 0,
            'corrupt': 0,
            'key': key,
            'event': 'stopped',
            'numwant': 0,
            'compact': 1,
            'no_peer_id': 1
        }

        # Send request
        r = requests.get(ann, params=stop, headers=header)

        # print elapsed time + response from stop request + how much data was "uploaded"
        print(f"Response from announce:{r.text}")
        print(f"Uploaded {round(randup/1000)} kB in {round(elapsed_time)} seconds")

        exit(0)
    # send stop request
    print("sending stop request, don't ctrl-c me now pls")
    r = requests.get(ann, params=stop, headers=header)
    elapsed_time = time.time() - starttime
    # print elapsed time + response from stop request + how much data was "uploaded"
    print(f"Response from announce:{r.text}")
    print(f"Uploaded {round(randup/1000)} kB in {round(elapsed_time)} seconds")


def seed():





    test_torrent = get_files()[0]

    startjson = start_seed(test_torrent)
    stop_seed(test_torrent, startjson['start'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--time', type=int, required=True, help='Seed time in minutes')
    parser.add_argument('--speed', type=int, default=1000, help='Upload speed in kBs default 1000')
    args = parser.parse_args()

    # these stay constant for every torrent in one run
    peer_id = get_peer_id()
    port = random.randint(10000, 65536)
    key = get_key()
    # Set user agent to utorrent 2.210. Can be set to whatever you want but i prefer Utorrent
    header = {"user-agent": "uTorrent/2210(25534)"}

    upspeed = args.speed
    seed_time = args.time * 60  # Get time in seconds



    seed()
