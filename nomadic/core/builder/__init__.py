"""
Builder
=======================

Builds note files a local HTML site
and manages built files.
"""

import os
import shutil
from collections import namedtuple

from lxml.html import fromstring, tostring
from jinja2 import Template, FileSystemLoader, environment

from nomadic.core import manager
from nomadic.core.builder import compiler

File = namedtuple('File', ['title', 'filename'])

# Load templates.
path = os.path.abspath(__file__)
dir = os.path.dirname(path)

env = environment.Environment()
env.loader = FileSystemLoader(os.path.join(dir, '../assets/templates'))
index_templ = env.get_template('notebook.html')
note_templ = env.get_template('note.html')

class Builder():
    def __init__(self, notes_path):
        # The last '' is to ensure a trailing slash.
        self.notes_path = os.path.join(notes_path, '')
        self.build_path = os.path.join(notes_path, u'.build', '')

        self._prepare_build_dir()


    def _prepare_build_dir(self, reset=False):
        """
        Prepare the build directory,
        creating it if necessary.
        """
        if reset and os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)

        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)

    def build(self):
        """
        Compile all notes into a
        browsable HTML structure.
        """
        self._prepare_build_dir(reset=True)
        self.compile_notebook(self.notes_path)

    def compile_notebook(self, path):
        """
        Build a notebook, recursively,
        compiling notes and indexes.
        """
        for root, dirnames, filenames in manager.walk(path):
            build_root = root.replace(self.notes_path, self.build_path)

            dirs = []
            files = []

            # Process valid sub-directories.
            for dirname in dirnames:
                build_path = os.path.join(build_root, dirname)

                if os.path.exists(build_path):
                    shutil.rmtree(build_path)
                os.makedirs(build_path)

                dirs.append(dirname.decode('utf-8'))

            # Process notes.
            for filename in filenames:
                title, ext = os.path.splitext(filename)
                compiled_filename = title + '.html'
                if ext in ['.html', '.md']:
                    path = os.path.join(root, filename)

                    self.compile_note(path)

                    file = File(title, compiled_filename)
                    files.append(file)

            # Write the index file for this node.
            self._write_index(build_root, dirs, files)

    def compile_note(self, path):
        """
        Compile a single Markdown or
        HTML note to the build tree.

        This will overwrite the
        existing note, if any.
        """
        build_path, ext = self.build_path_for_note_path(path)
        crumbs = self._build_breadcrumbs(build_path)

        # Process all relative paths to
        # point to the raw note directories,
        # so we don't have to copy resources over.
        with open(path, 'rb') as note:
            content = ''
            raw_content = note.read().decode('utf-8')
            if ext == '.html':
                raw_html = raw_content
            else:
                raw_html = compiler.compile_markdown(raw_content)

            if raw_html.strip():
                html = fromstring(raw_html)

                html.rewrite_links(self._rewrite_link(path, build_path))
                raw_html = tostring(html)
                content = note_templ.render(html=raw_html, crumbs=crumbs)

            # Write the compiled note.
            with open(build_path, 'w') as build_note:
                build_note.write(content.encode('utf-8'))


    def delete_note(self, path):
        """
        Deletes a compiled note
        from the build tree.
        """
        build_path, _ = self.build_path_for_note_path(path)

        if os.path.exists(build_path):
            os.remove(build_path)

    def delete_notebook(self, path):
        """
        Deletes a compiled notebook
        from the build tree.
        """
        build_path = self.build_path_for_path(path)

        if os.path.exists(build_path):
            shutil.rmtree(build_path)

    def index_notebook(self, dir):
        """
        Compiles an index for a given directory.
        This does not compile the notes in the directory,
        nor is it recursive.
        """
        build_path = self.build_path_for_path(dir)

        dirs, files_ = manager.filenames(dir)
        files = []

        for name in files_:
            title, ext = os.path.splitext(name)
            if ext in ['.html', '.md']:
                compiled_filename = title + '.html'
                file = File(title, compiled_filename)
                files.append(file)

        # Write the index file for this node.
        self._write_index(build_path, dirs, files)


    def build_path_for_note_path(self, path):
        """
        Returns a compiled note path for a given
        regular note path.

        Also returns the original extension.

        Notes are compiled to html so
        the extension will be `.html`.
        """
        build_path = self.build_path_for_path(path)
        base, ext = os.path.splitext(build_path)
        return base + '.html', ext

    def build_path_for_path(self, path):
        """
        Returns a build path
        for a given path.
        """
        if '.build' not in path:
            path = self.normalize_path(path)
            path = path.replace(self.notes_path, self.build_path)
        return path

    def normalize_path(self, path):
        """
        Normalizes a directory path
        so that it has a trailing slash and
        groups of slashes are compressed.
        
        i.e. 'A///B' => 'A/B/'
        """
        path = os.path.normpath(path)
        if os.path.isdir(path):
            path = os.path.join(path, '')
        return path

    def _write_index(self, path, dirs, files):
        """
        Write an `index.html` file
        at the specified path,
        listing the specified dirs and files.
        """
        crumbs = self._build_breadcrumbs(path)
        rendered = index_templ.render(dirs=dirs, files=files, crumbs=crumbs)

        if not os.path.exists(path):
            os.makedirs(path)

        with open( os.path.join(path, 'index.html'), 'w' ) as index:
            index.write(rendered.encode('utf-8'))

    def _build_breadcrumbs(self, path):
        # Get rid of the build path.
        path = path.replace(self.build_path, '')

        # Create some name for the root notebook.
        path = os.path.join('notes', path)

        # Split the path into the crumbs.
        # Filter out any empty crumbs.
        crumbs = filter(None, path.split('/'))

        # Remove the file extension from the last crumb.
        crumbs[-1], _ = os.path.splitext(crumbs[-1])

        return crumbs

    def _rewrite_link(self, path, build_path):
        # Build the relative base path for the note's references.
        note_dir = os.path.split(path.replace(self.notes_path, ''))[0]
        note_build_dir = build_path.replace(self.notes_path, '')
        dirs_up = len(note_build_dir.split('/')) - 1
        base_path = os.path.join(('../'*dirs_up), note_dir, '')

        def rewriter(link):
            # Ignore external, absolute, and hash links.
            if not link.startswith(('http', '/', '#')):
                root, ext = os.path.splitext(link)

                # Update references to non-note files
                # so that they point outside the build directory.
                if ext not in ['.html', '.md']:
                    return os.path.join(base_path, link)

                elif ext == '.md':
                    return root + '.html'
            return link
        return rewriter
