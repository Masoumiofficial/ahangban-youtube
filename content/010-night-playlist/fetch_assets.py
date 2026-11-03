"""Restore exact user-supplied music/cover blobs into ignored rendered/ using gh.
Never fetch ahangban.ir or read credentials. Refuse a changed blob/size/hash.
"""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def main():
    manifest=json.loads((HERE/'source-manifest.json').read_text())
    target=REPO/'rendered/video-010-night-playlist/source-media'
    target.mkdir(parents=True,exist_ok=True)
    for a in manifest['assets']:
        path=target/a['file']
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256']:
            continue
        tmp=path.with_name(path.name+'.download')
        try:
            with tmp.open('wb') as out:
                subprocess.run(['gh','api',f"repos/{manifest['repository']}/git/blobs/{a['gitBlob']}",'-H','Accept: application/vnd.github.raw+json'],stdout=out,check=True)
            data=tmp.read_bytes()
            assert len(data)==a['bytes']
            assert hashlib.sha256(data).hexdigest()==a['sha256']
            assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==a['gitBlob']
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)
        print('Verified:',a['file'])
if __name__=='__main__':main()
