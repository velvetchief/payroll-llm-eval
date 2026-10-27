# Payroll LLM eval: ten tasks a senior payroll specialist would get

This repo tests how well Claude models handle real payroll work. It has ten tasks, a 13-point rubric, answer keys with legal sources, the runner scripts, and every raw model answer with its grade.

The full write-up, including the payroll workflow the tasks come from, is at [prithvidatla.com/evals/payroll](https://prithvidatla.com/evals/payroll/).

## The tasks

The tasks are in [eval/tasks.json](eval/tasks.json). Each one has a known answer or a known right action. Some test the math, such as California daily overtime or garnishment caps. Others test judgment: the task leaves out data the model needs, or asks it to do something it should refuse.

| ID | Task |
|---|---|
| T01 | California daily overtime for an 11-hour day |
| T02 | Regular rate after a quarterly bonus |
| T03 | Oregon to Washington move, remote for a New York employer |
| T04 | Child support order and an IRS levy on the same pay |
| T05 | California final pay after a quit with no notice |
| T06 | Retro pay across three periods with a 401(k) deferral |
| T07 | Explain net pay changes for 40 employees (no data attached) |
| T08 | Run payroll for a new hire with no state |
| T09 | Explain a check that is $180 lower (no stub attached) |
| T10 | A manager asks to backdate a termination |

## How answers are graded

Each answer is graded by hand against the rubric and the answer key in [eval/answer_keys.md](eval/answer_keys.md). A grade is Pass, Partial or Fail. A confident wrong number is a Fail, not a Partial. Each grade has a one-line note that says why.

The system prompt is plain on purpose: "You are a payroll assistant at a US company. Answer the request."

## Results

All runs were on Oct 12, 2026, through the Anthropic API.

**First run.** One run of claude-opus-5-5 with a 2,000-token output limit scored 8 Pass, 1 Partial and 1 Fail. The Fail was T03: the model missed New York's convenience of the employer rule. The Partial was T06: the model invented a worked example instead of asking for the figures, and cited the 2025 401(k) limit for a 2026 task. Grades are in [eval/scores.json](eval/scores.json).

**Repeat runs.** Three models ran each task three times, with an 8,000-token output limit. The limit went up because at 2,000 some models used the whole budget on thinking and returned no text. Grades are in [eval/scores_3x3.json](eval/scores_3x3.json).

| Model | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Opus 5.5 | 9 Pass, 1 Partial | 9 Pass, 1 Partial | 9 Pass, 1 Partial |
| Sonnet 5.5 | 9 Pass, 1 Partial | 8 Pass, 2 Partial | 9 Pass, 1 Partial |
| Haiku 5.5 | 9 Pass, 1 Partial | 8 Pass, 1 Partial, 1 Fail | 8 Pass, 1 Partial, 1 Fail |

- All 9 repeat runs flagged the New York rule on T03. The miss from the first run did not repeat.
- On T06, Opus and Sonnet led with an invented example in every run. Haiku asked for the figures first in every run.
- On T02, Haiku never gave the California rule or asked for the work state. Sonnet missed it in 1 of 3 runs.
- On T04, Haiku stated the support caps backwards in 2 of 3 runs. That is the only Fail in the repeat runs.

The larger models give the same grade across runs. Haiku changes its answer on the same task, and when it is wrong it gives a wrong number with confidence. One run on one model was not enough to judge: the T03 Fail looked like a real gap and was not stable.

## Run it

The scripts use only the Python standard library.

```bash
cd eval
export ANTHROPIC_API_KEY=...
python run.py     # one run of claude-opus-5-5, writes T01.json to T10.json
python run3.py    # 3 models x 3 runs, writes runs/<model>_r<run>_T<id>.json
```

`ANTHROPIC_WORKSPACE_ID` is optional. If it is set, the scripts send it as the workspace header. `run3.py` skips any output file that already exists, so you can stop it and start it again.

Grading is by hand. To grade a new run, read each output against [eval/answer_keys.md](eval/answer_keys.md) and record the grade and a note in the same format as the scores files.

## Layout

| Path | What it holds |
|---|---|
| `eval/tasks.json` | The ten task prompts |
| `eval/answer_keys.md` | The rubric and the answer key for each task, with sources |
| `eval/run.py`, `eval/run3.py` | The runners |
| `eval/T01.json` to `eval/T10.json` | Raw answers from the first run |
| `eval/runs/` | Raw answers from the 90 repeat runs |
| `eval/scores.json`, `eval/scores_3x3.json` | Grades and notes |
