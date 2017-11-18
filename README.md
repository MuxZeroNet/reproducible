# reproducible
Create reproducible archives

## Usage
```bash
./reproducible.py -d dir_to_archive -o archive.tar.gz --prepend RepoName-master
```

## Tips
**First, get a .tar.gz file**

- GitHub users: download the archive using the green button or from the Release section.

- Git users: `git archive --format=tar.gz -o out.tar.gz master` or `... v1.2.3`

- PyPI users: `python3 setup.py sdist`

**Extract the archive**

```bash
mkdir out_dir
tar -xf out.tar.gz -C out_dir --strip_components=1
```

**Pack the archive, deterministically**

```bash
./reproducible.py -d out_dir -o archive.tar.gz --prepend RepoName-master
```
