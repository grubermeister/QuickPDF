#!/usr/bin/python
import os, sys, codecs, locale, glob, json, re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer import pdfparser, pdfdocument
from io import StringIO, BytesIO
from string import ascii_letters, digits
from collections import OrderedDict


def acroform(doc):
	return doc.catalog['AcroForm']
	
def xfa(form):
	return form.resolve()['XFA']
	
def evens(alist):
	return alist[::2]

def odds(alist):
	return alist[1::2]

def xfa_alist(xfa):
	return zip(evens(xfa), odds(xfa))

def xfa_dict(xfa):
	return OrderedDict(xfa_alist(xfa))

def stream_raw_data(stream):
	return stream.resolve().get_data()

def stripHTML(ret, wantWhite=False):
    """Strip away unwanted HTML artifacts."""

    # Fix because Python3 sees the returned request as a bytestream, not a string anymore.
    if isinstance(ret, bytes):
        ret = ret.decode(encoding='utf-8', errors='replace')

    ret = re.sub(r"(<!--.*?-->|<[^>]*>)", '', ret)
    ret = re.sub(r"(&nbsp;|&raquo;)", '', ret)
    ret = re.sub(r"&amp;", '&', ret)

    if not wantWhite:
        ret = re.sub("\s+", ' ', ret)  # We don't always want to normalize white space
    return ret

def getfirstpage(path):
	rsrcmgr     = PDFResourceManager()
	retstr      = BytesIO()
	codec       = "utf-8"
	laparams    = LAParams()
	password    = ''
	maxpages    = 0
	caching     = True
	pagenos     = set()
	device      = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	fp          = open(path, "rb")
	text        = ''
	
	for idx,page in enumerate(PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,
                                  caching=caching, check_extractable=True)):
		interpreter.process_page(page)
		text += ''.join([ch for ch in retstr.getvalue().decode("utf-8") if ch in (ascii_letters + digits + ' ' + '/')])
		if idx == 10:  break

	fp.close()
	device.close()
	retstr.close()
    
	return text
	
def parseXFA(path):
	with open(path, "rb") as pdf_file:
		text = ''
		parser = pdfparser.PDFParser(pdf_file)
		document = pdfdocument.PDFDocument(parser)
		tempy = json.dumps(
			[
				str( (k, stream_raw_data(v)) )
				for (k,v) in xfa_alist(xfa(acroform(document)))
			], indent=4,
		)
		text += ''.join([ch for ch in tempy if ch in (ascii_letters + digits + ' ' + '/')])
		
	return stripHTML(text)

def main(argv):
	if len(argv) == 1 or argv == '' or argv == None:
		os.chdir("C:\DIBBS")
		argc = glob.glob('*.pdf')
		for i,f in enumerate(argc):  argc[i] = f.split('.')[0]
		argc = list(set(argc))
		for i,f in enumerate(argc):  argc[i] = f + ".pdf"
	else:
		argc = [argv[1]]
	for doc in argc:
		#if os.path.exists((doc + ".txt")):  continue
		#else:
		rawDoc = getfirstpage(doc)
			
		if len(rawDoc) == 0:
			rawDoc = parseXFA(doc)

		newDoc = open((doc + ".txt"), 'w')
		try:
			newDoc.write(rawDoc); print(rawDoc)
		except:
			pass
	
		newDoc.close()
	
if __name__ == '__main__':
	main(sys.argv)
