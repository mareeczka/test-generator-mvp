import time
import random
import re
import json
import gc
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

    def __init__(self, model_path: str = None, batch_size: int = 3, max_retries: int = 3, temperature: float = 0.15):
        self.model_path = model_path
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.temperature = temperature
        self.model = None
        self.tokenizer = None
        self._model_loaded = False

    def _load_model(self):
        """Lazy load model and tokenizer"""
        if self._model_loaded:
            return

        if not self.model_path:
            raise ValueError("MODEL_PATH not configured for RealGenerator")

        print(f"Загрузка модели из {self.model_path}...")

        # Import here to avoid loading dependencies in dev mode
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import os

        # Set memory optimization
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            load_in_4bit=True,
            torch_dtype=torch.float16
        )

        self._model_loaded = True
        print("Модель успешно загружена!")

    def _clear_cuda(self):
        """Clear CUDA memory and run garbage collection"""
        try:
            import torch
            torch.cuda.empty_cache()
            gc.collect()
        except Exception:
            pass  # If torch not available, just skip

    def _extract_json_array_from_text(self, text: str):
        """Extract and parse JSON array from text with error recovery"""
        cleaned = re.sub(r'```json\s*|\s*```', '', text).strip()
        start = cleaned.find('[')
        end = cleaned.rfind(']') + 1
        if start == -1 or end <= start:
            return None
        candidate = cleaned[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Attempt to repair common issues
            try:
                repaired = re.sub(r',(\s*[}\]])', r'\1', candidate)  # remove trailing commas
                return json.loads(repaired)
            except Exception:
                return None

    def _truncate_to_n_words(self, s, n=3):
        """Truncate string to n words, removing punctuation"""
        if not isinstance(s, str):
            return s
        # Remove punctuation first
        s = re.sub(r'[^\w\s]', '', s)
        parts = s.strip().split()
        return " ".join(parts[:n])

    def _shorten_option(self, option, max_words=10):
        """Shorten option text to max_words, but only if it's significantly longer"""
        if not isinstance(option, str):
            return option
        parts = option.strip().split()
        # Only truncate if it's more than max_words + 2 (to avoid cutting useful info)
        if len(parts) <= max_words + 2:
            return option.strip()
        return " ".join(parts[:max_words]) + "..."

    def _ensure_test_set_name(self, parsed, name):
        """Ensure all questions have test_set name filled"""
        for item in parsed:
            if item.get("test_set", "") == "":
                item["test_set"] = name
        return parsed

    def _programmatically_mangle_match(self, questions_json, seed=None):
        """
        Shuffle MATCH-type options and remap answer indices.
        Avoids asking LLM to randomize (more reliable).
        """
        if seed is not None:
            random.seed(seed)

        output = []
        for q in questions_json:
            q_copy = dict(q)
            if q_copy.get("question_type") == "match":
                left = q_copy.get("question_options", [])
                right = q_copy.get("options", [])

                n = min(len(left), len(right))
                left = left[:n]
                right = right[:n]

                indices = list(range(n))
                random.shuffle(indices)
                shuffled_right = [right[i] for i in indices]

                # Remap answers to new positions
                new_answers = []
                for original_idx in range(n):
                    new_pos = indices.index(original_idx)
                    new_answers.append([original_idx, new_pos])

                q_copy["question_options"] = left
                q_copy["options"] = shuffled_right
                q_copy["answers"] = new_answers

            output.append(q_copy)
        return output

    def extract_facts(self, text: str) -> str:
        """Extract factual statements from text"""
        try:
            self._load_model()

            import torch

            prompt = f"""Извлеките ТОЛЬКО фактические утверждения, явно присутствующие в ТЕКСТЕ ниже.
НЕ добавляйте интерпретации, мнения или внешние знания.
Перепишите факты в виде коротких, четких пунктов (один факт на строку).
Избегайте избыточности. Если факт не указан явно в тексте, НЕ включайте его.
Верните ТОЛЬКО список пунктов, каждый пункт на отдельной строке (без нумерации, без markdown).

ТЕКСТ:
{text}

ФАКТЫ:
"""
            messages = [
                {"role": "system", "content": "Вы - точный ассистент по извлечению фактов. Извлекайте только явные факты."},
                {"role": "user", "content": prompt}
            ]

            text_input = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(text_input, return_tensors="pt").to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=self.temperature,
                    do_sample=True if self.temperature > 0 else False,
                    top_p=0.95
                )

            raw = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            del outputs, inputs
            self._clear_cuda()

            # Post-process: normalize and deduplicate
            cleaned = re.sub(r'^\s*\-+\s*$', '', raw, flags=re.MULTILINE).strip()
            lines = [line.strip(" -\t\n\r") for line in cleaned.splitlines() if line.strip()]

            # Deduplicate while preserving order
            seen = set()
            facts = []
            for L in lines:
                if L not in seen:
                    seen.add(L)
                    facts.append(L)

            return "\n".join(facts)

        except Exception as e:
            raise RuntimeError(f"Ошибка извлечения фактов: {str(e)}")

    def _generate_batch_via_model(self, facts: str, types_to_generate: List[str],
                                   start_index: int, test_set_name: str):
        """Generate a batch of questions of specified types"""
        import torch
        import math

        # Build dynamic template
        template = []
        for i, qtype in enumerate(types_to_generate):
            idx = start_index + i
            base = {
                "test_set": test_set_name,
                "question_number": idx,
                "question_type": qtype,
                "question_text": ""
            }
            if qtype == "mcq":
                base["options"] = ["", "", ""]
                base["answers"] = []
            elif qtype == "match":
                base["question_options"] = ["", ""]
                base["options"] = ["", ""]
                base["answers"] = [[0, 0], [1, 1]]
            elif qtype == "input":
                base["answer"] = ""
            elif qtype == "sequence":
                base["options"] = ["", "", ""]
                base["answers"] = [0, 1, 2]
            template.append(base)
        template_str = json.dumps(template, indent=2, ensure_ascii=False)

        # Create examples based on a completely different domain
        example_facts = """Фотосинтез преобразует световую энергию в химическую энергию.
Хлорофилл - это пигмент, который улавливает солнечный свет.
Углекислый газ и вода являются сырьем.
Глюкоза и кислород - это продукты.
Процесс происходит в хлоропластах."""

        example_output = """[
  {
    "test_set": "Пример",
    "question_number": 1,
    "question_type": "mcq",
    "question_text": "Что преобразует фотосинтез?",
    "options": ["световую энергию в химическую энергию", "химическую энергию в световую энергию", "воду в кислород"],
    "answers": [0]
  },
  {
    "test_set": "Пример",
    "question_number": 2,
    "question_type": "input",
    "question_text": "Какой пигмент улавливает солнечный свет в растениях?",
    "answer": "Хлорофилл"
  },
  {
    "test_set": "Пример",
    "question_number": 3,
    "question_type": "match",
    "question_text": "Сопоставьте каждый термин с его ролью в фотосинтезе:",
    "question_options": ["Углекислый газ", "Глюкоза", "Хлоропласты"],
    "options": ["Сырье, используемое в процессе", "Продукт процесса", "Место, где происходит процесс"],
    "answers": [[0,0],[1,1],[2,2]]
  }
]"""

        prompt = f"""Вы - строгий генератор вопросов. Изучите ПРИМЕР ниже, затем сгенерируйте вопросы для ЦЕЛЕВЫХ ФАКТОВ.

=== ПРИМЕР (только для справки) ===
ПРИМЕРНЫЕ ФАКТЫ:
{example_facts}

ПРИМЕРНЫЙ ВЫВОД:
{example_output}

=== ВАША ЗАДАЧА ===
Сгенерируйте ровно {len(types_to_generate)} вопросов в таком порядке: {', '.join(types_to_generate)}

ЦЕЛЕВЫЕ ФАКТЫ:
{facts}

КРИТИЧЕСКИЕ ПРАВИЛА:
1) Используйте ТОЛЬКО информацию из ЦЕЛЕВЫХ ФАКТОВ. Никаких внешних знаний.
2) Для INPUT: ответ должен быть 1-3 СЛОВА из фактов (термин, имя или концепция). Никогда не предложение. Удалите пунктуацию.
3) Для MCQ: ВСЕ 3 ВАРИАНТА ДОЛЖНЫ БЫТЬ РАЗНЫМИ. Если вы не можете создать 3 различных правдоподобных варианта, пропустите этот тип вопроса. Каждый вариант максимум 10 слов.
4) Для MATCH: создавайте различные пары термин-определение. Каждый вариант справа должен быть ПОЛНОЙ фразой/предложением, описывающим ОДНУ конкретную вещь.
5) Для SEQUENCE: используйте только если в фактах есть четкий хронологический порядок.
6) question_text ВСЕГДА должен быть заполнен (никогда не пустым).
7) Ответы используют индексацию с 0.
8) НЕ обрывайте варианты посередине предложения. Пишите полные фразы.

ХОРОШИЕ и ПЛОХИЕ ПРИМЕРЫ:

MCQ - ПЛОХО:
"Что такое фотосинтез?"
Варианты: ["Процесс с использованием солнечного света", "Процесс с использованием лунного света", "Процесс, превращающий растения в камни"]
Проблема: Вариант 3 абсурден и нереалистичен

MCQ - ХОРОШО:
"Что такое фотосинтез?"
Варианты: ["Процесс, преобразующий световую энергию в химическую энергию", "Процесс, преобразующий химическую энергию в световую энергию", "Процесс, хранящий воду в клетках растений"]
Почему: Все варианты - правдоподобные биологические процессы

MATCH - ПЛОХО:
Question_options: ["Термин А", "Термин Б"]
Options: ["Что-то неясное", "Другая неясная вещь"]
Проблема: Неясные соответствия

MATCH - ХОРОШО:
Question_options: ["Хлорофилл", "Глюкоза"]
Options: ["Пигмент, улавливающий солнечный свет", "Сахар, производимый фотосинтезом"]
Почему: Четкие пары термин-определение из фактов

SEQUENCE - ПЛОХО:
Использование фактов, которые происходят одновременно или не имеют четкого порядка
Проблема: Навязывает искусственную последовательность

SEQUENCE - ХОРОШО:
Использование фактов с явными временными маркерами, такими как "сначала", "затем", "после" или логическим прогрессом
Почему: Естественный порядок существует в исходном материале

ПРАВИЛА ВЫВОДА:
- Возвращайте ТОЛЬКО валидный JSON, без объяснений, без markdown, без преамбулы
- Не выдумывайте факты, термины или различия, не присутствующие в источнике
- Делайте вопросы сложными, но справедливыми
- Убедитесь, что все варианты четко различны и правдоподобны

ШАБЛОН:
{template_str}

Верните ТОЛЬКО JSON массив. Без комментариев.
"""
        messages = [
            {"role": "system", "content": "Вы - точный генератор вопросов, возвращающий только JSON."},
            {"role": "user", "content": prompt}
        ]

        text_input = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1500,
                temperature=self.temperature,
                do_sample=True if self.temperature > 0 else False,
                top_p=0.9
            )

        raw = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        del outputs, inputs
        self._clear_cuda()

        parsed = self._extract_json_array_from_text(raw)
        if parsed is None:
            return None

        parsed = self._ensure_test_set_name(parsed, test_set_name)
        return parsed

    def generate_questions(self, facts: str, test_set_name: str = "Test 1",
                          question_count: int = 10) -> List[Dict]:
        """Generate exam questions in batches with validation and error recovery"""
        try:
            self._load_model()

            import math

            # Distribution: prefer MCQ and INPUT (cheaper), some MATCH and SEQUENCE
            n_match = max(1, int(question_count * 0.10))
            n_seq = max(1, int(question_count * 0.10))
            remainder = question_count - (n_match + n_seq)
            n_mcq = math.ceil(remainder * 0.5)
            n_input = remainder - n_mcq

            types_pool = []
            types_pool.extend(["match"] * n_match)
            types_pool.extend(["sequence"] * n_seq)
            types_pool.extend(["mcq"] * n_mcq)
            types_pool.extend(["input"] * n_input)

            # Prefer MCQ/Input earlier, add randomness
            random.shuffle(types_pool)
            types_pool.sort(key=lambda t: 0 if t in ("mcq", "input") else 1)
            types_pool = types_pool[:question_count]

            all_questions = []
            total_batches = math.ceil(len(types_pool) / self.batch_size)

            for batch_idx in range(total_batches):
                start = batch_idx * self.batch_size
                end = min(start + self.batch_size, len(types_pool))
                batch_types = types_pool[start:end]
                batch_start_index = start + 1
                print(f"Обработка батча {batch_idx+1}/{total_batches}: {batch_types}")

                success = False
                for attempt in range(1, self.max_retries + 1):
                    parsed = self._generate_batch_via_model(
                        facts=facts,
                        types_to_generate=batch_types,
                        start_index=batch_start_index,
                        test_set_name=test_set_name
                    )
                    if parsed is None:
                        print(f"  Попытка {attempt}: невалидный JSON; повтор...")
                        continue

                    # Post-process and validate
                    valid = True
                    for q in parsed:
                        qtype = q.get("question_type", "").lower()

                        if q.get("test_set", "") == "":
                            q["test_set"] = test_set_name

                        # MCQ validation
                        if qtype == "mcq":
                            opts = q.get("options", [])
                            opts = [self._shorten_option(opt, max_words=10) for opt in opts]

                            # Check for duplicate options - if found, mark as invalid
                            if len(opts) != len(set(opts)):
                                print(f"    MCQ имеет дублирующиеся варианты, помечено как невалидное")
                                valid = False
                                break

                            q["options"] = opts
                            ans = q.get("answers", [])
                            if not isinstance(ans, list) or len(ans) == 0:
                                valid = False
                                break
                            filtered = [int(a) for a in ans if isinstance(a, int) or (isinstance(a, str) and a.isdigit())]
                            if not filtered:
                                valid = False
                                break
                            q["answers"] = [filtered[0]]

                        # INPUT validation
                        elif qtype == "input":
                            ans = q.get("answer", "")
                            if not isinstance(ans, str) or ans.strip() == "":
                                valid = False
                                break
                            q["answer"] = self._truncate_to_n_words(ans, 3)

                        # MATCH validation
                        elif qtype == "match":
                            left = q.get("question_options", [])
                            right = q.get("options", [])
                            n = min(len(left), len(right))
                            if n == 0:
                                valid = False
                                break
                            q["question_options"] = left[:n]
                            q["options"] = [self._shorten_option(x, max_words=8) for x in right[:n]]
                            q["answers"] = [[i, i] for i in range(n)]

                        # SEQUENCE validation
                        elif qtype == "sequence":
                            opts = q.get("options", [])
                            if len(opts) < 2:
                                valid = False
                                break
                            opts = [opt.strip() for opt in opts]
                            q["options"] = opts[:5]
                            q["answers"] = list(range(len(q["options"])))

                        else:
                            valid = False
                            break

                    if not valid:
                        print(f"  Попытка {attempt}: валидация не прошла; повтор...")
                        continue

                    # Shuffle match questions programmatically
                    parsed = self._programmatically_mangle_match(parsed)
                    all_questions.extend(parsed)
                    success = True
                    break

                if not success:
                    print(f"  Батч {batch_idx+1} не удался после {self.max_retries} попыток; пропуск.")

            # Trim and normalize
            all_questions = all_questions[:question_count]
            for i, q in enumerate(all_questions):
                q["question_number"] = i + 1
                if q.get("test_set", "") == "":
                    q["test_set"] = test_set_name

            return all_questions

        except Exception as e:
            raise RuntimeError(f"Ошибка генерации вопросов: {str(e)}")


def get_generator(use_mock: bool = True, **kwargs):
    if use_mock:
        delay = kwargs.get('delay', 2.0)
        return MockGenerator(delay=delay)
    else:
        model_path = kwargs.get('model_path')
        batch_size = kwargs.get('batch_size', 3)
        max_retries = kwargs.get('max_retries', 3)
        temperature = kwargs.get('temperature', 0.15)
        return RealGenerator(
            model_path=model_path,
            batch_size=batch_size,
            max_retries=max_retries,
            temperature=temperature
        )
