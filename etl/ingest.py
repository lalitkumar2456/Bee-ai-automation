from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.database import connection, initialize_database
from etl.normalize import clean, name_key, normalize_city, normalize_ctc, normalize_date, normalize_email, normalize_name, normalize_phone, normalize_skills

SCHEMAS = {
 'source1_naukri_applicants.csv': {'name':'Full Name','email':'Email','phone':'Phone','city':'City','skills':'Skills','experience':'Experience (Years)','ctc':'Current CTC','date':'Applied Date'},
 'source2_gig_workers.csv': {'name':'worker_name','email':'email_id','city':'location','skills':'skill_tags'},
 'source3_cbnexus_contacts.csv': {'name':'Name','phone':'Phone Number','city':'City'},
}
def canonical(row, schema):
    raw = {key: clean(row.get(col)) for key,col in schema.items()}
    # Repair the known Source 2 schema-shift pattern from field contents.
    if raw.get('email') and '@' not in raw['email'] and raw.get('name') and '@' in raw['name']:
        raw.update(email=raw['name'], name=clean(row.get('rate')), city=clean(row.get('status')), skills=raw['email'])
    return {'name':normalize_name(raw.get('name')), 'email':normalize_email(raw.get('email')), 'phone':normalize_phone(raw.get('phone')), 'city':normalize_city(raw.get('city')), 'skills':normalize_skills(raw.get('skills')), 'experience':clean(raw.get('experience')), 'ctc':normalize_ctc(raw.get('ctc')), 'date':normalize_date(raw.get('date')), 'raw':raw}
def find_match(conn, person):
    email_match = conn.execute('SELECT * FROM people WHERE email=?', (person['email'],)).fetchone() if person['email'] else None
    phone_match = conn.execute('SELECT * FROM people WHERE phone=?', (person['phone'],)).fetchone() if person['phone'] else None
    if email_match and phone_match and email_match['id'] != phone_match['id']:
        return None, 'conflicting_exact_identifiers'
    if email_match:
        return email_match, 'exact_email'
    if phone_match:
        return phone_match, 'exact_phone'
    if person['name'] and person['city']:
        matches=[p for p in conn.execute('SELECT * FROM people WHERE city=?',(person['city'],)) if name_key(p['canonical_name'])==name_key(person['name'])]
        if len(matches)==1: return matches[0], 'name_and_city'
        if len(matches)>1: return None, 'ambiguous_name_and_city'
    return None, 'new_person'
def run():
    initialize_database(); files=[p for p in (ROOT/'data').glob('*.csv') if p.name in SCHEMAS]
    if not files: raise SystemExit('Expected data/source1_naukri_applicants.csv, source2_gig_workers.csv, source3_cbnexus_contacts.csv')
    stats={'read':0,'skipped':0,'created':0,'matched':0,'ambiguous':0}
    with connection() as conn:
      for path in files:
       schema=SCHEMAS[path.name]
       with path.open(encoding='utf-8-sig',newline='') as f:
        for line,row in enumerate(csv.DictReader(f),start=2):
         stats['read']+=1
         if not any(clean(v) for v in row.values()) or row.get(schema['name'])==schema['name']: stats['skipped']+=1; continue
         person=canonical(row,schema)
         if not person['name']: stats['skipped']+=1; continue
         match,method=find_match(conn,person)
         if method.startswith('ambiguous'):
          conn.execute('INSERT INTO review_queue(source_name,source_record_id,reason,payload) VALUES(?,?,?,?)',(path.name,line,method,json.dumps(person))); stats['ambiguous']+=1; continue
         if match: person_id=match['id']; stats['matched']+=1
         else:
          person_id=conn.execute('INSERT INTO people(canonical_name,email,phone,city,experience_years,current_ctc_inr,applied_date) VALUES(?,?,?,?,?,?,?)',(person['name'],person['email'],person['phone'],person['city'],person['experience'],person['ctc'],person['date'])).lastrowid; stats['created']+=1
         conn.execute('INSERT OR IGNORE INTO person_sources(person_id,source_name,source_record_id,raw_name,raw_email,raw_phone,match_method) VALUES(?,?,?,?,?,?,?)',(person_id,path.name,line,person['raw'].get('name'),person['raw'].get('email'),person['raw'].get('phone'),method))
         for skill in person['skills']: conn.execute('INSERT OR IGNORE INTO person_skills(person_id,skill,source_name) VALUES(?,?,?)',(person_id,skill,path.name))
    print('ETL complete:', ', '.join(f'{k}={v}' for k,v in stats.items()))
if __name__ == '__main__': run()
