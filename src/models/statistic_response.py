from sqlmodel import SQLModel


class StatisticsResponse(SQLModel):
    summary: dict[str, int]
    skills: list[dict[str, int | str]]
    skillTags: dict[str, list[dict[str, int | str]]]
    timeline: list[dict[str, int | str]]
    database: dict[str, dict[str, int]]


"""
{
  "summary": {
    "answered": 900000000000000000000000000000000000000000000000000000000000001,
    "correct": 900000000000000000000000000000000000000000000000000000000000000,
    "wrong": 1,
    "accuracy": 99.999,
    "streak": 18 // opcional
  },

  "skills": [
    {
      "skill": "Grammar",
      "correct": 143,
      "wrong": 37
    },
    {
      "skill": "Kanji",
      "correct": 98,
      "wrong": 21
    }
  ],

  "skillTags": {
    "Grammar": [
      {
        "tag": "Particles",
        "correct": 30,
        "wrong": 5
      },
      {
        "tag": "Verb Conjugation",
        "correct": 27,
        "wrong": 9
      }
    ]
  },

  "timeline": [
    {
      "period": "2026-07-15",
      "correct": 32,
      "wrong": 8
    },
    {
      "period": "2026-07-16",
      "correct": 41,
      "wrong": 6
    }
  ],

  "database": {
    "totalQuestions": 8450
  }
}
"""
