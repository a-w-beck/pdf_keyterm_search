"""search a collection of PDFs for keyword hits"""
from pathlib import Path
from time import perf_counter as tpc

import pandas as pd
from pypdf import PdfReader

path_proj = Path(__file__).parent

# %% funcs
def label_time(label, time_start):
    print(f'{label+", [sec]:":<40}{(tpc() - time_start):>10.1f}')
    
def flatten(xs):
    for x in xs:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x

def split_term_set(term):
    if isinstance(term, float): # if np.nan
        return term
    if term.startswith('{'):
        y, x = term.lstrip('{').split('}')
        return [f'{z}{x}' for z in y.split(', ')]
    elif term.endswith('}'):
        x, y = term.rstrip('}').split(' {')
        return [f'{x} {z}' for z in y.split(', ')]
    else:
        return term

def expand_keyterms(terms: pd.Series):
    terms = flatten([split_term_set(x) for x in terms.dropna()])
    return list(terms)
    
def search_page(
        terms: list[str], 
        page_text: str, 
        keep_case: bool = False,
        ) -> list:
    if not keep_case:
        page_text = page_text.lower()
    hits = []
    for term in terms:
        if term in page_text:  # simple substring search
            hits.append([term, page_text.count(term)])
    return hits


# %% keyword & pdf I/O
path_docs = path_proj / 'docs'
fpaths_pdf = list(path_docs.glob('**/*.pdf'))
print(f'PDFs found: {len(fpaths_pdf)}')

fname_kt_input = 'keyterms.csv'
df_kw = pd.read_csv(path_proj / 'keywords.csv')
kt_full = expand_keyterms(df_kw.term)  # list of key-terms
kt_abbv = expand_keyterms(df_kw.abbv_or_alias)  # list of key-terms
# kt_all = kt_full + kt_abbv


# %% search
time_start = tpc()
hits = []
for fpath in fpaths_pdf:
    doc = PdfReader(fpath)
    doc_name = fpath.name    
    for page_num, page in enumerate(doc.pages, start=1):
        page_text = page.extract_text()
        hits_abbv = search_page(kt_abbv, page_text, keep_case=True)
        hits_kt = search_page(kt_full, page_text)
        hits_page = hits_abbv + hits_kt
        if hits_page:
            hits.extend([(doc_name, term, page_num, freq) 
                         for term, freq in hits_page])        
    label_time(f'Search time, {doc_name}', time_start)  # !!!: 8s per doc, all kw

# %%
df = pd.DataFrame(data=hits, columns=['file', 'key_term', 'page_num', 'freq'])
df.to_csv(path_proj / f'output_{fname_kt_input}', index=False)

# pd.Series([y for (x, y) in kt_hits.keys]).value_counts()
# set([y for (x, y, z) in kt_hits if z == "LCA"])



# %% Future Improvements

# TODO: [speed] on doc read, tokenize each page 
    # search over token sets >>> substring search

    # ???: partial matching (e.g. WBLCA --> LCA) in sets/token collections\
        # !!!: lots of substring matching is slow
        # Only an issue for abbreviations + short/single-word terms
        # ???: any way to use kt_abbv values in tokenization?
        
# ???: implement pdf bundle (corpus?) as dataclass?
    # from dataclasses import dataclass
    # @dataclass
    # class doc_pdf: 


# %% dict experiments

# !!!: dict.update() bad w/ nested dict, overwrites via top-level key

# hits = {}; 
# hits[fname][abbv][pagenum] = page_text.count(abbv)

# possible schema {fname: {term: {page_num: freq}}

# from collections import defaultdict
# kt_hits = defaultdict(list)
# kt_hits = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

# def rec_dd():
#     return defaultdict(rec_dd)
# x = rec_dd()
# x['a']['b']['c']['d'] = {1}
