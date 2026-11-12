# Here I will extract nutrition data
# It is a one time job, unless I need to change the source PDFs


from dotenv import load_dotenv      # To load environment variables from a .env file
load_dotenv()                       # Load environment variables from .env file

import warnings         # To suppress specific warnings during execution to have a cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

import json                         # To handle JSON data
import time                         # To handle time-related tasks
from pathlib import Path            # To handle file paths
import pdfplumber                   # To extract text from PDF files
from pydantic import BaseModel, Field                           # To define data models with validation
from langchain_google_genai import ChatGoogleGenerativeAI       # To interact with Google Generative AI


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define paths
DATA_DIR = Path("data")
HEALTH_CANADA_PDF = DATA_DIR / "nvscf-vnqau-eng.pdf"
FITFORFILMS_PDF = DATA_DIR / "Macros-of-common-foods-V3.pdf"
CHECKPOINT_FILE = DATA_DIR / "extraction_checkpoint.json"
OUTPUT_JSON = DATA_DIR / "nutrition_db.json"





# Define a Pydantic model for the nutrition data
class FoodItem(BaseModel):
    food_name: str = Field(description="Exact name of the edible food item.")
    portion: str = Field(
        description=(
            "Serving size or amount: weight in grams (e.g. '100g'), "
            "volume in mL (e.g. '125mL'), count (e.g. '1 slice'), "
            "or a combination (e.g. '125mL (49g)', '1 slice (35g)')."
        )
    )
    calories: float = Field(
        description="Energy value in 'kcal' or 'kcals' ONLY. Do NOT use the Weight column (g) and do NOT use Energy in kJ."
    )
    protein_g: float = Field(description="Protein content in grams.")
    fat_g: float = Field(
        description=(
            "Total fat in grams. Use the column labeled 'Total Fat' or 'Fat'. "
            "Do NOT use sub-types like 'Saturated Fat' or 'Trans Fat', and do NOT sum fat sub-types."
        )
    )
    carbs_g: float = Field(description="Total carbohydrate content in grams.")
    fiber_g: float = Field(
        default=0.0,
        description="Total dietary fiber in grams ('Total Dietary Fibre' or 'Fibre'). Default to 0.0 if not listed.",
    )
    source: str = Field(default="", description="Data source name")
    page_number: int = Field(default=0, description="Source page number")


# Define a Pydantic model for the page extraction result
# We are not using list[FoodItem] directly because we need JSON fpr Gemini Structured Output
class PageExtraction(BaseModel):
    items: list[FoodItem]


# Initialize the structured output extractor for nutrition data
nutrition_extractor = llm.with_structured_output(PageExtraction)


# Define the prompt template for extracting nutrition data from table text
PROMPT_TEMPLATE = """You are an accurate nutrition data extractor.
Extract all individual food items and their macronutrients from the provided table text.

CRITICAL PARSING RULES:
1. ENERGY vs WEIGHT vs kJ:
   - 'calories' MUST come from the Energy (kcal) column.
   - Do NOT use the 'Weight' column (which is in grams, e.g. 30g) as calories.
   - Do NOT use the 'Energy kJ' column as calories.
   - Example: For 'Chickpea flour | 125mL | 49 | 188 | 786', Weight is 49g, Energy kcal is 188, Energy kJ is 786. Calories MUST be 188.0.

2. PORTION:
   - Extract the serving size or amount: weight in grams (e.g. '100g'), volume in mL (e.g. '125mL'), count (e.g. '1 slice'), or a combination (e.g. '125mL (49g)', '1 slice (35g)').

3. FAT EXTRACTION:
   - 'fat_g' MUST be the overall fat value, labeled either 'Total Fat' (Health Canada) or 'Fat' (FitForFilms).
   - NEVER use sub-categories like 'Saturated Fat' or 'Trans Fat'.
   - NEVER add fat sub-types together (overall fat already includes them).

4. GENERAL:
   - If fiber is not present, set fiber_g to 0.0.
   - Treat 'tr', 'trace', or '-' as 0.0.
   - Ignore category headers and food group labels (e.g., 'Flours and Brans', 'Breads and Buns') as food items. Only extract actual edible items.

Table Content:
{table_markdown}
"""


# Define checkpoint functions to load and save the extraction progress
def load_checkpoint() -> dict:
    """Load the extraction checkpoint from a JSON file."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_pages": [], "items": []}


def save_checkpoint(data: dict):
    """Save the extraction checkpoint to a JSON file."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Define a function to format a 2D table grid as markdown
def format_table_as_markdown(table: list[list[str]]) -> str:
    """Converts a row extracted 2D table grid into clean readable markdown"""
    lines = []
    for row in table:
        clean_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        if any(clean_row):
            lines.append(" | ".join(clean_row))
    return "\n".join(lines)


# Define a function to process a PDF file and extract nutrition data
# The function handles page ranges, checkpointing, and rate limiting for API calls
def process_pdf(pdf_path: Path, source_name: str, start_page: int, end_page: int, state: dict):
    if not pdf_path.exists():
        print(f"Skipping {pdf_path}: file not found.")
        return

    print(f"\n--- Processing {source_name} (Pages {start_page} to {end_page}) ---")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        end = min(end_page, total_pages)

        for page_idx in range(start_page - 1, end):
            page_num = page_idx + 1
            page_key = f"{source_name}_p{page_num}"

            if page_key in state["processed_pages"]:
                print(f"Page {page_num}/{end} already in checkpoint. Skipping.")
                continue

            page = pdf.pages[page_idx]

            # layout=True preserves spatial column alignment across all layouts
            page_content = page.extract_text(layout=True) or ""

            if len(page_content.strip()) < 40:
                state["processed_pages"].append(page_key)
                save_checkpoint(state)
                continue

            prompt = PROMPT_TEMPLATE.format(table_markdown=page_content)

            retries = 3
            while retries > 0:
                try:
                    res = nutrition_extractor.invoke(prompt)
                    extracted_items = []
                    for item in res.items:
                        # Deterministically assign source and physical page number
                        item.source = source_name
                        item.page_number = page_num
                        extracted_items.append(item.model_dump())

                    state["items"].extend(extracted_items)
                    state["processed_pages"].append(page_key)
                    save_checkpoint(state)
                    print(f"Page {page_num}/{end} -> Extracted {len(extracted_items)} items.")
                    break
                except Exception as e:
                    print(f"Rate limit or network error on page {page_num}: {e}")
                    retries -= 1
                    if retries > 0:
                        print("Cooling down for 20 seconds before retrying...")
                        time.sleep(20)
                    else:
                        print(f"Failed page {page_num} after retries. Moving to next page.")

            # Quota sleep to prevent 429 rate limit errors
            time.sleep(5)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    state = load_checkpoint()

    # Process FitForFilms PDF (All pages)
    process_pdf(
        pdf_path=FITFORFILMS_PDF,
        source_name="FitForFilms",
        start_page=1,
        end_page=15,
        state=state
    )

    # Process Health Canada PDF (Pages 10-62)
    process_pdf(
        pdf_path=HEALTH_CANADA_PDF,
        source_name="Health Canada",
        start_page=10,
        end_page=62,
        state=state
    )

    # Write the final verifit consolidated nutrition database to a JSON file
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(state["items"], f, indent=2, ensure_ascii=False)


    print(f"\n--- Extraction complete! Saved {len(state['items'])} items to {OUTPUT_JSON} ---")
    
if __name__ == "__main__":
    main()