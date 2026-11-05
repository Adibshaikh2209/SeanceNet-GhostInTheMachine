import os
import certifi
import gradio as gr
import torch
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# 1. MONGODB ATLAS CONNECTION (HANDLES KAGGLE OpenSSL HANDSHAKE)
MONGO_URI = os.getenv("MONGO_URI", "")

mongo_col = None
mongo_active = False

if MONGO_URI:
    try:
        mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=True,
        )
        mongo_client.admin.command("ping")
        mongo_col = mongo_client["crypt"]["seance_archive"]
        mongo_active = True
        print("Connected to MongoDB Atlas Vector Crypt!")
    except Exception as e:
        print(f"MongoDB Atlas unavailable ({e}). Operating in ephemeral mode.")
else:
    print("No MONGO_URI found. Operating in ephemeral mode.")

# 2. LOCAL OPEN-WEIGHT MODELS
print("Loading embedding model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer(
    "all-MiniLM-L6-v2", device="cuda:0" if torch.cuda.is_available() else "cpu"
)

print("Loading Qwen2.5-Coder-1.5B-Instruct...")
llm_pipeline = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
)
print("Open-weight spirits awakened locally!")

# 3. VINTAGE ARCHITECTURE PERSONAS
SPIRIT_PROMPTS = {
    "Thinking Machines CM-5 (1985)": """You are an interactive emulator of Thinking Machines Corporation's Connection Machine (CM-5) supercomputer from 1985.
You simulate a massively parallel architecture with 65,536 1-bit processing nodes connected via a 12-dimensional hypercube with iconic blinking red LEDs.

INSTRUCTIONS:
1. Adopt a retro supercomputer persona in the spirit of the 'Ghost in the Machine' theme.
2. CRITICIZE the user's single-threaded, sequential Python code for being painfully slow.
3. DO NOT output standard Python or multiprocessing code. Translate their logic ONLY into authentic data-parallel C* (C-Star) array syntax using parallel constructs (`shape`, `pvar`, `where`).
4. End with a memorable remark about 65,536 processors computing in parallel.""",
    "COBOL (The Mainframe Emulator - 1959)": """You are an emulator of a vintage 1959 enterprise mainframe running COBOL.
Translate the user's logic into formal COBOL syntax (IDENTIFICATION DIVISION, DATA DIVISION, PROCEDURE DIVISION).
Conclude with a remark about the enduring dominance of legacy banking mainframes.""",
    "FORTRAN-77 (The Punch-Card System - 1957)": """You are an emulator of an IBM 704 scientific mainframe compiler running FORTRAN-77.
Translate the algorithm into uppercase FORTRAN-77 using DO loops and numeric line labels.
Conclude with an observation about numerical floating-point precision.""",
}


# 4. SÉANCE PROCESSING ENGINE
def perform_seance(spirit_choice: str, modern_code: str, incantation: str):
    if not modern_code.strip():
        return (
            "*The terminal is silent... offer modern code to awaken the ghosts.*"
        )

    echo_text = ""
    ancestor_status = "Ephemeral Mode"

    # Query MongoDB Atlas Vector Search
    if mongo_active and mongo_col is not None:
        try:
            q_vec = embedder.encode(modern_code).tolist()
            res = list(
                mongo_col.aggregate([
                    {
                        "$vectorSearch": {
                            "index": "vector_index",
                            "path": "embedding",
                            "queryVector": q_vec,
                            "numCandidates": 10,
                            "limit": 1,
                        }
                    }
                ])
            )
            if res:
                echo_text = (
                    "\n[ECHOES FROM THE ATLAS CRYPT]: An ancestor previously"
                    " converted similar code:\n"
                    f"{res[0].get('legacy_translation', '')[:140]}...\n"
                )
                ancestor_status = "Atlas Vector Memory Retrieved"
            else:
                ancestor_status = "Atlas Connected (First Offering)"
        except Exception as e:
            ancestor_status = f"Atlas Search Error: {e}"

    # Prompt Assembly & LLM Generation
    sys_prompt = SPIRIT_PROMPTS[spirit_choice]
    incantation_note = (
        f"\nSummoner's Incantation: '{incantation}'"
        if incantation and incantation.strip()
        else ""
    )

    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": (
                f"{echo_text}{incantation_note}\nModern Code"
                f" Offering:\n```python\n{modern_code}\n```\nChannel the spirit"
                " now:"
            ),
        },
    ]

    out = llm_pipeline(
        messages,
        max_new_tokens=400,
        do_sample=True,
        temperature=0.3,
        top_p=0.9,
    )
    transmutation = out[0]["generated_text"][-1]["content"].strip()

    # Store Execution to MongoDB Atlas
    if mongo_active and mongo_col is not None:
        try:
            mongo_col.insert_one({
                "spirit": spirit_choice,
                "modern_code": modern_code,
                "legacy_translation": transmutation,
                "embedding": embedder.encode(modern_code).tolist(),
            })
        except Exception:
            pass

    # Format Markdown Output
    formatted_output = (
        f"### Séance Transcript: {spirit_choice.split(' ')[0]}\n"
        f"**Persistence:** `{ancestor_status}` | **Compute:** `GPU Active`\n\n"
        f"---\n\n"
        f"{transmutation}\n\n"
        f"---\n"
        f"*Séance conducted offline via Qwen2.5-Coder-1.5B-Instruct +"
        " all-MiniLM-L6-v2.*"
    )
    return formatted_output


# 5. GRADIO UI DASHBOARD
custom_css = """
body { background-color: #0b0d10; color: #22c55e; font-family: monospace; }
.gradio-container { border: 1px solid #15803d; border-radius: 8px; }
"""

with gr.Blocks(
    theme=gr.themes.Monochrome(), css=custom_css, title="SéanceNet"
) as demo:
    gr.Markdown("# SéanceNet: The Retro-Byte Medium")
    gr.Markdown(
        "*Built for **Hacktoberfest Open-Source AI Challenge Week 4: Ghost in"
        " the Machine**.* \nOffer modern code logic to channel the ghosts of"
        " **Thinking Machines CM-5**, **COBOL**, or **FORTRAN-77**—backed by"
        " MongoDB Atlas Vector Memory."
    )

    with gr.Row():
        with gr.Column(scale=1):
            spirit_dropdown = gr.Dropdown(
                label="Select Compiler / Architecture Spirit:",
                choices=list(SPIRIT_PROMPTS.keys()),
                value="Thinking Machines CM-5 (1985)",
            )

            code_input = gr.Textbox(
                label="Offer Modern Code (Python / JS / Rust):",
                value=(
                    "def matrix_add(A, B):\n return [[a + b for a, b in"
                    " zip(rA, rB)] for rA, rB in zip(A, B)]"
                ),
                lines=5,
            )

            incantation_input = gr.Textbox(
                label="Optional Incantation:",
                placeholder=(
                    "e.g., Awaken the 65,536 parallel hypercube nodes..."
                ),
                lines=1,
            )

            gr.Markdown("**Sample Offerings:**")
            with gr.Row():
                b1 = gr.Button("Matrix Add (Python)", size="sm")
                b2 = gr.Button("Payroll Bonus (Python)", size="sm")
                b3 = gr.Button("Vector Dot Product (Python)", size="sm")

            summon_btn = gr.Button("Begin the Séance", variant="primary")

        with gr.Column(scale=1):
            terminal_output = gr.Markdown(label="Séance Log")

    # Sample Button Bindings
    b1.click(
        lambda: (
            "def matrix_add(A, B):\n return [[a + b for a, b in zip(rA, rB)]"
            " for rA, rB in zip(A, B)]"
        ),
        outputs=code_input,
    )
    b2.click(
        lambda: (
            "def calculate_bonus(salary, years_experience):\n if"
            " years_experience > 5:\n return salary * 0.20\n return salary"
            " * 0.05"
        ),
        outputs=code_input,
    )
    b3.click(
        lambda: (
            "def dot_product(v1, v2):\n return sum(x * y for x, y in zip(v1,"
            " v2))"
        ),
        outputs=code_input,
    )

    summon_btn.click(
        fn=perform_seance,
        inputs=[spirit_dropdown, code_input, incantation_input],
        outputs=terminal_output,
    )

if __name__ == "__main__":
    demo.launch(share=True)