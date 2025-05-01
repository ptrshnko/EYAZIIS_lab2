import os
import json
import logging
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_DIR = os.path.join(BASE_DIR, 'data', 'tokens')
METADATA_PATH = os.path.join(BASE_DIR, 'data', 'metadata', 'metadata.json')

class CorpusManager:
    def __init__(self):
        """Initialize corpus manager"""
        self.metadata = {}
        try:
            if not os.path.exists(METADATA_PATH):
                logger.error("Metadata file not found. Run corpus_loader first.")
                raise FileNotFoundError("Metadata file not found")
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            if not self.metadata:
                logger.error("Metadata is empty. No documents available.")
                raise ValueError("Metadata is empty")
            logger.info(f"Corpus manager initialized with {len(self.metadata)} documents")
        except Exception as e:
            logger.error(f"Error initializing corpus manager: {e}")
            raise

    def load_tokens(self, doc_ids=None):
        """Load tokens from JSON files"""
        tokens = []
        doc_ids = [int(did) for did in self.metadata.keys()] if doc_ids is None else doc_ids
        for doc_id in doc_ids:
            token_path = os.path.join(TOKENS_DIR, f'doc_{doc_id}.json')
            if os.path.exists(token_path):
                try:
                    with open(token_path, 'r', encoding='utf-8') as f:
                        doc_tokens = json.load(f)
                        tokens.extend(doc_tokens)
                    logger.debug(f"Loaded tokens for doc {doc_id}: {len(doc_tokens)} tokens")
                except Exception as e:
                    logger.error(f"Error loading tokens for doc {doc_id}: {e}")
            else:
                logger.warning(f"Token file not found for doc {doc_id}: {token_path}")
        if not tokens:
            logger.warning("No tokens loaded. Check token files in data/tokens.")
        return tokens

    def get_frequency(self, query, by='token', filters=None):
        """
        Count frequencies for tokens, lemmas, or POS.
        :param query: search string (token or lemma)
        :param by: 'token', 'lemma', or 'pos'
        :param filters: dict with keys 'pos', 'date_from', 'date_to', 'doc_ids'
        :return: Counter
        """
        try:
            logger.info(f"Running frequency analysis for query='{query}', by='{by}', filters={filters}")
            tokens = self.load_tokens(filters.get('doc_ids') if filters else None)
            if not tokens:
                logger.error("No tokens available for frequency analysis")
                return Counter()
            
            counter = Counter()
            for token in tokens:
                if token[by].lower() != query.lower():
                    continue
                if filters:
                    if 'pos' in filters and token['pos'] != filters['pos']:
                        continue
                    if 'date_from' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date < filters['date_from']:
                            continue
                    if 'date_to' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date > filters['date_to']:
                            continue
                counter[token[by]] += 1
            
            logger.info(f"Frequency analysis completed: {counter}")
            return counter
        except Exception as e:
            logger.error(f"Error calculating frequency: {e}")
            return Counter()

    def get_global_frequency(self, by='token', filters=None):
        """
        Count global frequency of all elements of the specified type.
        :param by: 'token', 'lemma', or 'pos'
        :param filters: same as get_frequency
        :return: Counter
        """
        try:
            logger.info(f"Running global frequency analysis by='{by}', filters={filters}")
            tokens = self.load_tokens(filters.get('doc_ids') if filters else None)
            if not tokens:
                logger.error("No tokens available for global frequency analysis")
                return Counter()
            
            counter = Counter()
            for token in tokens:
                if filters:
                    if 'pos' in filters and token['pos'] != filters['pos']:
                        continue
                    if 'date_from' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date < filters['date_from']:
                            continue
                    if 'date_to' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date > filters['date_to']:
                            continue
                counter[token[by]] += 1
            
            logger.info(f"Global frequency analysis completed: {len(counter)} unique elements")
            return counter
        except Exception as e:
            logger.error(f"Error calculating global frequency: {e}")
            return Counter()

    def get_concordance(self, query, window=5, filters=None):
        """
        KWIC: contexts around query.
        :param query: search string (token or lemma)
        :param window: number of tokens before and after
        :param filters: dict as above
        :return: list of (left_context, match, right_context, doc_id, sent_id)
        """
        try:
            logger.info(f"Running concordance for query='{query}', window={window}, filters={filters}")
            tokens = self.load_tokens(filters.get('doc_ids') if filters else None)
            if not tokens:
                logger.error("No tokens available for concordance")
                return []
            
            concordances = []
            for token in tokens:
                if token['token'].lower() != query.lower() and token['lemma'].lower() != query.lower():
                    continue
                if filters:
                    if 'pos' in filters and token['pos'] != filters['pos']:
                        continue
                    if 'date_from' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date < filters['date_from']:
                            continue
                    if 'date_to' in filters:
                        doc_date = self.metadata[str(token['doc_id'])]['date']
                        if doc_date and doc_date > filters['date_to']:
                            continue
                
                # Get sentence tokens
                sent_tokens = [t for t in tokens if t['doc_id'] == token['doc_id'] and t['sent_id'] == token['sent_id']]
                sent_tokens.sort(key=lambda x: x['token_id'])
                
                # Find token index
                idx = next(i for i, t in enumerate(sent_tokens) if t['token_id'] == token['token_id'])
                
                # Extract context
                left = [t['token'] for t in sent_tokens[max(0, idx-window):idx]]
                right = [t['token'] for t in sent_tokens[idx+1:idx+1+window]]
                concordances.append((left, token['token'], right, token['doc_id'], token['sent_id']))
            
            logger.info(f"Concordance completed: {len(concordances)} matches found")
            return concordances
        except Exception as e:
            logger.error(f"Error generating concordances: {e}")
            return []