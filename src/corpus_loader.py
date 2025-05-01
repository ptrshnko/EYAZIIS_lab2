import os
import json
import logging
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from striprtf.striprtf import rtf_to_text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
METADATA_DIR = os.path.join(BASE_DIR, 'data', 'metadata')
METADATA_PATH = os.path.join(METADATA_DIR, 'metadata.json')

def init_directories():
    """Initialize required directories"""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLEANED_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    if not os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    logger.info("Directories initialized")

def convert_file(filepath):
    """Convert file to text"""
    try:
        ext = filepath.lower().rsplit('.', 1)[-1]
        if ext == 'txt':
            with open(filepath, encoding='utf-8') as f:
                return f.read()
        elif ext == 'pdf':
            text = []
            reader = PdfReader(filepath)
            for page in reader.pages:
                text.append(page.extract_text() or '')
            return '\n'.join(text)
        elif ext == 'docx':
            doc = DocxDocument(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)
        elif ext == 'rtf':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return rtf_to_text(f.read())
        elif ext == 'doc':
            logger.warning("DOC format requires external tools (e.g., antiword). Skipping.")
            return ''
        else:
            logger.warning(f"Unsupported file format: {filepath}")
            return ''
    except Exception as e:
        logger.error(f"Error converting file {filepath}: {e}")
        return ''

def import_corpus():
    """Import corpus files into the file system"""
    try:
        init_directories()
        
        # Check if raw directory is empty
        if not os.listdir(RAW_DIR):
            logger.error("No files found in data/raw. Please add text files to process.")
            raise ValueError("No files found in data/raw")
        
        # Load existing metadata
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        doc_id = max([int(k) for k in metadata.keys()] + [0]) + 1
        
        for fname in os.listdir(RAW_DIR):
            path_raw = os.path.join(RAW_DIR, fname)
            if not os.path.isfile(path_raw):
                continue
                
            text = convert_file(path_raw)
            if not text.strip():
                logger.warning(f"Empty text in file: {fname}")
                continue
                
            # Save cleaned text
            base, _ = os.path.splitext(fname)
            txt_name = base + '.txt'
            path_txt = os.path.join(CLEANED_DIR, txt_name)
            
            try:
                with open(path_txt, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"Saved cleaned text: {path_txt}")
            except Exception as e:
                logger.error(f"Error saving text {path_txt}: {e}")
                continue
                
            # Update metadata
            metadata[str(doc_id)] = {
                'filename': fname,
                'path_raw': path_raw,
                'path_txt': path_txt,
                'title': text.splitlines()[0][:200],
                'date': ''  # Optional date field
            }
            logger.info(f"Added metadata for document {doc_id}: {fname}")
            doc_id += 1
        
        # Save metadata
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("Corpus import completed successfully")
    except Exception as e:
        logger.error(f"Critical error during corpus import: {e}")
        raise

if __name__ == '__main__':
    import_corpus()