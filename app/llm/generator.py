import time
import random
from typing import List, Dict


class MockGenerator:
    def __init__(self, delay: float = 2.0):
        self.delay = delay

    def extract_facts(self, text: str) -> str:
        time.sleep(self.delay * 0.5)  # Shorter delay for facts

        # Extract some real sentences from the text for realism
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        facts = sentences[:min(5, len(sentences))]

        return "\n".join(f"- {fact}" for fact in facts if fact)

    def generate_questions(self, facts: str, test_set_name: str = "Test 1",
                          question_count: int = 10) -> List[Dict]:
        time.sleep(self.delay)  # Simulate generation time

        words = facts.split()
        sample_words = [w.strip('.,;:!?-') for w in words if len(w) > 3][:20]

        questions = []

        # Generate mix of question types
        types_pool = (
            ["mcq"] * int(question_count * 0.5) +
            ["input"] * int(question_count * 0.3) +
            ["match"] * int(question_count * 0.1) +
            ["sequence"] * int(question_count * 0.1)
        )
        random.shuffle(types_pool)
        types_pool = types_pool[:question_count]

        for i, qtype in enumerate(types_pool, 1):
            if qtype == "mcq":
                questions.append(self._mock_mcq(i, test_set_name, sample_words))
            elif qtype == "input":
                questions.append(self._mock_input(i, test_set_name, sample_words))
            elif qtype == "match":
                questions.append(self._mock_match(i, test_set_name, sample_words))
            elif qtype == "sequence":
                questions.append(self._mock_sequence(i, test_set_name, sample_words))

        return questions

    def _mock_mcq(self, num: int, test_name: str, words: List[str]) -> Dict:
        base_word = words[num % len(words)] if words else "понятие"

        return {
            "test_set": test_name,
            "question_number": num,
            "question_type": "mcq",
            "question_text": f"Какова основная характеристика {base_word}?",
            "options": [
                f"Демонстрирует свойства {base_word}",
                f"Противоречит теории {base_word}",
                f"Представляет альтернативную интерпретацию"
            ],
            "answers": [0]
        }

    def _mock_input(self, num: int, test_name: str, words: List[str]) -> Dict:
        answer_word = words[num % len(words)] if words else "ответ"

        return {
            "test_set": test_name,
            "question_number": num,
            "question_type": "input",
            "question_text": f"Какой термин описывает это понятие? (одно слово)",
            "answer": answer_word[:15]  # Truncate to reasonable length
        }

    def _mock_match(self, num: int, test_name: str, words: List[str]) -> Dict:
        if len(words) < 3:
            words = ["Термин А", "Термин Б", "Термин В"]

        selected = words[:3] if len(words) >= 3 else words + ["Термин"]

        shuffled_indices = [0, 1, 2]
        random.shuffle(shuffled_indices)

        return {
            "test_set": test_name,
            "question_number": num,
            "question_type": "match",
            "question_text": "Сопоставьте каждый термин с его определением:",
            "question_options": selected,
            "options": [
                f"Определение для {selected[shuffled_indices[0]]}",
                f"Определение для {selected[shuffled_indices[1]]}",
                f"Определение для {selected[shuffled_indices[2]]}"
            ],
            "answers": [
                [0, shuffled_indices.index(0)],
                [1, shuffled_indices.index(1)],
                [2, shuffled_indices.index(2)]
            ]
        }

    def _mock_sequence(self, num: int, test_name: str, words: List[str]) -> Dict:
        """Generate mock SEQUENCE question"""
        steps = [
            "Первый шаг процесса",
            "Второй шаг процесса",
            "Третий шаг процесса",
            "Заключительный шаг процесса"
        ]

        return {
            "test_set": test_name,
            "question_number": num,
            "question_type": "sequence",
            "question_text": "Расположите эти шаги в правильном порядке:",
            "options": steps,
            "answers": [0, 1, 2, 3]
        }


class RealGenerator:
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

        self._model_loaded = False

    def _load_model(self):
        if self._model_loaded:
            return

        if not self.model_path:
            raise ValueError("MODEL_PATH not configured for RealGenerator")

        print(f"Loading model from {self.model_path}...")

        # Import here to avoid loading dependencies in dev mode
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            load_in_4bit=True,
            torch_dtype=torch.float16
        )

        self._model_loaded = True
        print("Model loaded successfully!")

    def extract_facts(self, text: str) -> str:
        self._load_model()
        
        raise NotImplementedError("TODO: Port extract_facts from Colab")

    def generate_questions(self, facts: str, test_set_name: str = "Test 1",
                          question_count: int = 10) -> List[Dict]:
        self._load_model()

        raise NotImplementedError("TODO: Port generate_exam_questions from Colab")


def get_generator(use_mock: bool = True, **kwargs):
    if use_mock:
        delay = kwargs.get('delay', 2.0)
        return MockGenerator(delay=delay)
    else:
        model_path = kwargs.get('model_path')
        return RealGenerator(model_path=model_path)
