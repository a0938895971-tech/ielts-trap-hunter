import json
import tempfile
import unittest
from pathlib import Path

from main import CHOICES, learning_summary, load_questions, mark_answer, save_record


class QuestionTests(unittest.TestCase):
    def setUp(self):
        self.questions = load_questions()

    def test_all_questions_have_valid_answers_and_exact_evidence(self):
        self.assertGreaterEqual(len(self.questions), 6)
        for question in self.questions:
            self.assertIn(question["answer"], CHOICES.values())
            self.assertIn(question["evidence"], question["passage"])

    def test_each_answer_type_is_covered(self):
        self.assertEqual({q["answer"] for q in self.questions}, set(CHOICES.values()))

    def test_mark_answer(self):
        self.assertTrue(mark_answer(self.questions[0], "TRUE"))
        self.assertFalse(mark_answer(self.questions[0], "FALSE"))

    def test_learning_summary(self):
        rows = [
            {"correct": True, "trap_type": "Paraphrase"},
            {"correct": False, "trap_type": "Missing information"},
            {"correct": False, "trap_type": "Missing information"},
        ]
        summary = learning_summary(rows)
        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["accuracy"], 33)
        self.assertEqual(summary["weakest_trap"], "Missing information")

    def test_history_is_valid_json_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "history.jsonl"
            save_record({"id": "R1", "correct": True}, file)
            save_record({"id": "R2", "correct": False}, file)
            records = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([r["id"] for r in records], ["R1", "R2"])

    def test_reject_broken_evidence(self):
        bad_question = dict(self.questions[0], evidence="NOT ACTUALLY IN THE TEXT")
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "q.json"
            file.write_text(json.dumps([bad_question]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_questions(file)


if __name__ == "__main__":
    unittest.main()

class StructuredOutputTests(unittest.TestCase):
    def test_coach_requests_schema_and_validates_response(self):
        """Mock Ollama transport: tests format handling, not model accuracy."""
        from types import SimpleNamespace
        from unittest.mock import patch
        from main import ai_coach, load_questions

        seen = {}

        def fake_chat(*, model, messages, format, options):
            seen["format"] = format
            seen["prompt"] = messages[0]["content"]
            return SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                "thinking_diagnosis": "你把文章沒有提到的事當成事實。",
                "useful_phrase": "was finished: 已經完成",
                "next_time_strategy": "先找證據，不可依賴常識。",
            }, ensure_ascii=False)))

        with patch.dict("sys.modules", {"ollama": SimpleNamespace(chat=fake_chat)}):
            output = ai_coach(load_questions()[2], "FALSE", "我覺得整修會關閉", "fake-model")
        self.assertIn("thinking_diagnosis", seen["format"]["properties"])
        self.assertIn("固定標準答案：NOT GIVEN", seen["prompt"])
        self.assertIn("證據", output["next_time_strategy"])
