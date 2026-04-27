import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import json
import random
from copy import deepcopy


class MCQTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MCQ Test App")
        self.root.geometry("950x750")

        self.raw_questions = []
        self.questions = []
        self.current_index = 0
        self.user_answers = {}

        self.mode = tk.StringVar(value="one_question")
        self.randomize_questions = tk.BooleanVar(value=True)
        self.randomize_options = tk.BooleanVar(value=True)

        self.build_start_screen()

    # -----------------------------
    # Screen management
    # -----------------------------

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_start_screen(self):
        self.clear_window()

        title = tk.Label(
            self.root,
            text="MCQ Test App",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=15)

        subtitle = tk.Label(
            self.root,
            text="Paste JSON from your Custom GPT or load a .json file.",
            font=("Arial", 12)
        )
        subtitle.pack(pady=5)

        format_note = tk.Label(
            self.root,
            text="Expected format: question, correct_answer, incorrect_answers, optional explanation",
            font=("Arial", 10),
            fg="gray"
        )
        format_note.pack(pady=3)

        self.json_box = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            height=25,
            font=("Consolas", 10)
        )
        self.json_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        example_button_frame = tk.Frame(self.root)
        example_button_frame.pack(pady=5)

        tk.Button(
            example_button_frame,
            text="Insert Example JSON",
            command=self.insert_example_json,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            example_button_frame,
            text="Load JSON File",
            command=self.load_json_file,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        options_frame = tk.LabelFrame(self.root, text="Test Settings", padx=10, pady=10)
        options_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Radiobutton(
            options_frame,
            text="One question at a time",
            variable=self.mode,
            value="one_question"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        tk.Radiobutton(
            options_frame,
            text="Full test mode",
            variable=self.mode,
            value="full_test"
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        tk.Checkbutton(
            options_frame,
            text="Randomize question order",
            variable=self.randomize_questions
        ).grid(row=1, column=0, sticky="w", padx=10, pady=5)

        tk.Checkbutton(
            options_frame,
            text="Randomize answer choices",
            variable=self.randomize_options
        ).grid(row=1, column=1, sticky="w", padx=10, pady=5)

        tk.Button(
            self.root,
            text="Start Test",
            command=self.start_test,
            width=25,
            height=2,
            font=("Arial", 11, "bold")
        ).pack(pady=15)

    # -----------------------------
    # JSON loading and validation
    # -----------------------------

    def insert_example_json(self):
        example = [
            {
                "question": "What does etiology mean?",
                "correct_answer": "The cause or origin of a disease",
                "incorrect_answers": [
                    "The treatment of a disease",
                    "The symptoms of a disease",
                    "The prognosis of a disease"
                ],
                "explanation": "Etiology refers to the cause or origin of a disease."
            },
            {
                "question": "Which term best describes disease of the heart muscle?",
                "correct_answer": "Cardiomyopathy",
                "incorrect_answers": [
                    "Arrhythmia",
                    "Pericarditis",
                    "Atherosclerosis"
                ],
                "explanation": "Cardiomyopathy means disease of the heart muscle."
            },
            {
                "question": "Which condition involves reduced blood flow to tissue?",
                "correct_answer": "Ischemia",
                "incorrect_answers": [
                    "Hypertrophy",
                    "Necrosis",
                    "Fibrosis"
                ],
                "explanation": "Ischemia means inadequate blood supply to tissue."
            }
        ]

        self.json_box.delete("1.0", tk.END)
        self.json_box.insert(tk.END, json.dumps(example, indent=2))

    def load_json_file(self):
        file_path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            self.json_box.delete("1.0", tk.END)
            self.json_box.insert(tk.END, content)

        except Exception as e:
            messagebox.showerror("File Error", f"Could not load file:\n\n{e}")

    def start_test(self):
        raw_json = self.json_box.get("1.0", tk.END).strip()

        if not raw_json:
            messagebox.showerror("Missing JSON", "Please paste JSON or load a JSON file first.")
            return

        try:
            loaded_questions = json.loads(raw_json)
            self.validate_question_data(loaded_questions)

            self.raw_questions = loaded_questions
            self.questions = self.prepare_questions(loaded_questions)

            self.current_index = 0
            self.user_answers = {}

            if self.mode.get() == "one_question":
                self.build_one_question_screen()
            else:
                self.build_full_test_screen()

        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Invalid JSON",
                f"Your pasted text is not valid JSON.\n\nDetails:\n{e}"
            )
        except Exception as e:
            messagebox.showerror("Question Format Error", str(e))

    def validate_question_data(self, questions):
        if not isinstance(questions, list):
            raise ValueError("The JSON must be a list of question objects.")

        if len(questions) == 0:
            raise ValueError("The JSON list is empty. Add at least one question.")

        for i, q in enumerate(questions, start=1):
            if not isinstance(q, dict):
                raise ValueError(f"Question {i} must be a JSON object.")

            if "question" not in q:
                raise ValueError(f"Question {i} is missing the 'question' field.")

            if "correct_answer" not in q:
                raise ValueError(f"Question {i} is missing the 'correct_answer' field.")

            if "incorrect_answers" not in q:
                raise ValueError(f"Question {i} is missing the 'incorrect_answers' field.")

            if not isinstance(q["question"], str) or not q["question"].strip():
                raise ValueError(f"Question {i} has an empty or invalid question.")

            if not isinstance(q["correct_answer"], str) or not q["correct_answer"].strip():
                raise ValueError(f"Question {i} has an empty or invalid correct_answer.")

            if not isinstance(q["incorrect_answers"], list):
                raise ValueError(f"Question {i} incorrect_answers must be a list.")

            if len(q["incorrect_answers"]) != 3:
                raise ValueError(f"Question {i} must have exactly three incorrect_answers.")

            for j, incorrect in enumerate(q["incorrect_answers"], start=1):
                if not isinstance(incorrect, str) or not incorrect.strip():
                    raise ValueError(
                        f"Question {i}, incorrect answer {j}, is empty or invalid."
                    )

            all_answers = [q["correct_answer"]] + q["incorrect_answers"]
            normalized_answers = [answer.strip().lower() for answer in all_answers]

            if len(set(normalized_answers)) != 4:
                raise ValueError(
                    f"Question {i} has duplicate answer choices. "
                    "The correct answer and incorrect answers must all be unique."
                )

    # -----------------------------
    # Randomization logic
    # -----------------------------

    def prepare_questions(self, questions):
        prepared = []

        for q in deepcopy(questions):
            correct_text = q["correct_answer"]
            incorrect_texts = q["incorrect_answers"]

            combined_options = []

            combined_options.append({
                "text": correct_text,
                "is_correct": True
            })

            for incorrect in incorrect_texts:
                combined_options.append({
                    "text": incorrect,
                    "is_correct": False
                })

            if self.randomize_options.get():
                random.shuffle(combined_options)

            letters = ["A", "B", "C", "D"]
            options = {}
            correct_letter = None

            for letter, option in zip(letters, combined_options):
                options[letter] = option["text"]

                if option["is_correct"]:
                    correct_letter = letter

            prepared_question = {
                "question": q["question"],
                "options": options,
                "answer": correct_letter,
                "explanation": q.get("explanation", "")
            }

            prepared.append(prepared_question)

        if self.randomize_questions.get():
            random.shuffle(prepared)

        return prepared

    # -----------------------------
    # One-question-at-a-time mode
    # -----------------------------

    def build_one_question_screen(self):
        self.clear_window()

        q = self.questions[self.current_index]

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=20, pady=10)

        progress_label = tk.Label(
            top_frame,
            text=f"Question {self.current_index + 1} of {len(self.questions)}",
            font=("Arial", 12, "bold")
        )
        progress_label.pack(side=tk.LEFT)

        answered_count = len(self.user_answers)
        answered_label = tk.Label(
            top_frame,
            text=f"Answered: {answered_count}/{len(self.questions)}",
            font=("Arial", 10),
            fg="gray"
        )
        answered_label.pack(side=tk.RIGHT)

        question_label = tk.Label(
            self.root,
            text=q["question"],
            wraplength=850,
            justify="left",
            font=("Arial", 16, "bold")
        )
        question_label.pack(anchor="w", padx=40, pady=20)

        self.selected_answer = tk.StringVar(
            value=self.user_answers.get(self.current_index, "")
        )

        choices_frame = tk.Frame(self.root)
        choices_frame.pack(fill=tk.X, padx=60, pady=10)

        for letter, option_text in q["options"].items():
            rb = tk.Radiobutton(
                choices_frame,
                text=f"{letter}. {option_text}",
                variable=self.selected_answer,
                value=letter,
                wraplength=800,
                justify="left",
                anchor="w",
                font=("Arial", 12)
            )
            rb.pack(fill=tk.X, anchor="w", pady=8)

        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=25)

        tk.Button(
            nav_frame,
            text="Previous",
            command=self.previous_question,
            width=15,
            state=tk.NORMAL if self.current_index > 0 else tk.DISABLED
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            nav_frame,
            text="Next",
            command=self.next_question,
            width=15,
            state=tk.NORMAL if self.current_index < len(self.questions) - 1 else tk.DISABLED
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            nav_frame,
            text="Submit Test",
            command=self.submit_one_question_test,
            width=15
        ).pack(side=tk.LEFT, padx=8)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10)

        tk.Button(
            bottom_frame,
            text="Back to Start",
            command=self.confirm_back_to_start,
            width=15
        ).pack()

    def save_current_answer(self):
        selected = self.selected_answer.get()

        if selected:
            self.user_answers[self.current_index] = selected
        elif self.current_index in self.user_answers:
            del self.user_answers[self.current_index]

    def previous_question(self):
        self.save_current_answer()

        if self.current_index > 0:
            self.current_index -= 1

        self.build_one_question_screen()

    def next_question(self):
        self.save_current_answer()

        if self.current_index < len(self.questions) - 1:
            self.current_index += 1

        self.build_one_question_screen()

    def submit_one_question_test(self):
        self.save_current_answer()

        unanswered = len(self.questions) - len(self.user_answers)

        if unanswered > 0:
            proceed = messagebox.askyesno(
                "Unanswered Questions",
                f"You have {unanswered} unanswered question(s).\n\nSubmit anyway?"
            )

            if not proceed:
                return

        self.show_results()

    # -----------------------------
    # Full-test mode
    # -----------------------------

    def build_full_test_screen(self):
        self.clear_window()

        title = tk.Label(
            self.root,
            text="Full Test Mode",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=10)

        instructions = tk.Label(
            self.root,
            text="Answer all questions, then submit at the bottom.",
            font=("Arial", 11)
        )
        instructions.pack(pady=3)

        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self.full_test_frame = tk.Frame(canvas)

        self.full_test_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=self.full_test_frame,
            anchor="nw"
        )

        def resize_canvas_window(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_canvas_window)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.full_test_vars = []

        for idx, q in enumerate(self.questions):
            question_frame = tk.LabelFrame(
                self.full_test_frame,
                text=f"Question {idx + 1}",
                padx=12,
                pady=12,
                font=("Arial", 10, "bold")
            )
            question_frame.pack(fill=tk.X, padx=15, pady=10)

            question_label = tk.Label(
                question_frame,
                text=q["question"],
                wraplength=820,
                justify="left",
                font=("Arial", 12, "bold")
            )
            question_label.pack(anchor="w", pady=5)

            answer_var = tk.StringVar()
            self.full_test_vars.append(answer_var)

            for letter, option_text in q["options"].items():
                rb = tk.Radiobutton(
                    question_frame,
                    text=f"{letter}. {option_text}",
                    variable=answer_var,
                    value=letter,
                    wraplength=800,
                    justify="left",
                    anchor="w",
                    font=("Arial", 10)
                )
                rb.pack(fill=tk.X, anchor="w", pady=3)

        button_frame = tk.Frame(self.full_test_frame)
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Submit Test",
            command=self.submit_full_test,
            width=20,
            height=2,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Back to Start",
            command=self.confirm_back_to_start,
            width=20,
            height=2
        ).pack(side=tk.LEFT, padx=10)

    def submit_full_test(self):
        self.user_answers = {}

        for idx, var in enumerate(self.full_test_vars):
            selected = var.get()

            if selected:
                self.user_answers[idx] = selected

        unanswered = len(self.questions) - len(self.user_answers)

        if unanswered > 0:
            proceed = messagebox.askyesno(
                "Unanswered Questions",
                f"You have {unanswered} unanswered question(s).\n\nSubmit anyway?"
            )

            if not proceed:
                return

        self.show_results()

    # -----------------------------
    # Results screen
    # -----------------------------

    def show_results(self):
        self.clear_window()

        score = 0
        total = len(self.questions)

        for idx, q in enumerate(self.questions):
            if self.user_answers.get(idx) == q["answer"]:
                score += 1

        percent = round((score / total) * 100, 2)

        title = tk.Label(
            self.root,
            text=f"Score: {score}/{total} ({percent}%)",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=15)

        summary = tk.Label(
            self.root,
            text=f"Correct: {score}    Incorrect: {total - score}",
            font=("Arial", 12)
        )
        summary.pack(pady=5)

        results_box = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        results_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for idx, q in enumerate(self.questions):
            user_answer = self.user_answers.get(idx, "No answer")
            correct_answer = q["answer"]

            is_correct = user_answer == correct_answer

            results_box.insert(tk.END, f"Question {idx + 1}\n")
            results_box.insert(tk.END, f"{q['question']}\n\n")

            for letter, option_text in q["options"].items():
                marker = ""

                if letter == correct_answer:
                    marker += "  <-- Correct answer"

                if letter == user_answer and not is_correct:
                    marker += "  <-- Your answer"

                if letter == user_answer and is_correct:
                    marker += "  <-- Your answer"

                results_box.insert(tk.END, f"{letter}. {option_text}{marker}\n")

            results_box.insert(tk.END, "\n")

            if is_correct:
                results_box.insert(tk.END, "Result: Correct\n")
            else:
                results_box.insert(tk.END, "Result: Incorrect\n")

            if q.get("explanation"):
                results_box.insert(tk.END, f"Explanation: {q['explanation']}\n")

            results_box.insert(tk.END, "\n" + "-" * 90 + "\n\n")

        results_box.config(state=tk.DISABLED)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Retake Same Randomized Test",
            command=self.retake_same_test,
            width=25
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            button_frame,
            text="Randomize Again",
            command=self.randomize_again,
            width=20
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            button_frame,
            text="Back to Start",
            command=self.build_start_screen,
            width=20
        ).pack(side=tk.LEFT, padx=8)

    def retake_same_test(self):
        self.current_index = 0
        self.user_answers = {}

        if self.mode.get() == "one_question":
            self.build_one_question_screen()
        else:
            self.build_full_test_screen()

    def randomize_again(self):
        self.questions = self.prepare_questions(self.raw_questions)
        self.current_index = 0
        self.user_answers = {}

        if self.mode.get() == "one_question":
            self.build_one_question_screen()
        else:
            self.build_full_test_screen()

    def confirm_back_to_start(self):
        proceed = messagebox.askyesno(
            "Return to Start",
            "Return to the start screen? Current test progress will be lost."
        )

        if proceed:
            self.build_start_screen()


if __name__ == "__main__":
    root = tk.Tk()
    app = MCQTestApp(root)
    root.mainloop()