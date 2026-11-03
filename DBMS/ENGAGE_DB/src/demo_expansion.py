"""Additional fictional, reproducible demo rows. Safe to run repeatedly without deleting data."""
from db import PostgresDB

# 25 additional students: total 35. JEE remains 21/35 = 60% in a fresh sample DB.
GOALS = (["JEE"] * 15 + ["NEET"] * 4 + ["GATE"] * 2 +
         ["UPSC", "CAT", "IELTS", "CUET"])
NAMES = [
    "Aditi Rao", "Kavya N", "Vikram S", "Rohit P", "Sahana R", "Mithun B", "Priya A", "Kiran T",
    "Lakshmi M", "Nikhil K", "Sanjana V", "Harish G", "Keerthana L", "Deepak N", "Ananya S",
    "Meghana D", "Arjun R", "Varsha P", "Naveen S", "Madhavi K", "Vishnu V", "Ira N",
    "Surya J", "Farah M", "Yash P"
]
CITIES = ["Chennai", "Bengaluru", "Hyderabad", "Coimbatore", "Madurai", "Mumbai", "Delhi", "Pune"]
COLORS = ["#e11d48", "#f97316", "#8b5cf6", "#2563eb", "#0891b2", "#16a34a", "#db2777"]
USERS = []
PROFILES = []
for i,(name, goal) in enumerate(zip(NAMES, GOALS), 11):
    uid = f"U{i:03d}"
    stage = "College" if goal in {"GATE", "CAT", "UPSC", "IELTS"} else "Class 12"
    budget = (700 + ((i*431) % 6500))
    city = CITIES[(i-11) % len(CITIES)]
    USERS.append((uid, name, f"demo.student{i:02d}", f"demo{i:02d}@engage.local", f"{goal} learner exploring affordable learning courses", city, COLORS[i % len(COLORS)]))
    PROFILES.append((uid, stage, goal, budget, "balanced", ("online", "offline", "hybrid")[i % 3], "English", city))

# Topic tags exactly match learning_resource.topic for real-looking but honest topic-level scoring.
EXTRA_POST_SPECS = [
    ("NEET","biology","NEET Biology revision marathon: NCERT diagrams, genetics and daily practice. #NEET #Biology"),
    ("NEET","biology","NEET quick biology checklist with active recall and chapter PYQs. #NEET #Biology"),
    ("NEET","mock_test","NEET mock test analysis: diagnose mistakes before another attempt. #NEET #MockTest"),
    ("NEET","chemistry","NEET Chemistry formula sheet and timed practice. #NEET #Chemistry"),
    ("GATE","computer_science","GATE CS algorithms, OS and DBMS preparation path. #GATE #CS"),
    ("GATE","computer_science","GATE previous year coding and operating systems practice. #GATE #CS"),
    ("GATE","mock_test","GATE subject-wise mini test and score improvement planning. #GATE #MockTest"),
    ("UPSC","current_affairs","UPSC daily current affairs with source verification and notes. #UPSC #CurrentAffairs"),
    ("UPSC","prelims","UPSC Prelims practice questions and revision calendar. #UPSC #Prelims"),
    ("UPSC","mains","UPSC Mains answer writing every week, with feedback. #UPSC #Mains"),
    ("CAT","quant","CAT quantitative aptitude: arithmetic, algebra and timers. #CAT #Quant"),
    ("CAT","verbal","CAT verbal ability and reading comprehension strategy. #CAT #Verbal"),
    ("CAT","mock_test","CAT mock analysis and accuracy versus speed trade-off. #CAT #MockTest"),
    ("IELTS","speaking","IELTS speaking fluency and interview practice every day. #IELTS #Speaking"),
    ("IELTS","writing","IELTS writing Task 2 peer review and essay templates. #IELTS #Writing"),
    ("CUET","general_test","CUET general test exam plan and practice question sets. #CUET #GeneralTest"),
    ("CUET","language","CUET language reading comprehension and grammar. #CUET #Language"),
    ("JEE","physics","JEE rotating mechanics problems and PYQ discussion. #JEE #Physics"),
    ("JEE","maths","JEE maths practice: calculus and coordinate geometry. #JEE #Maths"),
    ("JEE","mock_test","JEE full mock test review, chapter by chapter. #JEE #MockTest"),
    ("NEET","biology","NEET cell biology and physiology in one revision session. #NEET #Biology"),
    ("GATE","computer_science","GATE CS compiler theory and data structures rapid revision. #GATE #CS"),
    ("CAT","quant","CAT DI and LR logical puzzles for beginners. #CAT #Quant"),
    ("CUET","general_test","CUET university admissions, entrance calendar and planning. #CUET"),
    ("IELTS","speaking","IELTS speaking mock interview with partner feedback. #IELTS #Speaking"),
]

# provider values are fictitious demo examples, not real product offers.
EXTRA_RESOURCES = [
    ("NEET","biology","BioSprint 360","NEET Biology Active Recall",499,8.7,"online"),
    ("NEET","biology","MedLearn Demo","NEET NCERT Chapter Booster",0,8.5,"online"),
    ("NEET","mock_test","MedMock Demo","NEET Targeted Mock Tests",799,9.0,"hybrid"),
    ("NEET","chemistry","ChemQuest Demo","NEET Chemistry Practice Camp",999,8.3,"online"),
    ("GATE","computer_science","GateBridge Demo","GATE CS Core Concepts",1299,9.2,"online"),
    ("GATE","computer_science","Algorithmia Demo","GATE DSA and OS Revision",549,8.5,"online"),
    ("GATE","mock_test","GateMock Demo","GATE CS Test Series",999,8.8,"online"),
    ("UPSC","current_affairs","CivicNotes Demo","UPSC Daily Current Affairs",399,8.1,"online"),
    ("UPSC","prelims","PrelimsPilot Demo","UPSC Prelims MCQ Bank",599,8.5,"online"),
    ("UPSC","mains","AnswerCraft Demo","UPSC Mains Answer Review",1450,8.9,"hybrid"),
    ("CAT","quant","AptitudeBox Demo","CAT Quant Foundations",749,8.8,"online"),
    ("CAT","verbal","ReadingRoom Demo","CAT VARC Reading Sprint",649,8.7,"online"),
    ("CAT","mock_test","MBAPath Demo","CAT Adaptive Mocks",1100,8.4,"online"),
    ("IELTS","speaking","SpeakPro Demo","IELTS Speaking Workshop",950,8.6,"hybrid"),
    ("IELTS","writing","EssayForge Demo","IELTS Writing Task Mastery",699,8.8,"online"),
    ("CUET","general_test","CampusGate Demo","CUET General Test Crash Course",450,8.0,"online"),
    ("CUET","language","LanguageLaunch Demo","CUET English Language Practice",299,8.1,"online"),
    ("JEE","maths","CalcMaster Demo","JEE Calculus and Math PYQs",1299,8.9,"online"),
    ("JEE","physics","MechanicsLab Demo","JEE Physics Practice Studio",1799,9.0,"hybrid"),
    ("JEE","mock_test","TestTracker Demo","JEE Weekly Mock Review",249,8.4,"online"),
]


def insert_extra(db=None):
    db = db or PostgresDB()
    # Schema should exist. No truncation or updates to existing records.
    with db.connection() as conn:
        with conn.cursor() as cur:
            for uid, name, handle, email, bio, city, color in USERS:
                cur.execute("""INSERT INTO engage_user
                    (user_id,user_name,full_name,handle,email,bio,city,avatar_color)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (uid,name,name,handle,email,bio,city,color))
            for prof in PROFILES:
                cur.execute("""INSERT INTO student_profile
                    (user_id,academic_stage,exam_goal,max_monthly_budget,budget_preference,preferred_mode,language_preference,city)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING""", prof)
            # Posts published across 7 different goals, with independent engagement counters.
            for j,(goal,topic,caption) in enumerate(EXTRA_POST_SPECS,1):
                pid = f"P{100+j:03d}"
                creator = f"U{11 + (j-1)%25:03d}"
                cur.execute("""INSERT INTO post
                    (post_id,user_id,caption,content_type,genre,post_date,language,location,created_at,visual_seed,media_url)
                    VALUES (%s,%s,%s,'image','education',CURRENT_DATE,'English','Student Hub',NOW(),%s,%s)
                    ON CONFLICT (post_id) DO NOTHING""",
                    (pid,creator,caption,j,'/static/assets/study_table.svg'))
                cur.execute("""INSERT INTO post_learning_signal(post_id,exam_goal,topic,signal_type)
                    VALUES (%s,%s,%s,'study_resource') ON CONFLICT (post_id) DO NOTHING""", (pid,goal,topic))
                htag=f"#{goal}"
                hid=f"HX{j:03d}"
                cur.execute("""INSERT INTO hashtag(hashtag_id,hashtag_name,purpose)
                    VALUES (%s,%s,'exam_goal') ON CONFLICT (hashtag_name) DO NOTHING""", (hid,htag))
                cur.execute("""INSERT INTO post_hashtag(post_id,hashtag_id)
                    SELECT %s,hashtag_id FROM hashtag WHERE hashtag_name=%s
                    ON CONFLICT DO NOTHING""", (pid,htag))
                # deterministic differentiated activity volume ensures rankings are meaningful.
                # NEET, GATE and CAT are intentionally competitive in the demo leaderboard.
                audience = 5 + (j*7)%19
                if goal=='NEET': audience += 5
                if goal=='GATE': audience += 4
                if goal=='CAT': audience += 3
                for k in range(audience):
                    actor=f"U{11 + (j + k)%25:03d}"
                    cur.execute("INSERT INTO likes(post_id,user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",(pid,actor))
                    if k%2==0:
                        cur.execute("INSERT INTO saved(post_id,user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",(pid,actor))
                    if k%3==0:
                        cur.execute("INSERT INTO post_shares(post_id,user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",(pid,actor))
                    if k%5==0:
                        cur.execute("INSERT INTO reposts(post_id,user_id,text_highlight) VALUES (%s,%s,'Interesting study resource') ON CONFLICT (post_id,user_id) DO NOTHING",(pid,actor))
                    if k%4==0:
                        cid = f"CX{j:03d}{k:02d}"
                        cur.execute("""INSERT INTO comments(comment_id,comment_text,sentiment,user_id,post_id,created_at)
                            VALUES (%s,%s,'Positive',%s,%s,NOW()) ON CONFLICT (comment_id) DO NOTHING""",
                            (cid,'Helpful demo course discussion',actor,pid))
                cur.execute("""INSERT INTO reach(reach_id,post_id,impressions,unique_reach)
                    VALUES (%s,%s,%s,%s) ON CONFLICT (post_id) DO NOTHING""",
                    (f"RX{j:03d}",pid,1500+j*200,1100+j*140))
            for j,(goal,topic,provider,title,price,quality,mode) in enumerate(EXTRA_RESOURCES,1):
                rid=f"RD{j:03d}"
                cur.execute("""INSERT INTO learning_resource
                    (resource_id,provider_name,title,exam_goal,topic,resource_type,delivery_mode,monthly_cost,quality_score,scholarship_available,verified,description)
                    VALUES (%s,%s,%s,%s,%s,'demo_course',%s,%s,%s,FALSE,FALSE,%s)
                    ON CONFLICT (resource_id) DO NOTHING""",
                    (rid,provider,title,goal,topic,mode,price,quality,
                     'Fictional course listing for the ENGAGE PostgreSQL demo.'))
        conn.commit()
    return {"new_students":len(USERS),"new_posts":len(EXTRA_POST_SPECS),"new_resources":len(EXTRA_RESOURCES)}

if __name__ == '__main__':
    print('ENGAGE expanded demo data:',insert_extra())
