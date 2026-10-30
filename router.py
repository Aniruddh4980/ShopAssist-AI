from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router.index import LocalIndex

encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L12-v2",
    device="cuda"
)

faq = Route(
    name='faq',
    utterances=[
        "What is the return policy of the products?",
        "Do I get discount with the HDFC credit card?",
        "How can I track my order?",
        "What payment methods are accepted?",
        "How long does it take to process a refund?",
        "Can I return a damaged product?",
        "What is your policy on defective products?",
        "What should I do if I receive a faulty item?",
        "Can I get a replacement for a defective product?",
        "What happens if the product arrives damaged?",
    ]
)

sql = Route(
    name='sql',
    utterances=[
        "I want to buy nike shoes that have 50% discount.",
        "Are there any shoes under Rs. 3000?",
        "Do you have formal shoes in size 9?",
        "Are there any Puma shoes on sale?",
        "What is the price of puma running shoes?"
    ]
)

index = LocalIndex()

router = SemanticRouter(routes=[faq, sql], encoder=encoder, index=index, auto_sync='local')
router.set_threshold(threshold=0.4)

if __name__ == "__main__":
    print(router("What is your policy on defective product?").name)
    print(router("Pink shoes in price range 1000 to 5000").name)