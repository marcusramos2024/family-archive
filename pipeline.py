import warnings

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

from dotenv import load_dotenv

load_dotenv()

from steps.consensus import consensus
from steps.cross_verify import cross_verify
from steps.preprocess import preprocess
from steps.report import report
from steps.review import review_transcription
from steps.split import split
from steps.transcribe import transcribe
from steps.translate import translate
from steps.verify import verify

if __name__ == "__main__":
    preprocess()
    split()
    transcribe()
    consensus()
    verify()
    cross_verify()
    review_transcription()
    translate()
    report()
