from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI





CHROMA_DB_PATH = "./chroma_db"

# original embed model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5",trust_remote_code=True)

# groq_key = "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"
# llm = Groq(model="Llama3-8b-8192", api_key=groq_key)
from .utils import get_openai_api_key
OPENAI_API_KEY = get_openai_api_key()
llm = OpenAI(model="gpt-4o-mini")


class SaasPlanDocuments:
    Free = 4
    Basic = 20
    Standard = 100
    Premium = 200

class SaasPlanStorage:
    Free = 200
    Basic = 1000
    Standard = 5000
    Premium = 20000


class SaasPlanCredits:
    Free = 200
    Basic = 300000
    Standard = 1000000
    Premium = 2500000

class SaasPlanQueries:
    Free = 20
    Basic = 30000
    Standard = 100000
    Premium = 250000


class SaasPlanPricing:
    # Monthly pricing
    Free = 0
    Basic = 14
    Standard = 21
    Premium = 49

    # Yearly pricing (10x the monthly price)
    FreeYearly = 0
    BasicYearly = 14 * 10  # 140
    StandardYearly = 21 * 10  # 210
    PremiumYearly = 49 * 10  # 490

class SaasPlanPaypalMontly:
    Free = 0
    Basic = "P-5RK10458FE361174NM4PJE6Y"
    Standard = "P-1K3889856X7361201M4PJF4Q"
    Premium = "P-11198443KW9867508M4PJFSI"

class SaasPlanPaypalYearly:
    Free = 0
    Basic = "P-2BU7114417675874JM4PJGCA"
    Standard = "P-0GS20913FW4825218M4PJFXQ"
    Premium = "P-1SG12647MT9903930M4PJFMI"