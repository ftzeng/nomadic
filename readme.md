# nomadic

I wasn't able to find a satisfactory way to use Evernote in Linux,
which led me to reconsider my Evernote usage in general.

`nomadic` leverages other tools I use daily to create a replacement
for my Evernote usage.

`nomadic` supports a simple directory structure of HTML, Markdown, txt, and
pdf notes and any other files which may need to be referenced. nomadic
provides an easier way of searching through and browsing those files.

For example:

```bash
notes
├── economics
│   ├── more economics notes.pdf
│   ├── my economics notes.md
│   └── my economics notes.resources
│       └── some image.png
├── programming
│   └── scala guide.html
└── some note.md
```

Here are some useful tools to go with `nomadic`:
* [BitTorrent Sync](www.bittorrent.com/sync) to keep notes synced across devices.
* [Vim](http://www.vim.org/) with:
    * [vim-instant-markdown](https://github.com/suan/vim-instant-markdown) to have live previews
    of Markdown files as you edit them.
    * my fork of the [instant-markdown-d](https://github.com/ftzeng/instant-markdown-d) backend for
    vim-instant-markdown (supports MathJax and relative image references)

With these tools, `nomadic` becomes a decentralized, simplified alternative to Evernote.

Powerusers of Evernote might find it lacking but it's not for them :)

---

## Setup

### Installation
```bash
$ git clone https://github.com/ftzeng/nomadic.git
$ cd nomadic
$ pip install .
```

### Configuration
Create a config file (optional) at `~/.nomadic` in JSON format. See
[Configuration](#configuration) for more details.
If you don't create this config file, `nomadic` will create one for
you.


### The Daemon
The daemon watches your notes directory and automatically updates
the index and compiles notes when they change.
It will also automatically update references to other notes as they
change.

To get the `nomadic` daemon to run automatically on startup...

#### Linux (Upstart)
If you're on a Linux distro that uses Upstart, you can do:
```bash
$ sudo cp scripts/nomadic.conf /etc/init/nomadic.conf
```
Then you can start the daemon:
```bash
$ sudo start nomadic
```

#### OSX
If you're on a Linux distro that uses Upstart, you can do:
If you're on OSX, you can do:
```bash
$ cp scripts/com.nomadic.plist ~/Library/LaunchAgents/com.nomadic.plist
```
Then you can start the daemon:
```bash
$ launchctl load ~/Library/LaunchAgents/com.nomadic.plist 
```

### Extras
There's also an additional script which will setup
the dependencies for `vim-instant-markdown`.
```bash
$ ./scripts/install-instant-markdown.sh
```

---

## Configuration
`nomadic` checks for a configuration at `~/.nomadic`. If you
start `nomadic` without a config, one will be created for you.

For example:
```json
{
    "notes_dir": "~/Notes"
}
```

Whenever you change this file, you must restart
the `nomadic` daemon:

```bash
# Linux (Upstart)
$ sudo restart nomadic

# OSX (there might be a better way)
$ pkill -f nomadic-d
$ launchctl start com.nomadic
```


---

## Usage
Run the `nomadic` daemon if it isn't running already.

```bash
$ nomadic-d
```


Primary interaction with `nomadic` is through
the command line.

```bash
$ nomadic --help

Usage: nomadic [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  browse  Browse through notes via a web browser.
  build   Re-build the browsable tree.
  count   Get the number of notes.
  index   Update or reset the note index.
  search  Search through notes.
```

### Browsing notes
The `nomadic` daemon compiles your notes into a browsable local
HTML structure as they change.

It compiles only HTML and Markdown notes.

References to local files are made relative
to the build directory, so no
extra files are redundantly copied over.

You can browse this structure by running:
```bash
$ nomadic browse
```
which opens up the root directory ('notebook') in your
default web browser.

You can immediately jump to a specific notebook by
passing its name in:
```bash
$ nomadic browse economics
```

If the specified name matches multiple notebooks,
you'll be given the option to select the right one.

### Searching notes
The `nomadic` daemon will maintain a search index
for your notes as you update them.

You can search through your notes by running:
```bash
$ nomadic search <query>
```

This will present a list of results, along with snippets where the
keyword was found, for you to choose from.

`nomadic` can search through HTML, Markdown, txt, and pdf
files.

---

## Development
```bash
$ git clone https://github.com/ftzeng/nomadic.git
$ cd nomadic
$ pip install --editable .
```

This installs the package locally, allowing you to work on it and test
it easily.

To run the included tests:
```bash
$ pip install nose
$ nosetests test
```

---

## To Do
* better css stylesheet

I'm still testing this out personally to
work out the kinks but eventually I want to
release platform-specific distributions:

* OSX => [Homebrew](https://github.com/Homebrew/homebrew/wiki/Formula-Cookbook)
* Debian-based distros => `.deb` package

These will handle the setting up of the daemon for you.

---

## Shortcomings (future to dos?)
* You have to premeditate syncing. That is, with Evernote, you can
log into your Evernote account from any computer and access your
notes without needing to set anything up beforehand. To access `nomadic`
notes, you must sync them beforehand.
* It's very easy to copy and paste HTML into Evernote and preserve the
formatting. There is not yet an easy workflow for the same in `nomadic`.

---

## Acknowledgements
The CSS stylesheet used for the compiled notes is based on the one from [here](https://gist.github.com/tuzz/3331384).