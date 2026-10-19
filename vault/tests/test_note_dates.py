"""Content dates must not drift during maintenance or no-op generation."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vaultkit import frontmatter as fm
from vaultkit.check import Note, _check_frontmatter
from vaultkit.policy import load_policy
from vaultkit.tilsync import Generated, merge
from test_vault_index import SCRIPTS, _load


def gen(body='본문\n', tags=None):
    return Generated(stem='note', title='제목', sources=[], topics=['AI'],
                     tags=tags or ['ai/llm', 'til'], til_links=[], body=body)


class NoteDatesTest(unittest.TestCase):
    def test_create_then_content_change_preserves_created(self):
        first = merge(gen(), None, None, '2026-10-01')
        self.assertEqual(fm.get_list(fm.parse(first.text), 'updated'), ['2026-10-01'])
        changed = merge(gen('수정한 본문\n'), first.text, first.entry, '2026-10-19')
        doc = fm.parse(changed.text)
        self.assertEqual(fm.get_list(doc, 'created'), ['2026-10-01'])
        self.assertEqual(fm.get_list(doc, 'updated'), ['2026-10-19'])
        self.assertEqual(merge(gen('수정한 본문\n'), changed.text, changed.entry, '2026-10-20').action, 'unchanged')

    def test_metadata_and_legacy_noop_do_not_stamp_updated(self):
        first = merge(gen(), None, None, '2026-10-01')
        legacy = first.text.replace('updated: 2026-10-01\n', '')
        self.assertEqual(merge(gen(), legacy, first.entry, '2026-10-19').action, 'unchanged')
        changed = merge(gen(tags=['ai/agent', 'til']), legacy, first.entry, '2026-10-19')
        self.assertNotIn('updated', fm.parse(changed.text).fields)

    def test_tag_change_preserves_existing_date_and_user_body(self):
        first = merge(gen(), None, None, '2026-10-01')
        edited = first.text.replace('본문\n', '사용자 편집\n')
        changed = merge(gen(tags=['ai/agent', 'til']), edited, first.entry, '2026-10-19')
        self.assertEqual(changed.action, 'frontmatter-only')
        doc = fm.parse(changed.text)
        self.assertEqual(doc.body, '사용자 편집\n')
        self.assertEqual(fm.get_list(doc, 'updated'), ['2026-10-01'])

    def test_existing_unknown_created_is_not_invented_by_sync(self):
        first = merge(gen(), None, None, '2026-10-01')
        for replacement in ['created:\n', '']:
            existing = first.text.replace('created: 2026-10-01\n', replacement)
            changed = merge(gen(tags=['ai/agent', 'til']), existing, first.entry, '2026-10-19')
            doc = fm.parse(changed.text)
            self.assertEqual(fm.get_list(doc, 'created'), [])
            self.assertEqual('created' in doc.fields, bool(replacement))

    def test_legacy_blank_dates_remain_unknown(self):
        doc = fm.parse('---\ntitle: 제목\ntags: [ai/agent]\ncreated:\nupdated:\n---\n')
        errors=[]
        _check_frontmatter(doc, Note(Path('x'), 'x', 'projects'), load_policy(), set(), lambda *a: errors.append(a))
        self.assertEqual(errors, [])

    def test_date_validation_including_inbox(self):
        for scope in ['wiki-only', 'projects', 'sources', 'archive', 'inbox']:
            for value in ['2026-02-30', '2026-1-01', 'yesterday', '[2026-10-19]']:
                with self.subTest(scope=scope, value=value):
                    doc = fm.parse(f'---\ntitle: 제목\ntags: [ai/agent]\ncreated: 2026-10-01\nupdated: {value}\n---\n')
                    errors=[]
                    _check_frontmatter(doc, Note(Path('x'), 'x', scope), load_policy(), set(), lambda *a: errors.append(a))
                    self.assertTrue(any('updated' in e[2] for e in errors), errors)
        doc=fm.parse('---\ntitle: 제목\ntags: [ai/agent]\ncreated: 2026-10-19\nupdated: 2026-10-01\n---\n')
        errors=[]
        _check_frontmatter(doc, Note(Path('x'), 'x', 'projects'), load_policy(), set(), lambda *a: errors.append(a))
        self.assertTrue(any('updated' in e[2] for e in errors))


class IndexDatesTest(unittest.TestCase):
    def test_index_content_change_and_noop_preserve_dates(self):
        for script in SCRIPTS:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); (root/'Wiki').mkdir()
                note=root/'Wiki/note.md'; note.write_text('첫 요약\n')
                index=root/'_Inbox/Vault-Index.md'
                module=_load(script)
                with patch.object(module,'VAULT',root), patch.object(module,'INDEX_FILE',index), contextlib.redirect_stdout(io.StringIO()):
                    with patch.object(module,'DATE','2026-10-01'): module.main()
                    original=index.read_text(); stat=index.stat().st_mtime_ns
                    self.assertIn('updated: 2026-10-01', original)
                    with patch.object(module,'DATE','2026-10-19'): module.main()
                    self.assertEqual(index.read_text(),original)
                    self.assertEqual(index.stat().st_mtime_ns,stat)
                    note.write_text('바뀐 요약\n')
                    with patch.object(module,'DATE','2026-10-19'): module.main()
                    self.assertIn('created: 2026-10-01',index.read_text())
                    self.assertIn('updated: 2026-10-19',index.read_text())
                    self.assertIn('바뀐 요약',index.read_text())
