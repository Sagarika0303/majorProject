import os
import multiprocessing as mp
import io
import spacy
import pprint
from spacy.matcher import Matcher
from . import utils
from App import utils_override
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.layout import LAParams, LTTextBoxHorizontal, LTTextLineHorizontal

class ResumeParser(object):

    def __init__(
        self,
        resume,
        skills_file=None,
        custom_regex=None
    ):
        nlp = spacy.load('en_core_web_sm')
        custom_nlp = spacy.load("en_core_web_sm")
        self.__skills_file = skills_file
        self.__custom_regex = custom_regex
        self.__matcher = Matcher(nlp.vocab)
        self.__details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'degree': None,
            'no_of_pages': None,
        }
        self.__resume = resume
        
        # Check for the existence of the config.cfg file
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.cfg')
        if not os.path.isfile(config_path):
            raise FileNotFoundError("Configuration file 'config.cfg' is required but was not found. Please ensure it is located in the same directory as this script.")


        if not isinstance(self.__resume, io.BytesIO):
            ext = os.path.splitext(self.__resume)[1].split('.')[1]
        else:
            ext = self.__resume.name.split('.')[1]
        self.__text_raw = utils.extract_text(self.__resume, '.' + ext)
        self.__text = ' '.join(self.__text_raw.split())
        self.__nlp = nlp(self.__text)
        self.__custom_nlp = custom_nlp(self.__text_raw)
        self.__noun_chunks = list(self.__nlp.noun_chunks)
        self.__get_basic_details()

    def get_extracted_data(self):
        return self.__details

    def extract_name_from_pdf_layout(self):
        # Extract name based on largest font size and centered text on first page
        try:
            if isinstance(self.__resume, io.BytesIO):
                fp = self.__resume
                fp.seek(0)
            else:
                fp = open(self.__resume, 'rb')
            resource_manager = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(resource_manager, laparams=laparams)
            interpreter = PDFPageInterpreter(resource_manager, device)
            for page_number, page in enumerate(PDFPage.get_pages(fp)):
                if page_number > 0:
                    break  # Only first page
                interpreter.process_page(page)
                layout = device.get_result()
                candidates = []
                for element in layout:
                    if isinstance(element, (LTTextBoxHorizontal, LTTextLineHorizontal)):
                        text = element.get_text().strip()
                        if text:
                            # Heuristic: consider text with large font size and near center (approximate)
                            # pdfminer does not provide font size directly, so use height of bbox
                            bbox = element.bbox  # (x0, y0, x1, y1)
                            height = bbox[3] - bbox[1]
                            x_center = (bbox[0] + bbox[2]) / 2
                            y_center = (bbox[1] + bbox[3]) / 2
                            candidates.append((text, height, x_center, y_center))
                # Sort candidates by height descending (largest font size)
                candidates.sort(key=lambda x: x[1], reverse=True)
                # Filter candidates near vertical center of page (assuming page height ~792 pts)
                page_height = 792
                center_candidates = [c for c in candidates if abs(c[3] - page_height/2) < 200]
                if center_candidates:
                    # Return the text of the largest font size near center
                    return center_candidates[0][0]
                elif candidates:
                    return candidates[0][0]
                else:
                    return None
        except Exception as e:
            return None

    def __get_basic_details(self):
        cust_ent = utils.extract_entities_wih_custom_model(
                            self.__custom_nlp
                        )
        name = utils_override.extract_name(self.__nlp, matcher=self.__matcher)

        # Validate extracted name to avoid common location names or invalid values
        invalid_names = {'hyderabad', 'bangalore', 'chennai', 'delhi', 'mumbai', 'kolkata', 'pune', 'gurgaon', 'noida', 'india', 'telangana', 'karnataka',
                         'education', 'skills', 'experience', 'projects', 'internship', 'internships', 'work', 'company', 'organization', 'organizations', 'email', 'phone', 'contact'}
        
        def is_invalid_name(n):
            if not n:
                return True
            n_lower = n.lower()
            if n_lower in invalid_names:
                return True
            # Check if name contains unwanted keywords
            for invalid_word in invalid_names:
                if invalid_word in n_lower:
                    return True
            # Check if name is a single word and matches a location pattern
            if len(n.split()) == 1 and n_lower in invalid_names:
                return True
            # Check if name is too short or contains digits
            if len(n) < 2 or any(char.isdigit() for char in n):
                return True
            return False

        email = utils.extract_email(self.__text)
        mobile = utils.extract_mobile_number(self.__text, self.__custom_regex)
        skills = utils.extract_skills(
                    self.__nlp,
                    self.__noun_chunks,
                    self.__skills_file
                )

        entities = utils.extract_entity_sections_grad(self.__text_raw)

        # extract name
        try:
            cust_name = cust_ent['Name'][0]
            print(f"DEBUG: cust_name extracted: {cust_name}")
            print(f"DEBUG: name extracted: {name}")
            if is_invalid_name(cust_name):
                if is_invalid_name(name):
                    # Try PDF layout based extraction as fallback
                    pdf_name = self.extract_name_from_pdf_layout()
                    print(f"DEBUG: pdf_name extracted: {pdf_name}")
                    if is_invalid_name(pdf_name):
                        self.__details['name'] = None
                        print("DEBUG: All name extraction methods invalid, setting name to None")
                    else:
                        self.__details['name'] = pdf_name
                        print(f"DEBUG: Using pdf_name: {pdf_name}")
                else:
                    self.__details['name'] = name
                    print(f"DEBUG: Using name: {name}")
            else:
                self.__details['name'] = cust_name
                print(f"DEBUG: Using cust_name: {cust_name}")
        except (IndexError, KeyError):
            print(f"DEBUG: cust_name not found, name extracted: {name}")
            if is_invalid_name(name):
                pdf_name = self.extract_name_from_pdf_layout()
                print(f"DEBUG: pdf_name extracted: {pdf_name}")
                if is_invalid_name(pdf_name):
                    self.__details['name'] = None
                    print("DEBUG: All name extraction methods invalid, setting name to None")
                else:
                    self.__details['name'] = pdf_name
                    print(f"DEBUG: Using pdf_name: {pdf_name}")
            else:
                self.__details['name'] = name
                print(f"DEBUG: Using name: {name}")

        # extract email
        self.__details['email'] = email

        # extract mobile number
        self.__details['mobile_number'] = mobile

        # extract skills
        self.__details['skills'] = skills

        # no of pages
        self.__details['no_of_pages'] = utils.get_number_of_pages(self.__resume)

        # extract education Degree
        try:
            self.__details['degree'] = cust_ent['Degree']
        except KeyError:
            pass

        return


def resume_result_wrapper(resume):
    parser = ResumeParser(resume)
    return parser.get_extracted_data()


if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())

    resumes = []
    data = []
    for root, directories, filenames in os.walk('resumes'):
        for filename in filenames:
            file = os.path.join(root, filename)
            resumes.append(file)

    results = [
        pool.apply_async(
            resume_result_wrapper,
            args=(x,)
        ) for x in resumes
    ]

    results = [p.get() for p in results]

    pprint.pprint(results)
