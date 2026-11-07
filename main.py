"""IELTS Trap Hunter: fixed-answer questions with optional LLM coaching."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT / "data" / "questions.json"
CHOICES = {"T": "TRUE", "F": "FALSE", "N": "NOT GIVEN"}


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    questions = json.loads(path.read_text(encoding="utf-8"))
    required = {"id", "passage", "statement", "answer", "evidence", "trap_type", "explanation"}
    ids: set[str] = set()
    for q in questions:
        if not required <= q.keys():
            raise ValueError(f"Missing question fields: {q}")
        if q["answer"] not in CHOICES.values():
            raise ValueError(f"Invalid answer for question {q['id']}")
        if q["evidence"] not in q["passage"]:
            raise ValueError(f"Evidence not found in passage for question {q['id']}")
        if q["id"] in ids:
            raise ValueError(f"Duplicate question id {q['id']}")
        ids.add(q["id"])
    return questions


def mark_answer(question: dict, answer: str) -> bool:
    return answer.upper() == question["answer"]


def learning_summary(records: list[dict]) -> dict:
    if not records:
        return {"attempted": 0, "correct": 0, "accuracy": 0, "weakest_trap": "None"}
    incorrect = Counter(r["trap_type"] for r in records if not r["correct"])
    return {
        "attempted": len(records),
        "correct": sum(r["correct"] for r in records),
        "accuracy": round(100 * sum(r["correct"] for r in records) / len(records)),
        "weakest_trap": incorrect.most_common(1)[0][0] if incorrect else "None",
    }


def thinking_diagnosis(question: dict, chosen: str, reasoning: str) -> str:
    """Build a fact-based diagnosis without inventing a student's mistake.

    Answer correctness is decided using the fixed answer key, not by the LLM.
    A correct choice alone does not prove the reasoning is correct.
    """
    if mark_answer(question, chosen):
        verdict = "本題答案正確。"
    else:
        verdict = f"本題答案不正確：你選了 {chosen}，標準答案是 {question['answer']}。"

    if reasoning.strip():
        reasoning_note = f"你提供的理由是：「{reasoning.strip()}」。答案與理由仍需分開核對。"
    else:
        reasoning_note = "你沒有提供解題理由，因此無法判斷你的思考過程。"

    return f"{verdict}{reasoning_note} 原文依據：{question['evidence']}。"


def ai_coach(question: dict, chosen: str, reasoning: str, model: str) -> dict:
    """Call local Ollama for structured tips; keep verdict deterministic."""
    from pydantic import BaseModel, Field
    from ollama import chat

    class CoachingTips(BaseModel):
        # Legacy field retained for compatibility with earlier unit tests.
        # Its generated value is discarded; Python computes this diagnosis.
        thinking_diagnosis: str = Field(description="請固定填入空字串；答題診斷由 Python 產生")
        useful_phrase: str = Field(description="原文或題目中一個實用英文詞組及繁體中文解釋")
        next_time_strategy: str = Field(description="根據本題陷阱類型，提出一項具體的 IELTS 閱讀策略（繁體中文）")

    correct = mark_answer(question, chosen)
    prompt = f"""你是 IELTS Academic Reading 的友善中文教練。請使用繁體中文。
你的工作只有：解釋一個本題重要的英文詞組，以及給出下次閱讀策略。
不要判斷學生是否答對，不要推測學生誤解了哪些字或有什麼錯誤。
判分由 Python 固定答案完成，結果是：{'答對' if correct else '答錯'}。
學生未提供理由時，不能假裝知道其想法；即使答對也不代表其理由必定正確。
請只能根據文章提供內容，不得杜撰原文或新增未提供的事實。
尤其要區分：FALSE = 原文明確矛盾；NOT GIVEN = 原文無法判斷，不能靠常識推測。
文章：{question['passage']}
題目：{question['statement']}
固定標準答案：{question['answer']}
本題陷阱類型：{question['trap_type']}
答案依據：{question['evidence']}
預先審閱的解析：{question['explanation']}
學生答案：{chosen}
學生理由：{reasoning if reasoning.strip() else '未提供'}
請依照 JSON schema 回傳三個欄位，thinking_diagnosis 請填空字串；
只需實際生成 useful_phrase 與 next_time_strategy。
不要聲稱能提供官方雅思分數。"""
    response = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=CoachingTips.model_json_schema(),
        options={"temperature": 0},
    )
    tips = CoachingTips.model_validate_json(response.message.content).model_dump()
    tips["thinking_diagnosis"] = thinking_diagnosis(question, chosen, reasoning)
    return tips


def save_record(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def demo() -> None:
    question = load_questions()[2]
    print("\n=== IELTS TRAP HUNTER — 固定題庫展示（不呼叫 AI） ===")
    print("PASSAGE:", question["passage"])
    print("STATEMENT:", question["statement"])
    print("LEARNER ANSWER: FALSE")
    print("CORRECT ANSWER:", question["answer"])
    print("EVIDENCE:", question["evidence"])
    print("TRAP TYPE:", question["trap_type"])
    print("EXPLANATION:", question["explanation"])
    print("\n真正使用 LLM，請啟動 Ollama 並執行 uv run main.py")

def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="IELTS Trap Hunter — AI Reading Coach")
    parser.add_argument("--demo", action="store_true", help="Show fixed-answer example; no LLM call")
    parser.add_argument("--offline", action="store_true", help="Practice without LLM coaching")
    parser.add_argument("--limit", type=int, default=4, help="Questions per session, 1–8")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    questions = load_questions()
    if not 1 <= args.limit <= len(questions):
        parser.error(f"--limit must be from 1 to {len(questions)}")

    records = []
    print("\n=== IELTS TRAP HUNTER ===")
    print("T = TRUE | F = FALSE | N = NOT GIVEN | Q = 離開")
    print("AI 模式：", "OFFLINE (無模型)" if args.offline else f"Ollama / {args.model}")
    for n, q in enumerate(questions[: args.limit], 1):
        print(f"\n--- Question {n} / {args.limit} · {q['topic']} ---")
        print("\nPASSAGE:\n" + q["passage"])
        print("\nSTATEMENT:\n" + q["statement"])
        while True:
            raw = input("\nYour answer [T/F/N/Q]: ").strip().upper()
            if raw == "Q":
                break
            if raw in CHOICES:
                break
            print("請輸入 T、F、N 或 Q。")
        if raw == "Q":
            break
        chosen = CHOICES[raw]
        thinking = input("為什麼這樣選？（可直接 Enter 略過）：").strip()
        correct = mark_answer(q, chosen)
        print("\n" + ("✓ CORRECT" if correct else "✗ INCORRECT"))
        print(f"標準答案：{q['answer']} | 陷阱類型：{q['trap_type']}")
        print("原文依據：" + q["evidence"])
        print("解析：" + q["explanation"])
        if not args.offline:
            try:
                feedback = ai_coach(q, chosen, thinking, args.model)
                print("\n--- AI 個人化回饋 ---")
                print("思考診斷：" + feedback["thinking_diagnosis"])
                print("英文表達：" + feedback["useful_phrase"])
                print("下次策略：" + feedback["next_time_strategy"])
            except Exception as exc:
                print("\n無法連線或解析 Ollama 回應，本題仍顯示經確認的固定解析。")
                print("請確認已啟動 Ollama、下載指定模型，並檢查版本。")
                print(f"錯誤類型：{type(exc).__name__}: {exc}")
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "id": q["id"], "answer": chosen, "correct_answer": q["answer"],
            "correct": correct, "trap_type": q["trap_type"],
        }
        save_record(record, ROOT / "results" / "history.jsonl")
        records.append(record)
    summary = learning_summary(records)
    print(f"\n=== 本次完成 {summary['attempted']} 題，答對 {summary['correct']} 題，正確率 {summary['accuracy']}% ===")
    if summary["weakest_trap"] != "None":
        print("建議重點練習的陷阱：" + summary["weakest_trap"])
    print("學習紀錄存於本機 results/history.jsonl（已排除 Git 追蹤）")


if __name__ == "__main__":
    main()