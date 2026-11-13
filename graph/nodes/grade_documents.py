# Here I have created a document grader node that checks the relevance of the retrieved documents to the user's question.


from typing import Any, Dict
from graph.chains.retrieval_grader import retrieval_grader
from graph.state import GraphState


def grade_documents(state: GraphState) -> Dict[str, Any]:
    print("\n--- CHECKING RETRIEVED DOCUMENTS RELEVANCE TO THE QUESTION ---\n")

    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    web_search = False  # Initialize web_search to False


    for doc in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": doc.page_content}
        )

        if score.binary_score == True:
            print(f"--- GRADE: DOCUMENT IS RELEVANT ({doc.metadata.get('food_name', 'Unknown')}) ---")
            filtered_docs.append(doc)
        else:
            print(f"--- GRADE: DOCUMENT IS NOT RELEVANT ({doc.metadata.get('food_name', 'Unknown')}) ---")


    if len(filtered_docs) == 0:
        print("\n--- GRADE RESULT: NO RELEVANT DOCUMENTS FOUND - INITIATING WEB SEARCH ---\n")
        web_search = True       # Set web_search to True if no relevant documents are found
    else:
        print(f"\n--- GRADE RESULT: {len(filtered_docs)} RELEVANT DOCUMENT(S) FOUND - PROCEEDING TO GENERATE ANSWER---\n")

    return{
        "documents": filtered_docs,
        "question": question,
        "web_search": web_search
    }