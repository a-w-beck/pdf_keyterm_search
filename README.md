# pdf_keyterm_search
Simple script to search for a collection of key-terms and abbreviations across a bundle of PDFs.

Create the project environment via conda + [env_pdf_kt.yaml](env_pdf_kt.yaml), 
or adapt the YAML contents to a requirements.txt and use `venv`, `poetry`, etc.

Drop one or more PDF files and/or folders thereof into the `docs` directory, then run the script.

Returns a CSV with `file` name, `key_term`, `page_num`, and `freq`uency values, 
where `freq` quantifies the number of `key_term` matches on a given `file`'s `page_num`.