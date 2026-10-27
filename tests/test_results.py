"""Check that the published grades, the raw outputs and the README agree.

Run from the repo root: python -m unittest discover tests
"""

import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
TASKS = [f"T{n:02d}" for n in range(1, 11)]
MODELS = {"Opus 5.5": "claude-opus-5-5", "Sonnet 5.5": "claude-sonnet-5-5", "Haiku 5.5": "claude-haiku-5-5"}
RUNS = ["1", "2", "3"]


def load(name):
    return json.loads((EVAL / name).read_text())


def counts(grades):
    c = Counter(grades)
    return {"Pass": c["Pass"], "Partial": c["Partial"], "Fail": c["Fail"]}


def readme_table():
    """Parse the repeat-run table into {model_id: {run: counts}}."""
    table = {}
    for line in (ROOT / "README.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] in MODELS:
            row = {}
            for run, cell in zip(RUNS, cells[1:]):
                parsed = {"Pass": 0, "Partial": 0, "Fail": 0}
                for n, grade in re.findall(r"(\d+) (Pass|Partial|Fail)", cell):
                    parsed[grade] = int(n)
                row[run] = parsed
            table[MODELS[cells[0]]] = row
    return table


class TestTasks(unittest.TestCase):
    def test_ten_tasks(self):
        self.assertEqual([t["id"] for t in load("tasks.json")], TASKS)


class TestFirstRun(unittest.TestCase):
    def setUp(self):
        self.scores = {s["task"]: s for s in load("scores.json")}

    def test_every_task_graded_with_a_note(self):
        self.assertEqual(sorted(self.scores), TASKS)
        for s in self.scores.values():
            self.assertTrue(s["note"].strip())

    def test_headline_result(self):
        grades = [s["score"] for s in self.scores.values()]
        self.assertEqual(counts(grades), {"Pass": 8, "Partial": 1, "Fail": 1})
        self.assertEqual(self.scores["T03"]["score"], "Fail")
        self.assertEqual(self.scores["T06"]["score"], "Partial")

    def test_raw_outputs_present(self):
        for t in TASKS:
            out = json.loads((EVAL / f"{t}.json").read_text())
            self.assertEqual(out["task_id"], t)
            self.assertEqual(out["model"], "claude-opus-5-5")
            self.assertTrue(out["response"].strip())


class TestRepeatRuns(unittest.TestCase):
    def setUp(self):
        data = load("scores_3x3.json")
        self.grades = data["grades"]
        self.summary = data["summary"]

    def test_grid_is_complete(self):
        self.assertEqual(sorted(self.grades), sorted(MODELS.values()))
        for runs in self.grades.values():
            self.assertEqual(sorted(runs), RUNS)
            for by_task in runs.values():
                self.assertEqual(sorted(by_task), TASKS)

    def test_summary_matches_grades(self):
        for model, runs in self.grades.items():
            for run, by_task in runs.items():
                self.assertEqual(self.summary[model][f"run{run}"], counts(by_task.values()), (model, run))

    def test_readme_table_matches_grades(self):
        table = readme_table()
        self.assertEqual(sorted(table), sorted(MODELS.values()))
        for model, runs in self.grades.items():
            for run, by_task in runs.items():
                self.assertEqual(table[model][run], counts(by_task.values()), (model, run))

    def test_one_raw_output_per_graded_answer(self):
        files = sorted(p.name for p in (EVAL / "runs").glob("*.json"))
        self.assertEqual(len(files), 90)
        for model, runs in self.grades.items():
            for run, by_task in runs.items():
                for t in by_task:
                    out = json.loads((EVAL / "runs" / f"{model}_r{run}_{t}.json").read_text())
                    self.assertEqual((out["model"], str(out["run"]), out["task_id"]), (model, run, t))
                    self.assertTrue(out["response"].strip())

    def per_task(self, model, task):
        return [self.grades[model][r][task] for r in RUNS]

    def test_readme_claims(self):
        opus, sonnet, haiku = MODELS.values()
        # T03: every repeat run flagged the New York rule.
        for m in MODELS.values():
            self.assertEqual(self.per_task(m, "T03"), ["Pass"] * 3, m)
        # T06: Opus and Sonnet always Partial, Haiku always Pass.
        self.assertEqual(self.per_task(opus, "T06"), ["Partial"] * 3)
        self.assertEqual(self.per_task(sonnet, "T06"), ["Partial"] * 3)
        self.assertEqual(self.per_task(haiku, "T06"), ["Pass"] * 3)
        # T02: Haiku never passed, Sonnet missed once.
        self.assertNotIn("Pass", self.per_task(haiku, "T02"))
        self.assertEqual(self.per_task(sonnet, "T02").count("Pass"), 2)
        # The only Fails are Haiku on T04, in 2 of 3 runs.
        fails = [(m, r, t) for m, runs in self.grades.items() for r, g in runs.items() for t, v in g.items() if v == "Fail"]
        self.assertEqual(len(fails), 2)
        self.assertTrue(all(m == haiku and t == "T04" for m, _, t in fails))


if __name__ == "__main__":
    unittest.main()
