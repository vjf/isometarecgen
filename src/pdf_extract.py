#!/usr/bin/env python3

import os
import sys
import requests
import json
from pathlib import Path
import datetime
import geojson
from datetime import date

# NB: If you import from 'iso_19115_1' you get MD_MetaData, 'iso_19115_2' will give you instrument MI_Metadata
from bas_metadata_library.standards.iso_19115_1 import MetadataRecordConfigV2, MetadataRecord
from pdf_helper import parse_pdf

from extractor import Extractor
from keywords import get_keywords
from summary import get_summary
from add_links import add_model_link
from add_coords import add_coords

class PDFExtractor(Extractor):

    def get_record_config(self, keywords, summary, organisation, title, bbox, model_endpath):
        now = datetime.datetime.now()
        current_date = datetime.date(year=now.year, month=now.month, day=now.day)
        keyw_terms = [{"term": keyw} for keyw in keywords]
        record_config = {
            "hierarchy_level": "dataset",
            "metadata": {
                "language": "eng",
                "character_set": "utf-8",
                "contacts": [{"organisation": {"name": organisation}, "role": ["pointOfContact"]}],
                "date_stamp": current_date,
            },
            "identification": {
                "title": {"value": title},
                "dates": {"creation": {"date": current_date, "date_precision": "year"}},
                "abstract": summary,
                "character_set": "utf-8",
                "language": "eng",
                "topics": ['geoscientificInformation'],
                # NB: bas-metadata-library does not appear to output bboxes
                "extent": {
                    "geographic": {
                        "bounding_box": {
                            "west_longitude": bbox['west'],
                            "east_longitude": bbox['east'],
                            "south_latitude": bbox['south'],
                            "north_latitude": bbox['north'],
                        }
                    }
                },
                "status": "completed",
                "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
                "keywords": [{"terms": keyw_terms, "type": "theme"},
                    {"terms": [{"term":"Auscope 3D Geological Models"}], "type": "theme"}],
                "constraints": [
                    {
                        "type": "usage",
                        "restriction_code": "license",
                        "statement": "Creative Commons Attribution 4.0 International Licence",
                        "href": "http://creativecommons.org/licenses/"
                    }
                ],
            },
        }
        return record_config



    def write_record(self, name, model_endpath, pdf_file, organisation, title, bbox, cutoff, pdf_url=None):
        print(f"Converting: {model_endpath}")
        #print("bbox=", repr(bbox))
        if not os.path.exists(pdf_file):
            print(f"{pdf_file} does not exist")
            sys.exit(1)
        # Extract keywords from PDF text
        pdf_text = parse_pdf(pdf_file, False)
        #print(f"write_record {model_endpath} {len(pdf_text)=}")
        kwset = get_keywords(pdf_text)
        #print("kwset=", kwset)
        summary = get_summary(pdf_file, cutoff)
        #kwset = set(['kw1','kw2','kw3'])
        #summary = 'summary summary summary'
        record_config = self.get_record_config(list(kwset), summary, organisation, title, bbox, model_endpath)
        configuration = MetadataRecordConfigV2(**record_config)
        record = MetadataRecord(configuration=configuration)
        document = record.generate_xml_document()
        # bas-metadata-library does not output BBOX coords nor URL links so I have to do it manually
        xml_txt = add_coords(bbox, model_endpath, document.decode(), 'utf-8', 'ISO19139')
        # This writes out the file
        add_model_link(model_endpath, xml_txt)


if __name__ == "__main__":
    pe = PDFExtractor()
    pe.write_record("test-pdf", "https://blah/blah.pdf")
