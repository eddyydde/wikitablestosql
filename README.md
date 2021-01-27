# WikitablesToSQL

WikitablesToSQL extracts and parses the raw wikitables from the multistream database dump of the English Wikipedia and processes them into a sqlite3 database.


## Requirements

- Python >= 3.5
- defusedxml


## Installation
Make sure `git` is in PATH and run

```console
python -m pip install git+https://github.com/eddyydde/wikitablestosql#egg=wikitablestosql
```


## Usage
```console
wikitablestosql /path/to/wikipedia_dump_folder
```

For example, if we want to process one of the 2020-12-20 English Wikipedia multistream database dumps (articles, templates, media/file descriptions, and primary meta-pages, in multiple bz2 streams, 100 pages per stream) which can be found at <https://dumps.wikimedia.org/enwiki/20201220/>, wikipedia_dump_folder should contain

```
enwiki-20201220-pages-articles-multistream1.xml-p1p41242.bz2
enwiki-20201220-pages-articles-multistream-index1.txt-p1p41242.bz2
enwiki-20201220-pages-articles-multistream2.xml-p41243p151573.bz2
enwiki-20201220-pages-articles-multistream-index2.txt-p41243p151573.bz2
...
enwiki-20201220-pages-articles-multistream27.xml-p65475910p66163728.bz2
enwiki-20201220-pages-articles-multistream-index27.txt-p65475910p66163728.bz2
```

### Output
The output filename will be of the form

> enwiki-*YYYYMMDD*-pages-articles-multistream.db

so for the given example we will obtain

> enwiki-20201220-pages-articles-multistream.db

The database will contain the following 2 tables:

- WikitableInformation, having the following columns:
	- page_name
	- table_name
	- table_attributes
	- caption
	- caption_attributes
- WikitableData, having the following columns:
	- table_name
	- row
	- col
	- cell_data
	- cell_attributes
	- is_header
	- row_span
	- col_span
	
