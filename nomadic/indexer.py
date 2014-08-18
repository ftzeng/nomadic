"""
Indexer
=======================

Indexes note files.
"""

import os
import shutil
from functools import wraps

import whoosh.index as index
from whoosh.fields import *

from nomadic import extractor

schema = Schema(title=TEXT(stored=True),
        path=ID(stored=True, unique=True),
        last_mod=STORED,
        content=TEXT(stored=True))

VALID_EXTS = ['.html', '.md', '.pdf', '.txt']

class Index():
    def __init__(self, notes_path):
        self.notes_path = os.path.expanduser(notes_path)
        self._load_index()

    @property
    def size(self):
        return self.ix.doc_count()

    @property
    def schema(self):
        return self.ix.schema

    def reset(self):
        """
        Indexes all of the notes.
        """
        self._load_index(reset=True)

        # Collect all the notes.
        notes = [note for note in self._walk_notes()]

        # Process all the notes.
        with self.ix.writer() as writer:
            [writer.add_document(**note) for note in extractor.process_notes(notes)]

    def update(self):
        """
        Update the index with
        modified or new notes.
        """
        with self.ix.searcher() as searcher:
            writer = self.ix.writer()

            # All the note paths in the index.
            ix_paths = set()
            to_index = set()

            # Loop over the stored fields in the index.
            for fields in searcher.all_stored_fields():
                ix_path = fields['path']
                ix_paths.add(ix_path)

                # If the file no longer exists...
                if not os.path.exists(ix_path):
                    writer.delete_by_term('path', ix_path)

                # If the file has been modified...
                else:
                    ix_time = fields['last_mod']
                    mtime = os.path.getmtime(ix_path)

                    if mtime > ix_time:
                        # Delete the existing indexed note
                        # and queue for re-indexing.
                        writer.delete_by_term('path', ix_path)
                        to_index.add(ix_path)

            # See if there are any new files to index
            # and index queued notes.
            notes = []
            for note in self._walk_notes():
                if note.path in to_index or note.path not in ix_paths:
                    notes.append(note)

            [writer.add_document(**note) for note in extractor.process_notes(notes)]
            writer.commit()

    def add_note(self, path):
        with self.ix.writer() as writer:
            _, ext = os.path.splitext(path)
            if ext in VALID_EXTS:
                n = extractor.note_from_path(path)
                note = extractor.process_note(n)
                writer.add_document(**note)

    def delete_note(self, path):
        with self.ix.writer() as writer:
            writer.delete_by_term('path', path)

    def update_note(self, path):
        self.delete_note(path)
        self.add_note(path)

    def move_note(self, src_path, dest_path):
        self.delete_note(src_path)
        self.add_note(dest_path)

    def note_at(self, path):
        """
        Convenience method for
        fetching a note by path
        from the index.
        """
        searcher = self.ix.searcher()
        return searcher.document(path=path)

    def _walk_notes(self):
        """
        Yield Notes in the
        specified directory.
        """
        for root, dirnames, filenames in walk_notes(self.notes_path):
            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext in VALID_EXTS:
                    path = os.path.join(root, filename)
                    yield extractor.note_from_path(path)


    def _load_index(self, reset=False):
        index_path = os.path.join(self.notes_path, '.searchindex')

        # Load or create the index.
        if not os.path.exists(index_path):
            os.makedirs(index_path)
        if not index.exists_in(index_path) or reset:
            self.ix = index.create_in(index_path, schema)
        else:
            self.ix = index.open_dir(index_path)

def walk_notes(notes_dir):
    """
    Walk a notes directory,
    yielding only for valid directories.
    """
    for root, dirnames, filenames in os.walk(notes_dir):
        if '.build' not in root and '.searchindex' not in root:
            yield root, dirnames, filenames
