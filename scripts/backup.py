"""Export editable content and source without caches or generated output."""
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'backups';folder.mkdir(exist_ok=True)
archive=folder/('personal-site-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.zip')
with ZipFile(archive,'w',ZIP_DEFLATED) as out:
    for name in ['src','public','scripts','docs']:
        for file in (ROOT/name).rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc' and not (name=='docs' and (file.suffix=='.png' or file.name.endswith('-checks.json'))):
                out.write(file,file.relative_to(ROOT))
    for name in ['site.json','index.html','README.md','requirements.txt','.gitignore','direction-approved.md']:
        out.write(ROOT/name,name)
print(archive)
