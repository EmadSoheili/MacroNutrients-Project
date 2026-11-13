# Here I have defined a hallucination grader chain.
# It uses the LLM to assess whether a generated answer is grounded in the retrieved sources.

from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

from langchain_core.prompts import ChatPromptTemplate           # To create a chat prompt template for the LLM
from langchain_google_genai import ChatGoogleGenerativeAI       # To use the Google Generative AI LLM
from pydantic import BaseModel, Field                           # To create pydantic models for LLM output


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define GradeHallucinations class to assess if the answer is grounded in the retrieved sources
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generated answer."""

    binary_score: bool = Field(
        description="Answer is grounded in the retrieved sources, 'True' or 'False'",
    )


# Define the structured output parser for the LLM
structured_llm_grader = llm.with_structured_output(GradeHallucinations)


# Define the system message for the LLM
system = """You are a grader assessing whether an LLM generation is grounded in / supported by the retrieved sources.
Check that the macronutrient figures come directly from the retrieved sources (or accurate arithmetic scaling/summing of those sources).
Give a binary score True or False. True means that the answer is grounded in / supported by the retrieved sources."""


# Define the chat prompt template for the hallucination grader
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved sources: \n\n {documents} \n\n LLM generation: {generation}",),
    ]
)


# Create the hallucination grader chain by piping the prompt and structured LLM grader
hallucination_grader = hallucination_prompt | structured_llm_grader