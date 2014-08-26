import os
import shutil
from urllib import quote
from collections import namedtuple

from nomadic.core import Nomadic
from nomadic.demon.handler import Handler
from test import NomadicTest, _path, compiled_path

# Mock the watchdog events.
Event = namedtuple('Event', ['is_directory', 'src_path', 'dest_path'])

class MockServer():
    def refresh_clients(self):
        pass

class HandlerTest(NomadicTest):
    """
    This tests the handler's handling of
    events, but does not test
    the triggering of those events.
    (We're just assuming that the
    watchdog lib has got it covered!)

    So we do all the file handling
    and manually trigger the proper response.
    """
    def setUp(self):
        self.nomadic = Nomadic(self.notes_dir)
        self.nomadic.index.reset()
        self.nomadic.builder.build()

        self.handler = Handler(self.nomadic, MockServer())

    def test_on_created(self):
        path = _path('a new note.md')
        with open(path, 'w') as note:
            note.write('# a new note')

        e = Event(is_directory=False, src_path=path, dest_path=None)
        self.handler.on_created(e)

        self.assertTrue(self.nomadic.index.note_at(path))
        self.assertTrue(os.path.exists(compiled_path('a new note.html')))
        with open(compiled_path('index.html'), 'r') as index:
            self.assertTrue('a new note.html' in index.read())

    def test_on_deleted(self):
        path = _path('my note.md')
        path_ = compiled_path('my note.html')

        self.assertTrue(self.nomadic.index.note_at(path))
        self.assertTrue(os.path.exists(path_))
        with open(compiled_path('index.html'), 'r') as index:
            self.assertTrue('my note.html' in index.read())

        os.remove(path)
        e = Event(is_directory=False, src_path=path, dest_path=None)
        self.handler.on_deleted(e)

        self.assertFalse(self.nomadic.index.note_at(path))
        self.assertFalse(os.path.exists(path_))
        with open(compiled_path('index.html'), 'r') as index:
            self.assertFalse('my note.html' in index.read())

    def test_on_modified(self):
        path = _path('my note.md')
        path_ = compiled_path('my note.html')

        with open(path, 'w') as note:
            note.write('a changed note')

        e = Event(is_directory=False, src_path=path, dest_path=None)
        self.handler.on_modified(e)

        with open(path_, 'r') as note:
            self.assertTrue('<p>a changed note</p>' in note.read())

        note = self.nomadic.index.note_at(path)
        self.assertEqual('a changed note', note['content'])

    def test_on_moved(self):
        path = _path('my note.md')
        path_ = compiled_path('my note.html')

        path_new = _path('some_notebook/my moved note.md')
        path_new_ = compiled_path('some_notebook/my moved note.html')

        self.assertTrue(self.nomadic.index.note_at(path))
        self.assertTrue(os.path.exists(path_))

        with open(compiled_path('index.html'), 'r') as index:
            self.assertTrue('my note.html' in index.read())

        shutil.move(path, path_new)
        e = Event(is_directory=False, src_path=path, dest_path=path_new)
        self.handler.on_moved(e)

        self.assertFalse(self.nomadic.index.note_at(path))
        self.assertFalse(os.path.exists(path_))
        with open(compiled_path('index.html'), 'r') as index:
            self.assertFalse('my note.html' in index.read())

        self.assertTrue(self.nomadic.index.note_at(path_new))
        self.assertTrue(os.path.exists(path_new_))
        with open(compiled_path('some_notebook/index.html'), 'r') as index:
            self.assertTrue('my moved note.html' in index.read())

    def test_on_created_directory(self):
        path = _path('new notebook')
        path_ = compiled_path('new notebook/index.html')

        os.makedirs(path)
        e = Event(is_directory=True, src_path=path, dest_path=None)
        self.handler.on_created(e)

        self.assertTrue(os.path.exists(path_))

    def test_on_deleted_directory(self):
        path = _path('some_notebook')
        path_ = compiled_path('some_notebook')

        shutil.rmtree(path)
        e = Event(is_directory=True, src_path=path, dest_path=None)
        self.handler.on_deleted(e)

        self.assertFalse(os.path.exists(path_))
        with open(compiled_path('index.html'), 'r') as index:
            self.assertFalse('some_notebook/index.html' in index.read())
        self.assertFalse(self.nomadic.index.note_at(_path('some_notebook/a cool note.md')))

    def test_on_moved_directory(self):
        path = _path('some_notebook')
        path_ = compiled_path('some_notebook')

        path_new = _path('moved_notebook')
        path_new_ = compiled_path('moved_notebook')

        shutil.move(path, path_new)
        e = Event(is_directory=True, src_path=path, dest_path=path_new)
        self.handler.on_moved(e)

        with open(compiled_path('index.html'), 'r') as index:
            index_html = index.read()
            self.assertFalse('some_notebook/index.html' in index_html)
            self.assertTrue('moved_notebook/index.html' in index_html)

        self.assertFalse(os.path.exists(path_))
        self.assertFalse(self.nomadic.index.note_at(_path('some_notebook/a cool note.md')))

        self.assertTrue(os.path.exists(path_new_))
        self.assertTrue(self.nomadic.index.note_at(_path('moved_notebook/a cool note.md')))

    def test_update_references_markdown(self):
        path = _path('some_notebook/a cool note.md')
        path_ = compiled_path('some_notebook/a cool note.html')

        ref = _path('some_notebook/nested book/empty.md')
        ref_new = _path('moved empty note.md')

        rel_link = 'nested book/empty.md'
        rel_link_ = quote('nested book/empty.html')
        rel_link_new = '../moved empty note.md'
        rel_link_new_ = quote('../moved empty note.html')

        with open(path, 'r') as note:
            note_content = note.read()
            self.assertTrue(rel_link in note_content)
            self.assertFalse(rel_link_new in note_content)
        with open(path_, 'r') as note:
            note_content = note.read()
            self.assertTrue(rel_link_ in note_content)
            self.assertFalse(rel_link_new_ in note_content)

        self.handler.update_references(ref, ref_new)

        with open(path, 'r') as note:
            note_content = note.read()
            self.assertFalse(rel_link in note_content)
            self.assertTrue(rel_link_new in note_content)
        with open(path_, 'r') as note:
            note_content = note.read()
            print(note_content)
            self.assertFalse(rel_link_ in note_content)
            self.assertTrue(rel_link_new_ in note_content)

    def test_update_references_html(self):
        path = _path('another note.html')
        path_ = compiled_path('another note.html')

        ref = _path('some_notebook/a cool note.md')
        ref_new = _path('moved cool note.md')

        rel_link = 'some_notebook/a cool note.md'
        rel_link_ = quote('some_notebook/a cool note.html')
        rel_link_new = quote('moved cool note.md')
        rel_link_new_ = quote('moved cool note.html')

        with open(path, 'r') as note:
            note_content = note.read()
            self.assertTrue(rel_link in note_content)
            self.assertFalse(rel_link_new in note_content)
        with open(path_, 'r') as note:
            note_content = note.read()
            self.assertTrue(rel_link_ in note_content)
            self.assertFalse(rel_link_new_ in note_content)

        self.handler.update_references(ref, ref_new)

        with open(path_, 'r') as note:
            note_content = note.read()
            self.assertFalse(rel_link_ in note_content)
            self.assertTrue(rel_link_new_ in note_content)
        with open(path, 'r') as note:
            note_content = note.read()
            self.assertFalse(rel_link in note_content)
            self.assertTrue(rel_link_new in note_content)
