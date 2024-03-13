"""search a collection of PDFs for keyterm hits"""

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
        if isinstance(x, (list, tuple)):
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

# %% keyterm & pdf I/O
path_docs = path_proj / 'docs'
fpaths_pdf = list(path_docs.glob('**/*.pdf'))
print(f'PDFs found: {len(fpaths_pdf)}')

fpath_kt = path_proj / 'keyterms.csv'
df_kw = pd.read_csv(fpath_kt)

kt_dict = {a: split_term_set(t)
           for a,t in zip(df_kw.abbv_or_alias, df_kw.term)}
kt_full = flatten(kt_dict.values())
kt_abbv = kt_dict.keys()

# pd.DataFrame approach
# kt_full = expand_keyterms(df_kw.term)  # list of keyterms
# kt_abbv = expand_keyterms(df_kw.abbv_or_alias)  # list of keyterms

# %% search
t_s = tpc()  # start time
hits = []
for fpath in fpaths_pdf:
    doc = PdfReader(fpath)
    for page_num, page in enumerate(doc.pages, start=1):
        page_text = page.extract_text()
        hits_abbv = search_page(kt_abbv, page_text, keep_case=True)
        hits_kt = search_page(kt_full, page_text)
        hits_page = hits_abbv + hits_kt
        if hits_page:
            hits.extend([(fpath, term, page_num, freq)
                         for term, freq in hits_page])        
    label_time(f'Search time, {fpath.name}', t_s)

# TODO: cache doc-kt hits

# %% tidy metadata
def get_first_docs_subdir(fpath):
    return fpath.parent.relative_to(path_docs).parts[0].rstrip('s')

df = (pd.DataFrame(hits, columns=['fpath', 'key_term', 'page_num', 'freq'])
        .assign(fname=lambda _df: _df.fpath.apply(lambda f: f.name),
                is_original=lambda _df: (_df.fpath.astype(str)
                                                  .str.contains('Original')),
                ftype=lambda _df: _df.fpath.apply(get_first_docs_subdir))
        .drop(columns=['fpath']))

# %% summarize
kt_ord = list(flatten(kt_dict.items())) + ['All']
df_summ = (df.pivot_table(values='freq', columns='key_term',
                          aggfunc='sum', margins=True,
                          index=['fname', 'ftype', 'is_original'])
             .drop(index='All', level='fname')
             .reindex(columns=kt_ord)  # reorder kt cols
             .dropna(axis='columns', how='all')
             .reset_index()
             .sort_values(by=['ftype', 'All'], ascending=[True, False]))

# %% write output
fpath_out = path_proj / f'output_{fpath_kt.stem}.xlsx'
with pd.ExcelWriter(fpath_out) as ew:
    args = {'excel_writer': ew, 'index': False}
    df_summ.to_excel(sheet_name='Summary', **args)
    df.to_excel(sheet_name='Results', **args)


# %% future improvements

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


# %% nested dict approaches

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
