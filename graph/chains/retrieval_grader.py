# Here I have defined a retrieval grader chain that assesses the relevance of retrieved documents to a user question


from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

from langchain_core.prompts import ChatPromptTemplate           # To create a chat prompt template for the LLM
from langchain_google_genai import ChatGoogleGenerativeAI       # To use the Google Generative AI LLM
from pydantic import BaseModel, Field                           # To create pydantic models for LLM output


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define GradeDocuments class to assess the relevance of retrieved documents to the question
class GradeDocuments(BaseModel):
    """Binary score for the relevance check on the retrieved documents."""

    binary_score: bool = Field(
        description="Documents are relevant to the question, 'True' or 'False'",
    )


# Create a structured LLM grader that uses the GradeDocuments model for output
structured_llm_grader = llm.with_structured_output(GradeDocuments)


# Define the system message for the LLM
system = """You are a grader assessing relevance of a retrieved nutrition document to a user question.
If the document contains food items, nutritional values, or keywords related to the food(s) requested in the user question, grade it as relevant.
Give a binary score True or False. True means that the document is relevant to the question."""


# Define the chat prompt template for the retrieval grader
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved documents: \n\n {document} \n\n User question: {question}",),
    ]
)


# Create the retrieval grader chain by piping the prompt and structured LLM grader
retrieval_grader = grade_prompt | structured_llm_grader