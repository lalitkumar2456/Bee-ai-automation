from __future__ import annotations
import shutil, sys, uuid
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.audio import inspect_audio
from app.database import connection, initialize_database
from etl.normalize import normalize_name, normalize_phone

UPLOADS=ROOT/'uploads'; UPLOADS.mkdir(exist_ok=True)
app=FastAPI(title='ConsultBae Local Audio Collection')
app.mount('/media',StaticFiles(directory=UPLOADS),name='media')
@app.on_event('startup')
def startup(): initialize_database()
def layout(body): return HTMLResponse(f'''<!doctype html><html><head><title>ConsultBae</title><style>body{{max-width:900px;margin:40px auto;font-family:system-ui;color:#172033}}input,button{{padding:10px;margin:6px 0;font:inherit}}form{{display:grid;max-width:440px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}nav a{{margin-right:16px}}</style></head><body><nav><a href="/">Upload</a><a href="/submissions">Submissions</a></nav>{body}</body></html>''')
@app.get('/',response_class=HTMLResponse)
def home(): return layout('''<h1>Audio collection</h1><p>Identify yourself by name and phone, then upload an audio file.</p><form action="/audio/upload" method="post" enctype="multipart/form-data"><label>Name<input required name="name"></label><label>Phone<input required name="phone"></label><label>Audio file<input required name="audio_file" type="file" accept="audio/*,.wav"></label><button>Submit audio</button></form><p>Works fully locally. WAV works without FFmpeg; install FFmpeg locally for MP3/M4A metadata.</p>''')
@app.post('/audio/upload')
async def upload(name: str=Form(...), phone: str=Form(...), audio_file: UploadFile=File(...)):
    name,phone=normalize_name(name),normalize_phone(phone)
    if not name or not phone: raise HTTPException(422,'Enter a name and a valid 10-digit phone number.')
    if not audio_file.filename: raise HTTPException(422,'Choose an audio file.')
    ext=Path(audio_file.filename).suffix.lower()
    if ext not in {'.wav','.mp3','.m4a','.ogg','.webm'}: raise HTTPException(415,'Supported audio: WAV, MP3, M4A, OGG, WEBM.')
    with connection() as conn:
        person=conn.execute('SELECT * FROM people WHERE phone=?',(phone,)).fetchone()
        if not person:
            person_id=conn.execute('INSERT INTO people(canonical_name,phone) VALUES(?,?)',(name,phone)).lastrowid
        else: person_id=person['id']
    stored=f'{uuid.uuid4().hex}{ext}'; target=UPLOADS/stored
    with target.open('wb') as output: shutil.copyfileobj(audio_file.file,output)
    meta=inspect_audio(target)
    with connection() as conn:
        submission_id=conn.execute('INSERT INTO audio_submissions(person_id,file_path,file_name,duration_seconds,sample_rate_hz,bitrate_kbps,loudness_db,analysis_note) VALUES(?,?,?,?,?,?,?,?)',(person_id,stored,audio_file.filename,meta['duration_seconds'],meta['sample_rate_hz'],meta['bitrate_kbps'],meta['loudness_db'],meta['analysis_note'])).lastrowid
    return RedirectResponse(f'/submission/{submission_id}',303)
@app.get('/submission/{submission_id}',response_class=HTMLResponse)
def submitted(submission_id:int):
    with connection() as conn: row=conn.execute('SELECT a.*,p.canonical_name FROM audio_submissions a JOIN people p ON p.id=a.person_id WHERE a.id=?',(submission_id,)).fetchone()
    if not row: raise HTTPException(404,'Submission not found.')
    return layout(f'<h1>Upload successful</h1><p><b>{row["canonical_name"]}</b> — {row["file_name"]}</p><ul><li>Duration: {row["duration_seconds"] or "unavailable"} seconds</li><li>Sample rate: {row["sample_rate_hz"] or "unavailable"} Hz</li><li>Bitrate: {row["bitrate_kbps"] or "unavailable"} kbps</li><li>Loudness: {row["loudness_db"] or "not calculated"}</li></ul><p>{row["analysis_note"] or ""}</p><audio controls src="/media/{row["file_path"]}"></audio>')
@app.get('/submissions',response_class=HTMLResponse)
def submissions():
    with connection() as conn: rows=conn.execute('SELECT a.*,p.canonical_name,p.phone FROM audio_submissions a JOIN people p ON p.id=a.person_id ORDER BY a.created_at DESC').fetchall()
    cells=''.join(f'<tr><td>{r["canonical_name"]}</td><td>{r["phone"]}</td><td>{r["duration_seconds"] or "—"}s</td><td>{r["sample_rate_hz"] or "—"}</td><td>{r["bitrate_kbps"] or "—"}</td><td><audio controls src="/media/{r["file_path"]}"></audio></td></tr>' for r in rows)
    return layout(f'<h1>Submissions</h1><table><tr><th>Name</th><th>Phone</th><th>Duration</th><th>Rate</th><th>kbps</th><th>Play</th></tr>{cells or "<tr><td colspan=6>No audio submissions yet.</td></tr>"}</table>')

@app.get('/people/{person_id}/classification-input')
def classification_input(person_id: int):
    with connection() as conn:
        person = conn.execute(
            'SELECT id, canonical_name, email, phone, classification, classification_status '
            'FROM people WHERE id=?',
            (person_id,),
        ).fetchone()

        if not person:
            raise HTTPException(404, 'Person not found.')

        skills = conn.execute(
            'SELECT skill FROM person_skills WHERE person_id=? ORDER BY skill',
            (person_id,),
        ).fetchall()

    return {
        'person_id': person['id'],
        'name': person['canonical_name'],
        'email': person['email'],
        'phone': person['phone'],
        'skills': [row['skill'] for row in skills],
        'classification': person['classification'],
        'classification_status': person['classification_status'],
    }


@app.patch('/people/{person_id}/classification')
def update_classification(person_id: int, classification: str):
    classification = classification.strip()

    allowed = {
        'automation-heavy',
        'web-development',
        'data',
        'general',
    }

    if classification not in allowed:
        raise HTTPException(
            422,
            f'Invalid classification. Use one of: {", ".join(sorted(allowed))}.',
        )

    with connection() as conn:
        cursor = conn.execute(
            'UPDATE people '
            'SET classification=?, classification_status=?, updated_at=CURRENT_TIMESTAMP '
            'WHERE id=?',
            (classification, 'completed', person_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(404, 'Person not found.')

    return {
        'person_id': person_id,
        'classification': classification,
        'classification_status': 'completed',
    }