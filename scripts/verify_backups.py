import os
import hashlib
import tarfile

BACKUP_DIRS = [
    'backups',
    'aws_production_backup_20250828',
]

def sha256_file(path, block_size=1<<20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(block_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def verify_tar(path):
    try:
        with tarfile.open(path, 'r:gz') as tf:
            # iterate a few members to force read
            for i, _ in enumerate(tf):
                if i > 50:
                    break
        return True, ''
    except Exception as e:
        return False, str(e)

def main():
    results = []
    for base in BACKUP_DIRS:
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            for fn in files:
                if not fn.endswith('.tar.gz'):
                    continue
                path = os.path.join(root, fn)
                ok, err = verify_tar(path)
                try:
                    sha = sha256_file(path)
                except Exception as e:
                    sha = None
                    if not err:
                        err = f'sha256 failed: {e}'
                results.append({'path': path, 'ok': ok, 'error': err, 'sha256': sha})
    # Print report
    for r in results:
        status = 'OK' if r['ok'] else 'CORRUPT'
        err = r['error'] or ''
        print(f"{status}  {r['path']}  sha256={r['sha256']}  {err}")

if __name__ == '__main__':
    main()

