"""
Extractor
=======================

Extracts data from note files.
"""

from StringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def pdf_text(pdf_file):
    rsrcmgr = PDFResourceManager(caching=True)
    outp = StringIO()
    device = TextConverter(rsrcmgr, outp, codec='utf-8', laparams=LAParams())
    with open(pdf_file, 'rb') as f:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(f, set(), maxpages=0, caching=True, check_extractable=True):
            interpreter.process_page(page)
    device.close()
    text = outp.getvalue()
    outp.close()
    return text.strip().decode('utf-8')
