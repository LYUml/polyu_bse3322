"""Download reference files only. Does not install tools or run simulations."""
import concurrent.futures
import datetime
import hashlib
import json
import mmap
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COURSE = Path(r'C:\Users\lyuml-win\iCloudDrive\Desktop\y3_s1\bse3322')
REF = ROOT / '02_References'
MANIFEST = REF / '01_下载清单.json'

def fetch(url, target):
    request = urllib.request.Request(url, headers={'User-Agent': 'BSE3322-reference-download/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response, target.open('wb') as out:
        while data := response.read(1024 * 1024):
            out.write(data)

def validate(path):
    if path.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(path)
        if not reader.pages:
            raise ValueError('PDF has no pages')
        return {'pages': len(reader.pages)}
    if path.suffix.lower() in ('.pptx', '.xlsx') and is_compound_office(path):
        with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            encrypted = data.find('EncryptedPackage'.encode('utf-16le')) >= 0
        return {'format': 'Office compound container', 'encrypted': encrypted,
                'content_validation': 'not readable without authorized password' if encrypted else 'container only'}
    if path.suffix.lower() in ('.zip', '.pptx', '.xlsx'):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError('ZIP CRC failure: ' + bad)
            return {'archive_entries': len(archive.namelist())}
    return {}

def is_compound_office(path):
    with path.open('rb') as stream:
        return stream.read(8) == bytes.fromhex('d0cf11e0a1b11ae1')

def task(item):
    kind, source, destination = item
    target = ROOT / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {'source': source, 'path': destination, 'kind': kind}
    temporary = target.with_suffix(target.suffix + '.part')
    try:
        if not target.exists():
            if kind == 'copy':
                subprocess.run([sys.executable, '-c',
                    'import shutil,sys; shutil.copyfile(sys.argv[1],sys.argv[2])',
                    source, str(temporary)], check=True, timeout=90, capture_output=True)
            else:
                fetch(source, temporary)
            # Parse using intended extension before marking a download complete.
            if target.suffix == '.pdf':
                from pypdf import PdfReader
                if not PdfReader(temporary).pages:
                    raise ValueError('Not a valid PDF')
            elif target.suffix in ('.zip', '.pptx', '.xlsx') and not (target.suffix in ('.pptx', '.xlsx') and is_compound_office(temporary)):
                with zipfile.ZipFile(temporary) as archive:
                    if archive.testzip():
                        raise ValueError('Invalid ZIP archive')
            temporary.replace(target)
        record.update(validate(target))
        digest = hashlib.sha256()
        with target.open('rb') as stream:
            while data := stream.read(1024 * 1024):
                digest.update(data)
        record.update(status='ok', bytes=target.stat().st_size, sha256=digest.hexdigest())
    except Exception as exc:
        record.update(status='failed', error=str(exc)[:500])
        if temporary.exists():
            temporary.unlink()
    print(json.dumps(record, ensure_ascii=True), flush=True)
    return record

def main():
    items = []
    for filename in ['W03_Fire_Detectors_and_Smoke_Extraction.pdf', 'W04_Fire_Modelling.pdf']:
        items.append(('copy', str(COURSE / '01_lec' / filename), '02_References/01_Course_Materials/' + filename))
    for filename in ['AL01_Fire_Modelling.pptx', 'AL02_Steckler_Room_Fire.pptx', 'AL03_Smoke_Extraction.pptx']:
        items.append(('copy', str(COURSE / '03_adaptive_learning' / filename), '02_References/01_Course_Materials/' + filename))
    for source, filename in [('04_project/Presentation_Schedule_R2.xlsx','Presentation_Schedule_R2.xlsx'),
                             ('00_info/Teaching_Schedule.pdf','Teaching_Schedule.pdf')]:
        items.append(('copy', str(COURSE / source), '01_Assignment_Brief/' + filename))
    for source, filename in [
        ('https://www.hkfsd.gov.hk/eng/source/safety/File2022.pdf','01_FSD_Codes_of_Practice_2022.pdf'),
        ('https://www.hkfsd.gov.hk/eng/source/circular/e04_1996.pdf','02_FSD_Circular_4_1996_Smoke_Control.pdf'),
        ('https://www.hkfsd.gov.hk/eng/source/circular/2024_04_eng_20240426_164202.pdf','03_FSD_Circular_4_2024_Amendments.pdf'),
        ('https://www.hkfsd.gov.hk/eng/source/licensing/FSD_Web_20210416_PG_02.pdf','04_FSD_Smoke_Control_Submission_and_Acceptance.pdf'),
        ('https://www.bd.gov.hk/doc/en/resources/codes-and-references/code-and-design-manuals/fs_code2011.pdf','05_BD_Fire_Safety_Code_2011_2024_Edition.pdf')]:
        items.append(('url', source, '02_References/03_HK_Regulations/' + filename))
    items.append(('url','https://arxiv.org/pdf/2412.17146','02_References/02_Papers/Xu_2024_FoamPilot_arXiv_2412.17146.pdf'))
    for filename in ['FDS_User_Guide.pdf', 'FDS_Technical_Reference_Guide.pdf']:
        items.append(('copy', str(Path(r'C:\Program Files\PyroSim 2026\fds') / filename), '02_References/04_FDS_Documentation/' + filename))
    for repo in ['Meteor-Simulation/bulc-mcp','GraysonBellamy/pyfds','FireDynamics/fdsreader']:
        try:
            request = urllib.request.Request('https://api.github.com/repos/' + repo + '/commits/HEAD', headers={'User-Agent':'BSE3322-reference-download'})
            with urllib.request.urlopen(request, timeout=30) as response:
                info = json.load(response)
            sha = info['sha']
            folder = ROOT / '06_Tools/01_Repository_Snapshots'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (repo.split('/')[-1] + '_provenance.json')).write_text(json.dumps({'repository':'https://github.com/'+repo,'commit':sha,'download_date':'2026-11-13'}, indent=2), encoding='utf-8')
            items.append(('url','https://codeload.github.com/'+repo+'/zip/'+sha,'06_Tools/01_Repository_Snapshots/'+repo.split('/')[-1]+'_'+sha[:12]+'.zip'))
        except Exception as exc:
            print('REPOSITORY_METADATA_ERROR '+repo+' '+str(exc), flush=True)
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for future in concurrent.futures.as_completed([pool.submit(task, item) for item in items]):
            records.append(future.result())
            MANIFEST.write_text(json.dumps({'date':'2026-11-13','files':records}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('COMPLETE',len(records), 'OK',sum(r['status']=='ok' for r in records), flush=True)

if __name__ == '__main__':
    main()
