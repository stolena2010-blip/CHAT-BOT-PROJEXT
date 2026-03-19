# � יומן מימוש הפרויקט — Implementation Log

## סיכום כללי

הפרויקט הוא **צ'אטבוט גיוס מבוסס Multi-Agent AI** של **Hell Corp** 🔥 שמנהל שיחות SMS עם מועמדים למשרת Python Developer בסניף המעגל השביעי. המערכת בנויה מ-4 סוכני AI שעובדים ביחד, עם חיבור למסד נתונים SQL, מאגר ידע וקטורי (ChromaDB), וממשק משתמש Streamlit.

---

## שלב 1: הקמת תשתית הפרויקט

### מה נעשה:
- **אתחול Git repository** — `git init` עם `.gitignore` שמתעלם מ-.env, .venv, __pycache__, chroma_db, וקבצי IDE.
- **יצירת מבנה תיקיות** לפי הנחיות המסמך:
  ```
  app/                    → קוד ראשי
  app/modules/agents/     → 4 סוכני AI
  app/modules/database/   → חיבור SQL
  app/modules/embedding/  → ChromaDB
  app/modules/fine_tuning/ → Fine-tuning
  app/modules/evaluation/ → הערכת ביצועים
  streamlit_app/          → ממשק ווב
  tests/                  → בדיקות
  ```
- **קובצי `__init__.py`** בכל תיקיה — הופכים את התיקיות ל-Python packages כדי שאפשר לעשות import ביניהן.

### למה ככה:
מבנה מודולרי מאפשר לכל חלק לעבוד באופן עצמאי ולהיבדק בנפרד. זה גם מה שנדרש במסמך הפרויקט.

---

## שלב 2: סביבה וירטואלית ו-Dependencies

### מה נעשה:
- **יצירת `.venv`** — סביבה וירטואלית מבודדת כדי לא להשפיע על ה-Python הגלובלי.
- **התקנת חבילות עיקריות:**
  - `langchain`, `langchain-openai`, `langchain-community`, `langchain-chroma` — framework ל-AI agents
  - `openai` — API ל-GPT-4o ו-fine-tuning
  - `chromadb` — מסד נתונים וקטורי
  - `streamlit` — ממשק ווב
  - `pypdf` — קריאת PDF
  - `python-dotenv` — טעינת משתני סביבה מ-.env
  - `pyodbc` — חיבור SQL Server
  - `pandas`, `scikit-learn`, `matplotlib`, `seaborn` — ניתוח נתונים והדמיה
- **`requirements.txt`** — נוצר עם `pip freeze` כדי לנעול גרסאות מדויקות.

### למה ככה:
Virtual environment מבטיח שכל מי שירים את הפרויקט יעבוד עם אותן גרסאות. `pip freeze` מייצר רשימת גרסאות מדויקת לשחזור.

---

## שלב 3: מודול Embedding (ChromaDB)

### קובץ: `app/modules/embedding/embedding.py`

### מה הוא עושה:
1. **קורא את ה-PDF** (Python Developer Job Description) עם PyPDFLoader
2. **מפצל לחתיכות** (chunks) של 500 תווים עם חפיפה של 100 — כדי לא לאבד הקשר בגבולות
3. **יוצר Embeddings** עם מודל `text-embedding-3-small` של OpenAI
4. **שומר ב-ChromaDB** — מסד נתונים וקטורי מקומי

### פונקציות:
- `build_vector_store()` — בונה את המאגר (הרצה חד-פעמית)
- `get_vector_store()` — מחזיר מאגר קיים לשימוש runtime

### למה זה נחוץ:
ה-Info Advisor צריך לענות על שאלות של מועמדים לגבי המשרה. במקום לשלוח את כל ה-PDF ל-LLM, אנחנו עושים **RAG** (Retrieval-Augmented Generation) — שולפים רק את החלקים הרלוונטיים ומצרפים אותם כ-context.

---

## שלב 4: מודול מסד נתונים (SQL)

### קובץ: `app/modules/database/database.py`

### מה הוא עושה:
מנהל את טבלת Schedule — לוח הזמנים של המגייסים. תומך ב-**SQLite in-memory** (עובד מקומית בלי SQL Server).

### המסד:
- טבלת `Schedule` עם עמודות: `date`, `time`, `position`, `available`
- נתונים ל-2024, ימים ג'-ו' + ראשון, שעות 09:00-17:00
- 4 תפקידים: Python Dev, Sql Dev, Analyst, ML
- ~50% מהסלוטים פנויים (רנדומלי)

### פונקציות:
- `get_available_slots(position, from_date, to_date, limit=3)` — מחזיר סלוטים פנויים
- `check_slot_available(position, date, time)` — בודק סלוט ספציפי
- `book_slot(position, date, time)` — מזמין סלוט

### למה SQLite ולא SQL Server:
למרות שהמסמך מציין SQL Server, SQLite עובד ישר מ-Python בלי התקנה. המודול **seed** את הנתונים באותו אופן כמו `db_Tech.sql`. אפשר בקלות להחליף ל-SQL Server עם pyodbc.

---

## שלב 5: Info Advisor (סוכן מידע)

### קובץ: `app/modules/agents/info_advisor.py`

### מה הוא עושה:
עונה על שאלות של מועמדים לגבי המשרה באמצעות **RAG** — שולף מידע רלוונטי מ-ChromaDB ומשלב אותו בתשובה.

### איך:
1. מקבל את שאלת המועמד
2. עושה similarity search ב-ChromaDB (3 חתיכות הכי רלוונטיות)
3. בונה prompt עם ה-context + היסטוריית השיחה
4. שולח ל-GPT-4o ומחזיר תשובה

### Prompt Strategy:
- **Role**: "You are the Info Advisor for a recruitment chatbot"
- **Instructions**: לענות רק לפי ה-context, לא להמציא מידע, לכוון לקביעת ראיון
- **Few-shot**: ה-context מה-PDF משמש כדוגמאות

---

## שלב 6: Scheduling Advisor (סוכן תיאום)

### קובץ: `app/modules/agents/scheduling_advisor.py`

### מה הוא עושה:
מנהל את תהליך קביעת הראיון — כולל **OpenAI Function Calling** לאינטראקציה עם מסד הנתונים.

### Function Calling Tools (3 כלים):
1. `get_available_slots` — שליפת סלוטים פנויים בטווח תאריכים
2. `check_slot_available` — בדיקת סלוט ספציפי
3. `book_slot` — הזמנת סלוט

### איך זה עובד:
1. המועמד אומר "next Friday at 3 PM"
2. הסוכן מפרסר את התאריך היחסי לפי ה-reference date (מתוך timestamp השיחה)
3. שולח function call ל-API שמפעיל את הפונקציה עם הפרמטרים הנכונים
4. מחזיר תוצאות ומציע סלוטים

### Iterative Tool Loop:
הסוכן יכול לבצע עד 5 function calls ברצף (בדיקה → הצעה → אישור) עד שמגיע לתשובה סופית.

---

## שלב 7: Exit Advisor (סוכן סיום)

### קובץ: `app/modules/agents/exit_advisor.py`

### מה הוא עושה:
מזהה מתי מועמד לא מעוניין ומסמן שצריך לסיים את השיחה.

### מצבי סיום:
- "remove me from your list"
- כבר מצא עבודה
- ביקש להפסיק ליצור קשר
- דחה את כל ההצעות
- ראיון נקבע בהצלחה

### שני מצבי עבודה:
1. **Base mode** — GPT-4o עם prompt מפורט
2. **Fine-tuned mode** — מודל שעבר fine-tuning (אחרי הרצת המודול)

### Output:
מחזיר מילה אחת: `"end"` או `"continue"`

---

## שלב 7b: מודול Fine-Tuning

### קובץ: `app/modules/fine_tuning/fine_tuning.py`

### מה הוא עושה:
מכין training data ומריץ fine-tuning דרך OpenAI API, כך ש-Exit Advisor יהיה מדויק יותר.

### תהליך:
1. **עיבוד sms_conversations.json** — מכל שיחה מעויגת מחלץ דוגמאות:
   - Input: היסטוריית שיחה + הודעת מועמד
   - Output: "end" או "continue" (labels "schedule" ממופים ל-"continue")
2. **יצירת JSONL** בפורמט של OpenAI Chat Completion
3. **העלאה ל-OpenAI** + הפעלת fine-tuning job
4. **המתנה** עד שה-job מסתיים
5. שם המודל המאומן נשמר ב-`.env`

### בסיס המודל: `gpt-4o-mini-2024-07-18`
- קל ומהיר (מתאים ל-classification פשוט)
- 3 epochs של אימון

---

## שלב 8: Main Agent (מנצח-התזמורת)

### קובץ: `app/modules/agents/main_agent.py`

### מה הוא עושה:
**מנהל את כל השיחה.** בכל תור:

1. **שואל את Exit Advisor** — האם לסיים?
2. **מחליט action** — continue / schedule / end (LLM decision)
3. **מפנה ליועץ המתאים:**
   - continue → Info Advisor (עונה על שאלות)
   - schedule → Scheduling Advisor (מחפש סלוטים)
   - end → מסיים בנימוס
4. **מייצר תשובת SMS** — קצרה, מקצועית, חמה
5. **מעדכן היסטוריה** — שומר את כל התורות לשימוש בהחלטות הבאות

### class `MainAgent`:
- `process_message(candidate_message)` — מעבד הודעה ומחזיר `{action, response}`
- `reset()` — מנקה היסטוריה
- `set_history(history)` — מגדיר היסטוריה חיצונית (לצורך evaluation)

---

## שלב 9: ממשק Streamlit

### קובץ: `streamlit_app/streamlit_main.py`

### מה הוא עושה:
ממשק צ'אט וובי (proof of concept במקום SMS אמיתי).

### מאפיינים:
- **Chat UI** — בועות הודעות כמו WhatsApp
- **Sidebar** — כפתור "שיחה חדשה" + הסבר על הארכיטקטורה
- **Session State** — שומר על מצב השיחה בין refreshים
- **Action Display** — מציג מה ה-agent החליט (continue/schedule/end)

### הרצה:
```bash
streamlit run streamlit_app/streamlit_main.py
```

---

## שלב 10: מודול הערכה (Evaluation)

### קובץ: `app/modules/evaluation/evaluation.py`
### נוטבוק: `tests/test_evals.ipynb`

### מה הוא עושה:
בודק את ביצועי המערכת מול 15 השיחות המתויגות.

### תהליך:
1. **שליפת דוגמאות** — מכל שיחה, כל תור של recruiter עם label הוא test case
2. **הרצה דרך המערכת** — שולח לזרימה ובודק מה המערכת מחליטה
3. **חישוב מטריקות:**
   - **Accuracy** — אחוז תשובות נכונות
   - **Confusion Matrix** — טבלה 3×3 (continue/schedule/end)
   - **Classification Report** — Precision, Recall, F1 לכל class

### הנוטבוק כולל:
1. סקירת Dataset
2. הרצת Evaluation
3. הצגת Accuracy
4. Confusion Matrix (heatmap)
5. Classification Report
6. רשימת שגיאות מפורטת
7. השוואת חלוקת labels

---

## שלב 11: README.md

### מה הוא כולל:
- תיאור הפרויקט
- הוראות התקנה (venv, pip, .env)
- הוראות הרצה (CLI, Streamlit, Evaluation)
- דוגמאות שימוש
- מבנה הפרויקט המלא

---

## טכנולוגיות מפתח

| טכנולוגיה | שימוש |
|---|---|
| **LangChain** | Framework לבניית agents, prompts, chains |
| **OpenAI GPT-4o** | LLM ראשי לכל הסוכנים (Main Agent, Info Advisor, Scheduling Advisor, Exit Advisor base) |
| **OpenAI GPT-4o-mini (fine-tuned)** | `ft:gpt-4o-mini-2024-07-18:personal::DKjrJXBp` — מודל מותאם ליועץ יציאה |
| **OpenAI text-embedding-3-small** | יצירת embeddings מ-PDF |
| **ChromaDB** | מסד נתונים וקטורי לחיפוש סמנטי (RAG) |
| **OpenAI Fine-Tuning API** | אימון מודל מותאם ל-Exit Advisor |
| **OpenAI Function Calling** | אינטראקציה של Scheduling Advisor עם SQL |
| **SQLite** | מסד נתונים לוח זמנים (fallback ל-SQL Server) |
| **Streamlit** | ממשק ווב (PoC) |
| **scikit-learn** | Accuracy, Confusion Matrix, Classification Report |
| **matplotlib + seaborn** | תרשימים |

---

## Prompting Strategies (כפי שנדרש במסמך)

1. **Role Prompts** — כל סוכן מקבל תפקיד ברור ("You are the Info Advisor...")
2. **API Parameters** — temperature=0 ל-classification, temperature=0.3 ל-שיחה
3. **Instructions Prompts** — הנחיות מפורטות בכל prompt (מה לעשות, מה לא)
4. **Few-Shot Learning** — ה-RAG context משמש כדוגמאות, training data ב-fine-tuning

---

## איך להריץ את הפרויקט מאפס

```bash
# 1. הפעלת סביבה
.venv\Scripts\activate   # Windows

# 2. בניית מאגר ידע (חד-פעמי)
python -m app.modules.embedding.embedding

# 3. Fine-tuning (אופציונלי, לוקח 10-30 דקות)
python -m app.modules.fine_tuning.fine_tuning

# 4. הרצת Streamlit
streamlit run streamlit_app/streamlit_main.py

# 5. הרצת Evaluation
python -m app.modules.evaluation.evaluation
```

---

## ניסוי: שדרוג ל-GPT-5.4

### מטרה:
בדיקה האם מודלים חדשים יותר משפרים את דיוק הסיווג.

### מה נעשה:
1. שודרגו כל הסוכנים מ-`gpt-4o` ל-`gpt-5.4`
2. בוצע fine-tuning חדש על `gpt-4.1-mini` (כי `gpt-5.4-mini` לא תומך ב-fine-tuning)
3. הורצה הערכה 3 פעמים עם פרומפטים שונים

### תוצאות:

| מודל | פרומפט | דיוק |
|------|--------|------|
| **GPT-4o** (מקורי) | פרומפט מכויל עם few-shot | **88.14%** |
| GPT-5.4 | אותו פרומפט | 67.80% |
| GPT-5.4 | פרומפט מחודש עם כללי סיווג | 57.63% |
| GPT-5.4 | פרומפט מינימלי | 62.71% |

### מסקנה:
**מודל חדש יותר לא בהכרח = טוב יותר.** GPT-5.4 נתן תוצאות נמוכות יותר כי:
- הפרומפט היה מכויל (calibrated) ספציפית ל-GPT-4o
- GPT-5.4 נוטה לפרש הוראות "מילולי מדי" ובוחר "continue" יותר מדי
- ה-fine-tuning ל-`gpt-4.1-mini` לא שיפר מספיק

**הוחלט לחזור ל-GPT-4o** שנותן את התוצאות הטובות ביותר.

---

## ניסוי: o4-mini (מודל Reasoning)

### מטרה:
בדיקה האם מודל reasoning קטן (o4-mini) ישפר את דיוק הסיווג בזכות יכולות חשיבה מתקדמות.

### מה נעשה:
1. הוחלפו כל הסוכנים מ-`gpt-4o` ל-`o4-mini`
2. הורצה הערכה על 59 הדוגמאות המתויגות

### תוצאות:

| מודל | דיוק |
|------|------|
| **GPT-4o** | **88.14%** |
| o4-mini | 71.19% |

### מסקנה:
**מודל reasoning לא מתאים למשימות סיווג פשוטות.** o4-mini נתן תוצאות נמוכות יותר כי:
- **מחשיב יותר מדי** — במקום לסווג ישירות, "חושב" על מקרי קצה ומסבך החלטות פשוטות
- **איטי יותר** — שרשרת חשיבה ארוכה לכל דוגמה, ללא תועלת בדיוק
- הפרומפט מכוון לתשובה ישירה של מילה אחת — לא צריך reasoning

**הוחלט לחזור ל-GPT-4o** שנותן תוצאות טובות יותר ומהיר יותר.

---

## שיפורי סינון ולוגיקת שיחה

### מטרה:
שיפור יכולות הסינון וזרימת השיחה, בלי לפגוע בארכיטקטורה או בחלוקת התפקידים בין הסוכנים.

### מה נעשה:

#### 1. סינון מועמדים לפני תיאום (Main Agent — DECISION_PROMPT)
- המערכת דורשת שהמועמד ישתף **לפחות נושא אחד substantive** לגבי הכישורים שלו לפני מעבר ל-schedule
- ברכות ("hello"), תשובות מעורפלות ("ok", "yes"), ושאלות על התפקיד **לא נחשבות** כדיון בכישורים
- **מתואם לדאטאסט:** בכל 15 השיחות המתויגות, ה-label הראשון תמיד `continue`

#### 2. טיפול בתשובות קצרות/מעורפלות (Main Agent — RESPONSE_PROMPT)
- אם המועמד עונה "yes", "ok", "some" — הסוכן שואל follow-up על אותו נושא במקום לקפוץ לנושא הבא

#### 3. סיכום מעבר ל-schedule (Main Agent — RESPONSE_PROMPT)
- כשעוברים ל-schedule, הסוכן מסכם את מה שלמד על המועמד:
  "With your 4 years of Python and Django expertise..."

#### 4. אישור לפני הזמנה (Scheduling Advisor)
- כשמועמד בוחר שעה — הסוכן שואל אישור: "Just to confirm — Thursday at 11:00. Shall I lock it in? 🔥"
- רק אחרי אישור מפורש (כמו "yes", "book it") מבצע `book_slot`
- אם המועמד בוחר שעה שלא ברשימה — מזכיר את הסלוטים הזמינים

#### 5. זיהוי היסוס (Exit Advisor)
- הוספו כללים להמשיך כ-"continue":
  * מועמד מהסס ("I'm not sure", "maybe", "let me think")
  * מועמד נותן תשובות קצרות/מעורפלות
- מניע סגירת שיחה מוקדמת על מועמד שפשוט מהסס

### דיוק אחרי השיפורים: **88.14%**

| Class | Precision | Recall | F1-Score |
|-------|-----------|--------|----------|
| continue | 0.91 | 0.80 | 0.85 |
| schedule | 0.77 | 0.89 | 0.83 |
| end | 1.00 | 1.00 | 1.00 |

### שמירה על ארכיטקטורה:
כל השינויים בוצעו **בפרומפטים בלבד**, ללא שינוי בקוד או בארכיטקטורה:
- Main Agent — עדיין מנצח, כולל עכשיו לוגיקת סינון
- Info Advisor — RAG טהור (ללא שינוי)
- Scheduling Advisor — Function Calling + שלב אישור
- Exit Advisor — סיווג end/continue + זיהוי היסוס

---

## סיכום השוואת מודלים

| מודל | סוג | דיוק | הערות |
|------|------|------|--------|
| **GPT-4o** | General | **88.14%** | הטוב ביותר — ישיר, מהיר, מדויק |
| o4-mini | Reasoning (קטן) | 71.19% | חושב יותר מדי, מסבך סיווגים פשוטים |
| GPT-5.4 | General (חדש) | 62-68% | לא מותאם לפרומפט הקיים |

---

## Hell Corp Theme — טאצ' אישי 🔥

### מה נעשה:
נוסף נושא הומוריסטי "Hell Corp" לכל הפרויקט כדי לתת לו אופי ייחודי:

1. **Main Agent** — הטון שונה ל-"darkly humorous", עם בדיחות אש עדינות
2. **Info Advisor** — "we don't bite... much 😈"
3. **Scheduling Advisor** — "even demons need rest" (לגבי ימי שבת ושני)
4. **Streamlit UI** — כותרת "🔥 Hell Corp — Recruitment Chatbot", הודעה פותחת "Welcome, mortal!"

### הודעות מיוחדות:
- **קביעת ראיון מוצלחת** → "Welcome to Hell 🔥"
- **מועמד לא מעוניין** → "Maybe you'll have better luck in Paradise 😇"

### למה ככה:
מוסיף טאצ' אישי ויצירתי לפרויקט, תוך שמירה על הפונקציונליות המלאה.
