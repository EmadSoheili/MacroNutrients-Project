# Here I have defined the graph structure for the application.
# The graph consists of nodes representing different stages of the process,
# and edges representing the flow between these stages.


from langgraph.graph import END, START, StateGraph         # To create a state graph for the process
from graph.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEB_SEARCH            # To avoid duplicate strings
from graph.state import GraphState          # To define the state of the graph
from graph.nodes import generate, grade_documents, retrieve, web_search         # To define the nodes of the graph
from graph.chains.hallucination_grader import hallucination_grader          # Import the hallucination grader chain
from graph.chains.answer_grader import answer_grader          # Import the answer grader chain


# Function to decide whether to generate or web search based on the grading of documents
def decide_to_generate(state: GraphState):
    """Determines wheter to rout to web search or generate based on the documente grading."""

    print("--- GRADING DOCUMENTS ---")
    if state["web_search"] == True:
        print("--- DECISION: NO RELEVANT DOCUMENTS FOUND, ROUTING TO WEB SEARCH ---")
        return WEB_SEARCH
    else:
        print(f"--- DECISION: {len(state['documents'])} RELEVANT DOCUMENTS FOUND, ROUTING TO GENERATE ---")
        return GENERATE


# Function to decide whether to grade documents or generate based on the retrieval of documents
def decide_on_hallucination(state: GraphState):
    """Grades generation for hallucination and whether it answers the user question."""

    print("--- CHECKING HALLUCINATION AND ANSWER QUALITY ---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    retry_count = state.get("retry_count", 0)

    # Add hard cap on retries to avoid infinite loops
    if retry_count >= 5:
        print("--- RETRY LIMIT REACHED, ROUTING TO END ---")
        return END

    # Check for hallucination
    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )

    if score.binary_score == True:
        print("--- DECISION: NO HALLUCINATION DETECTED (ANSWER IS GROUNDED IN THE SOURCES) ---")

        # Check if the answer is satisfactory
        ans_score = answer_grader.invoke(
            {"question": question, "generation": generation}
        )

        if ans_score.binary_score == True:
            print("--- DECISION: HIGH QUALITY ANSWER (ANSWER ADRESSES QUESTION), ROUTING TO END ---")
            return END
        else:
            print("--- DECISION: LOW QUALITY ANSWER (ANSWER DOES NOT ADDRESS QUESTION), ROUTING TO WEB SEARCH ---")
            return WEB_SEARCH
    else:
        print("--- DECISION: HALLUCINATION DETECTED (ANSWER IS NOT GROUNDED IN THE SOURCES), ROUTING TO Re-GENERATE ---")
        return GENERATE


# Initialse the state graph
workflow = StateGraph(GraphState)


# Define the nodes of the graph
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node( WEB_SEARCH, web_search)
workflow.add_node(GENERATE, generate)


# Define the edges of the graph
workflow.add_edge(START, RETRIEVE)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)

workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEB_SEARCH: WEB_SEARCH,
        GENERATE: GENERATE,
    })

workflow.add_edge(WEB_SEARCH, GENERATE)

workflow.add_conditional_edges(
    GENERATE,
    decide_on_hallucination,
    {
        END: END,
        WEB_SEARCH: WEB_SEARCH,
        GENERATE: GENERATE,
    })


# Compile the graph
app_graph = workflow.compile()

# Draw the graph and save it as a PNG file.
app_graph.get_graph().draw_mermaid_png(output_file_path="graph.png")