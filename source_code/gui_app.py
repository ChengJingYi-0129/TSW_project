from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from fhir_kg_system import (
    ask_question,
    apply_simple_inference,
    create_graph_from_folder,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data" / "fhir"
OUTPUT_FOLDER = BASE_DIR.parent / "output"
QUESTIONS = [
    "What conditions does the patient have?",
    "Show observations.",
    "Which patient has risk?",
    "What care recommendation is available?",
    "Show immunization records",
    "Show medication records",
]


class HealthKGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HL7 FHIR Personal Health Knowledge Graph")
        self.root.geometry("1080x680")
        self.root.minsize(900, 600)

        self.graph = None
        self.current_headers = []

        self.setup_style()
        self.build_layout()
        self.load_graph()

    def setup_style(self):
        self.root.configure(bg="#f4f7fb")
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Header.TFrame", background="#143d59")
        style.configure("Header.TLabel", background="#143d59", foreground="white", font=("Segoe UI", 17, "bold"))
        style.configure("SubHeader.TLabel", background="#143d59", foreground="#d8eef8", font=("Segoe UI", 10))
        style.configure("Panel.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("PanelTitle.TLabel", background="white", foreground="#18324a", font=("Segoe UI", 12, "bold"))
        style.configure("Normal.TLabel", background="white", foreground="#263746", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="white", foreground="#66788a", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e8f0f7", foreground="#18324a")

    def build_layout(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(22, 16))
        header.pack(fill="x")

        title = ttk.Label(
            header,
            text="HL7 FHIR-Based Personal Health Knowledge Graph",
            style="Header.TLabel",
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text="RDF/RDFS triples + OWL classes/properties + inference + SPARQL queries",
            style="SubHeader.TLabel",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, style="Panel.TFrame", padding=16)
        left.pack(side="left", fill="y", padx=(0, 14))

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Demo Steps", style="PanelTitle.TLabel").pack(anchor="w")
        steps = [
            "1. Load FHIR-style JSON",
            "2. Convert data to RDF triples",
            "3. Add OWL-style ontology",
            "4. Apply risk inference",
            "5. Run SPARQL-style query",
        ]
        for step in steps:
            ttk.Label(left, text=step, style="Normal.TLabel").pack(anchor="w", pady=(8, 0))

        ttk.Separator(left).pack(fill="x", pady=18)

        ttk.Label(left, text="Query Question", style="PanelTitle.TLabel").pack(anchor="w")
        self.question_var = tk.StringVar(value=QUESTIONS[0])
        question_box = ttk.Combobox(left, textvariable=self.question_var, values=QUESTIONS, state="readonly", width=38)
        question_box.pack(anchor="w", pady=(8, 12))

        ttk.Button(left, text="Run Query", style="Accent.TButton", command=self.run_selected_query).pack(fill="x")
        ttk.Button(left, text="Run All Demo Queries", command=self.run_all_queries).pack(fill="x", pady=(8, 0))
        ttk.Button(left, text="Show RDF / Turtle", command=self.show_turtle).pack(fill="x", pady=(8, 0))

        ttk.Separator(left).pack(fill="x", pady=18)

        ttk.Label(left, text="Graph Summary", style="PanelTitle.TLabel").pack(anchor="w")
        self.summary_label = ttk.Label(left, text="", style="Muted.TLabel", wraplength=300, justify="left")
        self.summary_label.pack(anchor="w", pady=(8, 0))

        top_panel = ttk.Frame(right, style="Panel.TFrame", padding=16)
        top_panel.pack(fill="x")

        ttk.Label(top_panel, text="Selected Query Result", style="PanelTitle.TLabel").pack(anchor="w")
        self.query_label = ttk.Label(top_panel, text="Choose a question and click Run Query.", style="Muted.TLabel")
        self.query_label.pack(anchor="w", pady=(4, 0))

        table_panel = ttk.Frame(right, style="Panel.TFrame", padding=12)
        table_panel.pack(fill="both", expand=True, pady=(14, 0))

        self.tree_frame = ttk.Frame(table_panel)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        y_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

        self.text_output = tk.Text(
            table_panel,
            height=8,
            wrap="word",
            bg="#fbfdff",
            fg="#1e2f3f",
            insertbackground="#1e2f3f",
            relief="solid",
            borderwidth=1,
            font=("Consolas", 9),
        )
        self.text_output.pack(fill="x", pady=(12, 0))

    def load_graph(self):
        try:
            self.graph = create_graph_from_folder(DATA_FOLDER)
            apply_simple_inference(self.graph)
            OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
            
            self.graph.serialize(destination=OUTPUT_FOLDER / "personal_health_kg.ttl", format="turtle")
            
            self.summary_label.configure(
                text=(
                    f"FHIR input folder: {DATA_FOLDER}\n"
                    f"Total RDF triples: {len(self.graph)}\n"
                    "Inference: diabetes + hypertension or high glucose -> RiskPatient"
                )
            )
            self.run_selected_query()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    # For SPARQL query execution and displaying results
    def set_table(self, headers, rows):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = headers

        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=180, anchor="w", stretch=True)

        for row in rows:
            self.tree.insert("", "end", values=row)

    def run_selected_query(self):
        question = self.question_var.get()
        title, headers, rows = ask_question(self.graph, question)
        self.query_label.configure(text=f"{question}  ->  {title}")
        self.set_table(headers, rows)

        self.text_output.delete("1.0", "end")
        self.text_output.insert("end", "SPARQL query selected: " + title + "\n\n")
        self.text_output.insert("end", "Result rows:\n")
        for row in rows:
            self.text_output.insert("end", " - " + " | ".join(row) + "\n")

    def run_all_queries(self):
        self.text_output.delete("1.0", "end")
        all_result_lines = ["HL7 FHIR Personal Health Knowledge Graph Demo", f"Total RDF triples: {len(self.graph)}", ""]

        for question in QUESTIONS:
            title, headers, rows = ask_question(self.graph, question)
            all_result_lines.append("Question: " + question)
            all_result_lines.append("Query selected: " + title)
            all_result_lines.append("Headers: " + ", ".join(headers))
            for row in rows:
                all_result_lines.append(" - " + " | ".join(row))
            all_result_lines.append("")

        result_text = "\n".join(all_result_lines)
        self.text_output.insert("end", result_text)
        (OUTPUT_FOLDER / "query_results.txt").write_text(result_text, encoding="utf-8")
        messagebox.showinfo("Demo Complete", "All demo queries were saved to output/query_results.txt")

    def show_turtle(self):
        turtle_file = OUTPUT_FOLDER / "personal_health_kg.ttl"
        if not turtle_file.exists():
            self.graph.serialize(destination=turtle_file, format="turtle")

        self.query_label.configure(text="RDF / Turtle output preview")
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []
        self.text_output.delete("1.0", "end")
        self.text_output.insert("end", turtle_file.read_text(encoding="utf-8"))


def main():
    root = tk.Tk()
    HealthKGApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
