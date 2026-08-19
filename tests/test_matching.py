from __future__ import annotations

import sqlite3
import unittest

from etl.ingest import SCHEMAS, canonical, find_match
from etl.normalize import (normalize_city, normalize_ctc, normalize_date,
                           normalize_email, normalize_phone)


class MatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('CREATE TABLE people (id INTEGER PRIMARY KEY, canonical_name TEXT, email TEXT UNIQUE, phone TEXT UNIQUE, city TEXT)')

    def tearDown(self) -> None:
        self.conn.close()

    def test_normalization_handles_actual_source_formats(self) -> None:
        self.assertEqual(normalize_phone('+91-9000000131'), '9000000131')
        self.assertEqual(normalize_phone('09000000287'), '9000000287')
        self.assertEqual(normalize_email('ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG'), 'isha.chopra95@mailtest.example.org')
        self.assertEqual(normalize_city('gurugram '), 'Gurugram')
        self.assertEqual(normalize_city('Bangalore'), 'Bengaluru')
        self.assertEqual(normalize_date('7 Jul 2026'), '2026-07-07')
        self.assertEqual(normalize_ctc('4.2'), 420000)

    def test_shifted_source_two_row_is_reconstructed(self) -> None:
        row = {'email_id': 'react, javascript, mysql', 'worker_name': 'ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG', 'rate': 'Isha Chopra', 'location': '1406/hr', 'status': 'Pune', 'skill_tags': 'active'}
        result = canonical(row, SCHEMAS['source2_gig_workers.csv'])
        self.assertEqual(result['name'], 'Isha Chopra')
        self.assertEqual(result['email'], 'isha.chopra95@mailtest.example.org')
        self.assertEqual(result['city'], 'Pune')
        self.assertEqual(result['skills'], ['javascript', 'mysql', 'react'])

    def test_conflicting_exact_identifiers_are_not_auto_merged(self) -> None:
        self.conn.execute("INSERT INTO people(canonical_name, email, phone, city) VALUES ('Email Owner', 'email@example.com', '9000000001', 'Pune')")
        self.conn.execute("INSERT INTO people(canonical_name, email, phone, city) VALUES ('Phone Owner', 'phone@example.com', '9000000002', 'Pune')")
        record, method = find_match(self.conn, {'name': 'Unknown', 'email': 'email@example.com', 'phone': '9000000002', 'city': 'Pune'})
        self.assertIsNone(record)
        self.assertEqual(method, 'conflicting_exact_identifiers')

    def test_unique_name_and_city_is_a_last_resort_match(self) -> None:
        self.conn.execute("INSERT INTO people(canonical_name, email, phone, city) VALUES ('Isha Chopra', 'isha@example.com', '9000000001', 'Pune')")
        record, method = find_match(self.conn, {'name': 'Isha Chopra', 'email': None, 'phone': None, 'city': 'Pune'})
        self.assertEqual(record['canonical_name'], 'Isha Chopra')
        self.assertEqual(method, 'name_and_city')


if __name__ == '__main__':
    unittest.main()
