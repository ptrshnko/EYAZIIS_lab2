import os
import json
import logging
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
TOKENS_DIR = os.path.join(BASE_DIR, 'data', 'tokens')
METADATA_PATH = os.path.join(BASE_DIR, 'data', 'metadata', 'metadata.json')

# Initialize Natasha tools
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

def tokenize_and_store():
    """Tokenize texts and store tokens with morphological analysis in JSON files"""
    try:
        os.makedirs(TOKENS_DIR, exist_ok=True)
        
        # Load metadata
        if not os.path.exists(METADATA_PATH):
            logger.error("Metadata file not found. Run corpus_loader first.")
            raise FileNotFoundError("Metadata file not found")
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if not metadata:
            logger.error("Metadata is empty. No documents to process.")
            raise ValueError("Metadata is empty")
        
        for doc_id, meta in metadata.items():
            path_txt = meta['path_txt']
            if not os.path.exists(path_txt):
                logger.error(f"File not found: {path_txt}")
                continue
                
            try:
                with open(path_txt, encoding='utf-8') as f:
                    text = f.read()
                logger.info(f"Read text file: {path_txt}")
            except Exception as e:
                logger.error(f"Error reading file {path_txt}: {e}")
                continue
                
            # Process with Natasha
            try:
                nat_doc = Doc(text)
                nat_doc.segment(segmenter)
                nat_doc.tag_morph(morph_tagger)
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                continue
                
            tokens = []
            token_count = 0
            for sent_id, sent in enumerate(nat_doc.sents, start=1):
                for token in sent.tokens:
                    try:
                        token.lemmatize(morph_vocab)
                        tokens.append({
                            'doc_id': int(doc_id),
                            'sent_id': sent_id,
                            'token_id': token_count + 1,
                            'token': token.text,
                            'lemma': token.lemma or 'Неизвестно',
                            'pos': token.pos or 'Неизвестно',
                            'grammems': ','.join(f'{k}={v}' for k, v in token.feats.items()) or 'Нет граммем'
                        })
                        token_count += 1
                    except Exception as e:
                        logger.error(f"Error processing token: {e}")
                        continue
            
            # Save tokens
            token_path = os.path.join(TOKENS_DIR, f'doc_{doc_id}.json')
            try:
                with open(token_path, 'w', encoding='utf-8') as f:
                    json.dump(tokens, f, ensure_ascii=False, indent=2)
                logger.info(f'Saved {token_count} tokens for document {doc_id}: {token_path}')
            except Exception as e:
                logger.error(f"Error saving tokens for document {doc_id}: {e}")
                continue
        
        logger.info("Tokenization completed successfully")
    except Exception as e:
        logger.error(f"Critical error during tokenization: {e}")
        raise

if __name__ == '__main__':
    tokenize_and_store()